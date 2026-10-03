"""
Suite de tests de pkt_lab — à lancer avant chaque commit :

    python tests/test_all.py

Sans dépendance (pas besoin de pytest). Chaque test reproduit un bug réel
rencontré pendant le développement ou un comportement validé dans Packet Tracer.
"""
import io
import os
import random
import shutil
import sys
import tempfile
import contextlib
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import ptexplorer
import exercises
import missions
import ticket
import worksheet
from builder import build, THEMES
from faults import inject, available, CATALOGUE
from checker import check, read_state

TMP = tempfile.mkdtemp(prefix='pktlab_tests_')
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures')


def test_twofish_pur_python():
    """Twofish pur Python : vecteur officiel (clé et bloc nuls)."""
    from twofish_pure import Twofish
    assert Twofish(bytes(16)).encrypt(bytes(16)).hex().upper() == '9F589F5CF6122C32B6BFEC2F2AE8C35A'


def test_aller_retour_chiffrement():
    """Bug du fork corrigé : la détection du format sur 2 octets rendait ~1 fichier sur 128 illisible."""
    rng = random.Random(0)
    src, pkt, out = (os.path.join(TMP, n) for n in ('a.xml', 'a.pkt', 'b.xml'))
    for i in range(300):
        data = rng.randbytes(64 + i * 37)
        with open(src, 'wb') as f:
            f.write(data)
        with contextlib.redirect_stdout(io.StringIO()):
            ptexplorer.ptfile_encode(src, pkt)
            ptexplorer.ptfile_decode(pkt, out)
        with open(out, 'rb') as f:
            assert f.read() == data, f'aller-retour KO (taille {len(data)})'


def test_generation_lisible():
    for i in range(20):
        for theme in THEMES:
            pkt, _ = build(theme, seed=i, output_dir=TMP)
            read_state(pkt)


def test_chaque_panne_detectee_et_lab_sain_valide():
    for theme in THEMES:
        for fid in available(theme, 3):
            for seed in (1, 2):
                _, topo = build(theme, seed=seed, output_dir=TMP)
                out = os.path.join(TMP, 'p.pkt')
                inject(topo, fault_id=fid, seed=seed, output_path=out)
                sol = out.replace('.pkt', '_solution.json')
                panne, _ = check(sol)
                sain, _ = check(sol, pkt_path=topo['pkt_path'])
                assert not panne['success'], f'{theme}/{fid} : panne non détectée'
                assert sain['success'] and not sain['collateral'], f'{theme}/{fid} : fausse alerte sur lab sain'


def test_chaque_panne_a_ses_tickets():
    assert not [f for f in CATALOGUE if f not in ticket.SYMPTOMS]


def test_chaque_panne_bilingue():
    assert all({'fr', 'en'} <= set(ticket.SYMPTOMS[f]) for f in CATALOGUE)


def test_filtre_pannes_cachees():
    for topo_name in THEMES:
        visibles = available(topo_name, 3, hidden=False)
        cachees = available(topo_name, 3, hidden=True)
        toutes = available(topo_name, 3)
        assert set(visibles) | set(cachees) == set(toutes)
        assert not (set(visibles) & set(cachees))
        assert all(not CATALOGUE[f]['hidden'] for f in visibles)
        assert all(CATALOGUE[f]['hidden'] for f in cachees)


def test_selection_precise_de_plusieurs_pannes():
    _, topo = build('simple_lan', seed=7, output_dir=TMP)
    out = os.path.join(TMP, 'multi.pka')
    wanted = ['pc_wrong_gateway', 'cable_missing']
    reports = inject(topo, fault_ids=wanted, count=len(wanted), seed=7, output_path=out)
    assert [r['id'] for r in reports] == wanted


def test_instructions_bilingues_dans_le_pka():
    import instructions
    for lang in ('fr', 'en'):
        _, topo = build('simple_lan', seed=9, output_dir=TMP)
        out = os.path.join(TMP, f'instr_{lang}.pka')
        inject(topo, fault_id='cable_missing', seed=9, output_path=out, lang=lang)
        xml_out = os.path.join(TMP, f'instr_{lang}.xml')
        with contextlib.redirect_stdout(io.StringIO()):
            ptexplorer.ptfile_decode(out, xml_out)
        root = ET.parse(xml_out).getroot()
        tags = [c.tag for c in root]
        assert tags.index('ACTIVITY') == tags.index('OPTIONS') + 1, 'ACTIVITY doit suivre OPTIONS'
        activity = root.find('ACTIVITY')
        assert activity.get('ENABLED') == 'no', 'la notation native PT doit rester désactivée'
        page = activity.find('INSTRUCTIONS/PAGE')
        assert page is not None and '<table' in page.text and '<h1>' in page.text
        marker = 'Mise en situation' if lang == 'fr' else 'Background / Scenario'
        assert marker in page.text


