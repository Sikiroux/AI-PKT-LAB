import json
import unittest
from unittest.mock import Mock
import quiet_checks
from diagnostic import Engine

class QuietChecksTests(unittest.TestCase):
    def test_periodic_script_never_uses_console_or_fast_forward(self):
        code=quiet_checks.script([('PC-1','192.168.1.1')])
        for forbidden in ('enterCommand','getCommandLine','clearConsole','setSimulationMode','resetNetwork'):
            self.assertNotIn(forbidden,code)
        self.assertIn('if(false&&pending>0)ipc.appWindow()',code)
        self.assertIn('createPingProcess',code);self.assertIn('donePing.connect',code)
    def test_manual_acceleration_is_explicit_and_simulation_guarded(self):
        code=quiet_checks.script([('PC-1','192.168.1.1')],True)
        self.assertIn('if(true&&pending>0)ipc.appWindow()',code)
        self.assertIn('isSimulationMode()',code)
        self.assertIn('contrôle suspendu',code)
    def test_batch_is_correlated_and_bounded(self):
        engine=Mock();engine.call.return_value=json.dumps([{'status':'valide'},{'status':'non satisfait'}])
        rows=quiet_checks.run(engine,[('a','192.168.1.1'),('b','192.168.1.2')])
        self.assertEqual([r['status'] for r in rows],['valide','non satisfait'])
        self.assertEqual(engine.call.call_args.kwargs,{'timeout':12})
    def test_timeout_never_falls_back_to_console_or_reports_success(self):
        engine=Mock();engine.call.side_effect=RuntimeError('timeout')
        rows=quiet_checks.run(engine,[('a','192.168.1.1')])
        self.assertEqual(rows[0]['status'],'inconnu');engine.ping.assert_not_called()
    def test_incomplete_and_invalid_results_are_unknown(self):
        for response in ('[]','{"error":"unsupported"}','[{"status":"success"}]'):
            engine=Mock();engine.call.return_value=response
            self.assertEqual(quiet_checks.run(engine,[('a','192.168.1.1')])[0]['status'],'inconnu')
    def test_bad_ip_is_rejected_before_any_injection(self):
        engine=Mock()
        rows=quiet_checks.run(engine,[('a','not-an-ip')]);self.assertEqual(rows[0]['status'],'inconnu');engine.call.assert_not_called()
    def test_engine_uses_new_adapter(self):
        engine=Engine(Mock());engine.call=Mock(return_value='[{"status":"valide"}]')
        self.assertEqual(engine.quiet_pings([('a','192.168.1.1')])[0]['status'],'valide')

class TicketMetadataTests(unittest.TestCase):
    def test_manual_ticket_verification_targets_primary_when_legacy_ticket_has_no_serial(self):
        import test_unified_tickets as fixture
        fixture.UnifiedTickets.setUp(self)
        state=fixture.UnifiedTickets.state(self,'a')
        fixture.UnifiedTickets.bind(self,state)
        self.controller.engine=Engine(Mock())
        self.t.action('INC-1000','verify',{})
        self.controller.observe.assert_called_once_with(blocking=True,client_serial='a-client',accelerate=True)

    def test_public_snapshot_does_not_alias_live_notes(self):
        import tempfile
        from pathlib import Path
        from tickets_app import Tickets
        with tempfile.TemporaryDirectory() as folder:
            t=Tickets(Mock(),Path(folder)/'tickets.json')
            t.state['tickets']=[dict(id='x',kind='workspace',status='nouveau',notes='')]
            before=t.public();t.action('x','notes',{'notes':'after'})
            self.assertEqual(before['tickets'][0]['notes'],'')
            t.engine.ping.assert_not_called()
    def test_take_does_not_wait_for_network_lock(self):
        import tempfile,threading
        from pathlib import Path
        from tickets_app import Tickets
        with tempfile.TemporaryDirectory() as folder:
            engine=Mock();engine.lock=threading.Lock();engine.lock.acquire()
            t=Tickets(engine,Path(folder)/'tickets.json');t.state['tickets']=[dict(id='x',kind='workspace',status='nouveau')]
            finished=threading.Event()
            def take():
                with t.metadata_lock:t.action('x','take',{})
                finished.set()
            thread=threading.Thread(target=take);thread.start()
            try:self.assertTrue(finished.wait(1));self.assertEqual(t.get('x')['status'],'en_cours')
            finally:engine.lock.release();thread.join(1)
            engine.ping.assert_not_called()

if __name__=='__main__':unittest.main()
