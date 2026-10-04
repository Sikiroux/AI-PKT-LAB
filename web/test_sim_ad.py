"""Tests du moteur d'annuaire AD simulé (web/sim_ad.py).

Couvre un par un les critères d'acceptation de la section 8 du brief
(docs/BRIEF-IA-MOTEUR-AD.md). Lancer :
    python -m unittest discover -s web -p "test_sim_ad.py"
"""
import copy
import json
import random
import unittest

import sim_ad


ENV = 'env-test-1'
DEVICES = [
    {'id': 'dev-srv', 'name': 'SRV-FILES', 'role': 'server'},
    {'id': 'dev-pc1', 'name': 'PC-ALICE', 'role': 'client'},
]
REQUESTER = {'id': 'usr-req', 'username': 'alice.req', 'display_name': 'Alice Requester', 'device_id': 'dev-pc1'}
NOW = 1_700_000_000

FULL_ACTOR = {'id': 'actor-1', 'environment_id': ENV, 'permissions': [
    sim_ad.CAPABILITY_USERS, sim_ad.CAPABILITY_PASSWORDS, sim_ad.CAPABILITY_GROUPS,
    sim_ad.CAPABILITY_OUS, sim_ad.CAPABILITY_COMPUTERS]}
NO_ACTOR = {'id': 'actor-0', 'environment_id': ENV, 'permissions': []}


def make_directory(seed=42, environment_id=ENV):
    return sim_ad.generate_directory(seed, environment_id, DEVICES, REQUESTER, NOW)


def strip_credentials(directory):
    clone = copy.deepcopy(directory)
    for user in clone['users'].values():
        user.pop('credential', None)
    return clone


def passing_context(extra=None, at=NOW):
    context = {
        'environment_id': ENV,
        'source_device_id': 'dev-pc1',
        'target_device_id': 'dev-srv',
        'network': {'status': 'passed', 'observed_at': at - 10, 'valid_until': at + 35, 'evidence': 'icmp_proxy'},
        'directory_service': 'running',
        'resource_service': 'running',
    }
    if extra:
        context.update(extra)
    return context


class GenerationTests(unittest.TestCase):
    def test_reproducible_with_same_seed(self):
        a = make_directory(seed=7)
        b = make_directory(seed=7)
        self.assertEqual(strip_credentials(a), strip_credentials(b))
        # Les sels sont aléatoires : les vérificateurs ne doivent pas être identiques.
        self.assertNotEqual(a['users'][REQUESTER['id']]['credential'], b['users'][REQUESTER['id']]['credential'])

    def test_different_seed_changes_identities(self):
        a = make_directory(seed=7)
        b = make_directory(seed=8)
        self.assertNotEqual(a['domain'], b['domain'])

    def test_does_not_touch_global_random_stream(self):
        random.seed(12345)
        before = random.getstate()
        make_directory(seed=99)
        after = random.getstate()
        self.assertEqual(before, after)

    def test_does_not_mutate_devices_input(self):
        devices_copy = copy.deepcopy(DEVICES)
        make_directory()
        self.assertEqual(devices_copy, DEVICES)

    def test_healthy_state_has_no_hidden_fault(self):
        directory = make_directory()
        for user in directory['users'].values():
            self.assertTrue(user['enabled'])
            self.assertIsNone(user['locked_until'])
            self.assertFalse(user['must_change_password'])
            self.assertEqual(user['failed_attempts'], 0)
            self.assertGreater(user['password_expires_at'], NOW)

    def test_validate_directory_accepts_generated_state(self):
        sim_ad.validate_directory(make_directory())  # ne doit pas lever

    def test_computers_built_from_devices_without_inventing_any(self):
        directory = make_directory()
        device_ids = {c['device_id'] for c in directory['computers'].values()}
        self.assertEqual(device_ids, {d['id'] for d in DEVICES})


