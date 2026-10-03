import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
"""Réponses conservées dans le navigateur, avec export et import JSON."""
import json

def script(key):
 return '''<section><h2>Conserver tes réponses</h2><p id="answerStatus" role="status">Initialisation de la sauvegarde locale…</p>
 <button id="exportAnswers">Exporter mes réponses (JSON)</button>
 <label>Réimporter mes réponses <input id="importAnswers" type="file" accept=".json,application/json"></label>
 <p>La sauvegarde locale dépend du navigateur et de cette feuille. Exporte un fichier pour conserver une copie ou changer de navigateur.</p></section>
 <script>
 (()=>{const key=KEY,fields=[...document.querySelectorAll('textarea')],status=document.getElementById('answerStatus');
 const collect=()=>({version:1,worksheet:key,answers:fields.map(f=>({label:f.getAttribute('aria-label')||'',value:f.value}))});
 function load(data){if(data.version!==1||data.worksheet!==key||!Array.isArray(data.answers)||data.answers.length!==fields.length||data.answers.some(a=>typeof a.value!=='string'||a.value.length>100000))throw Error('Fichier incompatible avec cette feuille.');data.answers.forEach((a,i)=>{fields[i].value=a.value})}
 function save(){try{localStorage.setItem(key,JSON.stringify(collect()));status.textContent='Réponses enregistrées dans ce navigateur.'}catch(e){status.textContent='Sauvegarde locale indisponible : utilise l’export JSON.'}}
 try{const saved=localStorage.getItem(key);if(saved){load(JSON.parse(saved));status.textContent='Réponses précédentes restaurées.'}else status.textContent='Tes réponses seront enregistrées dans ce navigateur.'}catch(e){status.textContent='Sauvegarde locale indisponible ou incompatible : utilise l’export JSON.'}
 fields.forEach(f=>f.addEventListener('input',save));
 document.getElementById('exportAnswers').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(collect(),null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='reponses-netops.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 document.getElementById('importAnswers').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>2000000)throw Error('Fichier trop volumineux.');load(JSON.parse(await file.text()));save()}catch(error){status.textContent=error.message}finally{e.target.value=''}};
 })();
 </script>'''.replace('KEY',json.dumps('netops-answers:'+key))
