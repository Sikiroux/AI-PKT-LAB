"""Tests du moteur de partages de fichiers simulés (web/sim_files.py).

Couvre un par un les 26 critères d'acceptation de la section 9 du brief
(docs/BRIEF-IA-PARTAGES-FICHIERS.md). Lancer :
    python -m unittest discover -s web -p "test_sim_files.py"
"""
import copy
import json
import random
import unittest

import sim_files as sf


ENV = 'env-test-1'
SERVER = {'id': ENV, 'name': 'SRV-FILES', 'ip': '10.0.0.5', 'dns_name': 'files.corp.local'}
PRINCIPALS = {'user_ids': ['alice', 'bob'], 'group_ids': ['grp-staff']}
NOW = 1_700_000_000

FULL_ACTOR = {'id': 'tech-1', 'environment_id': ENV, 'permissions': [sf.CAPABILITY_FILES]}
NO_CAP_ACTOR = {'id': 'tech-0', 'environment_id': ENV, 'permissions': []}
WRONG_ENV_ACTOR = {'id': 'tech-2', 'environment_id': 'other-env', 'permissions': [sf.CAPABILITY_FILES]}


def make_service(seed=42, environment_id=ENV, server=None, principals=None, now=NOW):
    return sf.generate_file_service(seed, environment_id, server or SERVER, principals or PRINCIPALS, now)


def first_share_and_user(service):
    share_id = next(iter(service['shares']))
    user_id = service['principal_catalog']['user_ids'][0] if False else PRINCIPALS['user_ids'][0]
    return share_id, user_id


def passing_context(user='alice', groups=None, account_allowed=True, authentication_valid=True,
                    address_mode='ip', at=NOW, evidence='tcp445', name_resolution=None):
    context = {
        'environment_id': ENV,
        'source_device_id': 'dev-pc1',
        'target_device_id': ENV,
        'network': {'status': 'up', 'observed_at': at - 5, 'valid_until': at + 30,
                   'source_device_id': 'dev-pc1', 'target_device_id': ENV, 'evidence': evidence},
        'address_mode': address_mode,
        'identity': {'user_id': user, 'group_ids': list(groups or []),
                    'account_allowed': account_allowed, 'authentication_valid': authentication_valid},
    }
    if address_mode == 'name':
        context['name_resolution'] = name_resolution or {
            'status': 'resolved', 'resolved_ip': SERVER['ip'], 'observed_at': at - 5, 'valid_until': at + 30}
    return context


def strip_dynamic(service):
    """Copie du service sans les champs générés aléatoirement non déterministes
    (aucun ici — generate_file_service n'utilise pas de sel comme sim_ad — mais
    on garde cette fonction pour symétrie et robustesse si cela change)."""
    return copy.deepcopy(service)


class GenerationTests(unittest.TestCase):
    def test_reproducible_with_same_inputs(self):
        a = make_service(seed='same')
        b = make_service(seed='same')
        self.assertEqual(a, b)

    def test_different_seed_changes_layout(self):
        a = make_service(seed='seed-a')
        b = make_service(seed='seed-b')
        self.assertNotEqual(a['shares'], b['shares'])

    def test_does_not_touch_global_random_stream(self):
        random.seed(12345)
        before = random.getstate()
        make_service(seed='anything')
        after = random.getstate()
        self.assertEqual(before, after)

    def test_does_not_mutate_server_or_principals_input(self):
        server_copy = copy.deepcopy(SERVER)
        principals_copy = copy.deepcopy(PRINCIPALS)
        make_service()
        self.assertEqual(server_copy, SERVER)
        self.assertEqual(principals_copy, PRINCIPALS)

    def test_server_id_and_environment_id_are_distinct_identities(self):
        """server.id (appareil) et environment_id (session) ne sont pas la
        même identité : rien n'exige qu'ils soient égaux, et un service où ils
        diffèrent reste valide et pleinement fonctionnel (cf. REVIEW-SIM-FILES
        point 3 : server identifie l'appareil physique, environment_id la
        session)."""
        server = {'id': 'server-01', 'name': 'SRV-FILES', 'ip': '10.9.9.9', 'dns_name': 'files.lab'}
        service = make_service(environment_id='env-01', server=server,
                               principals={'user_ids': ['alice'], 'group_ids': []})
        sf.validate_file_service(service)
        self.assertEqual(service['environment_id'], 'env-01')
        self.assertEqual(service['server']['id'], 'server-01')

    def test_requires_at_least_one_user(self):
        with self.assertRaises(sf.FileServiceError) as cm:
            make_service(principals={'user_ids': [], 'group_ids': []})
        self.assertEqual(cm.exception.code, sf.INVALID_REQUEST)

    def test_accepts_zero_groups(self):
        service = make_service(principals={'user_ids': ['solo'], 'group_ids': []})
        sf.validate_file_service(service)

    def test_never_invents_unprovided_principal(self):
        service = make_service()
        known = set(service['principal_catalog']['user_ids']) | set(service['principal_catalog']['group_ids'])
        self.assertTrue(known.issubset(set(PRINCIPALS['user_ids']) | set(PRINCIPALS['group_ids'])))

    def test_healthy_state_has_no_hidden_fault(self):
        service = make_service()
        self.assertEqual(service['service_status'], 'running')
        self.assertTrue(service['firewall_tcp445_allowed'])
        self.assertTrue(all(s['enabled'] for s in service['shares'].values()))
        for share in service['shares'].values():
            if share['quota']['mode'] != 'off':
                used = sf._share_used_bytes(service, share['id'])
                self.assertLessEqual(used, share['quota']['limit_bytes'])
        self.assertGreater(service['volume']['capacity_bytes'], sf._volume_used_bytes(service))

    def test_first_user_can_perform_all_four_actions_on_first_share(self):
        service = make_service()
        share_id, user = first_share_and_user(service)
        for action in sf.ACTIONS:
            request = {'action': action, 'share_id': share_id}
            if action in ('read', 'delete'):
                fid = next(f['id'] for f in service['files'].values() if f['share_id'] == share_id)
                request['file_id'] = fid
            if action in ('write', 'delete'):
                request['expected_revision'] = service['revision']
            if action == 'write':
                request['file_id'] = next(f['id'] for f in service['files'].values() if f['share_id'] == share_id)
                request['content'] = 'contenu de test'
            result = sf.evaluate_access(service, request, passing_context(user=user), NOW)
            self.assertTrue(result['allowed'], msg=f'{action} refusé : {result}')
            self.assertEqual(result['code'], sf.OK)

    def test_generation_respects_caps(self):
        service = make_service()
        self.assertLessEqual(len(service['shares']), sf.MAX_SHARES)
        self.assertLessEqual(len(service['files']), sf.MAX_FILES)
        for f in service['files'].values():
            self.assertLessEqual(sf._file_size(f['content']), sf.MAX_FILE_BYTES)