class PublicProjectionTests(unittest.TestCase):
    def test_no_secret_in_public_view(self):
        directory = make_directory()
        public = sim_ad.public_directory(directory)
        dumped = json.dumps(public)
        for user in public['users'].values():
            self.assertNotIn('credential', user)
        for needle in ('credential', 'pbkdf2', 'salt', 'hash'):
            self.assertNotIn(needle, dumped)

    def test_projection_does_not_mutate_source(self):
        directory = make_directory()
        before = copy.deepcopy(directory)
        sim_ad.public_directory(directory)
        self.assertEqual(directory, before)

    def test_json_roundtrip_preserves_model(self):
        directory = make_directory()
        restored = json.loads(json.dumps(directory))
        self.assertEqual(restored, directory)
        sim_ad.validate_directory(restored)  # toujours cohérent après aller-retour
        self.assertNotIn('network', restored)
        self.assertNotIn('context', restored)


class ValidationTests(unittest.TestCase):
    def test_duplicate_username_case_insensitive_rejected(self):
        directory = make_directory()
        other_id = next(uid for uid in directory['users'] if uid != REQUESTER['id'])
        directory['users'][other_id]['username'] = REQUESTER['username'].upper()
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.validate_directory(directory)
        self.assertEqual(ctx.exception.code, sim_ad.DUPLICATE_USERNAME)

    def test_invalid_ou_reference_rejected(self):
        directory = make_directory()
        directory['users'][REQUESTER['id']]['ou_id'] = 'ou-does-not-exist'
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.validate_directory(directory)
        self.assertEqual(ctx.exception.code, sim_ad.UNKNOWN_OU)

    def test_group_member_reference_validated(self):
        directory = make_directory()
        group_id = next(iter(directory['groups']))
        directory['groups'][group_id]['member_user_ids'].append('usr-ghost')
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.validate_directory(directory)
        self.assertEqual(ctx.exception.code, sim_ad.UNKNOWN_USER)

    def test_ou_cycle_rejected(self):
        directory = make_directory()
        ou_ids = list(directory['ous'])
        a, b = ou_ids[0], ou_ids[1]
        directory['ous'][a]['parent_id'] = b
        directory['ous'][b]['parent_id'] = a
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.validate_directory(directory)
        self.assertEqual(ctx.exception.code, sim_ad.OU_CYCLE)

    def test_same_ou_name_allowed_under_different_parents(self):
        directory = make_directory()
        root_id = next(ou_id for ou_id, ou in directory['ous'].items() if ou['parent_id'] is None)
        result = sim_ad.apply_operation(directory, 'create_ou', {'name': 'Filiale', 'parent_id': root_id},
                                        FULL_ACTOR, NOW)
        directory = result['directory']
        other_parent = next(ou_id for ou_id, ou in directory['ous'].items()
                            if ou['name'] == 'Utilisateurs')
        result = sim_ad.apply_operation(directory, 'create_ou', {'name': 'Filiale', 'parent_id': other_parent},
                                        FULL_ACTOR, NOW)
        sim_ad.validate_directory(result['directory'])  # ne doit pas lever


