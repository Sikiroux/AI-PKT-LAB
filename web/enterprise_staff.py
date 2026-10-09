"""Effectif reproductible : comptes et postes restent deux identités distinctes."""
import hashlib
import random
DEPARTMENTS=('Comptabilité','Commercial','Ressources humaines','Direction','Accueil','Opérations')
FIRST=('Mina','Camille','Nora','Samir','Hugo','Alex','Lina','Adam','Sofia','Lucas','Emma','Karim','Sarah','Noé','Jade','Yanis','Léa','Thomas','Inès','Mehdi','Zoé','Louis','Clara','Rayan','Eva','Paul','Aya','Nathan','Julie','Malik')
LAST=('Martin','Bernard','Diallo','Moreau','Laurent','Dubois','Petit','Robert','Leroy','Roux','Nguyen','Garcia','Durand','Simon','Lopez','Michel','Lefevre','Ali','David','Bertrand','Sow','Richard','Girard','Andre','Mercier','Dupont','Lambert','Bonnet','Francois','Legrand')
def generate(seed):
    rng=random.Random(hashlib.sha256((str(seed)+':staff:v1').encode()).hexdigest())
    first=list(FIRST);last=list(LAST);rng.shuffle(first);rng.shuffle(last)
    return [dict(index=i+1,display_name=first[i]+' '+last[i],username='u'+str(i+1).zfill(3),department=DEPARTMENTS[i//5],activity=('Traiter les dossiers partagés','Préparer les propositions','Gérer les dossiers salariés','Suivre les indicateurs','Accueillir les visiteurs','Préparer les commandes')[i//5]) for i in range(30)]
