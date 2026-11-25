"""Execute the generated Packet Tracer JavaScript against a minimal IPC adapter."""
import json,shutil,subprocess,unittest
import live_faults

@unittest.skipUnless(shutil.which('node'),'Node.js required to execute the generated JavaScript')
class MutationGuardTests(unittest.TestCase):
 def run_case(self,restore,current,serial='S',dhcp=False):
  injection=dict(device='PC-01',serial='S',port='FastEthernet0',before=dict(ip='10.0.0.21',mask='255.255.255.0'),after=dict(ip='192.168.250.21',mask='255.255.255.0'))
  script='const current='+json.dumps(current)+';let writes=0,result;const port={getIpAddress:()=>current.ip,getSubnetMask:()=>current.mask,isDhcpClientOn:()=>'+json.dumps(dhcp)+',setIpSubnetMask:(ip,mask)=>{writes++;current.ip=ip;current.mask=mask}};const ipc={network:()=>({getDevice:()=>({getSerialNumber:()=>'+json.dumps(serial)+',getPort:()=>port})})};const reportResult=v=>result=v;'+live_faults.apply_js(injection,restore)+';process.stdout.write(JSON.stringify({writes,result,current}));'
  proc=subprocess.run(['node','-e',script],check=True,capture_output=True,text=True)
  return json.loads(proc.stdout)
 def test_apply_requires_unchanged_baseline(self):
  self.assertEqual(self.run_case(False,dict(ip='10.0.0.21',mask='255.255.255.0'))['writes'],1)
  self.assertEqual(self.run_case(False,dict(ip='10.0.0.22',mask='255.255.255.0'))['writes'],0)
 def test_restore_refuses_concurrent_ip_or_mask_change(self):
  valid=self.run_case(True,dict(ip='192.168.250.21',mask='255.255.255.0'))
  self.assertEqual(valid['writes'],1);self.assertEqual(valid['current']['ip'],'10.0.0.21')
  for current in [dict(ip='10.0.0.99',mask='255.255.255.0'),dict(ip='192.168.250.21',mask='255.255.0.0')]:
   result=self.run_case(True,current)
   self.assertEqual(result['writes'],0);self.assertEqual(result['current'],current);self.assertIn('modifiée',result['result'])
 def test_identity_and_dhcp_changes_refuse_writes(self):
  for options in [dict(serial='replacement'),dict(dhcp=True)]:
   self.assertEqual(self.run_case(True,dict(ip='192.168.250.21',mask='255.255.255.0'),**options)['writes'],0)
