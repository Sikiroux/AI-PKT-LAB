import json,threading,unittest
from vendor.live_bridge import PTCommandBridge

class PollLeaseTests(unittest.TestCase):
 def bridge(self):return PTCommandBridge(token='test-secret')
 def test_old_waiting_request_cannot_take_next_command(self):
  b=self.bridge();waiting=threading.Event();out=[]
  def eligible():waiting.set();return not b.diagnostic_poll_lease
  t=threading.Thread(target=lambda:out.extend(b.drain_commands(accept=eligible)));t.start();self.assertTrue(waiting.wait(1))
  b.set_diagnostic_poll_lease(True);b._queue.put_nowait('next-command');t.join(1)
  self.assertFalse(t.is_alive());self.assertEqual(out,[]);self.assertEqual(b._queue.qsize(),1)
  self.assertEqual(b.drain_commands(accept=lambda:True),['next-command'])
 def test_rejected_poll_does_not_remove_queued_command(self):
  b=self.bridge();b.set_diagnostic_poll_lease(True);b._queue.put_nowait('command')
  self.assertEqual(b.drain_commands(accept=lambda:not b.diagnostic_poll_lease),[])
  self.assertEqual(b.drain_commands(accept=lambda:True),['command'])
 def test_install_ack_activates_only_for_experimental_suite(self):
  b=self.bridge();b.diagnostic_events=[];body=json.dumps({'stage':'poll_fix_installed'})
  b.put_result('netops-webview-trace',body);self.assertFalse(b.diagnostic_poll_lease)
  b.diagnostic_poll_repair=True;b.put_result('netops-webview-trace',body);self.assertTrue(b.diagnostic_poll_lease)
 def test_ordinary_queue_still_drains_in_order(self):
  b=self.bridge();b._queue.put_nowait('one');b._queue.put_nowait('two');self.assertEqual(b.drain_commands(),['one','two'])
 def test_http_route_requires_tag_and_keeps_authentication(self):
  import urllib.request
  from urllib.error import HTTPError
  b=PTCommandBridge(port=0,token='a'*48);b.start();port=b._server.server_address[1]
  def get(path,token='a'*48):
   return urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+str(port)+path,headers={'X-PT-Token':token}),timeout=3).read()
  try:
   b.set_diagnostic_poll_lease(True);b._queue.put_nowait('command')
   self.assertEqual(get('/next'),b'');self.assertEqual(b._queue.qsize(),1)
   with self.assertRaises(HTTPError):get('/next?netops_poll=1','wrong')
   self.assertEqual(b._queue.qsize(),1);self.assertEqual(get('/next?netops_poll=1'),b'command')
  finally:b.stop()
