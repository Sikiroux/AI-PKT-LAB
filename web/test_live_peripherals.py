"""Matériel local : panne avant ticket, coexistence et clôture sans réseau."""
import copy
import unittest
from unittest.mock import patch
import test_enterprise_incidents as fixtures
import enterprise_incidents as live
import sim_peripherals as hardware

class PeripheralTests(unittest.TestCase):
 setUp=fixtures.LiveTests.setUp
 tickets=fixtures.LiveTests.tickets
 proofs=fixtures.LiveTests.proofs
 def repair(self,serial):
  model=self.s['peripherals']
  for item in model['items'].values():
   if item.get('station_serial')==serial or item['id'] in self.detached:
    item.update(station_serial=serial,working=True,connected=True,power=True,input='HDMI')
  model['revision']+=1
 def test_all_nine_causes_require_local_repair_without_ping(self):
  t=self.tickets();baseline=copy.deepcopy(self.s)
  for kind,cause in live.PERIPHERAL_CAUSES:
   with self.subTest(kind=kind,cause=cause):
    self.c.workspace.state=copy.deepcopy(baseline);self.s=self.c.workspace.state;t.state['tickets']=[]
    with patch.object(live.random,'Random') as rng:
     rng.return_value.choice.side_effect=lambda choices:'peripherals' if 'peripherals' in choices else next((p for p in choices if p==('peripherals',kind+':'+cause)),choices[0])
     live.receive(t,'peripherals',client_serial='second',engine='apps')
    row=t.state['tickets'][0];self.assertEqual(row['stage'],'prepared')
    model=self.s['peripherals'];self.detached=[i['id'] for i in model['items'].values() if i['station_serial'] is None]
    self.assertFalse(hardware.evaluate(model,'second')[kind]['available'])
    self.assertEqual(row['impact']['work_status'],'blocked')
    with self.assertRaises(ValueError):t.workspace_action(row,'close',{})
    self.c.observe.assert_not_called()
    self.repair('second');t.workspace_action(row,'close',{})
    self.assertEqual(row['status'],'clos');self.c.observe.assert_not_called()
 def test_other_employee_account_incident_is_preserved(self):
  t=self.tickets();live.receive(t,'ad',client_serial='client')
  uid=self.s['directory_user_id'];before=copy.deepcopy(self.s['directory'])
  live.receive(t,'peripherals',client_serial='second',engine='apps')
  self.assertEqual(before,self.s['directory']);self.assertFalse(self.s['directory']['users'][uid]['enabled'])
  self.assertEqual(len(t.state['tickets']),2)
 def test_accessory_fault_does_not_disconnect_remote_session(self):
  t=self.tickets()
  self.s['client_workspaces']['second']['local']['remote_session']=True
  live.receive(t,'peripherals',client_serial='second')
  self.assertTrue(self.s['client_workspaces']['second']['local']['remote_session'])
 def test_no_free_pass_when_hardware_state_is_missing(self):
  t=self.tickets();live.receive(t,'peripherals',client_serial='second')
  self.s.pop('peripherals')
  self.assertEqual(live.checks(self.s,t.state['tickets'][0],self.now)[0]['status'],'inconnu')
 def test_shared_history_rejects_another_environment(self):
  t=self.tickets();live.receive(t,'peripherals',client_serial='second')
  self.s['peripherals']['environment_id']='foreign'
  self.assertEqual(live.checks(self.s,t.state['tickets'][0],self.now)[0]['status'],'inconnu')

 def test_broken_screen_is_replaced_via_actual_stock_operations(self):
  t=self.tickets()
  with patch.object(live.random,'Random') as rng:
   rng.return_value.choice.side_effect=lambda choices:'peripherals' if 'peripherals' in choices else next((p for p in choices if p==('peripherals','monitor:working')),choices[0])
   live.receive(t,'peripherals',client_serial='second')
  old=next(i for i in self.s['peripherals']['items'].values() if i['station_serial']=='second' and i['kind']=='monitor')
  hardware.operate(self.s,'second',dict(operation='add',kind='monitor',expected_revision=self.s['peripherals']['revision']),self.now)
  spare=next(i for i in self.s['peripherals']['items'].values() if i['station_serial'] is None and i['kind']=='monitor' and i['working'])
  hardware.operate(self.s,'second',dict(operation='attach',item_id=spare['id'],expected_revision=self.s['peripherals']['revision']),self.now)
  self.assertIsNone(self.s['peripherals']['items'][old['id']]['station_serial'])
  self.assertFalse(self.s['peripherals']['items'][old['id']]['working'])
  t.workspace_action(t.state['tickets'][0],'close',{});self.c.observe.assert_not_called()
  self.assertEqual(t.state['tickets'][0]['status'],'clos')
