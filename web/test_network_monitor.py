import unittest
import network_monitor as monitor

class MonitorTests(unittest.TestCase):
    def state(self):
        return dict(devices={'client': {'serial': 'pc00'}}, observation=None,
                    client_workspaces={f'pc{i:02}': {'local': {'observation': None, 'remote_session': i < 8}}
                                       for i in range(30)}, remote_session=True)

    def test_all_thirty_receive_a_turn_despite_active_sessions(self):
        s=self.state(); seen=set()
        for at in range(1,61):
            serial=monitor.select_target(s);seen.add(serial)
            observation=dict(at=at,status='passed')
            if serial=='pc00':s['observation']=observation
            else:s['client_workspaces'][serial]['local']['observation']=observation
        self.assertEqual(len(seen),30)

    def test_active_priority_and_background_fairness(self):
        s=self.state()
        self.assertEqual(monitor.select_target(s),'pc00')
        s['observation']=dict(at=1,status='unknown')
        self.assertEqual(monitor.select_target(s),'pc01')
        s['client_workspaces']['pc01']['local']['observation']=dict(at=2,status='passed')
        self.assertEqual(monitor.select_target(s),'pc02')

    def test_expired_failure_is_not_reported_as_current_failure(self):
        s=dict(observation=dict(at=100,status='failed'),last_known_observation=dict(at=100,status='failed'))
        self.assertEqual(monitor.public_status(s,145)['status'],'failed')
        result=monitor.public_status(s,146)
        self.assertEqual((result['status'],result['reason']),('unknown','expired'))
        self.assertEqual(result['last_known_status'],'failed')

    def test_desktop_health_uses_remote_pair_not_aggregate_printing_failure(self):
        s=dict(observation=dict(at=100,status='failed',probes={'remote':dict(at=100,status='passed')}))
        self.assertEqual(monitor.public_status(s,101)['status'],'passed')

    def test_transport_error_and_future_timestamp_are_unknown(self):
        s=dict(observation=dict(at=100,status='unknown',detail='Pont arrêté'),last_known_observation=dict(at=90,status='passed'))
        self.assertEqual(monitor.public_status(s,101)['reason'],'transport')
        self.assertEqual(monitor.public_status(s,99)['status'],'unknown')
        self.assertEqual(monitor.public_status(s,101)['last_known_at'],90)

if __name__=='__main__':unittest.main()

class ControllerMonitorTests(unittest.TestCase):
    def test_periodic_observes_only_one_target_without_acceleration(self):
        from contextlib import nullcontext
        from unittest.mock import Mock
        import tempfile
        from workspace_app import Controller
        with tempfile.TemporaryDirectory() as folder:
            controller=Controller(None,folder)
            controller.workspace.state=dict(staff_size=30,devices={'client': {'serial':'a'}},
                client_workspaces={'a':{'local':{}},'b':{'local':{}}})
            controller.workspace.save=Mock()
            controller.client_scope=Mock(return_value=nullcontext())
            controller._observe_one=Mock()
            controller.observe(accelerate=True)
            controller.client_scope.assert_called_once_with('a')
            controller._observe_one.assert_called_once_with(blocking=True,accelerate=False)

    def test_explicit_request_keeps_target_and_acceleration(self):
        from contextlib import nullcontext
        from unittest.mock import Mock
        import tempfile
        from workspace_app import Controller
        with tempfile.TemporaryDirectory() as folder:
            controller=Controller(None,folder)
            controller.workspace.state=dict(staff_size=30)
            controller.workspace.save=Mock()
            controller.client_scope=Mock(return_value=nullcontext())
            controller._observe_one=Mock()
            controller.observe(blocking=True,client_serial='b',accelerate=True)
            controller.client_scope.assert_called_once_with('b')
            controller._observe_one.assert_called_once_with(blocking=True,accelerate=True)

class ForegroundTests(unittest.TestCase):
    def test_presence_is_short_lived_and_scoped(self):
        presence=monitor.BrowserPresence()
        presence.touch('A','pc1',100)
        self.assertEqual(presence.active('A',115),{'pc1'})
        self.assertEqual(presence.active('A',116),set())
        self.assertEqual(presence.active('B',101),set())
        self.assertEqual(presence.active('A',99),set())

    def test_visible_post_beats_old_open_sessions_without_starving_park(self):
        s=MonitorTests().state();seen=set()
        for at in range(1,61):
            serial=monitor.select_target(s,{'pc07','unknown'})
            if at%2==1:self.assertEqual(serial,'pc07')
            seen.add(serial)
            if serial=='pc00':s['observation']={'at':at}
            else:s['client_workspaces'][serial]['local']['observation']={'at':at}
        self.assertEqual(len(seen),30)

    def test_presence_does_not_validate_network_or_authenticate(self):
        import copy
        s=MonitorTests().state();before=copy.deepcopy(s)
        presence=monitor.BrowserPresence();presence.touch('A','pc00',100)
        self.assertEqual(s,before)
        self.assertEqual(monitor.public_status(s,101)['status'],'unknown')

class PresenceRouteTests(unittest.TestCase):
    def test_read_registers_only_visible_matching_environment(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from workspace_routes import WorkspaceRoutes
        snapshot=dict(environment_id='A',client_serial='pc1')
        controller=SimpleNamespace(public_snapshot=Mock(return_value=snapshot),browser_presence=monitor.BrowserPresence())
        routes=WorkspaceRoutes(controller,'token')
        def read(query):
            handler=SimpleNamespace(path='/workspace/state'+query,send=Mock())
            self.assertTrue(routes.get(handler));handler.send.assert_called_once_with(200,snapshot)
        read('?client_serial=pc1&visible=1&environment_id=B')
        self.assertEqual(controller.browser_presence.active('A'),set())
        read('?client_serial=pc1&environment_id=A')
        self.assertEqual(controller.browser_presence.active('A'),set())
        read('?client_serial=pc1&visible=1&environment_id=A')
        self.assertEqual(controller.browser_presence.active('A'),{'pc1'})
        self.assertEqual(controller.browser_presence.active('B'),set())
