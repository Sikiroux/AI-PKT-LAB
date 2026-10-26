"""Traces de téléchargements simulés réussis ; aucune opération réseau réelle."""
import hashlib
import math


def digest(content):return hashlib.sha256(content.encode()).hexdigest()


def record_download(state,source,name,content,at):
    ftp=state['desktop_services']['ftp']
    receipt=dict(direction='download',name=name,completed_at=at,
        environment_id=state.get('environment_id','legacy'),source_role=source,
        station_serial=state['devices'][source].get('serial'),
        account_id=state.get('directory_user_id') if source=='client' else None,
        username=ftp['sessions'][source]['username'],sha256=digest(content))
    ftp.setdefault('transfer_history',[]).append(receipt)
    ftp['transfer_history']=ftp['transfer_history'][-100:]


def download_confirmed(state,record,at):
    ftp=state['desktop_services']['ftp'];local=state['desktop_services']['endpoint']['local_files']
    goal=record.get('transfer_goal') or record.get('ticket',{}).get('transfer_goal') or {}
    expected=goal.get('name')
    start=record.get('applied_at',record.get('created'))
    if type(start) not in (int,float) or not math.isfinite(start):return False
    serial=state['devices']['client'].get('serial')
    if not serial:return False
    for row in reversed(ftp.get('transfer_history',[])):
        stamp=row.get('completed_at');name=row.get('name')
        if type(stamp) not in (int,float) or not math.isfinite(stamp) or not start<=stamp<=at:continue
        if (row.get('direction')!='download' or row.get('source_role')!='client' or
            row.get('station_serial')!=serial or row.get('environment_id')!=state.get('environment_id','legacy') or
            row.get('account_id')!=state.get('directory_user_id')):continue
        if expected and name!=expected:continue
        if name not in ftp['files'] or name not in local:continue
        if row.get('sha256')==digest(local[name])==digest(ftp['files'][name]):return True
    return False
