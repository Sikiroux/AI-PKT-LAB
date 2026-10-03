"""
worksheet.py — Fiche HTML autonome compagnon d'un .pka (bilingue FR/EN).

Inspiré du "lab companion" que NetAcad fournit à côté de ses .pka (voir un
exemplaire réel fourni par Damien : simple HTML/CSS/JS, un bouton
"Montrer/Masquer la réponse" par question qui bascule l'affichage d'un
<div> caché — aucune notation, aucun lien avec Packet Tracer). Repris ici en
plus simple pour nos labs :
  - mêmes objectifs/mise en situation/table d'adressage que l'onglet
    Instructions du .pka (dupliqués : lisibles sans ouvrir Packet Tracer) ;
  - par panne : indices progressifs (appareil, puis thème) et résultat
    attendu (cause + solution), chacun derrière un bouton Montrer/Masquer ;
  - autonome : peut servir d'auto-correction même sans lancer checker.py
    (pas de vérification automatique de la config réparée, juste la
    référence à comparer soi-même — moins rigoureux que checker.py, mais
    utilisable sans Python installé).
"""

import instructions as _instr

TEXT = {
    'fr': {
        'hint1_btn': 'Montrer l\'indice 1 (appareil)',
        'hint2_btn': 'Montrer l\'indice 2 (thème)',
        'result_btn': 'Montrer le résultat attendu',
        'hide_btn': 'Masquer',
        'hint1_text': 'Regarde du côté de « {device} ».',
        'hint2_text': 'Le problème relève du thème « {theme} ».',
        'cause_label': 'Cause :',
        'solution_label': 'Solution :',
        'fault_heading': 'Panne {i}',
        'mission_heading': 'Tâche {i}',
        'fiche_title': 'Fiche de correction — {title}',
        'offline_note': 'Cette fiche fonctionne sans Packet Tracer ni Python : elle ne vérifie pas '
                        'automatiquement ta réparation (contrairement à « Valider un lab » dans '
                        'pkt_lab), mais te permet de comparer toi-même une fois que tu as fini.',
    },
    'en': {
        'hint1_btn': 'Show hint 1 (device)',
        'hint2_btn': 'Show hint 2 (theme)',
        'result_btn': 'Show expected result',
        'hide_btn': 'Hide',
        'hint1_text': 'Look around « {device} ».',
        'hint2_text': 'The issue falls under the « {theme} » theme.',
        'cause_label': 'Cause:',
        'solution_label': 'Solution:',
        'fault_heading': 'Issue {i}',
        'mission_heading': 'Task {i}',
        'fiche_title': 'Answer sheet — {title}',
        'offline_note': "This sheet works without Packet Tracer or Python: it doesn't automatically "
                        "verify your fix (unlike pkt_lab's «Validate a lab»), but lets you "
                        "self-check once you're done.",
    },
}

_STYLE = """
body { font-family: Arial, sans-serif; margin: 1.5rem; max-width: 50rem; color: #222; }
h1 { font-size: 1.5em; } h2 { font-size: 1.2em; margin-top: 1.5em; } h3 { font-size: 1.05em; }
table { border-collapse: collapse; margin: 0.5em 0 1em; width: 100%; }
th, td { border: 1px solid #999; padding: 0.4em 0.6em; font-size: 0.9em; text-align: left; }
th { background: #dbe5f1; }
.step { border: 1px solid #ccc; border-radius: 4px; padding: 0.8em 1em; margin: 1em 0; }
.reveal-btn { background: #3d692b; color: #fff; border: 0; padding: 0.5em 1em; cursor: pointer;
              margin: 0.3em 0.3em 0.3em 0; border-radius: 2px; }
.answer-box { background: #f2dbdb; padding: 0.6em 0.8em; margin-top: 0.4em; border-radius: 2px; }
.hidden { display: none; }
.note { font-style: italic; color: #555; font-size: 0.9em; }
"""

