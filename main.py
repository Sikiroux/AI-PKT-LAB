"""
pkt_lab — Générateur de labs Packet Tracer (.pka) pour s'entraîner.

Menu principal :
  1. Nouveau lab    : génère un .pka (panne(s) + consignes embarquées, bilingue)
  2. Valider un lab : vérifie ta réparation (après Ctrl+S dans Packet Tracer)
  3. Historique
  0. Quitter

Chaque .pka contient déjà son propre onglet "Instructions" (objectifs, mise en
situation, table d'adressage) — pas besoin d'un fichier d'énoncé séparé.

Les labs sont rangés dans le dossier 'labs/' à côté du programme :
  labs/L12345/lab.pka            -> à ouvrir dans Packet Tracer
  labs/L12345/.solution.json     -> ne pas ouvrir, c'est la correction :)
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
# Dossier de travail (labs) : à côté de l'exe, ou à côté des .py
_BASE = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
LABS = os.path.join(_BASE, 'labs')

import builder
import faults
import ticket as scenario
import checker
import exercises
import missions

THEMES = {'1': ('adressage', 'Adressage IP des postes'),
          '2': ('cablage', 'Câblage'),
          '3': ('materiel', 'Matériel'),
          '4': ('routeur', 'Routeur'),
          '5': ('dhcp', 'DHCP'),
          '6': ('switch', 'Administration du switch'),
          '7': ('nat', 'NAT (multi-sites)')}
LANGUES = {'1': ('fr', 'Français'), '2': ('en', 'English')}
HIDDEN_FILTERS = {'1': (None, 'Toutes'), '2': (False, 'Seulement visibles (plainte utilisateur directe)'),
                  '3': (True, 'Seulement cachées (détectables uniquement depuis la supervision)')}
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


def list_labs(status=None):
    if not os.path.isdir(LABS):
        return []
    out = []
    for name in sorted(os.listdir(LABS)):
        folder = os.path.join(LABS, name)
        if os.path.isfile(os.path.join(folder, '.solution.json')):
            meta = load_meta(folder)
            if status is None or meta.get('status') == status:
                out.append((name, folder, meta))
    return out


# ─── 1. Nouveau lab ──────────────────────────────────────────────────────────

def new_lab():
    lang = LANGUES[ask('\n  Langue : 1) Français   2) English\n  > ', list(LANGUES))][0]

    print('\n  Mode : 1) Surprise   2) Choisir un thème   3) Choisir une ou plusieurs pannes précises')
    mode = ask('  > ', ['1', '2', '3'])
    level = int(ask(f'  Difficulté (1-{MAX_LEVEL}) : ', [str(i) for i in range(1, MAX_LEVEL + 1)]))

    theme, fault_ids = None, None
    if mode == '2':
        for k, (_, label) in THEMES.items():
            print(f'   {k}) {label}')
        theme = THEMES[ask('  > ', list(THEMES))][0]
    elif mode == '3':
        ids = [fid for fid, f in faults.CATALOGUE.items() if f['level'] <= level]
        for i, fid in enumerate(ids, 1):
            print(f'   {i}) {fid}' + (' [cachée]' if faults.CATALOGUE[fid]['hidden'] else ''))
        print('  Plusieurs numéros possibles, séparés par des virgules (ex: 1,3)')
        raw = input('  > ').strip()
        picked = []
        for tok in raw.split(','):
            tok = tok.strip()
            if tok.isdigit() and 1 <= int(tok) <= len(ids):
                picked.append(ids[int(tok) - 1])
        fault_ids = picked or None

    hidden = HIDDEN_FILTERS[ask(
        '\n  Pannes cachées : 1) Toutes   2) Visibles seulement   3) Cachées seulement\n  > ',
        list(HIDDEN_FILTERS))][0]

    default_count = max(len(fault_ids or []), faults.FAULTS_PER_LEVEL.get(level, 1))
    raw_count = input(f'  Nombre de pannes (défaut {default_count}, Entrée pour garder) : ').strip()
    count = int(raw_count) if raw_count.isdigit() else default_count

    # Topologie compatible avec les pannes/thème demandés
    seed = random.randint(1, 10 ** 9)
    rng = random.Random(seed)
    if fault_ids:
        topos = sorted({t for fid in fault_ids for t in faults.CATALOGUE[fid]['topos']})
    else:
        topos = sorted({t for fid, f in faults.CATALOGUE.items()
                        if (theme in (None, f['theme'])) and f['level'] <= level
                        and (hidden is None or f['hidden'] == hidden)
                        for t in f['topos']})
    topo_name = rng.choice(topos)

    number = f'L{rng.randint(10000, 99999)}'
    folder = os.path.join(LABS, number)
    os.makedirs(folder, exist_ok=True)

    _, topo = builder.build(topo_name, seed=seed, output_dir=folder)
    pka = os.path.join(folder, 'lab.pka')
    reports = faults.inject(topo, level=level, theme=theme, fault_ids=fault_ids, hidden=hidden,
                             count=count, seed=seed, output_path=pka, lang=lang)

    # Récupérer la solution, puis ne garder que lab.pka et la solution cachée
    sol_src = pka.rsplit('.', 1)[0] + '_solution.json'
    with open(sol_src, encoding='utf-8') as f:
        meta = json.load(f)
    for f in os.listdir(folder):
        if f.startswith('lab_'):
            os.remove(os.path.join(folder, f))
    meta.update(status='ouvert', level=level, created=datetime.datetime.now().isoformat(timespec='minutes'),
                attempts=0, hints=0, pkt=pka)
    save_meta(folder, meta)

    print(f'\n  Lab {number} créé ({pka}).')
    print('  Les consignes complètes (objectifs, mise en situation, table d\'adressage) '
          'sont dans l\'onglet Instructions du fichier, dans Packet Tracer.')
    print('  Aperçu :')
    for p in scenario.scenario_paragraphs(reports, lang=lang, seed=seed):
        print(f'   « {p} »')
    if open_in_pt(pka):
        print('  Packet Tracer s\'ouvre avec le lab...')


# ─── 2. Valider ──────────────────────────────────────────────────────────────

def validate():
    opened = list_labs('ouvert')
    if not opened:
        print('\n  Aucun lab ouvert.')
        return
    print()
    for i, (name, _, meta) in enumerate(opened, 1):
        print(f'   {i}) {name}  niveau {meta["level"]}  créé le {meta["created"]}  '
              f'({meta["attempts"]} tentative(s))')
    name, folder, meta = opened[int(ask('  Lab : ', [str(i) for i in range(1, len(opened) + 1)])) - 1]

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
    all_t = list_labs()
    if not all_t:
        print('\n  Aucun lab pour l\'instant.')
        return
    solved = sum(1 for *_, m in all_t if m['status'] == 'résolu')
    print(f'\n  {len(all_t)} lab(s), {solved} résolu(s)\n')
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
    folder = os.path.join(LABS, number)
    os.makedirs(folder, exist_ok=True)
    pkt, text = missions.vlsm_deploy(plan, seed=seed, output_dir=folder)
    sol_src = os.path.join(folder, 'lab_solution.json')
    with open(sol_src, encoding='utf-8') as f:
        meta = json.load(f)
    os.remove(sol_src)
    meta.update(status='ouvert', level=1, created=datetime.datetime.now().isoformat(timespec='minutes'),
                attempts=0, hints=0, pkt=pkt)
    save_meta(folder, meta)
    with open(os.path.join(folder, 'enonce.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
    print('\n' + text)
    print(f'  Mission {number} créée : valide-la depuis « 2) Valider un lab ».')
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
    os.makedirs(LABS, exist_ok=True)
    while True:
        print('\n' + '═' * 64)
        print('  pkt_lab — Générateur de labs Packet Tracer (.pka)')
        print('═' * 64)
        print('  1) Nouveau lab\n  2) Valider un lab\n  3) Historique\n  4) Exercices papier (sous-réseaux, VLSM, IPv6)\n  0) Quitter')
        try:
            c = ask('  > ', ['0', '1', '2', '3', '4'])
            if c == '1':
                new_lab()
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