class ApplyOperationContractTests(unittest.TestCase):
    def test_unknown_operation_rejected(self):
        directory = make_directory()
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.apply_operation(directory, 'teleport_user', {}, FULL_ACTOR, NOW)
        self.assertEqual(ctx.exception.code, sim_ad.UNKNOWN_OPERATION)

    def test_cross_environment_actor_rejected(self):
        directory = make_directory(environment_id=ENV)
        foreign_actor = {**FULL_ACTOR, 'environment_id': 'env-other'}
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.apply_operation(directory, 'unlock_user', {'user_id': REQUESTER['id']}, foreign_actor, NOW)
        self.assertEqual(ctx.exception.code, sim_ad.UNKNOWN_ENVIRONMENT)

    def test_missing_capability_rejected(self):
        directory = make_directory()
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.apply_operation(directory, 'set_user_enabled', {'user_id': REQUESTER['id'], 'enabled': False},
                                   NO_ACTOR, NOW)
        self.assertEqual(ctx.exception.code, sim_ad.PERMISSION_DENIED)

    def test_input_never_mutated_even_on_success(self):
        directory = make_directory()
        before = copy.deepcopy(directory)
        sim_ad.apply_operation(directory, 'unlock_user', {'user_id': REQUESTER['id']}, FULL_ACTOR, NOW)
        self.assertEqual(directory, before)

    def test_input_never_mutated_on_error(self):
        directory = make_directory()
        before = copy.deepcopy(directory)
        with self.assertRaises(sim_ad.DirectoryError):
            sim_ad.apply_operation(directory, 'unlock_user', {'user_id': 'usr-ghost'}, FULL_ACTOR, NOW)
        self.assertEqual(directory, before)

    def test_failed_operation_leaves_no_trace(self):
        directory = make_directory()
        revision_before, audit_len_before = directory['revision'], len(directory['audit'])
        with self.assertRaises(sim_ad.DirectoryError):
            sim_ad.apply_operation(directory, 'unlock_user', {'user_id': 'usr-ghost'}, FULL_ACTOR, NOW)
        self.assertEqual(directory['revision'], revision_before)
        self.assertEqual(len(directory['audit']), audit_len_before)

    def test_successful_operation_bumps_revision_and_audits_without_secret(self):
        directory = make_directory()
        outcome = sim_ad.apply_operation(directory, 'reset_password', {'user_id': REQUESTER['id']},
                                         FULL_ACTOR, NOW)
        new_directory = outcome['directory']
        self.assertEqual(new_directory['revision'], directory['revision'] + 1)
        last_audit = new_directory['audit'][-1]
        self.assertEqual(last_audit['operation'], 'reset_password')
        self.assertNotIn('temporary_password', last_audit)
        self.assertIn('temporary_password', outcome['result'])

    def test_update_user_rejects_unknown_field(self):
        directory = make_directory()
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.apply_operation(directory, 'update_user',
                                   {'user_id': REQUESTER['id'], 'failed_attempts': 0}, FULL_ACTOR, NOW)
        self.assertEqual(ctx.exception.code, sim_ad.IMMUTABLE_FIELD)

    def test_update_user_allows_documented_fields(self):
        directory = make_directory()
        outcome = sim_ad.apply_operation(directory, 'update_user',
                                         {'user_id': REQUESTER['id'], 'display_name': 'Alice R.'},
                                         FULL_ACTOR, NOW)
        self.assertEqual(outcome['directory']['users'][REQUESTER['id']]['display_name'], 'Alice R.')


class DirectoryOperationsTests(unittest.TestCase):
    def test_create_user_then_authenticate_with_initial_password(self):
        directory = make_directory()
        outcome = sim_ad.apply_operation(directory, 'create_user',
                                         {'username': 'nouvel.arrivant', 'display_name': 'Nouvel Arrivant',
                                          'ou_id': next(iter(directory['ous'])),
                                          'initial_password': 'Bienvenue!1', 'must_change_password': False},
                                         FULL_ACTOR, NOW)
        auth = sim_ad.authenticate(outcome['directory'], 'nouvel.arrivant', 'Bienvenue!1',
                                   passing_context(), NOW)
        self.assertTrue(auth['result']['allowed'])

    def test_create_group_and_membership_roundtrip(self):
        directory = make_directory()
        ou_id = next(iter(directory['ous']))
        outcome = sim_ad.apply_operation(directory, 'create_group', {'name': 'Comptabilité', 'ou_id': ou_id},
                                         FULL_ACTOR, NOW)
        group_id = outcome['result']['group_id']
        outcome = sim_ad.apply_operation(outcome['directory'], 'add_group_member',
                                         {'group_id': group_id, 'user_id': REQUESTER['id']}, FULL_ACTOR, NOW)
        self.assertIn(REQUESTER['id'], outcome['directory']['groups'][group_id]['member_user_ids'])
        outcome = sim_ad.apply_operation(outcome['directory'], 'remove_group_member',
                                         {'group_id': group_id, 'user_id': REQUESTER['id']}, FULL_ACTOR, NOW)
        self.assertNotIn(REQUESTER['id'], outcome['directory']['groups'][group_id]['member_user_ids'])

    def test_move_object_requires_matching_capability(self):
        directory = make_directory()
        ou_id = next(iter(directory['ous']))
        limited_actor = {'id': 'a', 'environment_id': ENV, 'permissions': [sim_ad.CAPABILITY_GROUPS]}
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.apply_operation(directory, 'move_object',
                                   {'object_type': 'user', 'object_id': REQUESTER['id'], 'new_ou_id': ou_id},
                                   limited_actor, NOW)
        self.assertEqual(ctx.exception.code, sim_ad.PERMISSION_DENIED)

    def test_join_and_leave_computer(self):
        directory = make_directory()
        ou_id = next(iter(directory['ous']))
        outcome = sim_ad.apply_operation(directory, 'join_computer',
                                         {'name': 'PC-NEW', 'ou_id': ou_id, 'device_id': 'dev-new'},
                                         FULL_ACTOR, NOW)
        computer_id = outcome['result']['computer_id']
        self.assertTrue(outcome['directory']['computers'][computer_id]['domain_joined'])
        outcome = sim_ad.apply_operation(outcome['directory'], 'leave_computer', {'computer_id': computer_id},
                                         FULL_ACTOR, NOW)
        self.assertFalse(outcome['directory']['computers'][computer_id]['domain_joined'])