def test_fiche_html_compagnon():
    _, topo = build('simple_lan', seed=4, output_dir=TMP)
    out = os.path.join(TMP, 'fiche.pka')
    reports = inject(topo, level=3, seed=4, output_path=out, lang='fr')
    html_path = out.replace('.pka', '.html')
    assert os.path.exists(html_path)
    with open(html_path, encoding='utf-8') as f:
        content = f.read()
    assert content.count('class="step"') == len(reports)
    for r in reports:
        assert r['cause'] in content and r['solution'] in content
        assert r['device'] in content  # indice 1


def test_niveau3_deux_pannes_distinctes():
    for seed in range(20):
        theme = list(THEMES)[seed % len(THEMES)]
        _, topo = build(theme, seed=seed, output_dir=TMP)
        out = os.path.join(TMP, 'm.pkt')
        reports = inject(topo, level=3, seed=seed, output_path=out)
        devices = [r['device'] for r in reports]
        assert len(reports) == 2 and len(set(devices)) == 2, devices
        assert 'PC-ADMIN' not in devices, 'une panne « poste » ne doit jamais viser PC-ADMIN'


def test_panne_routeur_ne_touche_pas_ladmin():
    _, topo = build('simple_lan', seed=5, output_dir=TMP)
    out = os.path.join(TMP, 'w.pkt')
    inject(topo, fault_id='router_wrong_ip', seed=5, output_path=out)
    lines = read_state(out)['devices']['R1']['running']
    assert f' ip address {topo["admin"]["gateway"]} 255.255.255.0' in lines


def test_mission_vierge_zero_point_gratuit():
    """Même défaut que les 28 % gratuits du .pka : un lab vierge doit valoir 0."""
    d = os.path.join(TMP, 'mission')
    os.makedirs(d, exist_ok=True)
    missions.vlsm_deploy([('RH', '10.1.1.0/26'), ('Direction', '10.1.1.64/27'), ('Accueil', '10.1.1.96/28')],
                         seed=1, output_dir=d)
    assert check(os.path.join(d, 'lab_solution.json'))[0]['fixed'] == 0


def test_fichier_reel_sauvegarde_par_pt():
    """Fichier configuré à la main par Damien dans PT 9 : 4 tâches sur 7 faites, sauvegarde manquante."""
    d = os.path.join(TMP, 'reel')
    os.makedirs(d, exist_ok=True)
    missions.vlsm_deploy([('Logistique', '172.17.253.0/26'), ('Comptabilité', '172.17.253.64/28'),
                          ('Production', '172.17.253.80/28')], seed=1, output_dir=d)
    res, _ = check(os.path.join(d, 'lab_solution.json'),
                   pkt_path=os.path.join(FIXTURES, 'mission_vlsm_damien_4sur7.pkt'))
    assert res['fixed'] == 4 and res['unsaved'] == ['R1'], res


def test_fichier_activite_reel_repare_par_pt():
    """Régression : un vrai .pka (gabarit multisite_ospf_nat, panne OSPF)
    réparé et sauvegardé par Damien dans PT 9. checker.py lisait le mauvais
    instantané (le 2e, 'working') et rapportait à tort 'non réparé' alors que
    la correction était bien là, dans le 1er instantané ('initial') — c'est
    celui que PT réécrit à Ctrl+S, pas le 2e comme on le pensait."""
    res, _ = check(os.path.join(FIXTURES, 'ospf_network_missing_damien_fixed_solution.json'),
                   pkt_path=os.path.join(FIXTURES, 'ospf_network_missing_damien_fixed.pka'))
    assert res['success'] and res['fixed'] == 1, res


def test_exercices_papier_coherents():
    for kind in exercises.GENERATORS:
        for seed in range(50):
            ex = exercises.generate(kind, level=1 + seed % 2, seed=seed)
            assert ex.statement and ex.fields and ex.correction


