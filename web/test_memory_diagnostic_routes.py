import os
import ast
import io
import json
from pathlib import Path
import secrets
from types import SimpleNamespace
import unittest
from urllib.parse import urlparse
ROOT=Path(__file__).parent
class MemoryRoutesTests(unittest.TestCase):
 def setUp(self):
  tree=ast.parse((ROOT/'tickets_app.py').read_text());handler=next(n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=='Handler')
  methods=[n for n in handler.body if isinstance(n,ast.FunctionDef) and n.name in ('do_GET','do_POST')]
  self.scope={'os':os,'memory_suite':SimpleNamespace(snapshot=lambda:{'running':False,'runs':[]},start=lambda:{'running':True},stop=lambda:{'running':False}),'ROOT':ROOT,'diagnostic_mode':True,'token':'test-token','secrets':secrets,'json':json,'urlparse':urlparse,'bridge':SimpleNamespace(is_connected=True),'memory_test':SimpleNamespace(snapshot=lambda:{'running':False},start=lambda mode:{'mode':mode},stop=lambda:{'running':False})}
  exec(compile(ast.fix_missing_locations(ast.Module(body=methods,type_ignores=[])),'<HTTP handlers>','exec'),self.scope)
 def request(self,method,path,body=None,token='test-token'):
  data=json.dumps(body or {}).encode();sent=[]
  req=SimpleNamespace(path=path,allowed=lambda:True,headers={'X-Diagnostic-Token':token,'Content-Length':str(len(data))},rfile=io.BytesIO(data),send=lambda *args:sent.append(args))
  self.scope['do_'+method](req);return sent[0]
 def test_root_serves_diagnostic_with_real_token(self):
  status,html,mime=self.request('GET','/');self.assertEqual(status,200);self.assertIn('test-token',html);self.assertNotIn('__UI_TOKEN__',html);self.assertIn('X-Diagnostic-Token',html)
 def test_state_and_start_are_local_only(self):
  self.assertEqual(self.request('GET','/memory-diagnostic')[1]['connected'],True)
  self.assertEqual(self.request('POST','/memory-diagnostic/start',{'mode':'inventory'})[1]['mode'],'inventory')
  self.assertEqual(self.request('POST','/memory-diagnostic/start',{},token='bad')[0],403)
 def test_mutations_blocked_before_workspace_dispatch(self):
  for path in ['/workspace/refresh','/new','/session-control','/action','/messaging']:
   result=self.request('POST',path);self.assertEqual(result[0],400);self.assertIn('suspendues',result[1]['error'])

 def test_suite_routes_and_token(self):
  self.assertTrue(self.request('POST','/memory-suite/start')[1]['running'])
  self.assertEqual(self.request('POST','/memory-suite/start',token='bad')[0],403)
  self.assertEqual(self.request('GET','/memory-suite')[1]['runs'],[])
  self.assertFalse(self.request('GET','/memory-suite/report')[1]['running'])
