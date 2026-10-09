"""Effectif reproductible : comptes et postes restent deux identités distinctes."""
import hashlib
import random
DEPARTMENTS=('Comptabilité','Commercial','Ressources humaines','Direction','Accueil','Opérations')
FIRST=('Mina','Camille','Nora','Samir','Hugo','Alex','Lina','Adam','Sofia','Lucas','Emma','Karim','Sarah','Noé','Jade','Yanis','Léa','Thomas','Inès','Mehdi','Zoé','Louis','Clara','Rayan','Eva','Paul','Aya','Nathan','Julie','Malik')
LAST=('Martin','Bernard','Diallo','Moreau','Laurent','Dubois','Petit','Robert','Leroy','Roux','Nguyen','Garcia','Durand','Simon','Lopez','Michel','Lefevre','Ali','David','Bertrand','Sow','Richard','Girard','Andre','Mercier','Dupont','Lambert','Bonnet','Francois','Legrand')
DEFAULT_DEPENDENCIES={department:['directory','files','dns','printing']+(['ftp'] if department in ('Commercial','Opérations') else []) for department in DEPARTMENTS}

def service_users(state, service):
    people={p['display_name']:p for p in state.get('staff',[]) if p.get('display_name')}
    affected=[];known=False
    for serial,profile in state.get('client_workspaces',{}).items():
        person=people.get(profile.get('requester'))
        if not person:continue
        known=True
        dependencies=person.get('service_dependencies',DEFAULT_DEPENDENCIES.get(person.get('department'),[]))
        if service in dependencies:affected.append(serial)
    return sorted(affected),known

def generate(seed):
    rng=random.Random(hashlib.sha256((str(seed)+':staff:v1').encode()).hexdigest())
    first=list(FIRST);last=list(LAST);rng.shuffle(first);rng.shuffle(last)
    return [dict(index=i+1,display_name=first[i]+' '+last[i],username='u'+str(i+1).zfill(3),department=DEPARTMENTS[i//5],service_dependencies=list(DEFAULT_DEPENDENCIES[DEPARTMENTS[i//5]]),activity=('Traiter les dossiers partagés','Préparer les propositions','Gérer les dossiers salariés','Suivre les indicateurs','Accueillir les visiteurs','Traiter les commandes clients')[i//5]) for i in range(30)]
