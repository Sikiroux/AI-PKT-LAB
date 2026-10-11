"""Lecture commune des preuves ICMP : paire exacte, horodatage, aucun ping."""
import math
TTL=45

def proof(state,key,source,target,now):
    item=(state.get('observation') or {}).get('probes',{}).get(key,{})
    expected=state.get('devices',{}).get(source,{}).get('name')
    stamp=item.get('at',0)
    valid=bool(expected and target) and item.get('source_device')==expected and item.get('target')==target
    stamp=stamp if type(stamp) in (int,float) and math.isfinite(stamp) else 0
    fresh=valid and 0<=now-stamp<=TTL
    status=item.get('status','unknown') if fresh else 'unknown'
    if status not in ('passed','failed'):status='unknown'
    return dict(status=status,observed_at=stamp if valid else 0,valid_until=stamp+TTL if valid and type(stamp) in (int,float) else 0,evidence='icmp_proxy')
