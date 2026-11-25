"""Compte à rebours persistant, indépendant du résultat pédagogique."""
import time

def configure(minutes,mode):
 if isinstance(minutes,bool):raise ValueError('Durée invalide')
 try:minutes=int(minutes)
 except (TypeError,ValueError):raise ValueError('Durée invalide')
 if not 0<=minutes<=1440 or mode not in ('training','challenge'):raise ValueError('Durée de 0 à 1440 minutes ; mode entraînement ou défi.')
 return dict(limit=minutes*60,mode=mode,elapsed=0,running_since=None,started=False,finished=False)

def elapsed(timer,at=None):
 at=time.time() if at is None else at
 return timer.get('elapsed',0)+max(0,at-timer['running_since']) if timer.get('running_since') is not None else timer.get('elapsed',0)

def operate(timer,action,at=None):
 at=time.time() if at is None else at
 if not timer.get('limit'):raise ValueError('Choisis une durée avant de démarrer.')
 if action!='start' and not timer.get('started'):raise ValueError('Chronomètre non démarré.')
 if timer.get('finished'):raise ValueError('Chronomètre déjà terminé.')
 if action=='start':
  if timer['started']:raise ValueError('Chronomètre déjà démarré.')
  timer.update(started=True,running_since=at)
 elif action=='pause':
  if timer['mode']=='challenge':raise ValueError('Le mode défi ne permet pas de pause.')
  if timer.get('running_since') is None:raise ValueError('Chronomètre non actif.')
  timer.update(elapsed=elapsed(timer,at),running_since=None)
 elif action=='resume':
  if not timer['started'] or timer.get('running_since') is not None:raise ValueError('Chronomètre non en pause.')
  timer['running_since']=at
 elif action=='finish':
  spent=elapsed(timer,at);timer.update(elapsed=spent,running_since=None,finished=True,exceeded=spent>timer['limit'])
 else:raise ValueError('Action chronomètre inconnue.')

def autostart(timer):
 if timer and timer.get('limit') and not timer['started']:operate(timer,'start')


def track_work(ticket,action,at=None):
 """Temps de travail, distinct du délai pédagogique démarré au signalement."""
 at=time.time() if at is None else at
 if action in ('take','reopen'):
  timer=ticket.setdefault('work_timer',dict(elapsed=0,running_since=None))
  if timer.get('running_since') is None:timer['running_since']=at
 elif action in ('wait','close','resolve') and ticket.get('work_timer'):
  timer=ticket['work_timer']
  if timer.get('running_since') is not None:
   timer['elapsed']=elapsed(timer,at);timer['running_since']=None
