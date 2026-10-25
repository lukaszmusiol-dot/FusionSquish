import sys
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

from test_face_selection import adapter, selection, triangle
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'FusionSquish/engine'))
from solver import flatten


class CombinedPatchTests(unittest.TestCase):
    def fixture(self):
        module, manager = adapter()
        body = object()
        # Native faces use their common source body; source body is not mutated.
        body = NS(name='Folded patch', convert=Mock())
        module.adsk.fusion.BRepConvertOptions = NS(ProceduralToNURBSConversion=0)
        a = NS(kind='face', nativeObject=None, body=body, assemblyContext=None, tempId=10)
        b = NS(kind='face', nativeObject=None, body=body, assemblyContext=None, tempId=20)
        copied_a, copied_b = NS(kind='face'), NS(kind='face')
        temp = body.convert.return_value
        temp.isTemporary = True
        manager.copy.side_effect = RuntimeError('3: invalid argument tempId')
        temp.faces.count = 6
        temp.findByTempId.side_effect = lambda key: {10:[copied_a],20:[copied_b]}[key]
        calc = temp.meshManager.createMeshCalculator.return_value
        # Two unit-square faces folded through 90 degrees; consistent shared edge.
        mesh = NS(triangleCount=4, nodeIndices=[0,1,2,0,2,3,1,4,5,1,5,2],
                  nodeCoordinates=[NS(x=x,y=y,z=z) for x,y,z in
                                   [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(1,0,1),(1,1,1)]])
        calc.calculate.return_value=mesh
        return module, manager, body, a, b, copied_a, copied_b

    def test_one_mesh_one_outline_no_shared_seam(self):
        module, manager, body, a, b, ca, cb = self.fixture()
        meshes=module.collect_combined_mesh(selection(a,b),11)
        self.assertEqual(len(meshes),1)
        body.convert.assert_called_once_with(0)
        manager.copy.assert_not_called()
        manager.deleteFaces.assert_called_once_with([ca,cb],False)
        mesh=meshes[0]
        result=flatten(mesh['vertices'],mesh['faces'],200)
        self.assertEqual(result['stats']['triangles'],4)
        self.assertEqual(len(result['boundary']),6)
        # The two shared-edge vertices have degree 3 in the triangulation,
        # but no shared edge is part of the output boundary.
        from collections import Counter
        counts=Counter(tuple(sorted((tri[i],tri[(i+1)%3]))) for tri in result['faces'] for i in range(3))
        loop=result['boundary']
        for i,a in enumerate(loop):
            self.assertEqual(counts[tuple(sorted((a,loop[(i+1)%len(loop)])))],1)
        self.assertLess(result['stats']['max_edge_strain_percent'],.1)
        # The UI's sketch builder creates only the six boundary segments.
        lines=Mock()
        lines.addByTwoPoints.side_effect=lambda a,b: NS(startSketchPoint=a,endSketchPoint=b)
        sketch=NS(name='',isComputeDeferred=False,isValid=True,attributes=Mock(),
                  sketchCurves=NS(sketchLines=lines))
        component=NS(sketches=Mock(),xYConstructionPlane=object())
        component.sketches.add.return_value=sketch
        module.adsk.core.Point3D=NS(create=lambda x,y,z: (x,y,z))
        module.make_sketch(component,dict(result,name='test'),0,False)
        self.assertEqual(lines.addByTwoPoints.call_count,6)

    def test_different_bodies_rejected_before_copy(self):
        module, manager, body, a, b, _, _=self.fixture()
        b.body=NS(name='other')
        with self.assertRaisesRegex(RuntimeError,'jednej bryły'):
            module.collect_combined_mesh(selection(a,b),11)
        manager.copy.assert_not_called()

    def test_different_occurrences_rejected(self):
        module, manager, body, a, b, _, _=self.fixture()
        b.assemblyContext=object()
        with self.assertRaisesRegex(RuntimeError,'wystąpieniu'):
            module.collect_combined_mesh(selection(a,b),11)
        manager.copy.assert_not_called()

    def test_missing_face_mapping_rejected(self):
        module, manager, body, a, b, _, _=self.fixture()
        body.convert.return_value.findByTempId.side_effect=lambda key: []
        with self.assertRaisesRegex(RuntimeError,'odnaleźć'):
            module.collect_combined_mesh(selection(a,b),11)
        manager.deleteFaces.assert_not_called()

    def test_single_mesh_supported_but_multiple_rejected(self):
        module, manager=adapter()
        mesh=NS(kind='mesh',nativeObject=None,name='Mesh',displayMesh=triangle())
        self.assertEqual(len(module.collect_combined_mesh(selection(mesh),11)),1)
        with self.assertRaisesRegex(RuntimeError,'jeden połączony'):
            module.collect_combined_mesh(selection(mesh,mesh),11)

    def test_failed_removal_does_not_mesh_whole_solid(self):
        module, manager, body, a, b, _, _=self.fixture()
        manager.deleteFaces.return_value=False
        with self.assertRaisesRegex(RuntimeError,'wydzielić'):
            module.collect_combined_mesh(selection(a,b),11)
        body.convert.return_value.meshManager.createMeshCalculator.assert_not_called()

    def test_split_converted_face_keeps_all_fragments(self):
        module, manager, body, a, b, ca, cb = self.fixture()
        extra = NS(kind='face')
        body.convert.return_value.findByTempId.side_effect = lambda key: {10:[ca,extra],20:[cb]}[key]
        module.collect_combined_mesh(selection(a,b),11)
        manager.deleteFaces.assert_called_once_with([ca,extra,cb],False)

    def test_non_temporary_body_never_modified(self):
        module, manager, body, a, b, _, _ = self.fixture()
        body.convert.return_value.isTemporary = False
        with self.assertRaisesRegex(RuntimeError,'tymczasowej'):
            module.collect_combined_mesh(selection(a,b),11)
        manager.deleteFaces.assert_not_called()

    def test_tessellation_alternatives_use_same_patch_and_bounded_tolerances(self):
        module, manager, body, a, b, _, _ = self.fixture()
        calc = body.convert.return_value.meshManager.createMeshCalculator.return_value
        original = calc.calculate.return_value
        calc.surfaceTolerance = .02
        alternate = triangle()
        calc.calculate.side_effect = [original, alternate, alternate]
        result = module.collect_combined_mesh(selection(a,b),11)
        self.assertEqual(len(result),1)
        self.assertEqual(len(result[0]['alternatives']),1)
        self.assertEqual(calc.calculate.call_count,3)
        self.assertEqual(calc.surfaceTolerance,.02)
        manager.deleteFaces.assert_called_once()

    def test_failed_optional_tessellation_keeps_primary(self):
        module, manager, body, a, b, _, _ = self.fixture()
        calc = body.convert.return_value.meshManager.createMeshCalculator.return_value
        original = calc.calculate.return_value
        calc.surfaceTolerance = .02
        calc.calculate.side_effect = [original, RuntimeError('mesh failure'), None]
        result=module.collect_combined_mesh(selection(a,b),11)
        self.assertNotIn('alternatives',result[0])
        self.assertEqual(len(result[0]['faces']),4)


if __name__=='__main__': unittest.main()
