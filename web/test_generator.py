import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from generator_app import Generator
class TestGenerator(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.g=Generator();self.g.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_catalogue_modes(self):
  self.assertEqual({x['mode'] for x in self.g.catalogue},{'atelier','depannage','mixte','reproduction'})
  self.assertEqual(len({x['id'] for x in self.g.catalogue}),len(self.g.catalogue))
 def test_invalid_selection(self):
  with self.assertRaises(ValueError):self.g.start({'mode':'atelier','scenario':'classic:pc_wrong_gateway'})
  with self.assertRaises(ValueError):self.g.start({'mode':'mixte','level':9})
 def test_download_allowlist(self):
  with self.assertRaises(ValueError):self.g.file('../secret','lab.pka')
  ident='a'*32;p=self.g.root/ident;p.mkdir();(p/'job.json').write_text(json.dumps(dict(id=ident,status='done',files=['lab.pka'],created='today')))
  with self.assertRaises(ValueError):self.g.file(ident,'../job.json')
 def test_interrupted_job(self):
  ident='a'*32;p=self.g.root/ident;p.mkdir();(p/'job.json').write_text(json.dumps(dict(id=ident,status='running',files=[],created='today')))
  self.assertEqual(self.g.jobs()[0]['status'],'interrupted')
if __name__=='__main__':unittest.main()