class ValidationTests(unittest.TestCase):
    def test_rejects_duplicate_name_case_insensitive_within_share(self):
        service = make_service()
        share_id = next(iter(service['shares']))
        service['files']['dup-1'] = {'id': 'dup-1', 'share_id': share_id, 'name': 'Rapport.txt',
                                     'content': 'a', 'read_only': False, 'updated_at': NOW}
        service['files']['dup-2'] = {'id': 'dup-2', 'share_id': share_id, 'name': 'rapport.TXT',
                                     'content': 'b', 'read_only': False, 'updated_at': NOW}
        with self.assertRaises(sf.FileServiceError) as cm:
            sf.validate_file_service(service)
        self.assertEqual(cm.exception.code, sf.INVALID_SCHEMA)

    def test_rejects_traversal_and_separators_in_filename(self):
        for bad_name in ('../secret.txt', 'a/b.txt', 'a\\b.txt', '..', 'ok\x00.txt'):
            self.assertFalse(sf._valid_file_name(bad_name), msg=bad_name)

    def test_accepts_plain_names(self):
        self.assertTrue(sf._valid_file_name('Rapport final.txt'))

    def test_rejects_bool_as_integer(self):
        service = make_service()
        service['revision'] = True
        with self.assertRaises(sf.FileServiceError):
            sf.validate_file_service(service)

    def test_server_id_distinct_from_environment_id_is_valid_schema(self):
        """server.id (appareil) et environment_id (session) sont deux
        identités distinctes ; validate_file_service ne doit pas exiger leur
        égalité (voir REVIEW-SIM-FILES point 3)."""
        service = make_service()
        service['server']['id'] = 'a-different-device-id'
        sf.validate_file_service(service)  # ne lève pas

    def test_administrative_overage_is_a_valid_state(self):
        service = make_service()
        actor = FULL_ACTOR
        out = sf.apply_operation(service, 'set_volume_capacity', {'capacity_bytes': 1}, actor, NOW)
        sf.validate_file_service(out['service'])  # ne lève pas malgré le dépassement


class AccessEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.share_id, self.user = first_share_and_user(self.service)
        self.file_id = next(f['id'] for f in self.service['files'].values() if f['share_id'] == self.share_id)

    def test_wrong_environment_in_context_refused(self):
        ctx = passing_context(user=self.user)
        ctx['environment_id'] = 'other-env'
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.INVALID_CONTEXT)

    def test_wrong_target_device_refused(self):
        ctx = passing_context(user=self.user)
        ctx['target_device_id'] = 'not-the-server'
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.INVALID_CONTEXT)

    def test_distinct_server_id_and_environment_id_both_checked_separately(self):
        """REVIEW-SIM-FILES point 3 : server.id (appareil) et environment_id
        (session) sont deux identités distinctes, chacune vérifiée pour
        elle-même — jamais l'une à la place de l'autre."""
        server = {'id': 'server-01', 'name': 'SRV-FILES', 'ip': '10.9.9.9', 'dns_name': 'files.lab'}
        service = make_service(environment_id='env-01', server=server,
                               principals={'user_ids': ['alice'], 'group_ids': []})
        share_id = next(iter(service['shares']))
        good_ctx = {
            'environment_id': 'env-01', 'source_device_id': 'pc1', 'target_device_id': 'server-01',
            'network': {'status': 'up', 'observed_at': NOW - 5, 'valid_until': NOW + 30,
                       'source_device_id': 'pc1', 'target_device_id': 'server-01', 'evidence': 'tcp445'},
            'address_mode': 'ip',
            'identity': {'user_id': 'alice', 'group_ids': [], 'account_allowed': True, 'authentication_valid': True},
        }
        result = sf.evaluate_access(service, {'action': 'list', 'share_id': share_id}, good_ctx, NOW)
        self.assertTrue(result['allowed'])

        wrong_env = dict(good_ctx, environment_id='env-99')
        self.assertFalse(sf.evaluate_access(service, {'action': 'list', 'share_id': share_id}, wrong_env, NOW)['allowed'])

        wrong_target = dict(good_ctx, target_device_id='env-01')  # confond server.id et environment_id
        self.assertFalse(sf.evaluate_access(service, {'action': 'list', 'share_id': share_id}, wrong_target, NOW)['allowed'])

    def test_file_from_another_share_refused_for_read_write_delete(self):
        """REVIEW-SIM-FILES point 1 : un file_id valide mais appartenant à un
        autre partage que celui demandé doit produire FILE_NOT_FOUND pour les
        trois actions concernées, sans fuite de contenu ni mutation."""
        service = make_service(seed='two-shares-cross-access',
                               principals={'user_ids': ['alice'], 'group_ids': []})
        share_ids = list(service['shares'])
        if len(share_ids) < 2:
            self.skipTest('seed did not produce 2 shares')
        share_a, share_b = share_ids[0], share_ids[1]
        # Donne à alice les 4 droits sur share_a (déjà le cas pour le 1er partage
        # généré) ET sur share_b, pour prouver que le refus vient bien du
        # rattachement fichier/partage, pas d'un droit manquant.
        for layer in ('share_acl', 'folder_acl'):
            for action in sf.ACL_ACTIONS:
                service['shares'][share_b][layer][action]['user_ids'] = ['alice']
        sf.validate_file_service(service)
        file_in_b = next(f['id'] for f in service['files'].values() if f['share_id'] == share_b)
        ctx = passing_context(user='alice')

        for action, extra in (('read', {}), ('write', {'content': 'x', 'expected_revision': service['revision']}),
                             ('delete', {'expected_revision': service['revision']})):
            request = {'action': action, 'share_id': share_a, 'file_id': file_in_b}
            request.update(extra)
            result = sf.evaluate_access(service, request, ctx, NOW)
            self.assertFalse(result['allowed'], msg=action)
            self.assertEqual(result['code'], sf.FILE_NOT_FOUND, msg=action)

        out = sf.perform_file_action(service, {'action': 'read', 'share_id': share_a, 'file_id': file_in_b},
                                     ctx, NOW)
        self.assertIsNone(out['result']['data'])
        self.assertEqual(out['service'], service)

    def test_unknown_user_id_in_identity_refused_even_via_known_group(self):
        """REVIEW-SIM-FILES point 2 : un user_id absent du principal_catalog ne
        doit jamais obtenir d'accès, même via un group_id connu et autorisé."""
        service = make_service(principals={'user_ids': ['alice'], 'group_ids': ['grp-staff']})
        share_id = next(iter(service['shares']))
        out = sf.apply_operation(service, 'set_acl',
                                 {'share_id': share_id, 'layer': 'share_acl', 'action': 'list',
                                  'user_ids': [], 'group_ids': ['grp-staff']}, FULL_ACTOR, NOW)
        out = sf.apply_operation(out['service'], 'set_acl',
                                 {'share_id': share_id, 'layer': 'folder_acl', 'action': 'list',
                                  'user_ids': [], 'group_ids': ['grp-staff']}, FULL_ACTOR, NOW)
        service2 = out['service']
        ctx = passing_context(user='mallory-unknown', groups=['grp-staff'])
        result = sf.evaluate_access(service2, {'action': 'list', 'share_id': share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.INVALID_CONTEXT)

    def test_unknown_group_id_in_identity_refused(self):
        service = make_service()
        ctx = passing_context(user=self.user, groups=['grp-unknown'])
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.INVALID_CONTEXT)

    def test_name_resolution_status_unknown_is_not_failed(self):
        """REVIEW-SIM-FILES point 4 : un statut explicitement 'unknown', une
        preuve absente, périmée ou invalide doivent rester 'unknown'
        (OBSERVATION_UNKNOWN), distinct d'un échec frais réellement observé
        (NAME_UNRESOLVED)."""
        for name_resolution, expected_status, expected_code in (
            ({'status': 'unknown', 'resolved_ip': None, 'observed_at': NOW - 5, 'valid_until': NOW + 30},
             'unknown', sf.OBSERVATION_UNKNOWN),
            (None, 'unknown', sf.OBSERVATION_UNKNOWN),
            ({'status': 'resolved', 'resolved_ip': SERVER['ip'], 'observed_at': 1, 'valid_until': 2},
             'unknown', sf.OBSERVATION_UNKNOWN),  # périmé
            ({'status': 'failed', 'resolved_ip': None, 'observed_at': NOW - 5, 'valid_until': NOW + 30},
             'failed', sf.NAME_UNRESOLVED),
        ):
            ctx = passing_context(user=self.user, address_mode='name', name_resolution=name_resolution)
            if name_resolution is None:
                ctx.pop('name_resolution', None)
            result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
            self.assertEqual(result['status'], expected_status, msg=name_resolution)
            self.assertEqual(result['code'], expected_code, msg=name_resolution)

    def test_stale_network_observation_is_unknown_not_failure(self):
        ctx = passing_context(user=self.user, at=NOW)
        ctx['network']['valid_until'] = NOW - 100  # observation périmée
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['code'], sf.OBSERVATION_UNKNOWN)

    def test_network_down_is_failure_not_unknown(self):
        ctx = passing_context(user=self.user)
        ctx['network']['status'] = 'down'
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['code'], sf.NETWORK_DOWN)

    def test_name_mode_resolved_ok(self):
        ctx = passing_context(user=self.user, address_mode='name')
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertTrue(result['allowed'])

    def test_name_mode_wrong_ip_refused(self):
        ctx = passing_context(user=self.user, address_mode='name',
                              name_resolution={'status': 'resolved', 'resolved_ip': '9.9.9.9',
                                              'observed_at': NOW - 5, 'valid_until': NOW + 30})
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.NAME_UNRESOLVED)

    def test_ip_mode_does_not_require_name_resolution(self):
        ctx = passing_context(user=self.user, address_mode='ip')
        self.assertNotIn('name_resolution', ctx)
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertTrue(result['allowed'])

    def test_name_resolution_stage_omitted_in_ip_mode(self):
        ctx = passing_context(user=self.user, address_mode='ip')
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        stages = []
        node = result['tree']
        while node:
            stages.append(node['stage'])
            node = node['children'][0] if node['children'] else None
        self.assertNotIn('name_resolution', stages)

    def test_tcp445_blocked_refuses_independently_and_repair_restores(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_firewall', {'allowed': False}, FULL_ACTOR, NOW)
        blocked = out['service']
        result = sf.evaluate_access(blocked, {'action': 'list', 'share_id': self.share_id},
                                    passing_context(user=self.user), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.TCP445_BLOCKED)
        repaired = sf.apply_operation(blocked, 'set_firewall', {'allowed': True}, FULL_ACTOR, NOW)['service']
        result2 = sf.evaluate_access(repaired, {'action': 'list', 'share_id': self.share_id},
                                     passing_context(user=self.user), NOW)
        self.assertTrue(result2['allowed'])

    def test_service_stopped_refuses_independently_and_repair_restores(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_service_status', {'status': 'stopped'}, FULL_ACTOR, NOW)
        stopped = out['service']
        result = sf.evaluate_access(stopped, {'action': 'list', 'share_id': self.share_id},
                                    passing_context(user=self.user), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.SERVICE_STOPPED)
        repaired = sf.apply_operation(stopped, 'set_service_status', {'status': 'running'}, FULL_ACTOR, NOW)['service']
        result2 = sf.evaluate_access(repaired, {'action': 'list', 'share_id': self.share_id},
                                     passing_context(user=self.user), NOW)
        self.assertTrue(result2['allowed'])

    def test_share_disabled_refuses_independently_and_repair_restores(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_share_enabled',
                                 {'share_id': self.share_id, 'enabled': False}, FULL_ACTOR, NOW)
        disabled = out['service']
        result = sf.evaluate_access(disabled, {'action': 'list', 'share_id': self.share_id},
                                    passing_context(user=self.user), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.SHARE_DISABLED)
        repaired = sf.apply_operation(disabled, 'set_share_enabled',
                                      {'share_id': self.share_id, 'enabled': True}, FULL_ACTOR, NOW)['service']
        result2 = sf.evaluate_access(repaired, {'action': 'list', 'share_id': self.share_id},
                                     passing_context(user=self.user), NOW)
        self.assertTrue(result2['allowed'])

    def test_account_unavailable_refused_without_leaking_state(self):
        ctx = passing_context(user=self.user, account_allowed=False)
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.ACCOUNT_UNAVAILABLE)
        dumped = json.dumps(result)
        self.assertNotIn('password', dumped.lower())
        self.assertNotIn('credential', dumped.lower())

    def test_not_authenticated_refused(self):
        ctx = passing_context(user=self.user, authentication_valid=False)
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.NOT_AUTHENTICATED)

    def test_group_grant_satisfies_permission_like_direct_grant(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_acl',
                                 {'share_id': self.share_id, 'layer': 'share_acl', 'action': 'list',
                                  'user_ids': [], 'group_ids': ['grp-staff']}, FULL_ACTOR, NOW)
        out2 = sf.apply_operation(out['service'], 'set_acl',
                                  {'share_id': self.share_id, 'layer': 'folder_acl', 'action': 'list',
                                   'user_ids': [], 'group_ids': ['grp-staff']}, FULL_ACTOR, NOW)
        service2 = out2['service']
        ctx = passing_context(user='bob', groups=['grp-staff'])
        result = sf.evaluate_access(service2, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertTrue(result['allowed'])

    def test_both_layers_required_share_only_is_not_enough(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_acl',
                                 {'share_id': self.share_id, 'layer': 'share_acl', 'action': 'read',
                                  'user_ids': ['bob'], 'group_ids': []}, FULL_ACTOR, NOW)
        service2 = out['service']
        ctx = passing_context(user='bob')
        result = sf.evaluate_access(service2, {'action': 'read', 'share_id': self.share_id,
                                               'file_id': self.file_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.FILESYSTEM_ACCESS_DENIED)

    def test_both_layers_required_folder_only_is_not_enough(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_acl',
                                 {'share_id': self.share_id, 'layer': 'folder_acl', 'action': 'read',
                                  'user_ids': ['bob'], 'group_ids': []}, FULL_ACTOR, NOW)
        service2 = out['service']
        ctx = passing_context(user='bob')
        result = sf.evaluate_access(service2, {'action': 'read', 'share_id': self.share_id,
                                               'file_id': self.file_id}, ctx, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.SHARE_ACCESS_DENIED)

    def test_read_right_does_not_imply_list_or_write_or_delete(self):
        service = make_service()
        for layer in ('share_acl', 'folder_acl'):
            service['shares'][self.share_id][layer]['read']['user_ids'] = ['bob']
            for action in ('list', 'write', 'delete'):
                service['shares'][self.share_id][layer][action]['user_ids'] = []
        sf.validate_file_service(service)
        ctx = passing_context(user='bob')
        for action, extra in (('list', {}), ('write', {'file_id': self.file_id, 'content': 'x',
                                                        'expected_revision': 0}),
                             ('delete', {'file_id': self.file_id, 'expected_revision': 0})):
            request = {'action': action, 'share_id': self.share_id}
            request.update(extra)
            result = sf.evaluate_access(service, request, ctx, NOW)
            self.assertFalse(result['allowed'], msg=action)
        result_read = sf.evaluate_access(service, {'action': 'read', 'share_id': self.share_id,
                                                    'file_id': self.file_id}, ctx, NOW)
        self.assertTrue(result_read['allowed'])

    def test_hidden_share_does_not_block_direct_access(self):
        service = make_service()
        out = sf.apply_operation(service, 'set_acl',
                                 {'share_id': self.share_id, 'layer': 'share_acl', 'action': 'list',
                                  'user_ids': ['bob'], 'group_ids': []}, FULL_ACTOR, NOW)
        out = sf.apply_operation(out['service'], 'set_acl',
                                 {'share_id': self.share_id, 'layer': 'folder_acl', 'action': 'list',
                                  'user_ids': ['bob'], 'group_ids': []}, FULL_ACTOR, NOW)
        service2 = out['service']
        service2['shares'][self.share_id]['hidden'] = True
        sf.validate_file_service(service2)
        ctx = passing_context(user='bob')
        result = sf.evaluate_access(service2, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertTrue(result['allowed'])

    def test_list_result_never_contains_file_content(self):
        out = sf.perform_file_action(self.service, {'action': 'list', 'share_id': self.share_id},
                                     passing_context(user=self.user), NOW)
        dumped = json.dumps(out['result']['data'])
        for f in self.service['files'].values():
            if f['share_id'] == self.share_id and f['content']:
                self.assertNotIn(f['content'], dumped)

    def test_icmp_proxy_evidence_is_distinct_from_tcp445(self):
        ctx = passing_context(user=self.user, evidence='icmp_proxy')
        result = sf.evaluate_access(self.service, {'action': 'list', 'share_id': self.share_id}, ctx, NOW)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['evidence'], 'icmp_proxy')
        self.assertNotEqual(result['evidence'], 'tcp445')


class PerformActionTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.share_id, self.user = first_share_and_user(self.service)
        self.file_id = next(f['id'] for f in self.service['files'].values() if f['share_id'] == self.share_id)

    def test_input_service_never_mutated_on_success(self):
        before = copy.deepcopy(self.service)
        sf.perform_file_action(self.service, {'action': 'write', 'share_id': self.share_id,
                                              'file_id': self.file_id, 'content': 'changed',
                                              'expected_revision': self.service['revision']},
                               passing_context(user=self.user), NOW)
        self.assertEqual(self.service, before)

    def test_input_service_never_mutated_on_refusal(self):
        before = copy.deepcopy(self.service)
        sf.perform_file_action(self.service, {'action': 'write', 'share_id': self.share_id,
                                              'file_id': self.file_id, 'content': 'changed',
                                              'expected_revision': self.service['revision']},
                               passing_context(user='nobody'), NOW)
        self.assertEqual(self.service, before)

    def test_returned_service_is_independent_copy(self):
        out = sf.perform_file_action(self.service, {'action': 'list', 'share_id': self.share_id},
                                     passing_context(user=self.user), NOW)
        out['service']['revision'] = 999999
        self.assertNotEqual(self.service['revision'], 999999)

    def test_successful_write_bumps_revision_and_audit(self):
        out = sf.perform_file_action(self.service, {'action': 'write', 'share_id': self.share_id,
                                                     'file_id': self.file_id, 'content': 'changed',
                                                     'expected_revision': self.service['revision']},
                                     passing_context(user=self.user), NOW)
        self.assertEqual(out['service']['revision'], self.service['revision'] + 1)
        self.assertEqual(len(out['service']['audit']), len(self.service['audit']) + 1)
        last_audit = out['service']['audit'][-1]
        self.assertNotIn('content', last_audit)
        self.assertNotIn('credential', last_audit)

    def test_successful_delete_bumps_revision_and_audit(self):
        out = sf.perform_file_action(self.service, {'action': 'delete', 'share_id': self.share_id,
                                                     'file_id': self.file_id,
                                                     'expected_revision': self.service['revision']},
                                     passing_context(user=self.user), NOW)
        self.assertEqual(out['service']['revision'], self.service['revision'] + 1)
        self.assertNotIn(self.file_id, out['service']['files'])

    def test_list_and_read_do_not_bump_revision(self):
        out_list = sf.perform_file_action(self.service, {'action': 'list', 'share_id': self.share_id},
                                          passing_context(user=self.user), NOW)
        self.assertEqual(out_list['service']['revision'], self.service['revision'])
        out_read = sf.perform_file_action(self.service, {'action': 'read', 'share_id': self.share_id,
                                                          'file_id': self.file_id},
                                          passing_context(user=self.user), NOW)
        self.assertEqual(out_read['service']['revision'], self.service['revision'])

    def test_refusal_does_not_bump_revision(self):
        out = sf.perform_file_action(self.service, {'action': 'write', 'share_id': self.share_id,
                                                     'file_id': self.file_id, 'content': 'changed',
                                                     'expected_revision': self.service['revision']},
                                     passing_context(user='nobody'), NOW)
        self.assertEqual(out['service']['revision'], self.service['revision'])
        self.assertEqual(out['service']['files'], self.service['files'])

    def test_stale_revision_refused_without_mutation(self):
        out = sf.perform_file_action(self.service, {'action': 'write', 'share_id': self.share_id,
                                                     'file_id': self.file_id, 'content': 'changed',
                                                     'expected_revision': self.service['revision'] + 5},
                                     passing_context(user=self.user), NOW)
        self.assertFalse(out['result']['allowed'])
        self.assertEqual(out['result']['code'], sf.REVISION_CONFLICT)
        self.assertEqual(out['service'], self.service)

    def test_write_create_then_replace_then_delete_size_deltas(self):
        content_a = 'bonjour é'  # accent pour vérifier le comptage UTF-8
        out1 = sf.perform_file_action(self.service, {'action': 'write', 'share_id': self.share_id,
                                                      'name': 'Nouveau.txt', 'content': content_a,
                                                      'expected_revision': self.service['revision']},
                                      passing_context(user=self.user), NOW)
        self.assertTrue(out1['result']['allowed'])
        new_file_id = out1['result']['data']['id']
        service1 = out1['service']
        used_before = sf._share_used_bytes(service1, self.share_id)

        content_b = 'plus long maintenant avec encore plus de texte'
        out2 = sf.perform_file_action(service1, {'action': 'write', 'share_id': self.share_id,
                                                  'file_id': new_file_id, 'content': content_b,
                                                  'expected_revision': service1['revision']},
                                      passing_context(user=self.user), NOW + 1)
        service2 = out2['service']
        used_after_replace = sf._share_used_bytes(service2, self.share_id)
        self.assertEqual(used_after_replace - used_before,
                         len(content_b.encode('utf-8')) - len(content_a.encode('utf-8')))

        out3 = sf.perform_file_action(service2, {'action': 'delete', 'share_id': self.share_id,
                                                  'file_id': new_file_id,
                                                  'expected_revision': service2['revision']},
                                      passing_context(user=self.user), NOW + 2)
        service3 = out3['service']
        used_after_delete = sf._share_used_bytes(service3, self.share_id)
        self.assertEqual(used_after_delete, used_before - len(content_a.encode('utf-8')))

    def test_create_rejects_name_conflict_case_insensitive(self):
        existing_name = next(f['name'] for f in self.service['files'].values() if f['share_id'] == self.share_id)
        result = sf.evaluate_access(self.service, {'action': 'write', 'share_id': self.share_id,
                                                    'name': existing_name.upper(), 'content': 'x',
                                                    'expected_revision': self.service['revision']},
                                    passing_context(user=self.user), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.NAME_CONFLICT)

    def test_malformed_request_raises_contract_error(self):
        with self.assertRaises(sf.FileServiceError):
            sf.evaluate_access(self.service, {'action': 'fly'}, passing_context(user=self.user), NOW)
        with self.assertRaises(sf.FileServiceError):
            sf.evaluate_access(self.service, {'action': 'write', 'share_id': self.share_id,
                                              'name': '../x', 'content': 'y'},
                               passing_context(user=self.user), NOW)
        with self.assertRaises(sf.FileServiceError):
            sf.evaluate_access(self.service, {'action': 'write', 'share_id': self.share_id,
                                              'file_id': self.file_id, 'content': 'y'},
                               passing_context(user=self.user), NOW)  # expected_revision manquant


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service(seed='quota-tests')
        self.share_id, self.user = first_share_and_user(self.service)

    def _set_quota(self, mode, limit_bytes):
        out = sf.apply_operation(self.service, 'set_quota',
                                 {'share_id': self.share_id, 'mode': mode, 'limit_bytes': limit_bytes},
                                 FULL_ACTOR, NOW)
        return out['service']

    def test_hard_quota_exact_boundary_allowed_one_byte_over_refused(self):
        base_used = sf._share_used_bytes(self.service, self.share_id)
        service = self._set_quota('hard', base_used + 5)
        ok_content = 'a' * 5
        result_ok = sf.evaluate_access(service, {'action': 'write', 'share_id': self.share_id,
                                                  'name': 'Exact.txt', 'content': ok_content,
                                                  'expected_revision': service['revision']},
                                       passing_context(user=self.user), NOW)
        self.assertTrue(result_ok['allowed'])

        over_content = 'a' * 6
        result_over = sf.evaluate_access(service, {'action': 'write', 'share_id': self.share_id,
                                                    'name': 'Over.txt', 'content': over_content,
                                                    'expected_revision': service['revision']},
                                         passing_context(user=self.user), NOW)
        self.assertFalse(result_over['allowed'])
        self.assertEqual(result_over['code'], sf.QUOTA_EXCEEDED)

    def test_soft_quota_warns_without_blocking(self):
        base_used = sf._share_used_bytes(self.service, self.share_id)
        service = self._set_quota('soft', base_used + 1)
        result = sf.evaluate_access(service, {'action': 'write', 'share_id': self.share_id,
                                              'name': 'Over.txt', 'content': 'a' * 10,
                                              'expected_revision': service['revision']},
                                    passing_context(user=self.user), NOW)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['code'], sf.QUOTA_WARNING)

    def test_quota_off_never_checked(self):
        service = self._set_quota('off', None)
        out = sf.apply_operation(service, 'set_volume_capacity', {'capacity_bytes': 10_000_000},
                                 FULL_ACTOR, NOW)
        service = out['service']
        result = sf.evaluate_access(service, {'action': 'write', 'share_id': self.share_id,
                                              'name': 'Big.txt', 'content': 'a' * 50000,
                                              'expected_revision': service['revision']},
                                    passing_context(user=self.user), NOW)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['code'], sf.OK)

    def test_disk_full_blocks_growth_but_allows_read_delete_and_shrink(self):
        out = sf.apply_operation(self.service, 'set_volume_capacity',
                                 {'capacity_bytes': sf._volume_used_bytes(self.service)}, FULL_ACTOR, NOW)
        full_service = out['service']
        file_id = next(f['id'] for f in full_service['files'].values() if f['share_id'] == self.share_id)
        current_content = full_service['files'][file_id]['content']

        growth = sf.evaluate_access(full_service, {'action': 'write', 'share_id': self.share_id,
                                                    'file_id': file_id, 'content': current_content + 'x',
                                                    'expected_revision': full_service['revision']},
                                    passing_context(user=self.user), NOW)
        self.assertFalse(growth['allowed'])
        self.assertEqual(growth['code'], sf.DISK_FULL)

        shrink = sf.evaluate_access(full_service, {'action': 'write', 'share_id': self.share_id,
                                                    'file_id': file_id, 'content': '',
                                                    'expected_revision': full_service['revision']},
                                    passing_context(user=self.user), NOW)
        self.assertTrue(shrink['allowed'])

        read = sf.evaluate_access(full_service, {'action': 'read', 'share_id': self.share_id,
                                                  'file_id': file_id}, passing_context(user=self.user), NOW)
        self.assertTrue(read['allowed'])

        delete = sf.evaluate_access(full_service, {'action': 'delete', 'share_id': self.share_id,
                                                    'file_id': file_id,
                                                    'expected_revision': full_service['revision']},
                                    passing_context(user=self.user), NOW)
        self.assertTrue(delete['allowed'])

    def test_capacity_is_volume_wide_quota_is_per_share(self):
        service = make_service(seed='two-share-quota',
                               principals={'user_ids': ['alice'], 'group_ids': []})
        share_ids = list(service['shares'])
        if len(share_ids) < 2:
            self.skipTest('seed did not produce 2 shares')
        share_a, share_b = share_ids[0], share_ids[1]
        used_a = sf._share_used_bytes(service, share_a)
        out = sf.apply_operation(service, 'set_quota',
                                 {'share_id': share_a, 'mode': 'hard', 'limit_bytes': used_a + 100000},
                                 FULL_ACTOR, NOW)
        service = out['service']
        huge_capacity_margin = sf._volume_used_bytes(service) + 20
        out = sf.apply_operation(service, 'set_volume_capacity',
                                 {'capacity_bytes': huge_capacity_margin}, FULL_ACTOR, NOW)
        service = out['service']
        result = sf.evaluate_access(service, {'action': 'write', 'share_id': share_a, 'name': 'Big.txt',
                                              'content': 'a' * 30, 'expected_revision': service['revision']},
                                    passing_context(user='alice'), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sf.DISK_FULL)


