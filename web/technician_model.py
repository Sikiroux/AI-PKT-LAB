"""Mobilité logique et VPN pédagogique, indépendants d'un tunnel réel."""
import copy
import hmac
import time
import directory_adapter as ad
import sim_ad
from network_proofs import proof

LOCATIONS={'office':'Bureau utilisateurs','server_room':'Salle serveurs','outside':'Télétravail (réseau extérieur simulé)'}

def ensure(s):
    if not s or 'technician' not in s.get('devices',{}) or 'technician_session' in s:return False
    s['technician_session']=dict(location='office',connection='wired',vpn=dict(connected=False,expires_at=0,service_enabled=True,account_enabled=True,profile_valid=True),pending=None,history=[])
    return True

def invalidate(s):
    if 'technician_session' in s:
        s['technician_session']['vpn'].update(connected=False,expires_at=0)
    s['observation']=None;s['remote_session']=False
    if 'directory' in s:ad.invalidate(s)

def policy(s,now=None):
    now=time.time() if now is None else now;t=s.get('technician_session')
    if not t:return dict(allowed=True,status='passed',reason='Poste technicien historique.')
    if t.get('pending'):return dict(allowed=False,status='unknown',reason='Raccordement à confirmer dans Packet Tracer.')
    if t['connection']!='wired':return dict(allowed=False,status='failed',reason='Raccordement réseau du portable requis (la console ne transporte pas IP).')
    if t['location']!='outside':return dict(allowed=True,status='passed',reason='Intervention sur site ; connectivité PT à vérifier.')
    vpn=t['vpn']
    if not (vpn['connected'] and now<vpn['expires_at'] and vpn['service_enabled'] and vpn['account_enabled'] and vpn['profile_valid']):return dict(allowed=False,status='failed',reason='VPN du technicien non connecté ou profil refusé.')
    profile=s.get('technician_locations',{}).get('outside',{})
    observed=proof(s,'vpn_gateway','technician',profile.get('gateway'),now)
    if observed['status']=='unknown':return dict(allowed=False,status='unknown',reason='Accessibilité du point d’entrée VPN non vérifiée récemment.')
    return dict(allowed=observed['status']=='passed',status=observed['status'],reason='VPN simulé ; transport réel contrôlé par ICMP dans PT.')

def vpn(s,action,password='',now=None):
    now=time.time() if now is None else now;ensure(s);t=s['technician_session'];v=t['vpn']
    if action=='disconnect':v.update(connected=False,expires_at=0);s['remote_session']=False;ad.invalidate(s);return dict(allowed=True,code='VPN_DISCONNECTED')
    if action!='connect':raise ValueError('Action VPN inconnue.')
    if t['location']!='outside' or t['connection']!='wired' or t.get('pending'):raise ValueError('Raccorde le portable au réseau extérieur simulé avant le VPN.')
    if not (v['service_enabled'] and v['account_enabled'] and v['profile_valid']):return dict(allowed=False,code='VPN_PROFILE_REFUSED')
    if not isinstance(password,str) or not hmac.compare_digest(password,sim_ad.TRAINING_PASSWORD):return dict(allowed=False,code='VPN_AUTHENTICATION_FAILED')
    profile=s.get('technician_locations',{}).get('outside',{})
    p=(s.get('observation') or {}).get('probes',{}).get('vpn_gateway',{})
    if p.get('source_device')!=s['devices']['technician']['name'] or p.get('target')!=profile.get('gateway') or p.get('status')!='passed' or not 0<=now-p.get('at',0)<=ad.TTL:return dict(allowed=False,code='VPN_GATEWAY_UNVERIFIED')
    v.update(connected=True,expires_at=now+1800);return dict(allowed=True,code='VPN_CONNECTED')

def public(s):
    t=s.get('technician_session')
    if not t:return None
    now=time.time();access=policy(s,now);v=t['vpn']
    connected=t['location']=='outside' and t['connection']=='wired' and not t.get('pending') and v['connected'] and now<v['expires_at'] and v['service_enabled'] and v['account_enabled'] and v['profile_valid']
    return dict(location=t['location'],connection=t['connection'],pending=copy.deepcopy(t.get('pending')),vpn_connected=bool(connected),vpn_access_status=access['status'],vpn_expires_at=v['expires_at'],access=access,locations=copy.deepcopy(s.get('technician_locations',{})),history=copy.deepcopy(t['history'][-20:]))
