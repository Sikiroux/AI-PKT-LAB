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
