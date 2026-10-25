import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'FusionSquish/engine'))
import solver

V=[[0,0,0],[10,0,0],[10,5,0],[0,5,0]]
F=[[0,1,2],[0,2,3]]


class SolverRecoveryTests(unittest.TestCase):
    def test_collapsed_cad_facets_removed_without_changing_outline(self):
        result=solver.flatten(V,F+[[0,0,1],[2,3,3]],100)
        self.assertEqual(result['stats']['removed_collapsed_triangles'],2)
        self.assertEqual(len(result['boundary']),4)
        self.assertLess(result['stats']['max_edge_strain_percent'],.1)

    def test_all_collapsed_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'wyłącznie zdegenerowane'):
            solver.flatten(V,[[0,0,1]])

    def test_last_safe_iterate_retained_and_reported(self):
        check=solver.check_boundary
        calls=0
        def crossing_after_one(uv,boundary):
            nonlocal calls
            calls+=1
            if calls==3:
                raise ValueError('Crossed boundary')
            return check(uv,boundary)
        with patch.object(solver,'check_boundary',side_effect=crossing_after_one):
            result=solver.flatten(V,F,100)
        self.assertEqual(result['stats']['iterations'],1)
        self.assertEqual(result['stats']['requested_iterations'],100)
        self.assertTrue(result['stats']['stopped_before_overlap'])
        check(__import__('numpy').array(result['uv_cm']),result['boundary'])

    def test_no_acceptable_iteration_rejected(self):
        with patch.object(solver,'check_boundary',side_effect=[None,ValueError('Crossed boundary')]):
            with self.assertRaisesRegex(ValueError,'Pierwsza iteracja'):
                solver.flatten(V,F)

    def test_worker_uses_alternative_only_after_primary_failure(self):
        item={'name':'Recovery','vertices':V,'faces':[[0,1,2]],'alternatives':[{'vertices':V,'faces':F}]}
        # First candidate is a closed tetrahedron, so the worker must retry.
        item['vertices']=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]]
        item['faces']=[[0,1,2],[0,3,1],[1,3,2],[0,2,3]]
        with tempfile.TemporaryDirectory() as folder:
            src,dst=Path(folder)/'in.json',Path(folder)/'out.json'
            src.write_text(json.dumps({'iterations':100,'meshes':[item]}))
            subprocess.run([sys.executable,str(Path(solver.__file__)),str(src),str(dst)],check=True)
            response=json.loads(dst.read_text())
        self.assertEqual(len(response['results']),1)
        result=response['results'][0]
        self.assertEqual(result['stats']['mesh_attempt'],2)
        self.assertEqual(len(result['boundary']),4)


if __name__=='__main__': unittest.main()
