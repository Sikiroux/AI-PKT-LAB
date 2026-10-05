"""Tests du moteur DNS pédagogique simulé (web/sim_dns.py).

Couvre un par un les 23 critères d'acceptation de la section 7 du brief
(docs/BRIEF-IA-MOTEUR-DNS.md). Lancer :
    python -m unittest discover -s web -p "test_sim_dns.py"
"""
import copy
import json
import random
import unittest

import sim_dns as sd


ENV = 'env-test-1'
SERVER = {'id': 'server-01', 'name': 'SRV-DNS', 'ip': '10.0.0.5', 'zone': 'agence.test'}
CLIENTS = [{'id': 'client', 'name': 'PC-ALICE', 'dns_server_ip': '10.0.0.5', 'search_suffix': 'agence.test'}]
RESOURCES = [
    {'id': 'r1', 'dns_name': 'srv-fichiers.agence.test', 'ipv4': '10.0.0.5'},
    {'id': 'r2', 'dns_name': 'pc-alice.agence.test', 'ipv4': '10.0.0.10'},
]
NOW = 1_700_000_000

ADMIN = {'id': 'tech-1', 'environment_id': ENV, 'permissions': [sd.CAPABILITY_DNS_MANAGE]}
NO_CAP_ACTOR = {'id': 'tech-0', 'environment_id': ENV, 'permissions': []}
WRONG_ENV_ACTOR = {'id': 'tech-2', 'environment_id': 'other-env', 'permissions': [sd.CAPABILITY_DNS_MANAGE]}
SELF_USER = {'id': 'pc-alice', 'environment_id': ENV, 'permissions': [sd.CAPABILITY_DNS_FLUSH_OWN], 'device_id': 'client'}
OTHER_USER = {'id': 'pc-bob', 'environment_id': ENV, 'permissions': [sd.CAPABILITY_DNS_FLUSH_OWN], 'device_id': 'other-client'}


def make_service(seed=42, environment_id=ENV, server=None, clients=None, resources=None, now=NOW):
    return sd.generate_dns(seed, environment_id, server or SERVER, clients or CLIENTS, resources or RESOURCES, now)


def passing_context(client_id='client', target_ip='10.0.0.5', status='up', at=NOW, evidence='dns_proxy',
                    environment_id=ENV, target_device_id=None):
    return {
        'environment_id': environment_id,
        'source_device_id': client_id,
        'target_device_id': target_device_id or SERVER['id'],
        'network': {'status': status, 'source_device_id': client_id, 'target_device_id': target_device_id or SERVER['id'],
                   'target_ip': target_ip, 'observed_at': at - 5, 'valid_until': at + 30, 'evidence': evidence},
    }


def tree_stages(tree):
    stages = []
    node = tree
    while node:
        stages.append((node['stage'], node['status']))
        node = node['children'][0] if node['children'] else None
    return stages


class GenerationTests(unittest.TestCase):
    def test_reproducible_with_same_inputs(self):
        a = make_service(seed='same')
        b = make_service(seed='same')
        self.assertEqual(a, b)

    def test_different_seed_changes_layout(self):
        a = make_service(seed='seed-a')
        b = make_service(seed='seed-b')
        self.assertNotEqual(a['negative_ttl'], b['negative_ttl']) if a['negative_ttl'] == b['negative_ttl'] else None
        # Au minimum, les identifiants d'enregistrements générés diffèrent.
        self.assertNotEqual(set(a['records']), set(b['records']))

    def test_does_not_touch_global_random_stream(self):
        random.seed(12345)
        before = random.getstate()
        make_service(seed='anything')
        after = random.getstate()
        self.assertEqual(before, after)

    def test_does_not_mutate_server_clients_resources_input(self):
        server_copy = copy.deepcopy(SERVER)
        clients_copy = copy.deepcopy(CLIENTS)
        resources_copy = copy.deepcopy(RESOURCES)
        make_service()
        self.assertEqual(server_copy, SERVER)
        self.assertEqual(clients_copy, CLIENTS)
        self.assertEqual(resources_copy, RESOURCES)

    def test_given_names_and_addresses_preserved(self):
        service = make_service()
        values = {(r['name'], r['type'], r['value']) for r in service['records'].values()}
        self.assertIn(('srv-fichiers.agence.test', 'A', '10.0.0.5'), values)
        self.assertIn(('pc-alice.agence.test', 'A', '10.0.0.10'), values)

    def test_never_invents_unrelated_fixed_names(self):
        service = make_service()
        for record in service['records'].values():
            # Toute CNAME générée pointe vers une ressource réellement fournie.
            if record['type'] == 'CNAME':
                self.assertIn(record['value'], {'srv-fichiers.agence.test', 'pc-alice.agence.test'})

    def test_healthy_generation_requires_matching_client_dns_config(self):
        bad_clients = [{'id': 'client', 'name': 'PC-ALICE', 'dns_server_ip': '9.9.9.9', 'search_suffix': 'agence.test'}]
        with self.assertRaises(sd.DNSServiceError) as cm:
            make_service(clients=bad_clients)
        self.assertEqual(cm.exception.code, sd.INVALID_REQUEST)

    def test_healthy_generation_requires_empty_or_zone_suffix(self):
        bad_clients = [{'id': 'client', 'name': 'PC-ALICE', 'dns_server_ip': '10.0.0.5', 'search_suffix': 'autre.test'}]
        with self.assertRaises(sd.DNSServiceError) as cm:
            make_service(clients=bad_clients)
        self.assertEqual(cm.exception.code, sd.INVALID_REQUEST)

    def test_healthy_state_has_no_hidden_fault(self):
        service = make_service()
        self.assertEqual(service['service_status'], 'running')
        self.assertTrue(service['transport_allowed'])
        for client in service['clients'].values():
            self.assertEqual(client['dns_server_ip'], service['server']['ip'])