class AuthenticationTests(unittest.TestCase):
    def test_unknown_username_and_wrong_password_share_generic_code(self):
        directory = make_directory()
        unknown = sim_ad.authenticate(directory, 'ne.existe.pas', 'whatever', passing_context(), NOW)
        wrong = sim_ad.authenticate(directory, REQUESTER['username'], 'mauvais-mdp', passing_context(), NOW)
        self.assertEqual(unknown['result']['code'], sim_ad.INVALID_CREDENTIALS)
        self.assertEqual(wrong['result']['code'], sim_ad.INVALID_CREDENTIALS)
        self.assertEqual(unknown['result']['tree'], wrong['result']['tree'])

    def test_correct_password_succeeds(self):
        directory = make_directory()
        outcome = sim_ad.authenticate(directory, REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                      passing_context(), NOW)
        self.assertTrue(outcome['result']['allowed'])
        self.assertEqual(outcome['result']['code'], sim_ad.OK)

    def test_lockout_threshold_then_auto_expiry(self):
        directory = make_directory()
        threshold = directory['policy']['lockout_threshold']
        for _ in range(threshold):
            outcome = sim_ad.authenticate(directory, REQUESTER['username'], 'faux', passing_context(), NOW)
            directory = outcome['directory']
        locked_user = directory['users'][REQUESTER['id']]
        self.assertIsNotNone(locked_user['locked_until'])
        blocked = sim_ad.authenticate(directory, REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                      passing_context(), NOW)
        self.assertEqual(blocked['result']['code'], sim_ad.ACCOUNT_LOCKED)
        after_expiry = locked_user['locked_until'] + 1
        recovered = sim_ad.authenticate(directory, REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                        passing_context(at=after_expiry), after_expiry)
        self.assertTrue(recovered['result']['allowed'])

    def test_unlock_user_operation_clears_lock(self):
        directory = make_directory()
        threshold = directory['policy']['lockout_threshold']
        for _ in range(threshold):
            outcome = sim_ad.authenticate(directory, REQUESTER['username'], 'faux', passing_context(), NOW)
            directory = outcome['directory']
        outcome = sim_ad.apply_operation(directory, 'unlock_user', {'user_id': REQUESTER['id']}, FULL_ACTOR, NOW)
        recovered = sim_ad.authenticate(outcome['directory'], REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                        passing_context(), NOW)
        self.assertTrue(recovered['result']['allowed'])

    def test_disabled_account_rejected(self):
        directory = make_directory()
        outcome = sim_ad.apply_operation(directory, 'set_user_enabled',
                                         {'user_id': REQUESTER['id'], 'enabled': False}, FULL_ACTOR, NOW)
        result = sim_ad.authenticate(outcome['directory'], REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                     passing_context(), NOW)
        self.assertEqual(result['result']['code'], sim_ad.ACCOUNT_DISABLED)

    def test_password_expired_rejected(self):
        directory = make_directory()
        directory['users'][REQUESTER['id']]['password_expires_at'] = NOW - 10
        result = sim_ad.authenticate(directory, REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                     passing_context(), NOW)
        self.assertEqual(result['result']['code'], sim_ad.PASSWORD_EXPIRED)

    def test_must_change_password_blocks_normal_login(self):
        directory = make_directory()
        outcome = sim_ad.apply_operation(directory, 'reset_password', {'user_id': REQUESTER['id']},
                                         FULL_ACTOR, NOW)
        temp_password = outcome['result']['temporary_password']
        result = sim_ad.authenticate(outcome['directory'], REQUESTER['username'], temp_password,
                                     passing_context(), NOW)
        self.assertFalse(result['result']['allowed'])
        self.assertEqual(result['result']['code'], sim_ad.MUST_CHANGE_PASSWORD)

    def test_network_or_service_failure_blocks_without_counting_attempt(self):
        directory = make_directory()
        bad_context = passing_context({'network': {'status': 'failed', 'observed_at': NOW - 1,
                                                    'valid_until': NOW + 10, 'evidence': 'icmp_proxy'}})
        outcome = sim_ad.authenticate(directory, REQUESTER['username'], 'faux-mot-de-passe', bad_context, NOW)
        self.assertEqual(outcome['result']['status'], 'blocked')
        self.assertEqual(outcome['directory']['users'][REQUESTER['id']]['failed_attempts'], 0)

    def test_stale_future_and_missing_network_never_succeed(self):
        directory = make_directory()
        stale = passing_context({'network': {'status': 'passed', 'observed_at': NOW - 200, 'valid_until': NOW - 100,
                                             'evidence': 'icmp_proxy'}})
        future = passing_context({'network': {'status': 'passed', 'observed_at': NOW + 50, 'valid_until': NOW + 90,
                                              'evidence': 'icmp_proxy'}})
        missing = passing_context({'network': None})
        for bad_context in (stale, future, missing):
            outcome = sim_ad.authenticate(directory, REQUESTER['username'], sim_ad.TRAINING_PASSWORD,
                                          bad_context, NOW)
            self.assertFalse(outcome['result']['allowed'])

    def test_foreign_environment_context_rejected(self):
        directory = make_directory()
        foreign = passing_context({'environment_id': 'env-other'})
        outcome = sim_ad.authenticate(directory, REQUESTER['username'], sim_ad.TRAINING_PASSWORD, foreign, NOW)
        self.assertFalse(outcome['result']['allowed'])


