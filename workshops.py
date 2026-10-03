"""Ateliers Packet Tracer : pannes de services et missions à correction manuelle.

Le fichier HTML est le contrat de validation. Aucun verdict automatique n'est
produit pour ces ateliers. Les fonctions utilisent les schémas des templates
fournis ; leur fonctionnement dans le moteur PT 9 reste à tester.
"""
import argparse
import contextlib
import html
import io
import ipaddress
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET

import builder
import ptexplorer
from addressing import private_networks

KINDS = {'fault':'Dépannage','configuration':'Configuration','evolution':'Évolution'}

TOPOLOGIES = {
    'enterprise_services': 'Entreprise : employés, serveurs et invités',
    'wifi_deployment': 'Agence : mise en service Wi-Fi',
    'meraki_branch': 'Agence Meraki : WAN, dashboard et sécurité',
}


class WorkshopLab(builder.PktLab):
    def _pick_template(self, requested_type, template_map):
        # Les anciens modèles DNS ne contiennent pas FTP/messagerie. Préférer
        # le Server-PT complet fourni par le catalogue pour ces ateliers.
        if requested_type.split(':')[-1] in ('Server-PT','AccessPoint-PT','Meraki-MX65W','Meraki-Server'):
            source = Path(__file__).parent / 'templates/packettracer/catalogue_source.xml'
            root = ET.parse(source).getroot()
            return next(d for d in root.findall('.//DEVICE')
                        if d.find('ENGINE/TYPE').get('model') == requested_type.split(':')[-1])
        return super()._pick_template(requested_type, template_map)


def put(parent, path, value):
    for part in path.split('/'):
        child = parent.find(part)
        if child is None:
            child = ET.SubElement(parent, part)
        parent = child
    parent.text = str(value)
    return parent