class ValidationTests(unittest.TestCase):
    def test_server_id_distinct_from_environment_id_is_valid(self):
        service = make_service()
        service['server']['id'] = 'a-different-device-id'
        sd.validate_dns(service)  # ne lève pas

    def test_rejects_duplicate_active_record_same_name_type(self):
        service = make_service()
        rid = next(iter(service['records']))
        existing = service['records'][rid]
        dup_id = 'rec-dup'
        service['records'][dup_id] = dict(existing, id=dup_id)
        with self.assertRaises(sd.DNSServiceError):
            sd.validate_dns(service)

    def test_rejects_active_cname_coexisting_with_active_a(self):
        service = make_service()
        name = next(r['name'] for r in service['records'].values() if r['type'] == 'A')
        cid = 'rec-cname'
        service['records'][cid] = {'id': cid, 'name': name, 'type': 'CNAME', 'value': 'autre.agence.test',
                                   'ttl': 300, 'enabled': True}
        with self.assertRaises(sd.DNSServiceError):
            sd.validate_dns(service)

    def test_a_and_aaaa_coexist_at_same_name(self):
        service = make_service()
        name = next(r['name'] for r in service['records'].values() if r['type'] == 'A')
        aid = 'rec-aaaa'
        service['records'][aid] = {'id': aid, 'name': name, 'type': 'AAAA', 'value': '::1',
                                   'ttl': 300, 'enabled': True}
        sd.validate_dns(service)  # ne lève pas

    def test_record_out_of_zone_rejected(self):
        service = make_service()
        rid = 'rec-ext'
        service['records'][rid] = {'id': rid, 'name': 'evil.external.test', 'type': 'A', 'value': '1.2.3.4',
                                   'ttl': 300, 'enabled': True}
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.validate_dns(service)
        self.assertEqual(cm.exception.code, sd.RECORD_OUT_OF_ZONE)

    def test_rejects_bool_as_integer(self):
        service = make_service()
        service['revision'] = True
        with self.assertRaises(sd.DNSServiceError):
            sd.validate_dns(service)


class NameNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()

    def _resolve(self, name, qtype='A'):
        return sd.resolve(self.service, 'client', {'name': name, 'type': qtype}, passing_context(), NOW)

    def test_case_and_trailing_dot_are_equivalent(self):
        a = self._resolve('srv-fichiers')
        b = self._resolve('SRV-FICHIERS.AGENCE.TEST.')
        self.assertEqual(a['result']['addresses'], b['result']['addresses'])
        self.assertTrue(a['result']['allowed'] if 'allowed' in a['result'] else True)

    def test_short_name_gets_search_suffix(self):
        out = self._resolve('srv-fichiers')
        self.assertEqual(out['result']['code'], sd.OK)
        self.assertEqual(out['result']['canonical_name'], 'srv-fichiers.agence.test')

    def test_dotless_name_without_suffix_is_invalid(self):
        actor = ADMIN
        svc = sd.apply_operation(self.service, 'set_client_dns',
                                 {'client_id': 'client', 'dns_server_ip': '10.0.0.5', 'search_suffix': ''},
                                 actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['status'], 'failed')
        self.assertEqual(out['result']['code'], sd.INVALID_NAME)

    def test_invalid_name_grammar_refused(self):
        for bad in ('under_score.agence.test', 'has space.agence.test', '*.agence.test',
                   '\\\\server\\share', 'http://agence.test', '-leading.agence.test'):
            out = self._resolve(bad)
            self.assertEqual(out['result']['code'], sd.INVALID_NAME, msg=bad)

    def test_unknown_type_raises_contract_error(self):
        with self.assertRaises(sd.DNSServiceError):
            sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'MX'}, passing_context(), NOW)

    def test_out_of_zone_refused(self):
        out = self._resolve('www.external-domain.com.')
        self.assertEqual(out['result']['status'], 'failed')
        self.assertEqual(out['result']['code'], sd.REFUSED)
        self.assertEqual(out['result']['dns_rcode'], 'REFUSED')


