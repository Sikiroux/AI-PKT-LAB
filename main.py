"""
pkt_lab — Simulateur de tickets helpdesk sur Packet Tracer.

Menu principal :
  1. Nouveau ticket   : génère un lab avec une panne + le ticket utilisateur
  2. Valider un ticket: vérifie ta réparation (après Ctrl+S dans Packet Tracer)
  3. Historique
  0. Quitter

Les tickets sont rangés dans le dossier 'tickets/' à côté du programme :
  tickets/T12345/lab.pkt            -> à ouvrir dans Packet Tracer
  tickets/T12345/ticket.txt         -> l'énoncé
  tickets/T12345/.solution.json     -> ne pas ouvrir, c'est la correction :)
"""

import os
import sys
import json
import random
import shutil
import datetime

# Dossier des ressources (templates) : à côté des .py, ou dans le paquet PyInstaller
_RES = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RES)
# Dossier de travail (tickets) : à côté de l'exe, ou à côté des .py
_BASE = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
TICKETS = os.path.join(_BASE, 'tickets')

import builder
import faults
import ticket as ticketgen
import checker
import exercises
import missions

THEMES = {'1': ('adressage', 'Adressage IP des postes'),
          '2': ('cablage', 'Câblage'),
          '3': ('materiel', 'Matériel'),
          '4': ('routeur', 'Routeur'),
          '5': ('dhcp', 'DHCP'),
          '6': ('switch', 'Administration du switch')}
MAX_LEVEL = 3  # 1-2 : une panne ; 3 : deux pannes simultanées. 4-5 (leurres, cascade) à venir
EX_HISTORY = os.path.join(_BASE, 'exercices_historique.json')


def ask(prompt, choices):
    while True:
        r = input(prompt).strip()
        if r in choices:
            return r
        print(f'  Choix invalide ({"/".join(choices)})')


def open_in_pt(path):
    """Ouvre le fichier avec Packet Tracer si l'association .pkt existe (Windows)."""
    if hasattr(os, 'startfile'):
        try:
            os.startfile(path)
            return True
        except OSError:
            pass
    return False


def load_meta(folder):
    with open(os.path.join(folder, '.solution.json'), encoding='utf-8') as f:
        return json.load(f)