class ReadOnlyTests(unittest.TestCase):
    def test_read_only_blocks_write_and_delete_not_read(self):
        service = make_service()
        share_id, user = first_share_and_user(service)
        file_id = next(f['id'] for f in service['files'].values() if f['share_id'] == share_id)
        out = sf.apply_operation(service, 'set_file_read_only', {'file_id': file_id, 'read_only': True},
                                 FULL_ACTOR, NOW)
        ro_service = out['service']

        write_result = sf.evaluate_access(ro_service, {'action': 'write', 'share_id': share_id,
                                                        'file_id': file_id, 'content': 'nope',
                                                        'expected_revision': ro_service['revision']},
                                          passing_context(user=user), NOW)
        self.assertFalse(write_result['allowed'])
        self.assertEqual(write_result['code'], sf.FILE_READ_ONLY)

        delete_result = sf.evaluate_access(ro_service, {'action': 'delete', 'share_id': share_id,
                                                         'file_id': file_id,
                                                         'expected_revision': ro_service['revision']},
                                           passing_context(user=user), NOW)
        self.assertFalse(delete_result['allowed'])
        self.assertEqual(delete_result['code'], sf.FILE_READ_ONLY)

        read_result = sf.evaluate_access(ro_service, {'action': 'read', 'share_id': share_id,
                                                       'file_id': file_id}, passing_context(user=user), NOW)
        self.assertTrue(read_result['allowed'])


class ApplyOperationTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.share_id, _ = first_share_and_user(self.service)

    def test_missing_capability_refused_without_mutation(self):
        before = copy.deepcopy(self.service)
        with self.assertRaises(sf.FileServiceError) as cm:
            sf.apply_operation(self.service, 'set_firewall', {'allowed': False}, NO_CAP_ACTOR, NOW)
        self.assertEqual(cm.exception.code, sf.PERMISSION_DENIED)
        self.assertEqual(self.service, before)

    def test_wrong_environment_actor_refused_without_mutation(self):
        before = copy.deepcopy(self.service)
        with self.assertRaises(sf.FileServiceError) as cm:
            sf.apply_operation(self.service, 'set_firewall', {'allowed': False}, WRONG_ENV_ACTOR, NOW)
        self.assertEqual(cm.exception.code, sf.UNKNOWN_ENVIRONMENT)
        self.assertEqual(self.service, before)

    def test_unknown_operation_refused_without_mutation(self):
        before = copy.deepcopy(self.service)
        with self.assertRaises(sf.FileServiceError) as cm:
            sf.apply_operation(self.service, 'reformat_disk', {}, FULL_ACTOR, NOW)
        self.assertEqual(cm.exception.code, sf.UNKNOWN_OPERATION)
        self.assertEqual(self.service, before)

    def test_unknown_field_in_payload_refused(self):
        with self.assertRaises(sf.FileServiceError):
            sf.apply_operation(self.service, 'set_firewall', {}, FULL_ACTOR, NOW)  # champ 'allowed' manquant

    def test_successful_operation_bumps_revision_and_audit(self):
        out = sf.apply_operation(self.service, 'set_firewall', {'allowed': False}, FULL_ACTOR, NOW)
        self.assertEqual(out['service']['revision'], self.service['revision'] + 1)
        self.assertEqual(out['service']['audit'][-1]['operation'], 'set_firewall')
        self.assertEqual(out['service']['audit'][-1]['actor_id'], FULL_ACTOR['id'])

    def test_repairing_one_share_does_not_touch_others(self):
        service = make_service(seed='multi-share-repair')
        share_ids = list(service['shares'])
        if len(share_ids) < 2:
            self.skipTest('seed did not produce 2 shares')
        target, other = share_ids[0], share_ids[1]
        other_before = copy.deepcopy(service['shares'][other])
        other_files_before = {fid: f for fid, f in service['files'].items() if f['share_id'] == other}

        out = sf.apply_operation(service, 'set_share_enabled', {'share_id': target, 'enabled': False},
                                 FULL_ACTOR, NOW)
        out2 = sf.apply_operation(out['service'], 'set_share_enabled', {'share_id': target, 'enabled': True},
                                  FULL_ACTOR, NOW)
        final = out2['service']
        self.assertEqual(final['shares'][other], other_before)
        other_files_after = {fid: f for fid, f in final['files'].items() if f['share_id'] == other}
        self.assertEqual(other_files_after, other_files_before)

    def test_input_service_never_mutated(self):
        before = copy.deepcopy(self.service)
        sf.apply_operation(self.service, 'set_firewall', {'allowed': False}, FULL_ACTOR, NOW)
        self.assertEqual(self.service, before)

    def test_set_acl_replaces_entire_layer_not_partial_merge(self):
        service = make_service()
        share_id, _ = first_share_and_user(service)
        out = sf.apply_operation(service, 'set_acl',
                                 {'share_id': share_id, 'layer': 'share_acl', 'action': 'read',
                                  'user_ids': ['bob'], 'group_ids': []}, FULL_ACTOR, NOW)
        grant = out['service']['shares'][share_id]['share_acl']['read']
        self.assertEqual(grant['user_ids'], ['bob'])