_SCRIPT = """
document.querySelectorAll('.reveal-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var box = document.getElementById(btn.dataset.target);
    var hiding = !box.classList.contains('hidden');
    box.classList.toggle('hidden');
    btn.textContent = hiding ? btn.dataset.showLabel : btn.dataset.hideLabel;
  });
});
"""


def _esc(s):
    return (str(s) if s is not None else '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _reveal_button(uid, show_label, hide_label):
    return (f'<button class="reveal-btn" data-target="{uid}" '
            f'data-show-label="{_esc(show_label)}" data-hide-label="{_esc(hide_label)}">{_esc(show_label)}</button>')


def _step_section(t, i, report, is_mission, theme):
    uid = f'step{i}'
    heading = (t['mission_heading'] if is_mission else t['fault_heading']).format(i=i)
    parts = [f'<div class="step"><h3>{_esc(heading)}</h3>']
    if not is_mission:
        parts.append(_reveal_button(f'{uid}-hint1', t['hint1_btn'], t['hide_btn']))
        parts.append(f'<div id="{uid}-hint1" class="answer-box hidden">'
                     f'{_esc(t["hint1_text"].format(device=report["device"]))}</div>')
        parts.append(_reveal_button(f'{uid}-hint2', t['hint2_btn'], t['hide_btn']))
        parts.append(f'<div id="{uid}-hint2" class="answer-box hidden">'
                     f'{_esc(t["hint2_text"].format(theme=theme))}</div>')
    parts.append(_reveal_button(f'{uid}-result', t['result_btn'], t['hide_btn']))
    parts.append(f'<div id="{uid}-result" class="answer-box hidden">')
    if not is_mission:
        parts.append(f'<p><strong>{_esc(t["cause_label"])}</strong> {_esc(report["cause"])}</p>')
    parts.append(f'<p><strong>{_esc(t["solution_label"])}</strong> {_esc(report["solution"])}</p>')
    parts.append('</div></div>')
    return ''.join(parts)


def build_worksheet_html(lang, topo, reports, scenario_paragraphs=(), is_mission=False, themes=None):
    """Fiche HTML autonome (bilingue) : objectifs/mise en situation/table
    d'adressage (dupliqués de l'onglet Instructions du .pka) + un bloc par
    panne/tâche avec indices progressifs et résultat attendu, chacun
    derrière un bouton Montrer/Masquer."""
    t = TEXT[lang]
    title = _instr.build_title(lang, len(reports), is_mission=is_mission)
    body = _instr.build_html(lang, topo, scenario_paragraphs, is_mission=is_mission)
    # Récupère juste le <body>...</body> de la page Instructions pour éviter
    # de dupliquer tout le squelette HTML ici.
    inner = body.split('<body>', 1)[1].rsplit('</body>', 1)[0]

    themes = themes or {}
    sections = [_step_section(t, i, r, is_mission, themes.get(r.get('id'), ''))
                for i, r in enumerate(reports, 1)]

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<title>{_esc(t["fiche_title"].format(title=title))}</title>'
        f'<style>{_STYLE}</style></head><body>'
        f'{inner}'
        + ''.join(sections)
        + f'<p class="note">{_esc(t["offline_note"])}</p>'
        + f'<script>{_SCRIPT}</script></body></html>'
    )


if __name__ == '__main__':
    demo_topo = {'devices': {
        'R1': {'type': 'router', 'interfaces': {'GigabitEthernet0/0': {'ip': '10.1.1.1', 'mask': '255.255.255.0'}}},
        'PC1': {'type': 'pc', 'ip': '10.1.1.10', 'mask': '255.255.255.0', 'gateway': '10.1.1.1'},
    }}
    demo_reports = [{'id': 'cable_missing', 'device': 'PC1', 'cause': 'Câble débranché',
                     'solution': 'Rebrancher le câble.'}]
    print(build_worksheet_html('fr', demo_topo, demo_reports,
                               ['Plus de réseau sur PC1 depuis ce matin.'],
                               themes={'cable_missing': 'cablage'})[:500])
