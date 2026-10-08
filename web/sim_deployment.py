"""Atelier isolé de déploiement : disque virtuel, aucun IO ou OS réel."""
import copy
import hashlib
import random

IMAGES = [dict(id='pro-base', name='Windows 11 Pro · Socle', edition='Pro', minimum_mib=65536),
          dict(id='pro-office', name='Windows 11 Pro · Bureautique', edition='Pro', minimum_mib=65536),
          dict(id='home', name='Windows 11 Famille · Standard', edition='Famille', minimum_mib=65536)]
LOCALES = ['fr-FR', 'en-GB']
KEYBOARDS = ['fr-FR', 'en-US']


def generate(seed, environment_id):
    rng = random.Random(int.from_bytes(hashlib.sha256((str(seed)+':deployment:v1').encode()).digest(), 'big'))
    capacity = rng.choice([128, 256, 512])*1024
    image = rng.choice(['pro-base', 'pro-office'])
    return dict(version=1, environment_id=environment_id, revision=0, attempt=1, stage='idle',
                station='PC-ATELIER-'+hashlib.sha256(str(seed).encode()).hexdigest()[:4].upper(),
                requirements=dict(image_id=image, locale=rng.choice(LOCALES), keyboard=rng.choice(KEYBOARDS), account='formation'),
                images=copy.deepcopy(IMAGES), image_id=None, media_mounted=False, backup=None,
                disk=dict(capacity_mib=capacity, style=rng.choice(['MBR', 'GPT']), visible=rng.choice([True, False]),
                          partitions=[dict(id='old-os', name='Ancien système et documents', kind='existing', mib=81920, filesystem='NTFS', has_data=True),
                                      dict(id='old-data', name='Données utilisateur', kind='existing', mib=capacity-81920, filesystem='NTFS', has_data=True)]),
                copy_step=0, settings={}, installed=False, history=[])


def evaluate(state):
    os_part = next((p for p in state['disk']['partitions'] if p['kind']=='windows'), None)
    checks = dict(completed=state['stage']=='complete', image=state['image_id']==state['requirements']['image_id'],
                  backup=bool(state['backup']), gpt=state['disk']['style']=='GPT',
                  installed=state['installed'] and bool(os_part and os_part['mib']>=65536),
                  locale=state['settings'].get('locale')==state['requirements']['locale'],
                  keyboard=state['settings'].get('keyboard')==state['requirements']['keyboard'],
                  account=state['settings'].get('account')==state['requirements']['account'])
    return dict(passed=all(checks.values()), checks=checks)


def apply(state, action, payload, revision):
    if type(revision) is not int or revision != state['revision']:
        raise ValueError('L’atelier a changé. Actualise avant de poursuivre.')
    if not isinstance(payload, dict):raise ValueError('Paramètres invalides.')
    d=copy.deepcopy(state)
    def stage(*allowed):
        if d['stage'] not in allowed:raise ValueError('Cette action ne correspond pas à l’étape actuelle.')
    def visible():
        if not d['disk']['visible']:raise ValueError('Aucun disque détecté. Charge le pilote de stockage de formation.')
    if action=='start':stage('idle');d['stage']='media'
    elif action=='mount':
        stage('media');ident=payload.get('image_id')
        if ident not in [i['id'] for i in IMAGES]:raise ValueError('Image de formation inconnue.')
        d.update(image_id=ident,media_mounted=True,stage='boot')
    elif action=='boot':
        stage('boot')
        if payload.get('source')!='usb':raise ValueError('Le démarrage sur le disque lance l’ancien système. Sélectionne le support USB pour installer.')
        d['stage']='setup'
    elif action=='setup':
        stage('setup');d['stage']='disk'
    elif action=='load_driver':stage('disk');d['disk']['visible']=True
    elif action=='backup':
        stage('disk');visible()
        if d['backup'] is None:d['backup']=copy.deepcopy(d['disk']['partitions'])
    elif action=='delete_partition':
        stage('disk');visible();ident=payload.get('partition_id');part=next((p for p in d['disk']['partitions'] if p['id']==ident),None)
        if part is None:raise ValueError('Partition inconnue.')
        if part['has_data'] and not d['backup']:raise ValueError('Sauvegarde les données simulées avant de supprimer cette partition.')
        d['disk']['partitions']=[p for p in d['disk']['partitions'] if p['id']!=ident]
    elif action=='partition':
        stage('disk');visible()
        if d['disk']['partitions']:raise ValueError('Cet atelier demande un disque vierge : supprime les anciennes partitions après sauvegarde.')
        size=payload.get('size_gib')
        if type(size) is not int or size<1 or size*1024+1340>d['disk']['capacity_mib']:raise ValueError('La taille demandée doit tenir sur le disque, avec 1 340 Mio réservés au système.')
        d['disk']['style']='GPT'
        d['disk']['partitions']=[dict(id=i,name=n,kind=k,mib=m,filesystem=f,has_data=False) for i,n,k,m,f in
            [('efi','Système EFI','system',300,'FAT32'),('msr','Réservée Microsoft','system',16,None),
             ('windows','Windows','windows',size*1024,'NTFS'),('recovery','Récupération','system',1024,'NTFS')]]
    elif action=='install':
        stage('disk');visible();p=next((p for p in d['disk']['partitions'] if p['id']==payload.get('partition_id')),None)
        if not p or p['kind']!='windows' or p['filesystem']!='NTFS':raise ValueError('Sélectionne la partition Windows NTFS.')
        image=next(i for i in IMAGES if i['id']==d['image_id'])
        if p['mib']<image['minimum_mib']:raise ValueError('Cette image de formation exige une partition Windows de 64 Gio minimum.')
        d.update(stage='copy',copy_step=0)
    elif action=='advance':
        stage('copy');d['copy_step']+=1
        if d['copy_step']==3:d.update(stage='restart',installed=True)
    elif action=='eject':stage('restart');d['media_mounted']=False
    elif action=='restart':
        stage('restart')
        if d['media_mounted']:raise ValueError('La priorité de cet atelier est USB : retire le support avant le premier démarrage sur disque.')
        d['stage']='oobe'
    elif action=='configure':
        stage('oobe');locale=payload.get('locale');keyboard=payload.get('keyboard');account=payload.get('account')
        if locale not in LOCALES or keyboard not in KEYBOARDS:raise ValueError('Région ou clavier inconnu.')
        if not isinstance(account,str) or not account.strip() or len(account)>64:raise ValueError('Nom du compte de formation requis, 64 caractères maximum.')
        d.update(settings=dict(locale=locale,keyboard=keyboard,account=account.strip()),stage='complete')
    elif action=='reset':
        raise ValueError('Utilise la remise à zéro du contrôleur pour régénérer le disque de formation.')
    else:raise ValueError('Action de déploiement inconnue.')
    d['revision']+=1;d['history'].append(dict(action=action,stage=d['stage'],revision=d['revision']));d['history']=d['history'][-50:]
    return d
