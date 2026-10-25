import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'FusionSquish/engine'))
from solver import flatten, prepare, weld_boundary_vertices


def l_patch(gap):
    vertices, faces = [], []
    for index, (x,y) in enumerate(((0,0),(1,0),(0,1))):
        offset = len(vertices)
        shift = gap * index
        vertices.extend([[x+shift,y,0],[x+1+shift,y,0],[x+1+shift,y+1,0],[x+shift,y+1,0]])
        faces.extend([[offset,offset+1,offset+2],[offset,offset+2,offset+3]])
    return vertices,faces


class BoundaryWeldTests(unittest.TestCase):
    def test_l_patch_with_numerical_seams(self):
        v,f = l_patch(1e-8)
        result = flatten(v,f)
        self.assertEqual(len(result['boundary']),8)
        self.assertEqual(result['stats']['triangles'],6)
        self.assertLess(result['stats']['max_edge_strain_percent'],.1)
        uv=np.array(result['uv_cm'])
        tri=np.array(result['faces'])
        a,b=uv[tri[:,1]]-uv[tri[:,0]],uv[tri[:,2]]-uv[tri[:,0]]
        self.assertAlmostEqual(float((a[:,0]*b[:,1]-a[:,1]*b[:,0]).sum()/2),3,places=4)

    def test_real_gap_is_not_closed(self):
        v,f=l_patch(.001)
        with self.assertRaisesRegex(ValueError,'jednego płata'):
            prepare(v,f)

    def test_existing_short_edges_are_not_collapsed(self):
        v=np.array([[0.,0,0],[1e-7,0,0],[0,1,0]])
        f=np.array([[0,1,2]],dtype=np.int32)
        vv,ff=weld_boundary_vertices(v,f)
        self.assertEqual(len(vv),3)
        self.assertEqual(len(set(ff[0])),3)

    def test_real_hole_still_reports_two_boundaries(self):
        from test_solver import grid
        v,f=grid(3,3)
        with self.assertRaisesRegex(ValueError,'2 obwodów'):
            prepare(v,f[:8]+f[10:])


if __name__=='__main__': unittest.main()