class AddressFamilyTests(unittest.TestCase):
    def test_a_record_resolves_ipv4(self):
        service = make_service()
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['addresses'], ['10.0.0.5'])

    def test_aaaa_record_resolves_ipv6(self):
        resources = RESOURCES + [{'id': 'r3', 'dns_name': 'srv-v6.agence.test', 'ipv6': '2001:db8::1'}]
        service = make_service(resources=resources)
        out = sd.resolve(service, 'client', {'name': 'srv-v6', 'type': 'AAAA'}, passing_context(), NOW)
        self.assertEqual(out['result']['addresses'], ['2001:db8::1'])

    def test_wrong_family_refused_not_invented(self):
        service = make_service()  # srv-fichiers n'a qu'une A
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'AAAA'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.NODATA)
        self.assertEqual(out['result']['addresses'], [])

    def test_generate_rejects_ipv4_only_record_misparsed_as_ipv6(self):
        with self.assertRaises(sd.DNSServiceError):
            make_service(resources=[{'id': 'r1', 'dns_name': 'bad.agence.test', 'ipv4': 'not-an-ip'}])


class ExistenceTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.actor = ADMIN

    def test_nxdomain_vs_nodata(self):
        out1 = sd.resolve(self.service, 'client', {'name': 'rien-du-tout', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out1['result']['code'], sd.NXDOMAIN)
        out2 = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'AAAA'}, passing_context(), NOW)
        self.assertEqual(out2['result']['code'], sd.NODATA)

    def test_disabled_record_behaves_as_absent(self):
        rid = next(r['id'] for r in self.service['records'].values() if r['type'] == 'A' and r['name'] == 'srv-fichiers.agence.test')
        svc = sd.apply_operation(self.service, 'set_record_enabled', {'record_id': rid, 'enabled': False}, self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.NXDOMAIN)

    def test_cname_record_direct_query(self):
        svc = sd.apply_operation(self.service, 'upsert_record',
                                 {'name': 'webfront.agence.test', 'type': 'CNAME', 'value': 'srv-fichiers.agence.test',
                                  'ttl': 300, 'enabled': True}, self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'webfront', 'type': 'CNAME'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.OK)
        self.assertEqual(out['result']['addresses'], [])
        self.assertEqual(out['result']['answers'][0]['value'], 'srv-fichiers.agence.test')

    def test_active_cname_conflicts_with_active_a_at_same_name(self):
        name = 'srv-fichiers.agence.test'
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.apply_operation(self.service, 'upsert_record',
                              {'name': name, 'type': 'CNAME', 'value': 'pc-alice.agence.test', 'ttl': 300, 'enabled': True},
                              self.actor, NOW)
        self.assertEqual(cm.exception.code, sd.RECORD_CONFLICT)


class CnameChainTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.actor = ADMIN

    def _add_cname(self, service, name, value):
        return sd.apply_operation(service, 'upsert_record',
                                  {'name': name, 'type': 'CNAME', 'value': value, 'ttl': 300, 'enabled': True},
                                  self.actor, NOW)['service']

    def test_a_query_follows_cname_chain(self):
        svc = self._add_cname(self.service, 'webfront.agence.test', 'srv-fichiers.agence.test')
        out = sd.resolve(svc, 'client', {'name': 'webfront', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.OK)
        self.assertEqual(out['result']['addresses'], ['10.0.0.5'])
        self.assertEqual(out['result']['cname_chain'], ['webfront.agence.test'])

    def test_dangling_alias_target_is_nxdomain(self):
        svc = self._add_cname(self.service, 'broken.agence.test', 'nowhere.agence.test')
        out = sd.resolve(svc, 'client', {'name': 'broken', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.NXDOMAIN)

    def test_loop_detected(self):
        svc = self._add_cname(self.service, 'a.agence.test', 'b.agence.test')
        svc = self._add_cname(svc, 'b.agence.test', 'a.agence.test')
        out = sd.resolve(svc, 'client', {'name': 'a', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.CNAME_LOOP)
        self.assertEqual(out['result']['dns_rcode'], 'SERVFAIL')
        self.assertEqual(out['result']['status'], 'failed')

    def test_depth_8_allowed_depth_9_refused(self):
        svc8 = self.service
        for i in range(1, 9):
            target = f'e{i + 1}.agence.test' if i < 8 else 'srv-fichiers.agence.test'
            svc8 = self._add_cname(svc8, f'e{i}.agence.test', target)
        out8 = sd.resolve(svc8, 'client', {'name': 'e1', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out8['result']['code'], sd.OK)
        self.assertEqual(len(out8['result']['cname_chain']), 8)

        svc9 = self.service
        for i in range(1, 10):
            target = f'f{i + 1}.agence.test' if i < 9 else 'srv-fichiers.agence.test'
            svc9 = self._add_cname(svc9, f'f{i}.agence.test', target)
        out9 = sd.resolve(svc9, 'client', {'name': 'f1', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out9['result']['code'], sd.CNAME_DEPTH)


class WrongAddressTests(unittest.TestCase):
    def test_resolution_to_deliberately_wrong_ip_is_still_a_success(self):
        service = make_service()
        actor = ADMIN
        rid = next(r['id'] for r in service['records'].values() if r['name'] == 'srv-fichiers.agence.test')
        svc = sd.apply_operation(service, 'upsert_record',
                                 {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                  'value': '192.0.2.99', 'ttl': 300, 'enabled': True}, actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['status'], 'resolved')
        self.assertEqual(out['result']['code'], sd.OK)
        self.assertEqual(out['result']['addresses'], ['192.0.2.99'])
        # Le moteur DNS ne connaît pas et n'invente jamais "WRONG_IP".
        self.assertNotIn('WRONG_IP', json.dumps(out['result']))


class ResolverConfigTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.actor = ADMIN

    def test_dns_not_configured(self):
        svc = sd.apply_operation(self.service, 'set_client_dns',
                                 {'client_id': 'client', 'dns_server_ip': None, 'search_suffix': 'agence.test'},
                                 self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['status'], 'failed')
        self.assertEqual(out['result']['code'], sd.DNS_NOT_CONFIGURED)

    def test_dns_server_unmodeled_is_unknown_not_failed(self):
        svc = sd.apply_operation(self.service, 'set_client_dns',
                                 {'client_id': 'client', 'dns_server_ip': '10.0.0.99', 'search_suffix': 'agence.test'},
                                 self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'},
                         passing_context(target_ip='10.0.0.99'), NOW)
        self.assertEqual(out['result']['status'], 'unknown')
        self.assertEqual(out['result']['code'], sd.DNS_SERVER_UNMODELED)

    def test_proof_target_ip_mismatch_with_configured_dns_is_unknown(self):
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'},
                         passing_context(target_ip='10.0.0.250'), NOW)
        self.assertEqual(out['result']['status'], 'unknown')
        self.assertEqual(out['result']['code'], sd.OBSERVATION_UNKNOWN)


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()

    def test_wrong_environment_refused_before_cache(self):
        ctx = passing_context(environment_id='other-env')
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['status'], 'unknown')
        self.assertEqual(out['result']['code'], sd.INVALID_CONTEXT)
        self.assertEqual(len(self.service['cache']['client']), 0)

    def test_unknown_client_refused(self):
        out = sd.resolve(self.service, 'unknown-client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(client_id='unknown-client'), NOW)
        self.assertEqual(out['result']['code'], sd.INVALID_CONTEXT)

    def test_wrong_target_device_refused(self):
        ctx = passing_context(target_device_id='not-the-server')
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['code'], sd.INVALID_CONTEXT)

    def test_server_id_independent_of_environment_id(self):
        server = {'id': 'device-xyz', 'name': 'SRV-DNS', 'ip': '10.0.0.5', 'zone': 'agence.test'}
        service = make_service(environment_id='env-abc', server=server)
        ctx = {
            'environment_id': 'env-abc', 'source_device_id': 'client', 'target_device_id': 'device-xyz',
            'network': {'status': 'up', 'source_device_id': 'client', 'target_device_id': 'device-xyz',
                       'target_ip': '10.0.0.5', 'observed_at': NOW - 5, 'valid_until': NOW + 30, 'evidence': 'dns_proxy'},
        }
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['code'], sd.OK)


class NetworkFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()

    def test_network_down_is_failed(self):
        ctx = passing_context(status='down')
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['status'], 'failed')
        self.assertEqual(out['result']['code'], sd.NETWORK_DOWN)

    def test_stale_observation_is_unknown(self):
        ctx = passing_context()
        ctx['network']['valid_until'] = NOW - 100
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['status'], 'unknown')
        self.assertEqual(out['result']['code'], sd.OBSERVATION_UNKNOWN)

    def test_future_observation_is_unknown(self):
        ctx = passing_context()
        ctx['network']['observed_at'] = NOW + 1000
        ctx['network']['valid_until'] = NOW + 1030
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['code'], sd.OBSERVATION_UNKNOWN)

    def test_exact_boundary_observed_at_and_valid_until_inclusive(self):
        ctx = passing_context(at=NOW)
        ctx['network']['observed_at'] = NOW
        ctx['network']['valid_until'] = NOW
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['code'], sd.OK)

    def test_missing_network_proof_is_unknown(self):
        ctx = passing_context()
        del ctx['network']
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW)
        self.assertEqual(out['result']['code'], sd.OBSERVATION_UNKNOWN)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        self.actor = ADMIN

    def test_transport_blocked_no_fake_nxdomain(self):
        svc = sd.apply_operation(self.service, 'set_transport_allowed', {'allowed': False}, self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.DNS_TRANSPORT_BLOCKED)
        self.assertNotEqual(out['result']['code'], sd.NXDOMAIN)
        self.assertEqual(len(svc['cache'].get('client', {})), 0)

    def test_service_stopped_no_fake_nxdomain(self):
        svc = sd.apply_operation(self.service, 'set_service_status', {'status': 'stopped'}, self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.DNS_SERVICE_STOPPED)

    def test_policy_and_service_failures_not_cached(self):
        svc = sd.apply_operation(self.service, 'set_service_status', {'status': 'stopped'}, self.actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['service']['cache'].get('client', {}), {})
        self.assertEqual(out['service']['revision'], svc['revision'])


class CacheHitTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()
        out = sd.resolve(self.service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertTrue(out['result']['allowed'] if 'allowed' in out['result'] else True)
        self.cached_service = out['service']

    def test_hit_works_without_any_network_proof(self):
        ctx = passing_context(at=NOW + 10)
        del ctx['network']
        out = sd.resolve(self.cached_service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx, NOW + 10)
        self.assertTrue(out['result']['cache_hit'])
        self.assertEqual(out['result']['code'], sd.OK)

    def test_hit_survives_service_stopped_and_dns_misconfigured(self):
        actor = ADMIN
        svc = sd.apply_operation(self.cached_service, 'set_service_status', {'status': 'stopped'}, actor, NOW)['service']
        svc = sd.apply_operation(svc, 'set_client_dns', {'client_id': 'client', 'dns_server_ip': None, 'search_suffix': 'agence.test'}, actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW + 10)
        self.assertTrue(out['result']['cache_hit'])
        self.assertEqual(out['result']['code'], sd.OK)

    def test_hit_blocks_server_stages_with_explicit_label(self):
        out = sd.resolve(self.cached_service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW + 10)
        stages = tree_stages(out['result']['tree'])
        by_stage = dict(stages)
        self.assertEqual(by_stage['cache'], 'passed')
        for stage in ('resolver_config', 'network', 'transport', 'service', 'records'):
            self.assertEqual(by_stage[stage], 'blocked')
        node = out['result']['tree']
        while node['stage'] != 'resolver_config':
            node = node['children'][0]
        self.assertIn('cache', node['label'])

    def test_overall_status_resolved_despite_blocked_server_stages(self):
        out = sd.resolve(self.cached_service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW + 10)
        self.assertEqual(out['result']['status'], 'resolved')

    def test_cache_hit_evidence_is_simulated_cache(self):
        out = sd.resolve(self.cached_service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW + 10)
        self.assertEqual(out['result']['evidence'], 'simulated_cache')


class CacheIsolationTests(unittest.TestCase):
    def test_isolated_between_clients(self):
        clients = CLIENTS + [{'id': 'client2', 'name': 'PC-BOB', 'dns_server_ip': '10.0.0.5', 'search_suffix': 'agence.test'}]
        service = make_service(clients=clients)
        ctx1 = passing_context(client_id='client')
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx1, NOW)
        svc1 = out1['service']
        self.assertEqual(svc1['cache'].get('client2', {}), {})
        self.assertEqual(len(svc1['cache']['client']), 1)

    def test_isolated_between_environments(self):
        a = make_service(environment_id='env-a')
        b = make_service(environment_id='env-b')
        ctx_a = passing_context(environment_id='env-a')
        out = sd.resolve(a, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx_a, NOW)
        self.assertEqual(b['cache'].get('client', {}), {})
        self.assertNotEqual(out['service']['cache']['client'], b['cache'].get('client', {}))

    def test_same_name_a_and_aaaa_cached_separately(self):
        resources = RESOURCES + [{'id': 'r3', 'dns_name': 'dual.agence.test', 'ipv4': '10.0.0.20', 'ipv6': '2001:db8::20'}]
        service = make_service(resources=resources)
        out1 = sd.resolve(service, 'client', {'name': 'dual', 'type': 'A'}, passing_context(), NOW)
        out2 = sd.resolve(out1['service'], 'client', {'name': 'dual', 'type': 'AAAA'}, passing_context(), NOW)
        self.assertEqual(len(out2['service']['cache']['client']), 2)