class EvaluateUserTests(unittest.TestCase):
    def test_unknown_user_raises(self):
        directory = make_directory()
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.evaluate_user(directory, 'usr-ghost', passing_context(), NOW)
        self.assertEqual(ctx.exception.code, sim_ad.UNKNOWN_USER)

    def test_reports_disabled_locked_and_expired_state(self):
        directory = make_directory()
        result = sim_ad.evaluate_user(directory, REQUESTER['id'], passing_context(), NOW)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['code'], sim_ad.OK)

    def test_does_not_mutate_directory(self):
        directory = make_directory()
        before = copy.deepcopy(directory)
        sim_ad.evaluate_user(directory, REQUESTER['id'], passing_context(), NOW)
        self.assertEqual(directory, before)


class EvaluateAccessTests(unittest.TestCase):
    def _resource(self, read_users=(), read_groups=(), write_users=(), write_groups=()):
        return {'id': 'res-1', 'server_device_id': 'dev-srv',
               'allowed_user_ids': {'read': list(read_users), 'write': list(write_users)},
               'allowed_group_ids': {'read': list(read_groups), 'write': list(write_groups)}}

    def _authenticated_context(self):
        return passing_context({'authentication': {'user_id': REQUESTER['id'], 'status': 'authenticated'}})

    def test_active_account_without_authentication_denied(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        result = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read', passing_context(), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sim_ad.NOT_AUTHENTICATED)

    def test_direct_user_grant(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        result = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read',
                                        self._authenticated_context(), NOW)
        self.assertTrue(result['allowed'])

    def test_group_membership_grants_and_removal_revokes(self):
        directory = make_directory()
        ou_id = next(iter(directory['ous']))
        outcome = sim_ad.apply_operation(directory, 'create_group', {'name': 'Finance', 'ou_id': ou_id},
                                         FULL_ACTOR, NOW)
        group_id = outcome['result']['group_id']
        outcome = sim_ad.apply_operation(outcome['directory'], 'add_group_member',
                                         {'group_id': group_id, 'user_id': REQUESTER['id']}, FULL_ACTOR, NOW)
        directory = outcome['directory']
        resource = self._resource(read_groups=[group_id])
        granted = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read',
                                         self._authenticated_context(), NOW)
        self.assertTrue(granted['allowed'])
        outcome = sim_ad.apply_operation(directory, 'remove_group_member',
                                         {'group_id': group_id, 'user_id': REQUESTER['id']}, FULL_ACTOR, NOW)
        revoked = sim_ad.evaluate_access(outcome['directory'], REQUESTER['id'], resource, 'read',
                                         self._authenticated_context(), NOW)
        self.assertFalse(revoked['allowed'])

    def test_read_does_not_grant_write(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        write_result = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'write',
                                              self._authenticated_context(), NOW)
        self.assertFalse(write_result['allowed'])

    def test_disabled_account_blocks_resource_right_step(self):
        directory = make_directory()
        outcome = sim_ad.apply_operation(directory, 'set_user_enabled',
                                         {'user_id': REQUESTER['id'], 'enabled': False}, FULL_ACTOR, NOW)
        resource = self._resource(read_users=[REQUESTER['id']])
        result = sim_ad.evaluate_access(outcome['directory'], REQUESTER['id'], resource, 'read',
                                        self._authenticated_context(), NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sim_ad.ACCOUNT_DISABLED)

    def test_network_or_service_failure_blocks(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        bad_context = self._authenticated_context()
        bad_context['resource_service'] = 'stopped'
        result = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read', bad_context, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['status'], 'blocked')

    def test_authentication_proof_for_other_user_rejected(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        context = passing_context({'authentication': {'user_id': 'usr-someone-else', 'status': 'authenticated'}})
        result = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read', context, NOW)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['code'], sim_ad.NOT_AUTHENTICATED)

    def test_target_mismatch_defeats_access(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        resource['server_device_id'] = 'dev-other-server'
        result = sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read',
                                        self._authenticated_context(), NOW)
        self.assertFalse(result['allowed'])

    def test_unknown_user_raises(self):
        resource = self._resource(read_users=['usr-ghost'])
        with self.assertRaises(sim_ad.DirectoryError):
            sim_ad.evaluate_access(make_directory(), 'usr-ghost', resource, 'read', passing_context(), NOW)

    def test_unknown_action_raises(self):
        directory = make_directory()
        resource = self._resource(read_users=[REQUESTER['id']])
        with self.assertRaises(sim_ad.DirectoryError):
            sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'delete',
                                   self._authenticated_context(), NOW)

    def test_does_not_mutate_directory(self):
        directory = make_directory()
        before = copy.deepcopy(directory)
        resource = self._resource(read_users=[REQUESTER['id']])
        sim_ad.evaluate_access(directory, REQUESTER['id'], resource, 'read', self._authenticated_context(), NOW)
        self.assertEqual(directory, before)


class EnvironmentIsolationTests(unittest.TestCase):
    def test_two_environments_independent(self):
        first = make_directory(seed=1, environment_id='env-a')
        second = make_directory(seed=1, environment_id='env-b')
        self.assertNotEqual(first['environment_id'], second['environment_id'])
        foreign_actor = {'id': 'x', 'environment_id': 'env-b', 'permissions': [sim_ad.CAPABILITY_PASSWORDS]}
        with self.assertRaises(sim_ad.DirectoryError) as ctx:
            sim_ad.apply_operation(first, 'unlock_user', {'user_id': REQUESTER['id']}, foreign_actor, NOW)
        self.assertEqual(ctx.exception.code, sim_ad.UNKNOWN_ENVIRONMENT)


if __name__ == '__main__':
    unittest.main(verbosity=2)