def engines(root):
    return {d.findtext('ENGINE/NAME'): d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')}


def port(e):
    return next(p for p in e.iter('PORT') if 'copper' in (p.findtext('TYPE') or '').lower())


def configs(e, lines):
    for tag in ('RUNNINGCONFIG', 'STARTUPCONFIG'):
        sec = e.find(tag)
        if sec is None:
            sec = ET.SubElement(e, tag)
        sec.clear()
        for line in lines:
            ET.SubElement(sec, 'LINE').text = line


def dns(e, records):
    s = e.find('DNS_SERVER')
    if s is None:
        s = ET.SubElement(e, 'DNS_SERVER')
    s.clear()
    put(s, 'ENABLED', 1)
    db = ET.SubElement(s, 'NAMESERVER-DATABASE')
    for name, address in records.items():
        rr = ET.SubElement(db, 'RESOURCE-RECORD')
        for tag, value in [('TYPE', 'A-REC'), ('NAME', name), ('TTL', 86400), ('IPADDRESS', address)]:
            put(rr, tag, value)


def dhcp_node(e):
    node = e.find('DHCP_SERVERS/ASSOCIATED_PORTS/ASSOCIATED_PORT/DHCP_SERVER')
    return node if node is not None else e.find('DHCP_SERVER')


def dhcp(e, pools):
    s = dhcp_node(e)
    if s is None:
        raise ValueError('Le template serveur ne contient aucun service DHCP connu')
    put(s, 'ENABLED', 1)
    container = s.find('POOLS')
    if container is None:
        container = ET.SubElement(s, 'POOLS')
    # serverPool est conservé (non éditable dans PT), mais hors des réseaux du lab.
    container.clear()
    default = ET.SubElement(container, 'POOL')
    for tag, value in [('NAME','serverPool'),('NETWORK','0.0.0.0'),('MASK','0.0.0.0'),
                       ('DEFAULT_ROUTER','0.0.0.0'),('START_IP','0.0.0.0'),('END_IP','0.0.0.0'),
                       ('DNS_SERVER','0.0.0.0'),('MAX_USERS',0),('TFTP_ADDRESS','0.0.0.0'),('LEASE_TIME',86400000)]:
        put(default,tag,value)
    for spec in pools:
        pool = ET.SubElement(container, 'POOL')
        net = ipaddress.IPv4Network(spec['network'])
        for tag, value in [('NAME',spec['name']),('NETWORK',str(net.network_address)),
                           ('MASK',str(net.netmask)),('DEFAULT_ROUTER',spec['gateway']),
                           ('START_IP',str(net[100])),('END_IP',str(net[149])),('MAX_USERS',50),
                           ('DNS_SERVER',spec['dns']),('TFTP_ADDRESS',spec['dns']),
                           ('DOMAIN_NAME','entreprise.test'),('LEASE_TIME',86400000),('WLC_ADDRESS','0.0.0.0')]:
            put(pool,tag,value)
        ET.SubElement(pool,'DHCP_POOL_LEASES')


def server_defaults(e):
    for tag in ('HTTP_SERVER','FTP_SERVER','SYSLOG_SERVER','NTP_SERVER','TFTP_SERVER','ACS_SERVER'):
        if e.find(tag) is not None:
            put(e, tag+'/ENABLED', 0)
    if e.find('EMAIL_SERVER') is not None:
        put(e,'EMAIL_SERVER/SMTP_ENABLED',0)
        put(e,'EMAIL_SERVER/POP3_ENABLED',0)
    s=dhcp_node(e)
    if s is not None:
        put(s,'ENABLED',0)
    if e.find('DNS_SERVER') is not None:
        put(e,'DNS_SERVER/ENABLED',0)


def make_topology(name, seed, folder, address_family=None, extra_web_server=False, reference_policy=None):
    """Crée le socle et retourne son arbre XML et ses valeurs attendues."""
    rng = random.Random(seed)
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    lab = WorkshopLab(rng=rng)
    devices, links = {}, []
    octet = rng.randint(20,180)
    family=address_family or '10'
    if family not in ('10','172','192'):raise ValueError('Famille IPv4 privée invalide')
    nets = private_networks(seed, family, octet)
    def host(key, number): return str(nets[key][number])
    def add_host(n, ip, gateway, pos, model='PC-PT', dhcp_client=False, dns_ip=None):
        settings={'ip_address': ip, 'subnet_mask':'255.255.255.0','default_gateway':gateway,
                  'dns_server':dns_ip or ip,'dhcp':dhcp_client}
        lab.add(n,'pc',model,pos,settings=settings)
        devices[n]={'type':'pc','model':model,'ip':ip,'mask':'255.255.255.0','gateway':gateway,
                    'dns':dns_ip or ip,'dhcp':dhcp_client}
    def link(*args):
        lab.add_link(*args); links.append(tuple(args))
    if name == 'enterprise_services':
        infra=host('servers',10)
        rlines=['hostname R1','!']
        for i,key in enumerate(nets):
            rlines += [f'interface GigabitEthernet0/{i}',f' ip address {host(key,1)} 255.255.255.0',' no shutdown']
            if key != 'servers': rlines += [f' ip helper-address {infra}']
            rlines += ['!']
        rlines += [f'ntp server {infra}',f'logging {infra}','logging trap informational','end']
        if reference_policy:
            if reference_policy not in ('guest_firewall', 'ban_one_device'):
                raise ValueError('Politique de référence inconnue')
            interface = rlines.index('interface GigabitEthernet0/2')
            rlines.insert(interface+3, ' ip access-group '+('130' if reference_policy=='guest_firewall' else '131')+' in')
            if reference_policy == 'guest_firewall':
                deny = f'access-list 130 deny ip {nets["guests"].network_address} 0.0.0.255 {nets["servers"].network_address} 0.0.0.255'
                permit = 'access-list 130 permit ip any any'
            else:
                deny = f'access-list 131 deny tcp host {host("guests",21)} host {host("servers",20)} eq 80'
                permit = 'access-list 131 permit ip any any'
            rlines[-1:-1] = [deny,permit]
        lab.add('R1','router','2911',(600,120),config=rlines)
        devices['R1']={'type':'router','interfaces':{f'GigabitEthernet0/{i}':{'ip':host(k,1),'mask':'255.255.255.0'} for i,k in enumerate(nets)}}
        for i,key in enumerate(nets):
            sw={'employees':'SW-EMP','servers':'SW-SRV','guests':'SW-GUEST'}[key]
            x=(200,600,1000)[i]
            lab.add(sw,'switch','2960-24TT',(x,320),config=builder.switch_mgmt_config(sw,host(key,2),'255.255.255.0',host(key,1)))
            devices[sw]={'type':'switch','mgmt':{'ip':host(key,2),'mask':'255.255.255.0','gateway':host(key,1)}}
            link('R1',f'GigabitEthernet0/{i}',sw,'GigabitEthernet0/1')
        for n,key,num,x,sp in [('PC-ALICE','employees',21,100,1),('PC-BOB','employees',22,300,2),('PC-ADMIN','employees',23,450,3),('PC-GUEST','guests',21,1000,1)]:
            add_host(n,host(key,num),host(key,1),(x,540),dns_ip=infra)
            link({'employees':'SW-EMP','guests':'SW-GUEST'}[key],f'FastEthernet0/{sp}',n,'FastEthernet0')
        for i,(n,num,x) in enumerate([('SRV-INFRA',10,420),('SRV-WEB',20,600),('SRV-FTP',30,780),('SRV-MAIL',40,600)],1):
            add_host(n,host('servers',num),host('servers',1),(x,700 if n=='SRV-MAIL' else 520),'Server-PT',dns_ip=infra)
            link('SW-SRV',f'FastEthernet0/{i}',n,'FastEthernet0')
        if extra_web_server:
            add_host('SRV-WEB2',host('servers',50),host('servers',1),(960,520),'Server-PT',dns_ip=infra)
            link('SW-SRV','FastEthernet0/5','SRV-WEB2','FastEthernet0')
    elif name == 'wifi_deployment':
        net=nets['employees'];gw=host('employees',1)
        lab.add('R1','router','2911',(300,100),config=['hostname R1','!','interface GigabitEthernet0/0',f' ip address {gw} 255.255.255.0',' no shutdown','!',f'ip dhcp excluded-address {gw} {host("employees",49)}','ip dhcp pool WIFI',f' network {net.network_address} 255.255.255.0',f' default-router {gw}',f' dns-server {host("employees",10)}','!','end'])
        devices['R1']={'type':'router','interfaces':{'GigabitEthernet0/0':{'ip':gw,'mask':'255.255.255.0'}}}
        lab.add('SW1','switch','2960-24TT',(300,300),config=['hostname SW1','!','end']);devices['SW1']={'type':'switch'}
        lab.add('AP1','wireless','AccessPoint-PT',(600,300));devices['AP1']={'type':'wireless','model':'AccessPoint-PT'}
        add_host('PC-ADMIN',host('employees',20),gw,(100,520),dns_ip=host('employees',10))
        add_host('SRV-WEB',host('employees',10),gw,(300,520),'Server-PT',dns_ip=host('employees',10))
        link('R1','GigabitEthernet0/0','SW1','GigabitEthernet0/1')
        link('SW1','FastEthernet0/1','PC-ADMIN','FastEthernet0')
        link('SW1','FastEthernet0/2','SRV-WEB','FastEthernet0')
        link('SW1','FastEthernet0/3','AP1','Port 0')
    elif name == 'meraki_branch':
        # MX non câblé : les noms de ports sont choisis dans l'interface PT par l'apprenant.
        # Aucun faux lab « sain » Meraki basé sur un schéma WAN deviné.
        cloud='203.0.113.10';web='198.51.100.10'
        lab.add('ISP','router','2911',(600,100),config=['hostname ISP','!','interface GigabitEthernet0/0',' ip address 203.0.113.1 255.255.255.0',' no shutdown','!','interface GigabitEthernet0/1',' ip address 198.51.100.1 255.255.255.0',' no shutdown','!','ip dhcp excluded-address 203.0.113.1 203.0.113.49','ip dhcp pool WAN',' network 203.0.113.0 255.255.255.0',' default-router 203.0.113.1',f' dns-server {cloud}','!','end'])
        devices['ISP']={'type':'router','interfaces':{'GigabitEthernet0/0':{'ip':'203.0.113.1','mask':'255.255.255.0'},'GigabitEthernet0/1':{'ip':'198.51.100.1','mask':'255.255.255.0'}}}
        lab.add('SW-WAN','switch','2960-24TT',(600,300),config=['hostname SW-WAN','!','end']);devices['SW-WAN']={'type':'switch'}
        lab.add('MX1','wireless','Meraki-MX65W',(200,300));devices['MX1']={'type':'wireless','model':'Meraki-MX65W'}
        lab.add('SW-LAN','switch','2960-24TT',(200,520),config=['hostname SW-LAN','!','end']);devices['SW-LAN']={'type':'switch'}
        add_host('PC-ADMIN','192.168.0.20','192.168.0.1',(100,720),dns_ip=cloud)
        add_host('PC-CLIENT','192.168.0.21','192.168.0.1',(300,720),dns_ip=cloud)
        add_host('MERAKI-CLOUD',cloud,'203.0.113.1',(650,520),'Meraki-Server',dns_ip=cloud)
        add_host('WEB-PUBLIC',web,'198.51.100.1',(900,520),'Server-PT',dns_ip=cloud)
        link('ISP','GigabitEthernet0/0','SW-WAN','GigabitEthernet0/1')
        link('SW-WAN','FastEthernet0/1','MERAKI-CLOUD','FastEthernet0')
        link('ISP','GigabitEthernet0/1','WEB-PUBLIC','FastEthernet0')
        link('SW-LAN','FastEthernet0/1','PC-ADMIN','FastEthernet0')
        link('SW-LAN','FastEthernet0/2','PC-CLIENT','FastEthernet0')
    else: raise ValueError(f'Topologie inconnue : {name}')
    xml=folder/'baseline.xml'
    with contextlib.redirect_stdout(io.StringIO()):lab.to_packettracer_xml(str(xml))
    tree=ET.parse(xml);e=engines(tree.getroot())
    for n,d in devices.items():
        if d.get('model') in ('Server-PT','Meraki-Server'):server_defaults(e[n])
    if name == 'meraki_branch':
        shown_networks={'lan':'192.168.0.0/24','wan':'203.0.113.0/24','public':'198.51.100.0/24'}
    elif name == 'wifi_deployment':
        shown_networks={'employees':str(nets['employees'])}
    else:
        shown_networks={k:str(v) for k,v in nets.items()}
    topo={'name':name,'devices':devices,'links':links,'seed':seed,
          'networks':shown_networks,'validation':'manual','status':'A tester dans Packet Tracer 9'}
    if name=='enterprise_services':
        records={'intranet.entreprise.test':host('servers',20),'ftp.entreprise.test':host('servers',30),'mail.entreprise.test':host('servers',40)}
        if extra_web_server:
            records['support.entreprise.test']=host('servers',50)
        dns(e['SRV-INFRA'],records)
        dhcp(e['SRV-INFRA'],[{'name':key.upper(),'network':str(nets[key]),'gateway':host(key,1),'dns':host('servers',10)} for key in ('employees','guests')])
        for svc in ('SYSLOG_SERVER','NTP_SERVER','TFTP_SERVER'):put(e['SRV-INFRA'],svc+'/ENABLED',1)
        put(e['SRV-WEB'],'HTTP_SERVER/ENABLED',1)
        if extra_web_server:
            put(e['SRV-WEB2'],'HTTP_SERVER/ENABLED',1)
            index=next(f for f in e['SRV-WEB2'].iter('FILE') if f.findtext('NAME')=='index.html')
            put(index,'FILE_CONTENT/TEXT','<html><body><h1>Support entreprise - SRV-WEB2</h1></body></html>')
        put(e['SRV-FTP'],'FTP_SERVER/ENABLED',1)
        accounts=e['SRV-FTP'].find('FTP_SERVER/USER_ACCOUNT_MNGR');accounts.clear()
        for user,password,permissions in [('lecteur','Lecture123','RL'),('depot','Depot123','RWNL')]:
            a=ET.SubElement(accounts,'ACCOUNT')
            for tag,value in [('USERNAME',user),('PASSWORD',password),('PERMISSIONS',permissions)]:put(a,tag,value)
        topo['records']=records
        topo['ftp_accounts']={'lecteur':'Lecture123','depot':'Depot123'}
    elif name=='wifi_deployment':
        put(e['AP1'],'WIRELESS_SERVER/WIRELESS_COMMON/SSID','Agence-Lab')
        dns(e['SRV-WEB'],{'intranet.agence.test':host('employees',10)})
        put(e['SRV-WEB'],'HTTP_SERVER/ENABLED',1)
        topo['ssid']='Agence-Lab';topo['records']={'intranet.agence.test':host('employees',10)}
    else:
        dns(e['MERAKI-CLOUD'],{'dashboard.meraki.com':'203.0.113.10','www.public.test':'198.51.100.10'})
        put(e['WEB-PUBLIC'],'HTTP_SERVER/ENABLED',1)
        topo['records']={'dashboard.meraki.com':'203.0.113.10','www.public.test':'198.51.100.10'}
        topo['serial']=e['MX1'].findtext('SERIALNUMBER')
    ET.indent(tree,space=' ');tree.write(xml,encoding='utf-8',short_empty_elements=False)
    return tree,topo


# Chaque fiche définit symptôme, indices, résultat observable et procédure.
CATALOGUE={}

def register(fid,title,kind,topology,mutate,statement,hints,solution,tests,level=1):
    CATALOGUE[fid]={'title':title,'kind':kind,'topology':topology,'mutate':mutate,
                   'statement':statement,'hints':hints,'solution':solution,'tests':tests,'level':level}


def set_value(device,path,value):
    def mutate(root,t):put(engines(root)[device],path,value(t) if callable(value) else value)
    return mutate


def enable(device,service):return set_value(device,service+'/ENABLED',0)

def record_change(mode):
    def mutate(root,t):
        db=engines(root)['SRV-INFRA'].find('DNS_SERVER/NAMESERVER-DATABASE')
        rr=next(r for r in db if r.findtext('NAME')=='intranet.entreprise.test')
        if mode=='delete':db.remove(rr)
        else:put(rr,'IPADDRESS',t['devices']['SRV-MAIL']['ip'])
    return mutate


def pool_change(field,value):
    def mutate(root,t):
        s=dhcp_node(engines(root)['SRV-INFRA'])
        pool=next(p for p in s.findall('POOLS/POOL') if p.findtext('NAME')=='EMPLOYEES')
        put(pool,field,value(t) if callable(value) else value)
        # Le poste test commence sans bail : aucun bail valide ne masque la panne.
        pc=engines(root)['PC-ALICE'];p=port(pc)
        for tag in ('IP','SUBNET','PORT_GATEWAY','PORT_DNS'):put(p,tag,'0.0.0.0')
        put(p,'PORT_DHCP_ENABLE','true');put(pc,'GATEWAY','0.0.0.0')
    return mutate


def dhcp_off(root,t):
    put(dhcp_node(engines(root)['SRV-INFRA']),'ENABLED',0)
    pool_change('MAX_USERS',50)(root,t)


def ios_change(prefix,replacement):
    def mutate(root,t):
        e=engines(root)['R1'];lines=[x.text or '' for x in e.findall('RUNNINGCONFIG/LINE')]
        result=[];done=False
        for line in lines:
            if not done and line.strip().startswith(prefix):
                if replacement:result.append(replacement(t))
                done=True
            else:result.append(line)
        if not done:raise ValueError(f'Commande saine absente : {prefix}')
        configs(e,result)
    return mutate


def relay_change(wrong=False):
    def mutate(root,t):
        ios_change('ip helper-address',lambda x:' ip helper-address '+x['devices']['SRV-MAIL']['ip'] if wrong else None)(root,t) if wrong else ios_change('ip helper-address',None)(root,t)
        pool_change('MAX_USERS',50)(root,t)
    return mutate


def ftp_change(field,value):
    def mutate(root,t):
        s=engines(root)['SRV-FTP'].find('FTP_SERVER/USER_ACCOUNT_MNGR')
        a=next(a for a in s if a.findtext('USERNAME')=='depot');put(a,field,value)
    return mutate


def gateway_wrong(root,t):
    e=engines(root)['SRV-WEB'];wrong=t['devices']['SRV-INFRA']['ip']
    put(e,'GATEWAY',wrong);put(port(e),'PORT_GATEWAY',wrong)


def blank_dns(root,t):
    dns(engines(root)['SRV-INFRA'],{})


def mail_blank(root,t):
    # Mission de configuration : aucun compte sain prétendu ni schéma de compte inventé.
    e=engines(root)['SRV-MAIL'];put(e,'EMAIL_SERVER/SMTP_ENABLED',0);put(e,'EMAIL_SERVER/POP3_ENABLED',0)


def ftp_blank(root,t):
    e=engines(root)['SRV-FTP'];put(e,'FTP_SERVER/ENABLED',0)
    e.find('FTP_SERVER/USER_ACCOUNT_MNGR').clear()


def noop(root,t):pass


def dhcp_blank(root,t):
    put(dhcp_node(engines(root)['SRV-INFRA']),'ENABLED',0)
    ios_change('ip helper-address',None)(root,t)
    pool_change('MAX_USERS',50)(root,t)


def dhcp_client_reference(root):
    """Prépare le client DHCP dans la référence, sans inventer un bail obtenu dans PT."""
    e=engines(root)['PC-ALICE'];p=port(e)
    for tag in ('IP','SUBNET','PORT_GATEWAY','PORT_DNS'):put(p,tag,'0.0.0.0')
    put(p,'PORT_DHCP_ENABLE','true')
    put(e,'GATEWAY','0.0.0.0')


def value(t,device):return t['devices'][device]['ip']

def describe(text,t):
    replacements={n:d.get('ip','') for n,d in t['devices'].items()}
    replacements.update(t['networks'])
    replacements.update({k+'_net':str(ipaddress.IPv4Network(v).network_address) for k,v in t['networks'].items()})
    replacements['serial']=t.get('serial') or 'visible dans Config > numéro de série du MX1'
    for key,v in replacements.items():text=text.replace('{'+key+'}',v)
    return text


E='enterprise_services';W='wifi_deployment';M='meraki_branch'
register('dns_service_off','DNS arrêté','fault',E,enable('SRV-INFRA','DNS_SERVER'),
 'Les employés peuvent ouvrir le serveur web par son adresse IP, mais pas par intranet.entreprise.test.',
 ['Compare accès par IP et par nom.','Contrôle le service DNS de SRV-INFRA.'],
 'SRV-INFRA > Services > DNS : On. Conserver les enregistrements existants.',
 ['nslookup intranet.entreprise.test doit renvoyer {SRV-WEB}.','Depuis PC-ALICE et PC-BOB, ouvrir http://intranet.entreprise.test.'])
for mode,title in [('delete','Enregistrement DNS absent'),('wrong','Enregistrement DNS incorrect')]:
 register('dns_record_'+mode,title,'fault',E,record_change(mode),
  'Le nom intranet.entreprise.test ne conduit plus à la page du serveur web ; ftp.entreprise.test doit continuer à fonctionner.',
  ['Teste les deux noms séparément.','Examine le contenu des enregistrements A.'],
  'SRV-INFRA > Services > DNS : créer/corriger le A intranet.entreprise.test vers {SRV-WEB}, sans changer FTP et MAIL.',
  ['nslookup intranet.entreprise.test retourne {SRV-WEB}.','La page par nom et par IP doit fonctionner ; ftp.entreprise.test reste à {SRV-FTP}.'])
register('http_service_off','Serveur web arrêté','fault',E,enable('SRV-WEB','HTTP_SERVER'),
 'La résolution du nom et le ping fonctionnent, mais le navigateur ne peut plus ouvrir l’intranet.',
 ['Vérifie séparément DNS, ping et HTTP.','Examine Services > HTTP sur le serveur web.'],
 'SRV-WEB > Services > HTTP : On. Ne pas modifier les IP.',
 ['Ouvrir http://{SRV-WEB} et http://intranet.entreprise.test depuis les employés.'])
register('ftp_service_off','Service FTP arrêté','fault',E,enable('SRV-FTP','FTP_SERVER'),
 'Les deux comptes FTP ne peuvent plus se connecter alors que SRV-FTP répond au ping.',
 ['Distingue indisponibilité du service et refus d’authentification.','Examine Services > FTP.'],
 'SRV-FTP > Services > FTP : On. Garder lecteur/Lecture123 et depot/Depot123.',
 ['Depuis PC-ALICE : ftp {SRV-FTP}, connexion avec les deux comptes.','Le compte depot doit pouvoir transférer un fichier.'])
register('ftp_write_denied','FTP : écriture refusée','fault',E,ftp_change('PERMISSIONS','RL'),
 'Le compte depot se connecte au FTP et peut lister les fichiers, mais ne peut plus déposer un document.',
 ['La connexion fonctionne : regarde les droits.','Compare le compte depot avec le cahier des charges.'],
 'Services > FTP : accorder Read, Write, Rename et List au compte depot. Le compte lecteur reste en Read/List.',
 ['Créer preuve.txt dans le Text Editor de PC-ALICE, sauvegarder, puis ftp {SRV-FTP} et put preuve.txt avec depot.','Le compte lecteur doit pouvoir lire/lister, mais son put doit être refusé.'],2)
register('ftp_password_wrong','FTP : authentification refusée','fault',E,ftp_change('PASSWORD','AncienSecret123'),
 'Le compte lecteur fonctionne, mais depot/Depot123 n’est plus accepté.',
 ['Compare les deux comptes.','Contrôle l’authentification du compte depot.'],
 'Services > FTP : rétablir le mot de passe Depot123 pour depot, en conservant ses permissions.',
 ['ftp {SRV-FTP} avec depot/Depot123 doit réussir.','La connexion lecteur/Lecture123 doit rester possible.'])
register('server_gateway_wrong','Serveur : passerelle incorrecte','fault',E,gateway_wrong,
 'L’intranet est accessible depuis SRV-INFRA, mais pas depuis les postes employés ou invités.',
 ['Compare une source locale et une source distante.','Examine la passerelle du serveur web.'],
 'SRV-WEB > Desktop > IP Configuration : passerelle = première adresse du réseau servers (table).',
 ['Depuis SRV-INFRA et PC-ALICE, ping {SRV-WEB}.','Ouvrir la page HTTP depuis PC-ALICE.'],2)
register('dhcp_server_off','DHCP arrêté','fault',E,dhcp_off,
 'PC-ALICE est en DHCP et ne reçoit plus de bail utilisable. PC-BOB reste en statique et fonctionne.',
 ['Compare la configuration des postes.','Examine le service DHCP et le relais de R1.'],
 'SRV-INFRA > Services > DHCP : On, conserver les pools EMPLOYEES et GUESTS. Renouveler le bail de PC-ALICE.',
 ['PC-ALICE reçoit une IP entre .100 et .149 dans employees, masque /24, passerelle .1 et DNS {SRV-INFRA}.','Ping de sa passerelle puis accès intranet par nom.'])
for field,fid,title,val,detail in [
 ('DEFAULT_ROUTER','dhcp_gateway_wrong','DHCP : mauvaise passerelle',lambda t:t['devices']['SRV-WEB']['ip'],'Default Gateway = première adresse de employees (.1)'),
 ('DNS_SERVER','dhcp_dns_wrong','DHCP : mauvais DNS',lambda t:t['devices']['SRV-MAIL']['ip'],'DNS Server = {SRV-INFRA}'),
 ('MASK','dhcp_mask_wrong','DHCP : mauvais masque','255.255.255.252','Subnet Mask = 255.255.255.0')]:
 register(fid,title,'fault',E,pool_change(field,val),
  'PC-ALICE demande sa configuration par DHCP, mais n’accède pas correctement aux services (bail incorrect ou impossible). PC-BOB en statique fonctionne.',
  ['Lis toutes les valeurs du bail avec ipconfig /all.','Compare le pool EMPLOYEES à la table d’adressage.'],
  'SRV-INFRA > Services > DHCP > EMPLOYEES : '+detail+'. Save ; renouveler le bail de PC-ALICE.',
  ['PC-ALICE : adresse employees entre .100 et .149, /24, passerelle .1, DNS {SRV-INFRA}.','Tester passerelle, SRV-WEB et intranet par nom.'],2)
for wrong,title in [(False,'Relais DHCP absent'),(True,'Relais DHCP vers le mauvais serveur')]:
 register('dhcp_relay_'+('wrong' if wrong else 'missing'),title,'fault',E,relay_change(wrong),
  'PC-ALICE, en DHCP sur le réseau employés, ne reçoit pas de bail. Le serveur DHCP est sur le réseau serveurs.',
  ['Le broadcast DHCP doit franchir une frontière de routage.','Examine l’interface de R1 reliée à SW-EMP.'],
  'R1 : interface GigabitEthernet0/0 ; ip helper-address {SRV-INFRA}. Renouveler le bail et sauvegarder R1.',
  ['PC-ALICE reçoit un bail du pool EMPLOYEES.','PC-BOB en statique reste fonctionnel.'],2)
register('ntp_destination_wrong','NTP : mauvaise destination','fault',E,ios_change('ntp server',lambda t:'ntp server '+t['devices']['SRV-MAIL']['ip']),
 'R1 ne se synchronise plus sur le serveur de temps prévu.',
 ['Examine show ntp associations et la configuration.','Le service NTP est sur SRV-INFRA.'],
 'R1 : retirer le mauvais ntp server, ajouter ntp server {SRV-INFRA} et sauvegarder.',
 ['show ntp associations doit présenter {SRV-INFRA}.','Attendre la synchronisation et vérifier show ntp status selon le modèle PT.'],2)
register('syslog_destination_missing','Syslog : collecte absente','fault',E,ios_change('logging ',None),
 'L’équipe réseau ne voit plus les nouveaux événements de R1 dans le collecteur Syslog.',
 ['Déclenche un événement sur une interface inutilisée et compare console/collecteur.','Examine la destination logging de R1.'],
 'R1 : logging {SRV-INFRA} ; logging trap informational. Sauvegarder. SRV-INFRA > Services > SYSLOG doit être On.',
 ['Sur une interface inutilisée de R1, faire no shutdown puis shutdown ; consulter SYSLOG sur SRV-INFRA.','Un nouvel événement provenant de R1 doit apparaître ; conserver les interfaces de production actives.'],2)
register('tftp_service_off','TFTP : sauvegarde impossible','fault',E,enable('SRV-INFRA','TFTP_SERVER'),
 'La sauvegarde de R1 vers le serveur TFTP échoue alors que le serveur répond au ping.',
 ['Vérifie la destination et le service de transfert.','Examine Services > TFTP sur SRV-INFRA.'],
 'Activer TFTP sur SRV-INFRA puis, sur R1 : copy running-config tftp: ; destination {SRV-INFRA}, fichier R1-backup.cfg.',
 ['Services > TFTP doit afficher R1-backup.cfg après le transfert.','Le réseau des employés conserve son accès à l’intranet.'],2)
register('configure_dns','Publier les noms des services','configuration',E,blank_dns,
 'Le réseau IP fonctionne. Publie intranet.entreprise.test, ftp.entreprise.test et mail.entreprise.test dans le DNS central.',
 ['Le DNS central est SRV-INFRA.','Chaque nom doit pointer vers le serveur de son service.'],
 'Services > DNS : On. Ajouter trois enregistrements A : intranet → {SRV-WEB}, ftp → {SRV-FTP}, mail → {SRV-MAIL}.',
 ['nslookup sur les trois noms retourne les IP correspondantes.','Ouvrir l’intranet par son nom.'])
register('configure_mail','Déployer la messagerie','configuration',E,mail_blank,
 'Mets en service la messagerie entreprise.test. Crée alice/Alice123 et bob/Bob123 puis configure les clients mail sur PC-ALICE et PC-BOB.',
 ['Le transport réseau et DNS sont déjà configurés.','Services > EMAIL puis Desktop > Email sur les deux PC.'],
 'SRV-MAIL > Services > EMAIL : SMTP et POP3 On, Domain entreprise.test > Set. Ajouter alice/Alice123 et bob/Bob123. Clients : alice@entreprise.test et bob@entreprise.test, SMTP/POP3 = {SRV-MAIL}, identifiants correspondants.',
 ['Alice envoie un mail à Bob ; Bob clique Receive et reçoit le message.','Bob répond ; Alice reçoit la réponse.'],2)
register('configure_ftp','Déployer un dépôt avec permissions','configuration',E,ftp_blank,
 'Configure le serveur FTP : lecteur/Lecture123 peut lire et lister ; depot/Depot123 peut lire, écrire, renommer et lister, mais pas supprimer.',
 ['Les comptes et les droits se configurent dans Services > FTP.','Valide les autorisations ET les refus attendus.'],
 'Activer FTP, créer lecteur (Read/List) et depot (Read/Write/Rename/List), sans Delete.',
 ['depot dépose preuve.txt et peut le relire.','lecteur lit preuve.txt mais ne peut pas écrire.','depot ne peut pas supprimer preuve.txt.'],2)
register('configure_dhcp_relay','Déployer DHCP centralisé','configuration',E,dhcp_blank,
 'Remets en service DHCP pour les employés : pool EMPLOYEES .100 à .149, masque /24, passerelle .1, DNS SRV-INFRA. Configure le relais sur R1 et passe PC-ALICE en DHCP.',
 ['Le serveur est situé dans un autre sous-réseau.','Le relais doit être sur l’interface recevant les requêtes des clients.'],
 'SRV-INFRA : activer DHCP et contrôler EMPLOYEES (réseau employees, 50 utilisateurs à partir de .100). R1 G0/0 : ip helper-address {SRV-INFRA}. Renouveler PC-ALICE.',
 ['PC-ALICE reçoit un bail conforme puis ouvre l’intranet par nom.','Le réseau invités et PC-BOB ne doivent pas être modifiés.'],2)
CATALOGUE['configure_dhcp_relay']['reference_extension']='dhcp_relay'
register('guest_firewall','Isoler les invités','evolution',E,noop,
 'Les invités peuvent actuellement accéder aux serveurs. Bloque tout trafic initié depuis le réseau guests vers servers. Conserve leur accès à R1 et au réseau employees pour ce lab. Ne change pas les adresses.',
 ['Applique une ACL étendue à l’entrée de l’interface invités.','Le refus ciblé doit précéder permit ip any any.'],
 'R1 : access-list 130 deny ip {guests_net} 0.0.0.255 {servers_net} 0.0.0.255 ; access-list 130 permit ip any any. Interface GigabitEthernet0/2 : ip access-group 130 in. Les réseaux exacts sont dans la table. Sauvegarder.',
 ['PC-GUEST ne joint plus SRV-WEB (ping et HTTP).','PC-GUEST joint sa passerelle et PC-BOB.','PC-ALICE conserve son accès aux serveurs.'],2)
register('ban_one_device','Bloquer un poste précis','evolution',E,noop,
 'Bloque uniquement les accès HTTP de PC-GUEST à SRV-WEB. Le ping doit rester possible ; les employés doivent conserver HTTP.',
 ['Une ACL étendue peut sélectionner source, destination et port.','Évite de bloquer tout le sous-réseau ou tous les protocoles.'],
 'R1 : access-list 131 deny tcp host {PC-GUEST} host {SRV-WEB} eq 80 ; access-list 131 permit ip any any. Sur G0/2 : ip access-group 131 in. Sauvegarder.',
 ['PC-GUEST : HTTP vers {SRV-WEB} refusé, ping autorisé.','PC-ALICE : HTTP vers le même serveur autorisé.'],2)
register('add_web_server','Ajouter un serveur web','evolution',E,noop,
 'Ajoute SRV-WEB2 sur SW-SRV, avec l’adresse .50 du réseau servers, passerelle .1 et DNS SRV-INFRA. Publie support.entreprise.test et une page identifiant ce nouveau serveur.',
 ['Ajoute un Server-PT et un câble sur un port libre de SW-SRV.','Adresse, service HTTP et DNS sont trois étapes distinctes.'],
 'Ajouter SRV-WEB2 ; IP <réseau servers>.50/24, passerelle .1, DNS {SRV-INFRA}. HTTP On ; éditer index.html. Ajouter le A support.entreprise.test vers .50 sur SRV-INFRA.',
 ['Un nouveau serveur nommé SRV-WEB2 est présent et câblé.','PC-ALICE ouvre support.entreprise.test et voit la page du nouveau serveur.','L’intranet d’origine reste accessible.'],2)
CATALOGUE['add_web_server']['reference_extension']='web_server'
CATALOGUE['guest_firewall']['reference_extension']='guest_firewall'
CATALOGUE['ban_one_device']['reference_extension']='ban_one_device'
register('configure_aaa','Centraliser les accès avec AAA','configuration',E,noop,
 'Configure RADIUS sur SRV-INFRA et R1 pour l’authentification des accès VTY. Compte technicien/Tech123, clé partagée LabRadius123. Garde un compte local de secours.',
 ['Services > AAA : déclarer R1 avec son IP du réseau servers.','Configure le client RADIUS et la méthode AAA sur R1 ; garde la console ouverte pendant les tests.'],
 'Services > AAA : On, client R1 adresse <passerelle servers>, clé LabRadius123, type Radius ; ajouter technicien/Tech123. R1 : aaa new-model ; radius-server host {SRV-INFRA} auth-port 1645 key LabRadius123 (adapter la syntaxe au ? du modèle). aaa authentication login default group radius local. Créer un compte local de secours, puis appliquer login authentication default aux VTY et autoriser SSH avec domaine/clé RSA.',
 ['Un PC ouvre une session SSH avec technicien/Tech123.','Un mauvais mot de passe échoue.','Serveur AAA indisponible : le compte local doit fonctionner ; restaurer AAA après le test.'],3)
for fid,title,statement,solution,tests in [
 ('wifi_add_client','Connecter un portable Wi-Fi','Ajoute un Laptop-PT sans câble Ethernet. Installe une carte Wi-Fi compatible, connecte-le au SSID Agence-Lab et utilise DHCP.',
  'Laptop Physical : éteindre, remplacer la carte Ethernet par WPC300N si proposée, rallumer. Desktop > PC Wireless : SSID Agence-Lab. IP Configuration > DHCP.',
  ['Le portable est associé sans câble Ethernet.','Bail dans employees, passerelle .1 ; ouvrir http://intranet.agence.test.']),
 ('wifi_secure','Sécuriser le Wi-Fi','Le point d’accès est ouvert. Configure WPA2-PSK avec une clé de lab AgenceLab2026. Ajoute deux portables : un avec la bonne clé, un avec une mauvaise clé pour vérifier le refus.',
  'AP1 > Config > interface radio : WPA2-PSK/AES si disponible sur ce modèle. Clé AgenceLab2026. Ajouter un portable avec carte compatible ; configurer SSID et clé identiques. Si WPA2 indisponible, remplacer AP1 par un modèle compatible, conserver le câblage.',
  ['Un client avec la bonne clé reçoit un bail et ouvre l’intranet.','Un deuxième client avec une mauvaise clé ne s’associe pas.']),
 ('wifi_diagnose_client','Créer puis résoudre un incident Wi-Fi','Connecte deux portables au SSID Agence-Lab. Sur le second, configure volontairement un SSID incorrect, observe le symptôme, puis rétablis sa connexion.',
  'Mettre les deux portables en DHCP avec une carte Wi-Fi. Dégrader uniquement le SSID du deuxième client, puis restaurer Agence-Lab.',
  ['Avant injection, les deux clients ouvrent l’intranet.','Pendant la panne, le premier continue de fonctionner et le deuxième perd l’association.','Après réparation, les deux accèdent de nouveau au site.']),
 ('wifi_add_ap','Étendre la couverture','Ajoute AP2 sur un port libre de SW1. Donne-lui un SSID Agence-Extension et connecte un nouveau portable en DHCP.',
  'Ajouter AccessPoint-PT, connecter son port Ethernet à SW1, configurer son SSID. Ajouter un Laptop-PT avec carte Wi-Fi, choisir Agence-Extension et DHCP.',
  ['AP2 est présent et câblé.','Le portable utilise Agence-Extension et accède à l’intranet.','AP1 conserve son SSID et reste utilisable.'])]:
 register(fid,title,'configuration' if fid!='wifi_add_ap' else 'evolution',W,noop,statement,
          ['Commence par vérifier le réseau filaire avec PC-ADMIN.','Traite association Wi-Fi, DHCP et service web séparément.'],solution,tests,2)
for fid,title,statement,solution,tests in [
 ('meraki_commission','Mettre en service l’agence Meraki','Le MX1 est présent mais non câblé. Connecte Internet 1 à SW-WAN et un port LAN à SW-LAN. Configure le WAN par DHCP et vérifie le LAN 192.168.0.0/24.',
  'Dans PT, choisir les ports réellement nommés Internet 1 et LAN du MX1. Depuis PC-ADMIN : http://setup.meraki.com, identifiant = numéro de série {serial}, mot de passe vide. WAN DHCP. DNS du WAN = 203.0.113.10 via ISP. Vérifier que le LAN reste 192.168.0.1/24.',
  ['MX1 possède deux nouveaux câbles, WAN et LAN.','Internet 1 obtient une adresse 203.0.113.50 ou supérieure par DHCP.','PC-ADMIN et PC-CLIENT ouvrent http://www.public.test.']),
 ('meraki_dashboard','Enregistrer le MX dans le dashboard','Mets en service l’agence (WAN DHCP) puis crée un compte dans le dashboard simulé et enregistre MX1 dans un réseau nommé Agence-Damien.',
  'Câbler et configurer le MX comme dans meraki_commission. Depuis PC-ADMIN : https://dashboard.meraki.com (serveur simulé du lab). Créer un compte de lab, créer Agence-Damien et ajouter le numéro de série {serial}. Ne pas utiliser un compte Meraki réel.',
  ['Le réseau Agence-Damien et MX1 apparaissent dans le dashboard simulé.','Le numéro de série enregistré correspond à Config de MX1.','Le site public reste accessible.']),
 ('meraki_wifi','Déployer le Wi-Fi du MX','Mets en service et enregistre MX1 dans le dashboard simulé. Configure le SSID Agence-Meraki en WPA2-PSK et connecte un portable en DHCP.',
  'Après mise en service WAN et enregistrement, Security Appliance > Wireless Settings : SSID Agence-Meraki, WPA2 PSK, clé MerakiLab2026. Ajouter un Laptop-PT avec carte Wi-Fi compatible et paramètres identiques.',
  ['Le portable est associé à Agence-Meraki sans câble.','Il obtient une adresse LAN et ouvre http://www.public.test.','Un client avec une clé incorrecte ne s’associe pas.']),
 ('meraki_filter','Bloquer un client au pare-feu Meraki','Mets en service et enregistre MX1. Dans le dashboard, bloque HTTP de PC-CLIENT (192.168.0.21) vers WEB-PUBLIC (198.51.100.10), en conservant HTTP pour PC-ADMIN.',
  'Security Appliance > Firewall : règle sortante deny TCP, source 192.168.0.21/32, destination 198.51.100.10/32, port 80 ; vérifier l’ordre des règles. Garder les autres accès autorisés.',
  ['PC-CLIENT ne peut plus ouvrir http://198.51.100.10.','PC-ADMIN peut ouvrir le même site.','Le dashboard reste accessible.']),
 ('meraki_wan_incident','Diagnostiquer une passerelle WAN erronée','Mets en service MX1 avec WAN statique 203.0.113.50/24, passerelle 203.0.113.1 et DNS 203.0.113.10. Prouve son fonctionnement, puis remplace uniquement la passerelle par 203.0.113.254 et répare.',
  'Depuis setup.meraki.com, régler le WAN statique. Tester le site http://www.public.test depuis les clients LAN avant et après la modification de passerelle. Restaurer 203.0.113.1. WEB-PUBLIC est situé derrière ISP dans 198.51.100.0/24, distinct du WAN 203.0.113.0/24 : son accès permet de vérifier la passerelle WAN.',
  ['La configuration WAN finale contient 203.0.113.50/24 et passerelle 203.0.113.1.','http://www.public.test fonctionne avant injection, échoue après et refonctionne après réparation.','Le WAN reste dans 203.0.113.0/24 et WEB-PUBLIC reste dans 198.51.100.0/24.'])]:
 register(fid,title,'configuration' if fid!='meraki_filter' else 'evolution',M,noop,statement,
          ['Commence par le câblage et le WAN ; le dashboard est un serveur local simulé.','Distingue setup local, accès au dashboard, enregistrement et règles de filtrage.'],solution,tests,2)


register('dns_alias','Publier un alias DNS','evolution',E,noop,
 'Ajoute www.entreprise.test comme alias CNAME de intranet.entreprise.test. Ne crée pas un deuxième enregistrement A pour cet alias.',
 ['Le nom cible existe déjà.','Choisis CNAME et indique un nom cible, pas une adresse IP.'],
 'SRV-INFRA > DNS : Name www.entreprise.test, Type CNAME, Host Name intranet.entreprise.test. Conserver le A existant.',
 ['Le navigateur ouvre http://www.entreprise.test et affiche la même page que l’intranet.','Le A intranet.entreprise.test conserve {SRV-WEB}.'])
register('web_publish','Publier une page web','evolution',E,noop,
 'Publie une page support.html sur SRV-WEB, accessible par http://intranet.entreprise.test/support.html. Elle doit afficher le nom de l’entreprise et le contact du support.',
 ['Le réseau et HTTP fonctionnent déjà.','Services > HTTP permet de créer et éditer les fichiers HTML.'],
 'SRV-WEB > Services > HTTP : ajouter support.html, écrire une page HTML avec titre et contact, sauvegarder. Ajouter un lien depuis index.html.',
 ['L’URL /support.html affiche la nouvelle page depuis PC-ALICE.','La page index.html reste accessible et contient un lien fonctionnel vers support.html.'])
register('backup_restore','Sauvegarder et restaurer R1','configuration',E,noop,
 'Sauvegarde la configuration de R1 sur SRV-INFRA par TFTP. Modifie uniquement la description de G0/0, puis restaure la sauvegarde et prouve le retour de la description d’origine.',
 ['Sauvegarde avant de modifier.','La copie vers running-config fusionne les commandes : un élément absent de la sauvegarde ne sera pas forcément supprimé.'],
 'Configurer d’abord description EMPLOYES sur G0/0, puis copy running-config tftp: vers {SRV-INFRA}, nom R1-backup.cfg. Remplacer la description par TEST. Faire copy tftp: running-config, source {SRV-INFRA}, fichier R1-backup.cfg ; vérifier description EMPLOYES puis sauvegarder startup-config.',
 ['R1-backup.cfg existe dans TFTP avant la modification.','Après restauration, show running-config montre description EMPLOYES sur G0/0.','Les employés conservent leur accès aux serveurs.'],2)
register('monitoring_deploy','Déployer NTP et Syslog','configuration',E,noop,
 'Configure SW-EMP et SW-GUEST pour utiliser SRV-INFRA comme serveur NTP et collecteur Syslog.',
 ['Ces switches disposent déjà d’une SVI et d’une passerelle.','Vérifie la connectivité de management avant les services.'],
 'Sur chaque switch : ntp server {SRV-INFRA}, logging {SRV-INFRA}, logging trap informational. Sauvegarder. Vérifier les services NTP/SYSLOG sur SRV-INFRA.',
 ['Les deux switches présentent SRV-INFRA dans leurs associations NTP après attente.','Des événements provoqués sur des ports inutilisés apparaissent dans SYSLOG avec les noms des deux switches.'],2)
register('mail_client_incident','Diagnostiquer un client mail','configuration',E,mail_blank,
 'Configure deux comptes et clients mail fonctionnels (alice/Alice123 et bob/Bob123, domaine entreprise.test). Sur PC-ALICE, remplace seulement le serveur SMTP par SRV-WEB, observe puis répare.',
 ['Établis d’abord un échange de mails dans les deux sens.','Compare les paramètres entrant POP3 et sortant SMTP.'],
 'Configurer EMAIL sur SRV-MAIL et les deux clients. Après le test sain, SMTP de PC-ALICE = {SRV-WEB}, POP3 = {SRV-MAIL}. Envoi impossible, réception encore possible. Restaurer SMTP = {SRV-MAIL}.',
 ['Avant injection, Alice et Bob échangent des mails.','Pendant l’incident, Alice ne peut pas envoyer mais peut recevoir un nouveau mail de Bob.','Après réparation, les échanges fonctionnent dans les deux sens.'],2)
register('mail_pop3_incident','Diagnostiquer la réception de mails','configuration',E,mail_blank,
 'Configure une messagerie saine avec alice/Alice123 et bob/Bob123, domaine entreprise.test. Désactive ensuite uniquement POP3 sur SRV-MAIL, observe puis rétablis le service.',
 ['Teste envoi et réception séparément.','SMTP et POP3 sont deux services distincts.'],
 'Configurer la messagerie et valider les échanges. SRV-MAIL > Services > EMAIL : POP3 Off, SMTP On. Les clients ne récupèrent plus leurs nouveaux mails. Rétablir POP3 On.',
 ['Avant injection, les échanges réussissent.','Pendant l’incident, SMTP reste actif mais Receive échoue.','Après réparation, les nouveaux messages envoyés pendant l’incident sont récupérables.'],2)


def render(topo,spec):
    esc=html.escape
    rows=[]
    for n,d in topo['devices'].items():
        if d.get('ip'):rows.append((n,d['ip'],d['mask'],d['gateway'],d.get('dns','')))
        for iface,cfg in d.get('interfaces',{}).items():rows.append((n+' '+iface,cfg['ip'],cfg['mask'],'—','—'))
    parts=['<!doctype html><html lang="fr"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(spec['title'])+'</title>',
           '<style>body{font:17px/1.55 system-ui;max-width:1000px;margin:40px auto;padding:0 20px;color:#172b3a}h1,h2{color:#155b65}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:8px;border:1px solid #cbd5df;text-align:left}details{padding:12px;border:1px solid #b6c9cf;margin:14px 0;border-radius:6px}summary{cursor:pointer;font-weight:600}.note{background:#edf5f6;padding:15px}code{background:#edf2f7}li{margin:7px 0}</style></head><body>',
           '<h1>'+esc(spec['title'])+'</h1>',
           '<p>'+esc(TOPOLOGIES[topo['name']])+' · '+esc(KINDS[spec['kind']])+' · seed '+str(topo['seed'])+'</p>',
           '<p class="note">Validation manuelle dans Packet Tracer. Les fichiers sont générés et testés en Python ; le comportement réseau doit encore être confirmé dans PT 9. Aucun score automatique ne valide cet atelier.</p>',
           '<h2>Mise en situation et consignes</h2><p>'+esc(describe(spec['statement'],topo))+'</p>',
           '<p>Conserve les équipements et services existants, sauf modification demandée. Attends la convergence et renouvelle les baux DHCP après correction. Sauvegarde les configurations IOS puis le fichier Packet Tracer.</p>',
           '<h2>Table d’adressage de référence</h2><table><tr><th>Appareil/interface</th><th>IP</th><th>Masque</th><th>Passerelle</th><th>DNS</th></tr>']
    for row in rows:parts.append('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>')
    parts.append('</table><p>Réseaux : '+esc(', '.join(k+' = '+v for k,v in topo['networks'].items()))+'</p>')
    if spec['id'].startswith('dhcp_') or spec['id']=='configure_dhcp_relay':
        parts.append('<p>PC-ALICE démarre en DHCP sans bail. Sa ligne dans la table est une référence statique du socle ; le résultat attendu du DHCP est une adresse .100 à .149 du réseau employees.</p>')
    parts.append('<h2>Indices progressifs</h2>')
    for i,hint in enumerate(spec['hints'],1):parts.append('<details><summary>Indice '+str(i)+'</summary><p>'+esc(describe(hint,topo))+'</p></details>')
    parts.append('<h2>Correction — à consulter à la fin</h2><details><summary>Afficher une méthode et les résultats attendus</summary><h3>Méthode possible</h3><p>'+esc(describe(spec['solution'],topo))+'</p><h3>Tests et résultats attendus</h3><ul>')
    parts.extend('<li>'+esc(describe(x,topo))+'</li>' for x in spec['tests'])
    parts.append('</ul><p>Une autre configuration est acceptable si elle respecte toutes les consignes et réussit les tests, y compris les refus de trafic demandés.</p></details></body></html>')
    return ''.join(parts)


def generate(scenario_id,seed=None,output_dir='.',embed=True,address_family=None):
    if scenario_id not in CATALOGUE:raise ValueError(f'Atelier inconnu : {scenario_id}')
    spec=dict(CATALOGUE[scenario_id],id=scenario_id)
    seed=seed if seed is not None else random.SystemRandom().randrange(10**9)
    folder=Path(output_dir).resolve();folder.mkdir(parents=True,exist_ok=True)
    tree,topo=make_topology(spec['topology'],seed,folder,address_family)
    baseline=folder/'baseline.xml'
    spec['mutate'](tree.getroot(),topo)
    start=folder/'initial.xml';ET.indent(tree,space=' ');tree.write(start,encoding='utf-8',short_empty_elements=False)
    content=render(topo,spec);(folder/'consignes.html').write_text(content,encoding='utf-8')
    # Le .pkt simple reste disponible même si le wrapper PKA d'un modèle GUI doit être ajusté.
    pkt=folder/'lab.pkt'
    with contextlib.redirect_stdout(io.StringIO()):ptexplorer.ptfile_encode(str(start),str(pkt))
    if embed:
        import activity
        activity_xml=folder/'activity.xml'
        # Seules les consignes et l'adressage, sans les indices ni la solution, sont embarqués.
        instructions=content.split('<h2>Indices progressifs</h2>')[0]+'</body></html>'
        activity.assemble_activity(base_xml_path=str(start),template_path=str(Path(__file__).parent/'templates/activities/subnetting_activity.xml'),output_xml_path=str(activity_xml),pages=[{'title':spec['title'],'content':instructions}],initial_state='generated',answer_xml_path=str(baseline),title=spec['title'])
        with contextlib.redirect_stdout(io.StringIO()):ptexplorer.ptfile_encode(str(activity_xml),str(folder/'lab.pka'))
    meta={'kind':'workshop','validation':'manual','scenario':scenario_id,'title':spec['title'],
          'topology':topo,'pkt':str(pkt),'worksheet':str(folder/'consignes.html'),
          'expected':[describe(t,topo) for t in spec['tests']], 'solution':describe(spec['solution'],topo)}
    portable_meta = dict(meta, pkt='lab.pkt', worksheet='consignes.html')
    (folder/'solution.json').write_text(json.dumps(portable_meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true');parser.add_argument('--scenario',choices=sorted(CATALOGUE));parser.add_argument('--seed',type=int);parser.add_argument('--output',default='atelier');parser.add_argument('--pkt-only',action='store_true')
    args=parser.parse_args()
    if args.list or not args.scenario:
        for fid,s in CATALOGUE.items():print(f'{fid:30} {s["kind"]:14} {s["title"]}')
    else:
        meta=generate(args.scenario,args.seed,args.output,embed=not args.pkt_only)
        print(meta['pkt']);print(meta['worksheet'])

if __name__=='__main__':main()
