import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def adapter():
    core = NS(CommandEventHandler=object, CommandCreatedEventHandler=object)
    manager = Mock()
    fusion = NS(BRepFace=NS(cast=lambda x: x if x.kind == 'face' else None),
                MeshBody=NS(cast=lambda x: x if x.kind == 'mesh' else None),
                TemporaryBRepManager=NS(get=lambda: manager))
    adsk = NS(core=core, fusion=fusion)
    spec = importlib.util.spec_from_file_location('face_adapter', ROOT/'FusionSquish/FusionSquish.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'adsk': adsk, 'adsk.core': core, 'adsk.fusion': fusion}):
        spec.loader.exec_module(module)
    return module, manager


def selection(*entities):
    return NS(selectionCount=len(entities), selection=lambda i: NS(entity=entities[i]))


def triangle():
    return NS(triangleCount=1, nodeIndices=[0,1,2], nodeCoordinates=[NS(x=0,y=0,z=0),NS(x=2,y=0,z=0),NS(x=0,y=1,z=0)])


class FaceSelectionTests(unittest.TestCase):
    def test_copies_only_selected_face_and_tessellates_copy(self):
        module, manager = adapter()
        native = object()
        face = NS(kind='face', nativeObject=native, body=NS(name='Model'))
        calc = manager.copy.return_value.meshManager.createMeshCalculator.return_value
        calc.calculate.return_value = triangle()
        result = module.collect_meshes(selection(face), 11)
        manager.copy.assert_called_once_with(native)
        calc.setQuality.assert_called_once_with(11)
        self.assertEqual(result[0]['vertices'], [[0,0,0],[2,0,0],[0,1,0]])
        self.assertEqual(result[0]['faces'], [[0,1,2]])
        self.assertIn('powierzchnia 1', result[0]['name'])

    def test_existing_mesh_and_multiple_faces_are_separate(self):
        module, manager = adapter()
        calc = manager.copy.return_value.meshManager.createMeshCalculator.return_value
        calc.calculate.return_value = triangle()
        face = NS(kind='face', nativeObject=None, body=NS(name='Model'))
        body = NS(kind='mesh', nativeObject=None, name='Mesh', displayMesh=triangle())
        results = module.collect_meshes(selection(face, body, face), 8)
        self.assertEqual(len(results), 3)
        self.assertEqual(manager.copy.call_count, 2)
        self.assertEqual(results[1]['name'], 'Mesh')
        self.assertNotEqual(results[0]['name'], results[2]['name'])

    def test_failed_copy_is_reported(self):
        module, manager = adapter()
        manager.copy.return_value = None
        face = NS(kind='face', nativeObject=None, body=NS(name='Model'))
        with self.assertRaisesRegex(RuntimeError, 'skopiować'):
            module.collect_meshes(selection(face), 11)

    def test_triangle_limit_checked_before_coordinates(self):
        module, manager = adapter()
        body = NS(kind='mesh', nativeObject=None, name='Huge', displayMesh=NS(triangleCount=30001))
        with self.assertRaisesRegex(RuntimeError, '30 000'):
            module.collect_meshes(selection(body), 11)


if __name__ == '__main__': unittest.main()
