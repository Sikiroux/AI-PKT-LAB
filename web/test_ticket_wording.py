import unittest
import ticket_wording as w

class WordingTests(unittest.TestCase):
 def test_replay_and_identity(self):
  a=w.compose('seed','printing','Mina','Entreprise','PC-MINA','SN-01')
  self.assertEqual(a,w.compose('seed','printing','Mina','Entreprise','PC-MINA','SN-01'))
  for value in ('Mina','Entreprise','PC-MINA','SN-01'):self.assertIn(value,a['description'])
  self.assertEqual(a['request_context']['reported_scope'],'one_user')
 def test_each_family_varies_without_secret_cause(self):
  for family,variants in w.CATALOGUE.items():
   with self.subTest(family=family):
    outputs=[w.compose(seed,family,'Mina','Entreprise','PC-01','SERIAL') for seed in range(100)]
    self.assertEqual({x['title'] for x in outputs},{v[0] for v in variants})
    self.assertEqual({x['request_context']['urgency'] for x in outputs},{v[0] for v in w.URGENCIES})
    for x in outputs:
     self.assertNotIn('cause',x['request_context']);self.assertNotIn('password',x['description'])
     self.assertEqual(x['severity'],next(u[2] for u in w.URGENCIES if u[0]==x['request_context']['urgency']))
 def test_unknown_family_is_rejected(self):
  with self.assertRaises(ValueError):w.compose('seed','unreal','x','x','x','x')
