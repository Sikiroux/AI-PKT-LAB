"""Jobs locaux, catalogue et fichiers de labs séparés des sites de tickets."""
import json,os,random,subprocess,sys,threading,uuid
from pathlib import Path
import timers
ROOT=Path(__file__).resolve().parent
class Generator:
 def __init__(self):
  self.root=ROOT/'labs';self.root.mkdir(exist_ok=True);self.lock=threading.RLock()
  self.catalogue=json.loads(subprocess.check_output([sys.executable,str(ROOT/'lab_engine/web_worker.py'),'catalogue'],text=True,encoding='utf-8'))
 def jobs(self):
  with self.lock:
   out=[]
   for p in self.root.glob('*/job.json'):
    try:
     d=json.loads(p.read_text(encoding='utf-8'))
     if d['status']=='running' and d['id'] not in getattr(self,'active',set()):d['status']='interrupted';d['error']='Génération interrompue. Crée un nouveau lab.'
     out.append(d)
    except (ValueError,OSError):pass
   return sorted(out,key=lambda d:d['created'],reverse=True)
 def start(self,data):
  mode=data.get('mode');level=int(data.get('level',1));count=int(data.get('count',1));seed=int(random.SystemRandom().randrange(10**9) if data.get('seed') in (None,'') else data['seed'])
  if mode not in ('atelier','depannage','mixte','reproduction') or not 1<=level<=5 or not 1<=count<=5 or not 0<=seed<10**9:raise ValueError('Options du générateur invalides.')
  if data.get('address_family') not in (None,'10','172','192'):raise ValueError('Famille IPv4 privée invalide.')
  site_code=str(data.get('site_code','AG1')).upper()
  import re
  if not re.fullmatch(r'[A-Z][A-Z0-9]{1,5}',site_code):raise ValueError('Code de site invalide (2 à 6 caractères).')
  eligible=[s for s in self.catalogue if s['mode']==mode and s['level']<=level]
  if data.get('scenario') not in (None,'','random'):eligible=[s for s in eligible if s['id']==data['scenario']]
  if not eligible:raise ValueError('Aucun scénario compatible avec ce mode et ce niveau.')
  chosen=random.Random(seed).choice(eligible)
  import time
  ident=uuid.uuid4().hex;folder=self.root/ident;folder.mkdir()
  job=dict(id=ident,title=str(data.get('ticket_title') or chosen['title'])[:180],mode=mode,level=level,count=count,seed=seed,status='running',created=time.strftime('%Y-%m-%d %H:%M:%S'),files=[])
  with self.lock:
   if any(j['status']=='running' for j in self.jobs()):raise ValueError('Une génération est déjà en cours. Attends sa fin.')
   if not hasattr(self,'active'):self.active=set()
   self.active.add(ident);self.save(job)
  req=dict(site_code=site_code,address_family=data.get('address_family'),folder=str(folder),scenario=chosen['id'],seed=seed,level=level,count=count,ticket_title=str(data.get('ticket_title',''))[:180])
  threading.Thread(target=self.work,args=(job,req),daemon=True).start();return job
 def save(self,job):
  path=self.root/job['id']/'job.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(job,ensure_ascii=False),encoding='utf-8');os.replace(tmp,path)
 def work(self,job,req):
  try:
   result=subprocess.run([sys.executable,str(ROOT/'lab_engine/web_worker.py'),'generate'],input=json.dumps(req),capture_output=True,text=True,encoding='utf-8',timeout=600)
   if result.returncode:raise RuntimeError(result.stderr[-1500:] or 'Génération impossible')
   job.update(json.loads(result.stdout));job['status']='done'
  except Exception as e:job.update(status='failed',error=str(e))
  finally:
   with self.lock:self.save(job);self.active.discard(job['id'])
 def file(self,ident,name):
  if not isinstance(ident,str) or len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('Lab inconnu')
  job=json.loads((self.root/ident/'job.json').read_text(encoding='utf-8'))
  if job['status']!='done' or name not in job['files']:raise ValueError('Fichier non disponible')
  return self.root/ident/name
 def timer(self,data):
  ident=data.get('id');cmd=data.get('timer_action')
  # Reuse the same identity and completed-job validation as downloads.
  self.file(ident,'lab.pka')
  with self.lock:
   job=json.loads((self.root/ident/'job.json').read_text(encoding='utf-8'));timer=job.get('timer')
   if cmd=='configure':
    if timer and timer.get('started'):raise ValueError('Durée verrouillée après le démarrage.')
    job['timer']=timers.configure(data.get('minutes',0),data.get('mode','training'))
   else:
    if not timer:raise ValueError('Configure le chronomètre avant de démarrer.')
    timers.operate(timer,cmd)
   self.save(job);return job
 def open(self,ident,name):
  p=self.file(ident,name)
  if os.name!='nt' or p.suffix not in ('.pkt','.pka'):raise ValueError('Ouverture Packet Tracer disponible sous Windows pour les fichiers pkt/pka.')
  os.startfile(str(p));return {'message':'Ouverture du lab demandée. Ce lab est distinct du site de tickets : rouvre le site avant de reprendre ses tickets.'}
