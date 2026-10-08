import copy
import unittest
import sim_deployment as sim

class DeploymentTests(unittest.TestCase):
    def setUp(self):self.s=sim.generate('test','env')
    def act(self,a,**p):self.s=sim.apply(self.s,a,p,self.s['revision']);return self.s
    def disk(self,image=None):
        self.act('start');self.act('mount',image_id=image or self.s['requirements']['image_id']);self.act('boot',source='usb');self.act('setup');self.act('load_driver')
    def partition(self,size=100):
        self.act('backup');self.act('delete_partition',partition_id='old-os');self.act('delete_partition',partition_id='old-data');self.act('partition',size_gib=size)
    def finish(self):
        self.act('install',partition_id='windows')
        for _ in range(3):self.act('advance')
        self.act('eject');self.act('restart');self.act('configure',**{k:self.s['requirements'][k] for k in ('locale','keyboard','account')})
    def test_reproducible(self):self.assertEqual(self.s,sim.generate('test','env'))
    def test_variety(self):self.assertGreater(len({str(sim.generate(str(i),'env')['requirements']) for i in range(30)}),3)
    def test_baseline_fails(self):self.assertFalse(sim.evaluate(self.s)['passed'])
    def test_complete(self):self.disk();self.partition();self.finish();self.assertTrue(sim.evaluate(self.s)['passed'])
    def test_wrong_image(self):self.disk('home');self.partition();self.finish();self.assertFalse(sim.evaluate(self.s)['checks']['image'])
    def test_backup_required(self):
        self.disk();old=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.act('delete_partition',partition_id='old-os')
        self.assertEqual(old,self.s)
    def test_backup_preserved(self):
        self.disk();self.act('backup');original=copy.deepcopy(self.s['backup']);self.act('delete_partition',partition_id='old-os');self.act('backup');self.assertEqual(original,self.s['backup'])
    def test_missing_driver(self):
        self.disk();self.s['disk']['visible']=False
        with self.assertRaises(ValueError):self.act('backup')
    def test_stale_revision(self):
        with self.assertRaises(ValueError):sim.apply(self.s,'start',{},1)
    def test_boolean_revision(self):
        with self.assertRaises(ValueError):sim.apply(self.s,'start',{},False)
    def test_stage_guard(self):
        with self.assertRaises(ValueError):self.act('advance')
    def test_copy_on_write(self):
        old=copy.deepcopy(self.s);sim.apply(self.s,'start',{},0);self.assertEqual(old,self.s)
    def test_capacity_guard(self):
        self.disk();self.partition()
        self.s['disk']['partitions']=[]
        with self.assertRaises(ValueError):self.act('partition',size_gib=self.s['disk']['capacity_mib']//1024)
    def test_partition_layout(self):
        self.disk();self.partition();parts=self.s['disk']['partitions'];self.assertEqual([p['id'] for p in parts],['efi','msr','windows','recovery']);self.assertLessEqual(sum(p['mib'] for p in parts),self.s['disk']['capacity_mib'])
    def test_small_partition(self):
        self.disk();self.partition(20)
        with self.assertRaises(ValueError):self.act('install',partition_id='windows')
    def test_wrong_partition(self):
        self.disk();self.partition()
        with self.assertRaises(ValueError):self.act('install',partition_id='efi')
    def test_remove_media(self):
        self.disk();self.partition();self.act('install',partition_id='windows')
        for _ in range(3):self.act('advance')
        with self.assertRaises(ValueError):self.act('restart')
    def test_wrong_account(self):
        self.disk();self.partition();self.finish();self.s['settings']['account']='other';self.assertFalse(sim.evaluate(self.s)['passed'])
    def test_old_boot(self):
        self.act('start');self.act('mount',image_id='pro-base')
        with self.assertRaises(ValueError):self.act('boot',source='disk')
    def test_revision_history(self):
        self.disk();self.partition();self.finish();self.assertEqual(self.s['revision'],len(self.s['history']))

if __name__=='__main__':unittest.main()
