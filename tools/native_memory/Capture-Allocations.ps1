#requires -Version 5.1
param([string]$DebugTools)
$ErrorActionPreference='Stop'
Write-Host '[1/6] Verification des droits et des outils Microsoft...';
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Lance ce script dans PowerShell 64 bits en administrateur : GFlags doit activer puis restaurer le suivi des piles.'}
if(-not [Environment]::Is64BitProcess){throw 'PowerShell 64 bits requis.'}
if(-not $DebugTools){$DebugTools=Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\Debuggers\x64'}
$gflags=Join-Path $DebugTools 'gflags.exe';$umdh=Join-Path $DebugTools 'umdh.exe';$cdb=Join-Path $DebugTools 'cdb.exe'
if(!(Test-Path $gflags) -or !(Test-Path $umdh)){throw 'Installe Debugging Tools for Windows (SDK Windows), puis relance. Aucun suivi active. Tu peux preciser -DebugTools avec le dossier x64.'}
Write-Host ('Outils trouves : '+$DebugTools)
Write-Host '[2/6] Verification de la fermeture de NetOps et Packet Tracer...'
if(@(Get-Process -Name PacketTracer,PacketTracer8,PacketTracer9 -ErrorAction SilentlyContinue).Count){throw 'Sauvegarde puis ferme toutes les fenetres Packet Tracer avant cette capture.'}
try{$null=Invoke-RestMethod 'http://127.0.0.1:8765/memory-suite' -TimeoutSec 2;throw 'NetOps est deja ouvert. Ferme-le avant cette capture.'}catch{if($_.Exception.Message -like 'NetOps est deja*'){throw}}
$out=Join-Path $root ('diagnostics-allocations\capture-'+(Get-Date -Format 'yyyyMMdd-HHmmss'));New-Item -ItemType Directory -Path $out -Force|Out-Null
$state=[ordered]@{kind='native_heap_capture';started=(Get-Date).ToString('o');phase='preparing';snapshots=@();errors=@();flag_added=$false;flag_restored=$false;modules=@()}
function Save-State {$state|ConvertTo-Json -Depth 12|Set-Content (Join-Path $out 'capture.json') -Encoding UTF8}
function Run-Tool([string]$Exe,[string[]]$ToolArgs,[string]$Name){
 $std=Join-Path $out ($Name+'.stdout.txt');$err=Join-Path $out ($Name+'.stderr.txt')
 $proc=Start-Process -FilePath $Exe -ArgumentList $ToolArgs -PassThru -WindowStyle Hidden -RedirectStandardOutput $std -RedirectStandardError $err
 # Keep the native process handle open before a short-lived tool exits.
 $nativeHandle=$proc.Handle
 if(-not $proc.WaitForExit(120000)){$proc.Kill();throw "$Name : delai de 120 secondes depasse."}
 $proc.WaitForExit();$exitCode=$proc.ExitCode
 if($null -eq $exitCode){throw "$Name : code de sortie indisponible, voir les journaux."}
 if($exitCode -ne 0){throw "$Name : erreur $exitCode, voir les journaux."}
}
function Snapshot([string]$Name,[int]$TargetId){
 $file=Join-Path $out ($Name+'.txt');Write-Host "Capture des allocations : $Name (PID $TargetId)"
 Run-Tool -Exe $umdh -ToolArgs @("-p:$TargetId",('-f:"'+$file+'"')) -Name $Name
 if(!(Test-Path $file) -or (Get-Item $file).Length -eq 0){throw 'UMDH : aucune capture exploitable produite.'}
 if(-not (Select-String -Path $file -Pattern 'BackTrace' -Quiet)){throw 'UMDH ne fournit pas de piles BackTrace ; conserver les journaux pour analyse.'}
 $state.snapshots+=@{name=$Name;pid=$TargetId;time=(Get-Date).ToString('o');file=(Split-Path $file -Leaf);cycles=$d.cycles;diagnostic_elapsed=$d.elapsed};Save-State
}
$reg='HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\PacketTracer.exe'
$oldFlag=(Get-ItemProperty $reg -Name GlobalFlag -ErrorAction SilentlyContinue).GlobalFlag
$bits=0
if($null -ne $oldFlag){if($oldFlag -is [string]){$bits=[Convert]::ToUInt32(($oldFlag -replace '^0x',''),16)}else{$bits=[uint32]$oldFlag}}
$state.original_global_flag=$oldFlag
$previousSymbols=$env:_NT_SYMBOL_PATH;$previousNative=$env:NETOPS_NATIVE_MEMORY_PROFILE
try{
 Write-Host '[3/6] Preparation du suivi des allocations (UST)...'
 if(($bits -band 0x1000) -eq 0){$state.flag_added=$true;Save-State;Run-Tool -Exe $gflags -ToolArgs @('/i','PacketTracer.exe','+ust') -Name 'enable-ust'}
 $env:_NT_SYMBOL_PATH='srv*'+(Join-Path $out 'symbols')+'*https://msdl.microsoft.com/download/symbols'
 $env:NETOPS_NATIVE_MEMORY_PROFILE='1'
 $launcher=Join-Path $root 'LANCER-DIAGNOSTIC-COMPLET.bat'
 Write-Host '[4/6] Ouverture de NetOps et de la copie Packet Tracer...'
 $null=Start-Process -FilePath $env:ComSpec -ArgumentList ('/d /c ""{0}""' -f $launcher) -WorkingDirectory $root -PassThru
 $state.phase='waiting_initial_inventory';Save-State;$deadline=(Get-Date).AddMinutes(12);$targetId=0;$seen=$false;$mid=$false;$end=$false
 $lastProgress=[datetime]::MinValue;$launchTime=Get-Date;$httpSeen=$false;$startupCaptured=$false
 while((Get-Date) -lt $deadline){
  if(((Get-Date)-$lastProgress).TotalSeconds -ge 10){Write-Host ('[5/6] Etat : '+$state.phase+' ; captures : '+$state.snapshots.Count);$lastProgress=Get-Date}
  if(-not $httpSeen -and ((Get-Date)-$launchTime).TotalSeconds -ge 120){throw 'NetOps ne repond pas apres deux minutes. Consulte sa fenetre de demarrage.'}
  try{$d=Invoke-RestMethod 'http://127.0.0.1:8765/memory-diagnostic' -TimeoutSec 3;$suite=Invoke-RestMethod 'http://127.0.0.1:8765/memory-suite' -TimeoutSec 3;$httpSeen=$true}catch{Start-Sleep -Seconds 2;continue}
  # Capture startup thread stacks before the suite's 90-second deadline.
  if(-not $seen -and -not $startupCaptured -and ((Get-Date)-$launchTime).TotalSeconds -ge 45){
   $startupProcess=Get-Process -Name PacketTracer -ErrorAction SilentlyContinue|Sort-Object StartTime -Descending|Select-Object -First 1
   if($startupProcess -and (Test-Path $cdb)){
    $startupCaptured=$true
    Write-Host 'Releve des piles de demarrage (attachement non invasif)...'
    $state.startup_pid=$startupProcess.Id;Save-State
    try{Run-Tool -Exe $cdb -ToolArgs @('-pv','-p',([string]$startupProcess.Id),'-c','".sympath;lm;~* kb;qd"') -Name 'startup-stacks'}catch{$state.errors+=('Piles demarrage : '+$_.Exception.Message);Save-State}
   }
  }
  if(-not $seen -and $d.memory_after_initial_inventory){
   $main=$d.memory_after_initial_inventory.processes|Sort-Object private_bytes -Descending|Select-Object -First 1
   $targetId=[int]$main.pid;$state.target_pid=$targetId
   try{$state.modules=@((Get-Process -Id $targetId).Modules|ForEach-Object{@{name=$_.ModuleName;base=('0x{0:x}' -f $_.BaseAddress.ToInt64());size=$_.ModuleMemorySize}})}catch{$state.errors+=('Modules : '+$_.Exception.Message)}
   $state.phase='capturing';Snapshot '01-after-initial' $targetId;$seen=$true
  }
  if($seen -and -not $mid -and $d.elapsed -ge 90 -and $d.running){Snapshot '02-during-reads' $targetId;$mid=$true}
  if($seen -and -not $end -and -not $d.running){Snapshot '03-after-reads' $targetId;$end=$true
   Run-Tool -Exe $umdh -ToolArgs @((('"'+(Join-Path $out '01-after-initial.txt')+'"')),(('"'+(Join-Path $out '03-after-reads.txt')+'"'))) -Name 'comparison'
  }
  if($suite.report_file -and -not $suite.running){
   $report=Invoke-RestMethod 'http://127.0.0.1:8765/memory-suite/report' -TimeoutSec 3
   $report|ConvertTo-Json -Depth 60|Set-Content (Join-Path $out 'netops-report.json') -Encoding UTF8
   if(-not $seen -or -not $end){throw ('Diagnostic termine sans inventaire exploitable : '+$suite.error+'. Consulter startup-stacks.stdout.txt si present.')}
   $state.phase=if($suite.error){'diagnostic_failed'}else{'completed'};break
  }
  Start-Sleep -Seconds 2
 }
 if($state.phase -notin @('completed','diagnostic_failed')){throw 'Capture non terminee apres 12 minutes. Arrete le diagnostic depuis sa fenetre.'}
}catch{$state.errors+=$_.Exception.Message;$state.phase='error';Write-Host $_.Exception.Message -ForegroundColor Red}
finally{
 Write-Host '[6/6] Restauration du suivi et creation du ZIP...'
 if($state.flag_added){try{Run-Tool -Exe $gflags -ToolArgs @('/i','PacketTracer.exe','-ust') -Name 'restore-ust';$state.flag_restored=$true}catch{$state.errors+=('RESTAURATION UST ECHOUEE : '+$_.Exception.Message);Write-Host 'Execute gflags.exe /i PacketTracer.exe -ust pour retirer le suivi ajoute.' -ForegroundColor Red}}else{$state.flag_restored=$true}
 $env:_NT_SYMBOL_PATH=$previousSymbols;$env:NETOPS_NATIVE_MEMORY_PROFILE=$previousNative;Save-State
 try{Compress-Archive -Path (Join-Path $out '*.txt'),(Join-Path $out '*.json') -DestinationPath ($out+'.zip') -Force;Write-Host ('Fichier a envoyer : '+$out+'.zip')}catch{Write-Host ('Rapport conserve dans '+$out)}
}