class PublicProjectionTests(unittest.TestCase):
    def test_unauthorized_actor_refused(self):
        service = make_service()
        with self.assertRaises(sf.FileServiceError) as cm:
            sf.public_file_service(service, NO_CAP_ACTOR)
        self.assertEqual(cm.exception.code, sf.PERMISSION_DENIED)

    def test_wrong_environment_actor_refused(self):
        service = make_service()
        with self.assertRaises(sf.FileServiceError) as cm:
            sf.public_file_service(service, WRONG_ENV_ACTOR)
        self.assertEqual(cm.exception.code, sf.UNKNOWN_ENVIRONMENT)

    def test_projection_has_no_file_content_or_auth_context(self):
        service = make_service()
        projection = sf.public_file_service(service, FULL_ACTOR)
        dumped = json.dumps(projection)
        for f in service['files'].values():
            if f['content']:
                self.assertNotIn(f['content'], dumped)
        self.assertNotIn('identity', projection)
        self.assertNotIn('authentication', dumped.lower())

    def test_projection_exposes_computed_occupation(self):
        service = make_service()
        projection = sf.public_file_service(service, FULL_ACTOR)
        self.assertEqual(projection['volume']['used_bytes'], sf._volume_used_bytes(service))
        for share_id, share_view in projection['shares'].items():
            self.assertEqual(share_view['used_bytes'], sf._share_used_bytes(service, share_id))


