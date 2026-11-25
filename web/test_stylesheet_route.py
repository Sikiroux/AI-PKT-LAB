"""Exercise the real HTTP handler method without launching PT or background workers."""
import ast
from pathlib import Path
import unittest
from urllib.parse import urlparse
from types import SimpleNamespace

ROOT=Path(__file__).parent
class StylesheetRouteTests(unittest.TestCase):
 def test_current_and_versioned_stylesheet_return_css(self):
  tree=ast.parse((ROOT/'tickets_app.py').read_text())
  handler=next(n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=='Handler')
  method=next(n for n in handler.body if isinstance(n,ast.FunctionDef) and n.name=='do_GET')
  module=ast.Module(body=[method],type_ignores=[]);scope={'diagnostic_mode':False,'ROOT':ROOT,'urlparse':urlparse,'workspace_routes':SimpleNamespace(get=lambda request:False)}
  exec(compile(ast.fix_missing_locations(module),'<real HTTP handler>','exec'),scope)
  for path in ['/workspace-design.css','/workspace-design.css?v=111']:
   sent=[];request=SimpleNamespace(path=path,allowed=lambda:True,send=lambda *args:sent.append(args))
   scope['do_GET'](request)
   self.assertEqual(sent[0][0],200);self.assertEqual(sent[0][2],'text/css')
   self.assertIn('.app-shell',sent[0][1]);self.assertIn('.intervention-compact',sent[0][1])
 def test_page_uses_canonical_stylesheet_url(self):
  self.assertIn('href="/workspace-design.css"',(ROOT/'tickets.html').read_text())
