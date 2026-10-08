import copy
import unittest
import sim_inventory as stock
import company_registry
from test_files_integration import FilesIntegrationTests

class InventoryTests(unittest.TestCase):
    setUp=FilesIntegrationTests.setUp
    def setup_stock(self):
        self.c.workspace.save()
        self.employee=next(iter(self.s['company_registry']['people']))
    def op(self,operation,**kw):
        return self.c.inventory('operation',dict(operation=operation,item_id='reserve-laptop',expected_revision=self.s['inventory']['revision'],**kw))
    def test_lifecycle_persists_identity_and_never_changes_network(self):
        self.setup_stock();devices=copy.deepcopy(self.s['devices']); serial=self.s['inventory']['items']['reserve-laptop']['serial']
        self.op('prepare');self.op('assign',employee_id=self.employee)
        self.assertEqual(self.s['inventory']['items']['reserve-laptop']['employee_id'],self.employee)
        self.op('return');item=self.s['inventory']['items']['reserve-laptop']
        self.assertEqual(item['serial'],serial);self.assertFalse(item['prepared']);self.assertIsNone(item['employee_id'])
        self.assertEqual(devices,self.s['devices']);self.assertEqual(len(self.s['inventory']['history']),3)
    def test_unprepared_assignment_refused_without_mutation(self):
        self.setup_stock();before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.op('assign',employee_id=self.employee)
        self.assertEqual(before,self.s)
    def test_unknown_employee_and_stale_revision_refused(self):
        self.setup_stock();self.op('prepare');before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.op('assign',employee_id='foreign')
        with self.assertRaises(ValueError):stock.operate(self.s,dict(operation='return',item_id='reserve-laptop',expected_revision=0),1)
        self.assertEqual(before,self.s)
    def test_initial_stock_seed_reproducible_and_ensure_idempotent(self):
        self.setup_stock();fresh=copy.deepcopy(self.s);fresh.pop('inventory');stock.ensure(fresh)
        self.assertEqual(fresh['inventory'],self.s['inventory']);self.assertFalse(stock.ensure(fresh))
    def test_state_is_read_only_after_initialization(self):
        self.setup_stock();before=copy.deepcopy(self.s);self.c.inventory('state',{})
        self.assertEqual(before,self.s)
    def test_routes_refuse_foreign_environment_and_client_scope(self):
        self.setup_stock()
        from unittest.mock import Mock
        from workspace_routes import WorkspaceRoutes
        handler=Mock();handler.path='/workspace/inventory/state'
        routes=WorkspaceRoutes(self.c,'token')
        with self.assertRaises(ValueError):routes.post(handler,{'environment_id':'foreign'})
        with self.assertRaises(ValueError):routes.post(handler,{'environment_id':'env','client_serial':self.s['devices']['client']['serial']})
        handler.send.assert_not_called()
    def test_restoration_keeps_assignment(self):
        self.setup_stock();self.op('prepare');self.op('assign',employee_id=self.employee)
        from workspace_model import Workspace
        restored=Workspace(self.c.workspace.path)
        self.assertEqual(restored.state['inventory'],self.s['inventory'])

del FilesIntegrationTests