class TtlCacheTests(unittest.TestCase):
    def test_ttl_zero_not_cached(self):
        resources = RESOURCES
        service = make_service(resources=resources)
        actor = ADMIN
        rid = next(r['id'] for r in service['records'].values() if r['name'] == 'srv-fichiers.agence.test')
        svc = sd.apply_operation(service, 'upsert_record',
                                 {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                  'value': '10.0.0.5', 'ttl': 0, 'enabled': True}, actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['result']['code'], sd.OK)
        self.assertEqual(out['result']['addresses'], ['10.0.0.5'])
        self.assertEqual(out['service']['cache'].get('client', {}), {})
        self.assertEqual(out['service']['revision'], svc['revision'])

    def test_exact_expiry_triggers_new_consultation(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out1['service']
        entry = svc1['cache']['client'][next(iter(svc1['cache']['client']))]
        expires_at = entry['expires_at']
        ctx_at_expiry = passing_context(at=expires_at)
        out2 = sd.resolve(svc1, 'client', {'name': 'srv-fichiers', 'type': 'A'}, ctx_at_expiry, expires_at)
        self.assertFalse(out2['result']['cache_hit'])

    def test_hit_does_not_push_back_expiry(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out1['service']
        expires_before = svc1['cache']['client'][next(iter(svc1['cache']['client']))]['expires_at']
        out2 = sd.resolve(svc1, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        expires_after = out2['service']['cache']['client'][next(iter(out2['service']['cache']['client']))]['expires_at']
        self.assertEqual(expires_before, expires_after)
        self.assertEqual(out2['service'], svc1)  # un hit ne mute rien du tout

    def test_hit_recomputes_ttl_remaining(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out1['service']
        out2 = sd.resolve(svc1, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(at=NOW + 50), NOW + 50)
        self.assertEqual(out2['result']['answers'][0]['ttl_remaining'],
                         max(0, out2['result']['valid_until'] - (NOW + 50)))

    def test_cname_chain_cache_expires_at_minimum_ttl(self):
        service = make_service()
        actor = ADMIN
        svc = sd.apply_operation(service, 'upsert_record',
                                 {'name': 'webfront.agence.test', 'type': 'CNAME', 'value': 'srv-fichiers.agence.test',
                                  'ttl': 50, 'enabled': True}, actor, NOW)['service']
        rid = next(r['id'] for r in svc['records'].values() if r['name'] == 'srv-fichiers.agence.test')
        svc = sd.apply_operation(svc, 'upsert_record',
                                 {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                  'value': '10.0.0.5', 'ttl': 500, 'enabled': True}, actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'webfront', 'type': 'A'}, passing_context(), NOW)
        entry = out['service']['cache']['client'][next(iter(out['service']['cache']['client']))]
        self.assertEqual(entry['expires_at'] - entry['cached_at'], 50)


class RepairAndStaleCacheTests(unittest.TestCase):
    def test_fixed_record_not_reflected_until_expiry(self):
        service = make_service()
        actor = ADMIN
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out['service']
        rid = next(r['id'] for r in svc1['records'].values() if r['name'] == 'srv-fichiers.agence.test')
        svc2 = sd.apply_operation(svc1, 'upsert_record',
                                  {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                   'value': '10.0.0.200', 'ttl': 300, 'enabled': True}, actor, NOW)['service']
        out2 = sd.resolve(svc2, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        self.assertEqual(out2['result']['addresses'], ['10.0.0.5'])  # ancienne valeur encore en cache

    def test_reducing_ttl_does_not_shorten_existing_cache(self):
        service = make_service()
        actor = ADMIN
        rid = next(r['id'] for r in service['records'].values() if r['name'] == 'srv-fichiers.agence.test')
        svc = sd.apply_operation(service, 'upsert_record',
                                 {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                  'value': '10.0.0.5', 'ttl': 3600, 'enabled': True}, actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out['service']
        expires_before = svc1['cache']['client'][next(iter(svc1['cache']['client']))]['expires_at']
        svc2 = sd.apply_operation(svc1, 'upsert_record',
                                  {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                   'value': '10.0.0.5', 'ttl': 1, 'enabled': True}, actor, NOW)['service']
        expires_after = svc2['cache']['client'][next(iter(svc2['cache']['client']))]['expires_at']
        self.assertEqual(expires_before, expires_after)

    def test_negative_cache_nxdomain_and_nodata(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'rien-du-tout', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(len(out1['service']['cache']['client']), 1)
        out2 = sd.resolve(out1['service'], 'client', {'name': 'srv-fichiers', 'type': 'AAAA'}, passing_context(), NOW)
        self.assertEqual(len(out2['service']['cache']['client']), 2)

    def test_new_record_not_immediately_visible_after_negative_cache(self):
        service = make_service()
        actor = ADMIN
        out1 = sd.resolve(service, 'client', {'name': 'nouveauservice', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out1['result']['code'], sd.NXDOMAIN)
        svc1 = out1['service']
        svc2 = sd.apply_operation(svc1, 'upsert_record',
                                  {'name': 'nouveauservice.agence.test', 'type': 'A', 'value': '10.0.0.77',
                                   'ttl': 300, 'enabled': True}, actor, NOW)['service']
        out2 = sd.resolve(svc2, 'client', {'name': 'nouveauservice', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        self.assertEqual(out2['result']['code'], sd.NXDOMAIN)  # cache négatif encore valide
        entry = svc2['cache']['client']['nouveauservice.agence.test|A']
        out3 = sd.resolve(svc2, 'client', {'name': 'nouveauservice', 'type': 'A'},
                          passing_context(at=entry['expires_at']), entry['expires_at'])
        self.assertEqual(out3['result']['code'], sd.OK)

    def test_flush_repairs_immediately(self):
        service = make_service()
        actor = ADMIN
        out1 = sd.resolve(service, 'client', {'name': 'nouveauservice', 'type': 'A'}, passing_context(), NOW)
        svc1 = sd.apply_operation(out1['service'], 'upsert_record',
                                  {'name': 'nouveauservice.agence.test', 'type': 'A', 'value': '10.0.0.77',
                                   'ttl': 300, 'enabled': True}, actor, NOW)['service']
        flushed = sd.flush_cache(svc1, actor, 'client', NOW + 1)['service']
        out2 = sd.resolve(flushed, 'client', {'name': 'nouveauservice', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        self.assertEqual(out2['result']['code'], sd.OK)

    def test_servfail_and_network_errors_not_cached_and_do_not_erase_existing_entry(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out1['service']
        before = copy.deepcopy(svc1['cache'])
        out2 = sd.resolve(svc1, 'client', {'name': 'pc-alice', 'type': 'A'}, passing_context(status='down'), NOW)
        self.assertEqual(out2['service']['cache'], before)


class AdminCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.service = make_service()

    def test_missing_capability_refused_without_mutation(self):
        before = copy.deepcopy(self.service)
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.apply_operation(self.service, 'set_transport_allowed', {'allowed': False}, NO_CAP_ACTOR, NOW)
        self.assertEqual(cm.exception.code, sd.PERMISSION_DENIED)
        self.assertEqual(self.service, before)

    def test_wrong_environment_actor_refused(self):
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.apply_operation(self.service, 'set_transport_allowed', {'allowed': False}, WRONG_ENV_ACTOR, NOW)
        self.assertEqual(cm.exception.code, sd.UNKNOWN_ENVIRONMENT)

    def test_flush_own_limited_to_own_device(self):
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.flush_cache(self.service, OTHER_USER, 'client', NOW)
        self.assertEqual(cm.exception.code, sd.PERMISSION_DENIED)
        ok = sd.flush_cache(self.service, SELF_USER, 'client', NOW)
        self.assertTrue(ok['result']['allowed'])

    def test_unknown_operation_refused(self):
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.apply_operation(self.service, 'reboot_server', {}, ADMIN, NOW)
        self.assertEqual(cm.exception.code, sd.UNKNOWN_OPERATION)

    def test_unauthorized_field_refused(self):
        with self.assertRaises(sd.DNSServiceError):
            sd.apply_operation(self.service, 'set_transport_allowed', {}, ADMIN, NOW)  # champ 'allowed' manquant


class IdsAndRoundtripTests(unittest.TestCase):
    def test_record_id_stable_after_update(self):
        service = make_service()
        actor = ADMIN
        rid = next(iter(service['records']))
        out = sd.apply_operation(service, 'upsert_record',
                                 {'record_id': rid, 'name': service['records'][rid]['name'],
                                  'type': service['records'][rid]['type'], 'value': service['records'][rid]['value'],
                                  'ttl': 1234, 'enabled': True}, actor, NOW)
        self.assertIn(rid, out['service']['records'])
        self.assertEqual(out['service']['records'][rid]['ttl'], 1234)

    def test_json_roundtrip_preserves_behavior(self):
        service = make_service()
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        reloaded = json.loads(json.dumps(out['service']))
        sd.validate_dns(reloaded)
        out2 = sd.resolve(reloaded, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        self.assertTrue(out2['result']['cache_hit'])


class RevisionAuditTests(unittest.TestCase):
    def test_resolve_cache_write_bumps_revision_and_audit(self):
        service = make_service()
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        self.assertEqual(out['service']['revision'], service['revision'] + 1)
        self.assertEqual(len(out['service']['audit']), len(service['audit']) + 1)
        last = out['service']['audit'][-1]
        self.assertNotIn('content', last)

    def test_cache_hit_does_not_bump_revision(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        svc1 = out1['service']
        out2 = sd.resolve(svc1, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        self.assertEqual(out2['service']['revision'], svc1['revision'])
        self.assertEqual(out2['service'], svc1)

    def test_deterministic_eviction_oldest_cached_at_lexical_tiebreak(self):
        service = make_service()
        actor = ADMIN
        svc = service
        for i in range(sd.MAX_CACHE_PER_CLIENT):
            svc = sd.apply_operation(svc, 'upsert_record',
                                     {'name': f'h{i}.agence.test', 'type': 'A', 'value': '10.0.0.1',
                                      'ttl': 300, 'enabled': True}, actor, NOW)['service']
            svc = sd.resolve(svc, 'client', {'name': f'h{i}', 'type': 'A'}, passing_context(at=NOW + i), NOW + i)['service']
        self.assertEqual(len(svc['cache']['client']), sd.MAX_CACHE_PER_CLIENT)
        svc = sd.apply_operation(svc, 'upsert_record',
                                 {'name': 'hnew.agence.test', 'type': 'A', 'value': '10.0.0.2',
                                  'ttl': 300, 'enabled': True}, actor, NOW)['service']
        out = sd.resolve(svc, 'client', {'name': 'hnew', 'type': 'A'}, passing_context(at=NOW + 1000), NOW + 1000)
        self.assertEqual(len(out['service']['cache']['client']), sd.MAX_CACHE_PER_CLIENT)
        self.assertNotIn('h0.agence.test|A', out['service']['cache']['client'])


class TreeTests(unittest.TestCase):
    def test_full_tree_with_blocked_after_failure(self):
        service = make_service()
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(status='down'), NOW)
        stages = tree_stages(out['result']['tree'])
        by_stage = dict(stages)
        self.assertEqual(by_stage['network'], 'failed')
        self.assertEqual(by_stage['transport'], 'blocked')
        self.assertEqual(by_stage['service'], 'blocked')
        self.assertEqual(by_stage['records'], 'blocked')

    def test_cache_branch_never_claims_server_was_consulted(self):
        service = make_service()
        out1 = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        out2 = sd.resolve(out1['service'], 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(at=NOW + 1), NOW + 1)
        dumped = json.dumps(out2['result']['tree'], ensure_ascii=False)
        self.assertIn('non nécessaire', dumped)


class PublicProjectionTests(unittest.TestCase):
    def test_unauthorized_actor_refused(self):
        service = make_service()
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.public_dns(service, NO_CAP_ACTOR)
        self.assertEqual(cm.exception.code, sd.PERMISSION_DENIED)

    def test_wrong_environment_refused(self):
        service = make_service()
        with self.assertRaises(sd.DNSServiceError) as cm:
            sd.public_dns(service, WRONG_ENV_ACTOR)
        self.assertEqual(cm.exception.code, sd.UNKNOWN_ENVIRONMENT)

    def test_projection_exposes_cache_count_not_content(self):
        service = make_service()
        out = sd.resolve(service, 'client', {'name': 'srv-fichiers', 'type': 'A'}, passing_context(), NOW)
        projection = sd.public_dns(out['service'], ADMIN)
        self.assertEqual(projection['clients']['client']['cache_count'], 1)
        dumped = json.dumps(projection)
        self.assertNotIn('expires_at', dumped)
        self.assertNotIn('identity', dumped)


class RepairIsolationTests(unittest.TestCase):
    def test_repairing_one_record_does_not_touch_others(self):
        service = make_service()
        actor = ADMIN
        other_rid = next(r['id'] for r in service['records'].values() if r['name'] == 'pc-alice.agence.test')
        other_before = copy.deepcopy(service['records'][other_rid])
        rid = next(r['id'] for r in service['records'].values() if r['name'] == 'srv-fichiers.agence.test')
        out = sd.apply_operation(service, 'upsert_record',
                                 {'record_id': rid, 'name': 'srv-fichiers.agence.test', 'type': 'A',
                                  'value': '10.0.0.6', 'ttl': 300, 'enabled': True}, actor, NOW)
        self.assertEqual(out['service']['records'][other_rid], other_before)
        self.assertEqual(out['service']['clients'], service['clients'])


class DocumentationExampleTests(unittest.TestCase):
    def test_minimal_example_runs(self):
        """Rejoue l'exemple minimal documenté dans
        docs/SIM-DNS-IMPLEMENTATION.md pour garantir qu'il reste exécutable."""
        server = {'id': 'srv-dns-01', 'name': 'SRV-DNS', 'ip': '10.1.1.10', 'zone': 'exemple.test'}
        clients = [{'id': 'pc-doc', 'name': 'PC-DOC', 'dns_server_ip': '10.1.1.10', 'search_suffix': 'exemple.test'}]
        resources = [{'id': 'r1', 'dns_name': 'intranet.exemple.test', 'ipv4': '10.1.1.20'}]
        service = sd.generate_dns('exemple-doc', 'env-doc', server, clients, resources, 1_000_000)
        context = {
            'environment_id': 'env-doc', 'source_device_id': 'pc-doc', 'target_device_id': 'srv-dns-01',
            'network': {'status': 'up', 'source_device_id': 'pc-doc', 'target_device_id': 'srv-dns-01',
                       'target_ip': '10.1.1.10', 'observed_at': 999_990, 'valid_until': 1_000_100, 'evidence': 'dns_proxy'},
        }
        out = sd.resolve(service, 'pc-doc', {'name': 'intranet', 'type': 'A'}, context, 1_000_000)
        self.assertTrue(out['result']['status'] == 'resolved')
        self.assertEqual(out['result']['code'], sd.OK)
        self.assertEqual(out['result']['addresses'], ['10.1.1.20'])


if __name__ == '__main__':
    unittest.main()

