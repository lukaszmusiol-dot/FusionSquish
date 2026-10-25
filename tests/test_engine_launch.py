"""Exercise the actual Fusion adapter's process launch without a running UI."""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class EngineLaunchTests(unittest.TestCase):
    def test_calculate_ignores_host_python_settings(self):
        # The fake adsk only replaces UI/event classes. calculate() and the
        # subprocess, JSON exchange, libigl import and SLIM solve are real.
        core = SimpleNamespace(CommandEventHandler=object, CommandCreatedEventHandler=object)
        adsk = SimpleNamespace(core=core, fusion=SimpleNamespace(), doEvents=lambda: None)
        modules = {'adsk': adsk, 'adsk.core': core, 'adsk.fusion': adsk.fusion}
        spec = importlib.util.spec_from_file_location('squish_launch_test', ROOT/'FusionSquish/FusionSquish.py')
        adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(adapter)
        progress = Mock(wasCancelled=False)
        interface = Mock()
        interface.createProgressDialog.return_value = progress
        fake_home = '/nonexistent-fusion-embedded-python'
        with patch.object(adapter, 'ui', return_value=interface), \
             patch.object(adapter, 'python_path', return_value=sys.executable), \
             patch.dict(os.environ, {'PYTHONHOME': fake_home, 'PYTHONPATH': fake_home}):
            result = adapter.calculate({'iterations': 100, 'meshes': [{
                'name': 'Regression', 'vertices': [[0,0,0],[10,0,0],[10,5,0],[0,5,0]],
                'faces': [[0,1,2],[0,2,3]]}]})
        self.assertEqual(result[0]['name'], 'Regression')
        self.assertLess(result[0]['stats']['max_edge_strain_percent'], .1)
        progress.hide.assert_called_once()


if __name__ == '__main__':
    unittest.main()
