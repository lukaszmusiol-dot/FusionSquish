import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'FusionSquish/engine'))
from solver import flatten, check_boundary


def grid(nx=8,ny=5,curved=False):
    vertices=[]
    for j in range(ny+1):
        for i in range(nx+1):
            t=i/nx*math.pi/2
            vertices.append([10*math.sin(t),j,10*math.cos(t)] if curved else [i,j,0])
    faces=[]
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i
            faces.extend([[a,a+1,a+nx+2],[a,a+nx+2,a+nx+1]])
    return vertices,faces


class SolverTests(unittest.TestCase):
    def test_plane_real_scale(self):
        v,f=grid()
        r=flatten(v,f)
        self.assertLess(r['stats']['max_edge_strain_percent'],0.1)
        self.assertLess(abs(r['stats']['area_change_percent']),0.1)

    def test_cylinder(self):
        v,f=grid(curved=True)
        r=flatten(v,f,200)
        self.assertLess(r['stats']['max_edge_strain_percent'],0.1)
        np.testing.assert_allclose(np.linalg.norm(np.array(r['uv_cm'])[r['edges'][0][0]]-np.array(r['uv_cm'])[r['edges'][0][1]]),
                                   np.linalg.norm(np.array(v)[0]-np.array(v)[1]),rtol=.001)

    def test_units_translation_and_scale(self):
        v,f=grid()
        r=flatten(np.array(v)*0.01+100,f)
        uv=np.array(r['uv_cm'])
        edges=np.array(r['edges'])
        lengths=np.linalg.norm(uv[edges[:,1]]-uv[edges[:,0]],axis=1)
        self.assertAlmostEqual(float(lengths.min()),.01,places=5)

    def test_stl_duplicate_vertices_and_winding(self):
        v,f=grid()
        vv=np.array(v)[np.array(f)].reshape(-1,3)
        ff=np.arange(len(vv)).reshape(-1,3)
        ff[::2]=ff[::2,::-1]
        r=flatten(vv,ff)
        self.assertLess(r['stats']['max_edge_strain_percent'],.1)

    def test_closed_rejected(self):
        with self.assertRaisesRegex(ValueError,'Zamknięta'):
            flatten([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],[[0,1,2],[0,3,1],[1,3,2],[0,2,3]])

    def test_hole_rejected(self):
        v,f=grid(3,3)
        f=f[:8]+f[10:]
        with self.assertRaisesRegex(ValueError,'otworów'):
            flatten(v,f)

    def test_disconnected_rejected(self):
        with self.assertRaisesRegex(ValueError,'jednego płata'):
            flatten([[0,0,0],[1,0,0],[0,1,0],[3,0,0],[4,0,0],[3,1,0]],[[0,1,2],[3,4,5]])

    def test_degenerate_rejected(self):
        with self.assertRaisesRegex(ValueError,'zdegenerowane'):
            flatten([[0,0,0],[1,0,0],[2,0,0]],[[0,1,2]])

    def test_nonmanifold_rejected(self):
        with self.assertRaisesRegex(ValueError,'non-manifold'):
            flatten([[0,0,0],[1,0,0],[0,1,0],[0,-1,0],[0,0,1]],[[0,1,2],[0,1,3],[0,1,4]])

    def test_crossing_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError,'przecina'):
            check_boundary(np.array([[0,0],[1,1],[0,1],[1,0]]),[0,1,2,3])

    def test_worker_protocol(self):
        v,f=grid()
        with tempfile.TemporaryDirectory() as tmp:
            inp,out=Path(tmp)/'in.json',Path(tmp)/'out.json'
            inp.write_text(json.dumps({'iterations':100,'meshes':[{'name':'Próba','vertices':v,'faces':f}]}))
            subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'FusionSquish/engine/solver.py'),str(inp),str(out)],check=True)
            result=json.loads(out.read_text())
            self.assertTrue(result['ok'])
            self.assertEqual(result['results'][0]['name'],'Próba')


if __name__=='__main__': unittest.main()