def save_meta(folder, meta):
    with open(os.path.join(folder, '.solution.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def list_tickets(status=None):
    if not os.path.isdir(TICKETS):
        return []
    out = []
    for name in sorted(os.listdir(TICKETS)):
        folder = os.path.join(TICKETS, name)
        if os.path.isfile(os.path.join(folder, '.solution.json')):
            meta = load_meta(folder)
            if status is None or meta.get('status') == status:
                out.append((name, folder, meta))
    return out


# ─── 1. Nouveau ticket ───────────────────────────────────────────────────────

def new_ticket():
    print('\n  Mode : 1) Surprise   2) Choisir un thème   3) Choisir une panne précise')
    mode = ask('  > ', ['1', '2', '3'])
    level = int(ask(f'  Difficulté (1-{MAX_LEVEL}) : ', [str(i) for i in range(1, MAX_LEVEL + 1)]))

    theme, fault_id = None, None
    if mode == '2':
        for k, (_, label) in THEMES.items():
            print(f'   {k}) {label}')
        theme = THEMES[ask('  > ', list(THEMES))][0]
    elif mode == '3':
        ids = [fid for fid, f in faults.CATALOGUE.items() if f['level'] <= level]
        for i, fid in enumerate(ids, 1):
            print(f'   {i}) {fid}')
        fault_id = ids[int(ask('  > ', [str(i) for i in range(1, len(ids) + 1)])) - 1]

    # Topologie compatible avec la panne ou le thème demandé
    seed = random.randint(1, 10 ** 9)
    rng = random.Random(seed)
    topos = sorted({t for fid, f in faults.CATALOGUE.items()
                    if (fault_id in (None, fid)) and (theme in (None, f['theme'])) and f['level'] <= level
                    for t in f['topos']})
    topo_name = rng.choice(topos)

    number = f'T{rng.randint(10000, 99999)}'
    folder = os.path.join(TICKETS, number)
    os.makedirs(folder, exist_ok=True)

    _, topo = builder.build(topo_name, seed=seed, output_dir=folder)
    pkt = os.path.join(folder, 'lab.pkt')
    reports = faults.inject(topo, level=level, theme=theme, fault_id=fault_id, seed=seed, output_path=pkt)

    # Récupérer la solution, puis ne garder que lab.pkt, l'énoncé et la solution cachée
    sol_src = pkt.replace('.pkt', '_solution.json')
    with open(sol_src, encoding='utf-8') as f:
        meta = json.load(f)
    for f in os.listdir(folder):
        if f.startswith('lab_'):
            os.remove(os.path.join(folder, f))
    meta.update(status='ouvert', level=level, created=datetime.datetime.now().isoformat(timespec='minutes'),
                attempts=0, hints=0, pkt=pkt)
    save_meta(folder, meta)

    text = ticketgen.make_ticket(reports, level=level, seed=seed)
    with open(os.path.join(folder, 'ticket.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
    print('\n' + text)
    if open_in_pt(pkt):
        print('  Packet Tracer s\'ouvre avec le lab...')


# ─── 2. Valider ──────────────────────────────────────────────────────────────

def validate():
    opened = list_tickets('ouvert')
    if not opened:
        print('\n  Aucun ticket ouvert.')
        return
    print()
    for i, (name, _, meta) in enumerate(opened, 1):
        print(f'   {i}) {name}  niveau {meta["level"]}  créé le {meta["created"]}  '
              f'({meta["attempts"]} tentative(s))')
    name, folder, meta = opened[int(ask('  Ticket : ', [str(i) for i in range(1, len(opened) + 1)])) - 1]

    meta['attempts'] += 1
    result, text = checker.check(os.path.join(folder, '.solution.json'), pkt_path=meta['pkt'])
    print('\n' + text)

    if result['success']:
        meta['status'] = 'résolu'
        meta['closed'] = datetime.datetime.now().isoformat(timespec='minutes')
        save_meta(folder, meta)
        return

    print('  1) Je retente   2) Un indice   3) Abandonner et voir la solution')
    choice = ask('  > ', ['1', '2', '3'])
    if choice == '2':
        meta['hints'] += 1
        fault_list = meta.get('faults') or [meta['fault']]
        target = fault_list[result['unfixed'][0]] if result['unfixed'] else fault_list[0]
        if meta['hints'] == 1:
            print(f'\n  💡 Indice : regarde du côté de « {target["device"]} ».')
        else:
            theme = faults.CATALOGUE.get(target['id'], {}).get('theme', 'adressage')
            print(f'\n  💡 Indice 2 : le problème relève du thème « {theme} ».')
    elif choice == '3':
        meta['status'] = 'abandonné'
        print('\n' + checker.check(os.path.join(folder, '.solution.json'), pkt_path=meta['pkt'], reveal=True)[1])
    save_meta(folder, meta)


# ─── 3. Historique ───────────────────────────────────────────────────────────

def history():
    hist = _load_ex_history()
    if hist:
        print('\n  Exercices papier :')
        for kind, h in hist.items():
            pct = round(100 * h['points'] / h['max']) if h['max'] else 0
            print(f'   {exercises.GENERATORS[kind][0]:45} {h["faits"]:3} fait(s)  réussite {pct} %')
    all_t = list_tickets()
    if not all_t:
        print('\n  Aucun ticket pour l\'instant.')
        return
    solved = sum(1 for *_, m in all_t if m['status'] == 'résolu')
    print(f'\n  {len(all_t)} ticket(s), {solved} résolu(s)\n')
    for name, _, m in all_t:
        extra = f'{m["attempts"]} tentative(s), {m["hints"]} indice(s)'
        print(f'   {name}  niv.{m["level"]}  {m["status"]:10}  {extra}')


# ─── 4. Exercices papier ─────────────────────────────────────────────────────

def _load_ex_history():
    try:
        with open(EX_HISTORY, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def run_exercise(ex):
    """Pose un exercice, corrige, affiche le corrigé. Retourne (points, total, réponses, résultats)."""
    print('\n' + '─' * 64 + f'\n {ex.title}\n' + '─' * 64)
    print(' ' + ex.statement.replace('\n', '\n '))
    answers = [input(f'  {label} : ') for label in ex.fields]
    results = ex.grade(answers)
    print()
    for ok, msg in results:
        print(f'  {"✔" if ok else "✘"} {msg}')
    score = sum(ok for ok, _ in results)
    print(f'\n  Score : {score}/{len(results)}')
    if score < len(results):
        print('\n  Corrigé :')
        for line in ex.correction.splitlines():
            print('    ' + line.strip())
    return score, len(results), answers, results


def vlsm_to_pt():
    """Concevoir un plan VLSM (3 services), puis le déployer dans Packet Tracer.
    Plan valide -> c'est TON plan qui est déployé ; sinon le corrigé."""
    seed = random.randint(1, 10 ** 9)
    ex = exercises.vlsm_plan(random.Random(seed), level=1, services=3)
    pts, mx, answers, results = run_exercise(ex)
    if pts == mx:
        import ipaddress
        plan = [(name, str(ipaddress.IPv4Network(a.strip()))) for name, a in zip(ex.fields, answers)]
        print('\n  Ton plan est valide : c\'est lui que tu vas déployer.')
    else:
        plan = ex.extra['plan']
        print('\n  Ton plan contient des erreurs : tu vas déployer le corrigé ci-dessus.')
    if ask('  Générer le lab Packet Tracer ? (o/n) : ', ['o', 'n']) == 'n':
        return

    number = f'M{random.Random(seed).randint(10000, 99999)}'
    folder = os.path.join(TICKETS, number)
    os.makedirs(folder, exist_ok=True)
    pkt, text = missions.vlsm_deploy(plan, seed=seed, output_dir=folder)
    sol_src = os.path.join(folder, 'lab_solution.json')
    with open(sol_src, encoding='utf-8') as f:
        meta = json.load(f)
    os.remove(sol_src)
    meta.update(status='ouvert', level=1, created=datetime.datetime.now().isoformat(timespec='minutes'),
                attempts=0, hints=0, pkt=pkt)
    save_meta(folder, meta)
    with open(os.path.join(folder, 'ticket.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
    print('\n' + text)
    print(f'  Mission {number} créée : valide-la depuis « 2) Valider un ticket ».')
    if open_in_pt(pkt):
        print('  Packet Tracer s\'ouvre avec le lab...')


def paper_exercises():
    kinds = list(exercises.GENERATORS)
    print()
    for i, k in enumerate(kinds, 1):
        print(f'   {i}) {exercises.GENERATORS[k][0]}')
    print(f'   {len(kinds) + 1}) Série de 5 exercices au hasard')
    print(f'   {len(kinds) + 2}) Plan VLSM puis mise en place dans Packet Tracer')
    c = int(ask('  > ', [str(i) for i in range(1, len(kinds) + 3)]))
    if c == len(kinds) + 2:
        return vlsm_to_pt()
    level = int(ask('  Difficulté (1-2) : ', ['1', '2']))
    chosen = [kinds[c - 1]] if c <= len(kinds) else [None] * 5

    hist = _load_ex_history()
    total_pts = total_max = 0
    for kind in chosen:
        ex = exercises.generate(kind, level=level, seed=random.randint(1, 10 ** 9))
        pts, mx, *_ = run_exercise(ex)
        total_pts, total_max = total_pts + pts, total_max + mx
        h = hist.setdefault(ex.kind, {'faits': 0, 'points': 0, 'max': 0})
        h['faits'] += 1
        h['points'] += pts
        h['max'] += mx
    if len(chosen) > 1:
        print(f'\n  Série terminée : {total_pts}/{total_max}')
    with open(EX_HISTORY, 'w', encoding='utf-8') as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def main():
    # Console Windows : forcer l'UTF-8 pour les traits et symboles (✅, ─, 💡)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass
    os.makedirs(TICKETS, exist_ok=True)
    while True:
        print('\n' + '═' * 64)
        print('  pkt_lab — Simulateur de tickets helpdesk (Packet Tracer)')
        print('═' * 64)
        print('  1) Nouveau ticket\n  2) Valider un ticket\n  3) Historique\n  4) Exercices papier (sous-réseaux, VLSM, IPv6)\n  0) Quitter')
        try:
            c = ask('  > ', ['0', '1', '2', '3', '4'])
            if c == '1':
                new_ticket()
            elif c == '2':
                validate()
            elif c == '3':
                history()
            elif c == '4':
                paper_exercises()
            else:
                break
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:  # on reste dans le menu quoi qu'il arrive
            print(f'\n  ⚠ Erreur : {e}')


if __name__ == '__main__':
    main()
