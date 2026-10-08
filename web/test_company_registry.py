import copy
import json
import tempfile
import unittest
from pathlib import Path
import company_registry as registry
from workspace_model import Workspace


def fixture(env='env', seed='seed'):
    return dict(seed=seed, environment_id=env, requester='Mina', directory_user_id='u1',
                devices={'client': dict(serial='s1', name='PC-1', ip='192.168.1.2'),
                         'client2': dict(serial='s2', name='PC-2'), 'technician': dict(serial='tech', name='LT-TECH')},
                directory={'users': {'u1': dict(display_name='Mina', username='mina'), 'u2': dict(display_name='Alex', username='alex')}},
                client_workspaces={'s2': dict(user_id='u2', requester='Alex', device=dict(serial='s2', name='PC-2'))})


class RegistryTests(unittest.TestCase):
    def test_deterministic_initial_links_and_environment_scope(self):
        a, b = fixture(), fixture('second')
        registry.ensure(a); registry.ensure(b)
        self.assertEqual(set(a['company_registry']['people']), set(b['company_registry']['people']))
        self.assertEqual(registry.links(a, 's1')['asset_id'], registry.links(b, 's1')['asset_id'])
        self.assertNotEqual(registry.links(a, 's1')['environment_id'], registry.links(b, 's1')['environment_id'])

    def test_idempotent_preserves_extra_business_fields(self):
        s = fixture(); self.assertTrue(registry.ensure(s))
        p = next(iter(s['company_registry']['people'].values())); p['department'] = 'Comptabilité'
        self.assertFalse(registry.ensure(s)); self.assertEqual(p['department'], 'Comptabilité')

    def test_rename_keeps_links_and_refreshes_display(self):
        s = fixture(); registry.ensure(s); before = registry.links(s, 's1')
        s['devices']['client']['name'] = 'PC-MINA'; s['directory']['users']['u1']['display_name'] = 'Mina E.'
        registry.ensure(s); self.assertEqual(before, registry.links(s, 's1'))
        self.assertEqual(s['company_registry']['people'][before['employee_id']]['display_name'], 'Mina E.')

    def test_second_pc_and_technician_are_distinct(self):
        s = fixture(); registry.ensure(s)
        self.assertNotEqual(registry.links(s, 's1')['employee_id'], registry.links(s, 's2')['employee_id'])
        self.assertIsNone(registry.links(s, 'tech')['employee_id'])
        self.assertEqual(len(s['company_registry']['people']), 2)

    def test_account_removed_is_retained_as_missing(self):
        s = fixture(); registry.ensure(s); refs = registry.links(s, 's1'); del s['directory']['users']['u1']
        registry.ensure(s); p = s['company_registry']['people'][refs['employee_id']]
        self.assertFalse(p['account_present']); self.assertEqual(p['account_id'], 'u1')

    def test_removed_asset_not_resolved_or_deleted(self):
        s = fixture(); registry.ensure(s); ident = registry.links(s, 's2')['asset_id']
        del s['devices']['client2']; registry.ensure(s)
        self.assertFalse(s['company_registry']['assets'][ident]['represented'])
        self.assertEqual(registry.links(s, 's2'), {})

    def test_ambiguous_serial_never_resolves(self):
        s = fixture(); s['devices']['client2']['serial'] = 's1'; registry.ensure(s)
        self.assertEqual(registry.links(s, 's1'), {})

    def test_foreign_environment_is_rejected(self):
        s = fixture(); registry.ensure(s); s['environment_id'] = 'other'
        self.assertEqual(registry.links(s, 's1'), {})
        with self.assertRaises(ValueError): registry.ensure(s)

    def test_tickets_link_known_target_only_without_changing_result(self):
        s = fixture(); registry.ensure(s)
        tickets = [dict(id='INC-1000', kind='workspace', complete=False),
                   dict(id='new', kind='workspace', target_serial='s2', complete=True),
                   dict(id='old', kind='workspace', environment_id='foreign', target_serial='s1'),
                   dict(id='unknown', kind='workspace'), dict(id='lab', kind='lab', target_serial='s1')]
        self.assertTrue(registry.link_tickets(s, tickets)); self.assertFalse(registry.link_tickets(s, tickets))
        self.assertEqual(tickets[0]['target_serial'], 's1'); self.assertFalse(tickets[0]['complete'])
        self.assertEqual(tickets[1]['employee_id'], registry.links(s, 's2')['employee_id'])
        self.assertTrue(tickets[1]['complete'])
        for t in tickets[2:]: self.assertNotIn('employee_id', t)

    def test_public_report_is_copy_without_credentials_or_full_staff_claim(self):
        s = fixture(); s['directory']['users']['u1']['password'] = 'secret'; registry.ensure(s)
        report = registry.public(s); self.assertNotIn('secret', json.dumps(report))
        self.assertFalse(report['complete_staff']); report['people'].clear()
        self.assertEqual(len(s['company_registry']['people']), 2)

    def test_projection_cannot_rewrite_canonical_registry(self):
        s = fixture(); registry.ensure(s); old = copy.deepcopy(s['company_registry'])
        s['_client_view'] = 's2'; s['devices']['client'] = s['devices']['client2']
        self.assertFalse(registry.ensure(s)); self.assertEqual(old, s['company_registry'])

    def test_initial_second_account_id_is_reproducible(self):
        import directory_adapter as ad
        import files_adapter as fa
        import dns_adapter as da
        import desktop_services as ds
        import client_workspaces as clients
        from workspace_model import generate
        states = []
        for env in ('first', 'second'):
            s = generate('reproducible');s['environment_id'] = env
            s['devices'] = {k: dict(name=k, serial=k, ip=ip) for k, ip in [('client','192.168.1.2'), ('server','192.168.1.10'), ('technician','192.168.1.20'), ('client2','192.168.1.3')]}
            ad.ensure(s);fa.ensure(s);da.ensure(s);ds.ensure(s);clients.ensure(s);registry.ensure(s)
            states.append(s)
        self.assertEqual(states[0]['client_workspaces']['client2']['user_id'], states[1]['client_workspaces']['client2']['user_id'])
        self.assertEqual(set(states[0]['company_registry']['people']), set(states[1]['company_registry']['people']))

    def test_saved_registry_preserves_assignment_across_restart(self):
        s = fixture();registry.ensure(s);refs = registry.links(s, 's2')
        s.update(observation=None, remote_session=False, validated=False)
        for profile in s['client_workspaces'].values():profile['local'] = {};profile['ftp_session'] = None
        s['desktop_services'] = {'endpoint': {}, 'printing': {'printer': {}}, 'ftp': {'sessions': {}}}
        s['dns_service'] = {'clients': {'client': {}}, 'cache': {}}
        # Profiles for the canonical endpoint are normally populated by clients.ensure.
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'session.json';p.write_text(json.dumps(s))
            restored = Workspace(p).state
            self.assertEqual(refs, registry.links(restored, 's2'))

    def test_migration_backups_original_session_before_registry_is_saved(self):
        from unittest.mock import patch
        from workspace_app import Controller
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'session.json';raw = json.dumps(fixture()).encode();p.write_bytes(raw)
            w = Workspace.__new__(Workspace);w.path = p;w.state = fixture()
            c = Controller.__new__(Controller)
            with patch('workspace_app.files_adapter.ensure', return_value=False), patch('workspace_app.dns_adapter.ensure', return_value=False), patch('workspace_app.technician_model.ensure', return_value=False), patch('workspace_app.desktop_services.ensure', return_value=False), patch('workspace_app.clients.ensure', return_value=False):
                c._migrate_directory(w)
            self.assertEqual(p.with_suffix('.before-registry.json').read_bytes(), raw)
            self.assertIn('company_registry', json.loads(p.read_text()))
