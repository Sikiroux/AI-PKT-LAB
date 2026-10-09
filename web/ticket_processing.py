"""Traitement helpdesk pédagogique, indépendant du réseau et du correcteur."""
import copy
import uuid
import time

LEVELS = ('faible', 'moderee', 'elevee', 'critique')
# Matrice pédagogique explicite ; ce n'est pas une copie de la configuration GLPI.
MATRIX = ((0, 0, 1, 2), (0, 1, 2, 2), (1, 2, 2, 3), (2, 2, 3, 3))

def classification(ticket):
    saved = ticket.get('classification')
    if saved:
        return copy.deepcopy(saved)
    urgency = 'elevee' if ticket.get('request_context', {}).get('urgency_label') == 'Activité bloquée' else 'moderee'
    impact = ticket.get('impact', {})
    count = impact.get('affected_count', 1) if isinstance(impact, dict) else 1
    scope = 'elevee' if count >= 10 else 'moderee' if count > 1 else 'faible'
    suggested = LEVELS[MATRIX[LEVELS.index(urgency)][LEVELS.index(scope)]]
    return dict(urgency=urgency, impact=scope, suggested=suggested,
                priority=ticket.get('severity', 'moderee'), source='legacy', reason='Priorité conservée depuis la sauvegarde.')

def set_classification(ticket, data, stamp):
    urgency, impact = data.get('urgency'), data.get('impact_level')
    if urgency not in LEVELS or impact not in LEVELS:
        raise ValueError('Urgence ou impact inconnu.')
    suggested = LEVELS[MATRIX[LEVELS.index(urgency)][LEVELS.index(impact)]]
    priority = data.get('priority', suggested)
    reason = data.get('reason', '')
    if priority not in LEVELS or not isinstance(reason, str) or len(reason) > 1000:
        raise ValueError('Priorité ou justification invalide.')
    if priority != suggested and len(reason.strip()) < 10:
        raise ValueError('Justifie la priorité manuelle avec au moins 10 caractères.')
    entry = dict(urgency=urgency, impact=impact, suggested=suggested, priority=priority,
                 source='manual' if priority != suggested else 'matrix', reason=reason.strip())
    ticket['classification'] = entry
    ticket['severity'] = priority
    ticket.setdefault('processing_history', []).append(dict(date=stamp, kind='priority', text='Priorité : '+priority, **entry))

def add_task(ticket, data, stamp):
    text = data.get('text')
    minutes = data.get('minutes', 0)
    if not isinstance(text, str) or not 3 <= len(text.strip()) <= 1000:
        raise ValueError('Décris la tâche (3 à 1000 caractères).')
    if isinstance(minutes, bool) or not isinstance(minutes, int) or not 0 <= minutes <= 1440:
        raise ValueError('Durée prévue : 0 à 1440 minutes.')
    if len(ticket.get('tasks', [])) >= 100:
        raise ValueError('Limite de 100 tâches atteinte.')
    task = dict(id=uuid.uuid4().hex, text=text.strip(), minutes=minutes, status='todo',
                created=stamp, updated=stamp, revision=0, author='Technicien de la session')
    ticket.setdefault('tasks', []).append(task)
    ticket.setdefault('processing_history', []).append(dict(date=stamp, kind='task', text='Tâche ajoutée : '+task['text'], task_id=task['id']))
    return task

def update_task(ticket, data, stamp):
    task = next((t for t in ticket.get('tasks', []) if t['id'] == data.get('task_id')), None)
    if task is None:
        raise ValueError('Tâche inconnue pour ce ticket.')
    if type(data.get('expected_revision')) is not int or data['expected_revision'] != task['revision']:
        raise ValueError('Cette tâche a changé. Actualise le ticket.')
    status = data.get('task_status')
    if status not in ('todo', 'doing', 'done'):
        raise ValueError('État de tâche inconnu.')
    if status == task['status']:
        return task
    task.update(status=status, updated=stamp, revision=task['revision']+1)
    ticket.setdefault('processing_history', []).append(dict(date=stamp, kind='task', text='Tâche '+status+' : '+task['text'], task_id=task['id']))
    return task

def timeline(ticket, public_only=False):
    entries = []
    if ticket.get('created'):
        entries.append(dict(date=ticket['created'], kind='created', text='Demande reçue : '+ticket.get('title', ticket.get('id', '')), visibility='public'))
    for entry in ticket.get('dialogue', []):
        stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['at'])) if isinstance(entry.get('at'), (int, float)) else ''
        entries.append(dict(date=stamp, kind='dialogue', text=entry.get('question', '')+'\n'+entry.get('answer', ''), author=entry.get('speaker', ''), visibility='public'))
    for entry in ticket.get('followups', []):
        private = entry.get('visibility', 'public') == 'private'
        if public_only and private:
            continue
        entries.append(dict(date=entry['date'], kind=entry['kind'], text=entry['text'], author=entry.get('author', ''), visibility='private' if private else 'public'))
    if not public_only:
        for entry in ticket.get('workflow', []):
            entries.append(dict(date=entry['date'], kind='status', text=entry.get('previous', '')+' → '+entry['status']+((' · '+entry['reason']) if entry.get('reason') else ''), visibility='private'))
        for entry in ticket.get('processing_history', []):
            entries.append(dict(entry, visibility='private'))
    return sorted(entries, key=lambda entry: entry['date'])
