"""Planification bornée et état informatif des preuves réseau, sans accès au pont."""
from workspace_model import TTL


def select_target(state):
    profiles = state.get('client_workspaces', {})
    primary = state.get('devices', {}).get('client', {}).get('serial')
    if not profiles:
        return primary

    def observation(serial):
        return (state.get('observation') if serial == primary else profiles[serial]['local'].get('observation')) or {}

    def age_key(serial):
        return (observation(serial).get('at', 0), serial)

    active = [serial for serial, profile in profiles.items()
              if (state.get('remote_session') if serial == primary else profile['local'].get('remote_session'))]
    # Un passage sur deux reste consacré au parc entier : aucune session active
    # ne peut affamer les autres postes. Le poste le moins récemment tenté passe.
    turn = state.get('monitor_turn', 0)
    state['monitor_turn'] = turn + 1
    pool = active if active and turn % 2 == 0 else list(profiles)
    return min(pool, key=age_key)


def public_status(state, now):
    aggregate = state.get('observation') or {}
    last = state.get('last_known_observation') or {}
    current = aggregate.get('probes', {}).get('remote', aggregate)
    known = last.get('probes', {}).get('remote', last)
    stamp = current.get('at', 0)
    fresh = bool(stamp) and 0 <= now - stamp <= TTL
    status = current.get('status', 'unknown') if fresh else 'unknown'
    devices=state.get('devices',{})
    if devices.get('technician',{}).get('name') and devices.get('client',{}).get('ip'):
        from network_proofs import proof
        status=proof(state,'remote','technician',devices['client']['ip'],now)['status']
    reason = ('expired' if stamp and not fresh else
              'transport' if status == 'unknown' and current.get('detail') else
              'unverified' if status == 'unknown' else 'observed')
    return dict(status=status, reason=reason, observed_at=stamp or None,
                last_known_status=known.get('status'), last_known_at=known.get('at'),
                detail=current.get('detail', ''), ttl_seconds=TTL)