class JSONRoundtripTests(unittest.TestCase):
    def test_service_survives_json_roundtrip_and_still_behaves(self):
        service = make_service()
        share_id, user = first_share_and_user(service)
        dumped = json.dumps(service)
        reloaded = json.loads(dumped)
        # Les clés de dict JSON sont toujours des chaînes : déjà le cas ici (ids).
        sf.validate_file_service(reloaded)
        result = sf.evaluate_access(reloaded, {'action': 'list', 'share_id': share_id},
                                    passing_context(user=user), NOW)
        self.assertTrue(result['allowed'])

    def test_documentation_example_runs(self):
        """Rejoue l'exemple minimal documenté dans
        docs/SIM-FILES-IMPLEMENTATION.md pour garantir qu'il reste exécutable."""
        server = {'id': 'env-doc', 'name': 'SRV-FILES', 'ip': '10.1.1.10', 'dns_name': 'files.exemple.local'}
        principals = {'user_ids': ['alice'], 'group_ids': []}
        service = sf.generate_file_service('exemple-doc', 'env-doc', server, principals, 1_000_000)
        share_id = next(iter(service['shares']))
        context = {
            'environment_id': 'env-doc', 'source_device_id': 'pc-alice', 'target_device_id': 'env-doc',
            'network': {'status': 'up', 'observed_at': 999_990, 'valid_until': 1_000_100,
                       'source_device_id': 'pc-alice', 'target_device_id': 'env-doc', 'evidence': 'tcp445'},
            'address_mode': 'ip',
            'identity': {'user_id': 'alice', 'group_ids': [], 'account_allowed': True, 'authentication_valid': True},
        }
        request = {'action': 'list', 'share_id': share_id}
        result = sf.evaluate_access(service, request, context, 1_000_000)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['code'], sf.OK)


if __name__ == '__main__':
    unittest.main()