def test_vlsm_refuse_les_erreurs():
    ex = exercises.generate('vlsm_plan', seed=4)   # Informatique 7, Production 6, Commercial 3 dans 10.155.73.0/24
    assert all(ok for ok, _ in ex.grade(['10.155.73.0/28', '10.155.73.16/29', '10.155.73.24/29']))
    assert not all(ok for ok, _ in ex.grade(['10.155.73.0/28', '10.155.73.8/29', '10.155.73.24/29']))  # chevauchement
    assert not all(ok for ok, _ in ex.grade(['10.155.73.4/28', '10.155.73.16/29', '10.155.73.24/29']))  # non aligné



def test_regression_timers_et_trunks():
    from checker import evaluate
    def evaluate_lines(kind, lines, *args):
        state = {'devices': {'S': {'running': ['interface GigabitEthernet0/1'] +
                                   [' ' + line for line in lines] + ['!']}}}
        return evaluate([kind, 'S', 'GigabitEthernet0/1', *args], state)[0]
    assert evaluate_lines('ospf_default_timers', ['ip ospf hello-interval 10', 'ip ospf dead-interval 40'])
    assert not evaluate_lines('ospf_default_timers', ['ip ospf hello-interval 5'])
    for expression in (None, 'all', '10,20', '10-20', '1-9,10-30', 'except 30-40'):
        lines = ['switchport mode trunk']
        if expression is not None:
            lines.append('switchport trunk allowed vlan ' + expression)
        assert evaluate_lines('trunk_allowed_vlan', lines, 20), expression
    for expression in ('none', '10', '1-19', 'except 20', 'remove 20', 'bad'):
        assert not evaluate_lines('trunk_allowed_vlan', ['switchport trunk allowed vlan ' + expression], 20)
    assert evaluate_lines('trunk_allowed_vlan', ['switchport trunk allowed vlan 10',
                                               'switchport trunk allowed vlan add 20'], 20)


def test_regression_dns_et_bundle_local():
    from builder import THEMES
    from faults import f_channel_group_mismatch, _devices, _config_lines, _interface_block
    import instructions
    lab, topo = THEMES['multisite_ospf_nat'](random.Random(7))
    path = os.path.join(TMP, 'dns_regression.xml')
    with contextlib.redirect_stdout(io.StringIO()):
        lab.to_packettracer_xml(path)
    root = ET.parse(path).getroot()
    engine = _devices(root)['WEB'].find('ENGINE')
    assert engine.findtext('DNS_SERVER/ENABLED') == '1'
    records = engine.findall('DNS_SERVER/NAMESERVER-DATABASE/RESOURCE-RECORD')
    assert len(records) == 1
    assert records[0].findtext('NAME') == topo['web_hostname']
    assert records[0].findtext('IPADDRESS') == topo['devices']['WEB']['ip']
    acl = topo['devices']['R-EDGE']['acl_lines']
    assert any(' udp ' in line and line.endswith('eq 53') for line in acl)
    assert any(' tcp ' in line and line.endswith('eq 53') for line in acl)
    assert topo['web_hostname'] in instructions.build_html('fr', topo)
    lab, topo = THEMES['etherchannel'](random.Random(7))
    path = os.path.join(TMP, 'bundle_regression.xml')
    with contextlib.redirect_stdout(io.StringIO()):
        lab.to_packettracer_xml(path)
    root = ET.parse(path).getroot()
    before = {name: _config_lines(dev.find('ENGINE')) for name, dev in _devices(root).items()}
    report = f_channel_group_mismatch(root, topo, random.Random(7))
    switch = report['device']
    ec = topo['devices'][switch]['etherchannel']
    lines = _config_lines(_devices(root)[switch].find('ENGINE'))
    groups = []
    for iface in ec['members']:
        start, end = _interface_block(lines, iface)
        groups += [int(line.split()[1]) for line in lines[start+1:end] if line.strip().startswith('channel-group ')]
    assert sorted(groups) == [ec['group'], ec['group'] + 1]
    for name, dev in _devices(root).items():
        if name != switch:
            assert _config_lines(dev.find('ENGINE')) == before[name]
    assert 'switch_no_default_gateway' not in available('switched_redundant', 3)
    assert 'switch_no_default_gateway' in available('simple_lan', 3)


if __name__ == '__main__':
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_') and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✔ {name}')
        except Exception as e:
            failed += 1
            print(f'  ✘ {name} : {type(e).__name__} {e}')
    shutil.rmtree(TMP, ignore_errors=True)
    print(f'\n{len(tests) - failed}/{len(tests)} tests OK')
    sys.exit(1 if failed else 0)
