import copy
import threading
import unittest
from unittest.mock import Mock,patch
import desktop_services as ds
import desktop_controller as dc

class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.s={'environment_id':'env','desktop_services':{'printing':{'spooler_running':False},'ftp':{'service_running':True,'accounts':{'secret':'hidden'}}},'file_service':{'service_status':'running'},'dns_service':{'service_status':'stopped'},'directory_service':True,'events':[{'at':i,'text':str(i),'extra':'hidden'} for i in range(105)]}
    def test_read_only(self):
        before=copy.deepcopy(self.s);r=ds.inspection(self.s);self.assertEqual(self.s,before);self.assertEqual(len(r['events']),100);self.assertEqual(r['events'][0]['at'],5);self.assertNotIn('accounts',str(r));self.assertNotIn('extra',str(r))
    def test_actual_and_unknown(self):
        values={x['id']:x['status'] for x in ds.inspection(self.s)['services']};self.assertEqual(values,dict(spooler='stopped',files='running',dns='stopped',ftp='running',directory='running'));self.assertTrue(all(x['status']=='unknown' for x in ds.inspection({})['services']))
    def test_controller_scope_and_no_write(self):
        c=Mock();c.lock=threading.RLock();c.workspace.state=self.s
        with patch.object(dc,'admin') as admin,patch.object(dc,'remote') as remote:
            r=dc.handle(c,'inspection/state',{'source':'technician'});admin.assert_called_once();remote.assert_not_called();self.assertEqual(r['environment_id'],'env')
            dc.handle(c,'inspection/state',{'source':'client'});remote.assert_called_once()
            with self.assertRaises(ValueError):dc.handle(c,'inspection/state',{'source':'other'})
            with self.assertRaises(ValueError):dc.handle(c,'inspection/operation',{})
        c.workspace.save.assert_not_called();c.workspace.event.assert_not_called()
    def test_refusal(self):
        c=Mock();c.lock=threading.RLock();c.workspace.state=self.s
        with patch.object(dc,'admin',side_effect=ValueError('network')):
            with self.assertRaises(ValueError):dc.handle(c,'inspection/state',{'source':'technician'})

if __name__=='__main__':unittest.main()
