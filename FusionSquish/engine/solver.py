"""Independent SLIM integration. Coordinates and returned UV are in Fusion cm."""
import json
import sys
from collections import defaultdict, deque

import igl
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

# Fusion cm: 0.00001 mm. Only coincident boundary samples are joined.
WELD_TOLERANCE_CM = 1e-6


def weld_boundary_vertices(v, f, tolerance=WELD_TOLERANCE_CM):
    """Join numerical seam duplicates; never fill holes or move interior nodes."""
    edges = np.sort(np.vstack((f[:, [0,1]], f[:, [1,2]], f[:, [2,0]])), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    boundary = np.unique(unique[counts == 1])
    if len(boundary) < 2:
        return v, f
    tree = cKDTree(v[boundary])
    parent = np.arange(len(v))
    incident = [set() for _ in v]
    members = [{i} for i in range(len(v))]
    for index, tri in enumerate(f):
        for node in tri:
            incident[node].add(index)
    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    # Never collapse an existing short edge or degenerate a triangle.
    existing = {tuple(edge) for edge in unique}
    for i, node in enumerate(boundary):
        nearby = tree.query_ball_point(v[node], tolerance)
        for j in nearby:
            if j <= i:
                continue
            other = boundary[j]
            a, b = root(node), root(other)
            if a == b or tuple(sorted((node, other))) in existing:
                continue
            if np.linalg.norm(v[a]-v[b]) > tolerance:
                continue
            if incident[a] & incident[b]:
                continue
            if any(np.linalg.norm(v[a]-v[x]) > tolerance for x in members[b]):
                continue
            parent[b] = a
            incident[a].update(incident[b])
            members[a].update(members[b])

    remap = np.array([root(i) for i in range(len(v))])
    f = remap[f]
    used, inverse = np.unique(f, return_inverse=True)
    return v[used], inverse.reshape(-1, 3).astype(np.int32)


def prepare(vertices, faces):
    v = np.asarray(vertices, dtype=float)
    raw = np.asarray(faces)
    if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
        raise ValueError('Nieprawidłowe współrzędne siatki.')
    if raw.ndim != 2 or raw.shape[1] != 3 or not len(raw):
        raise ValueError('Brak trójkątów.')
    if len(raw) > 30000:
        raise ValueError('Limit 30 000 trójkątów. Użyj Mesh > Modify > Reduce.')
    if not np.issubdtype(raw.dtype, np.integer) or raw.min() < 0 or raw.max() >= len(v):
        raise ValueError('Nieprawidłowe indeksy trójkątów.')
    # STL and display meshes may repeat identical vertices at normal seams.
    v, inverse = np.unique(v, axis=0, return_inverse=True)
    f = inverse[raw].astype(np.int32)
    used, inverse = np.unique(f, return_inverse=True)
    v, f = v[used], inverse.reshape(-1, 3).astype(np.int32)
    v, f = weld_boundary_vertices(v, f)
    # CAD tessellation can emit zero-area facets on collapsed parametric edges.
    # Remove only repeated-index triangles; other degeneracies remain errors.
    keep = (f[:,0] != f[:,1]) & (f[:,1] != f[:,2]) & (f[:,2] != f[:,0])
    f = f[keep]
    if not len(f):
        raise ValueError('Siatka zawiera wyłącznie zdegenerowane trójkąty.')
    used, inverse = np.unique(f, return_inverse=True)
    v, f = v[used], inverse.reshape(-1,3).astype(np.int32)
    extent = np.linalg.norm(np.ptp(v, axis=0))
    if extent <= 1e-9:
        raise ValueError('Siatka jest zbyt mała lub pusta.')
    v0 = (v - v.mean(axis=0)) / extent
    areas = np.linalg.norm(np.cross(v0[f[:, 1]]-v0[f[:, 0]], v0[f[:, 2]]-v0[f[:, 0]]), axis=1)
    if np.any(areas < 1e-14):
        raise ValueError('Siatka zawiera zerowe lub zdegenerowane trójkąty. Napraw siatkę.')
    if len(np.unique(np.sort(f, axis=1), axis=0)) != len(f):
        raise ValueError('Siatka zawiera powielone trójkąty.')
    edge_faces = defaultdict(list)
    links = defaultdict(list)
    for ti, tri in enumerate(f):
        a, b, c = map(int, tri)
        for x, y in ((a, b), (b, c), (c, a)):
            edge_faces[tuple(sorted((x, y)))].append((ti, x < y))
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            links[x].append((y, z))
    if any(len(x) > 2 for x in edge_faces.values()):
        raise ValueError('Siatka non-manifold: ponad dwie ściany na krawędzi.')
    adjacent = defaultdict(list)
    boundary_adj = defaultdict(list)
    for (a, b), refs in edge_faces.items():
        if len(refs) == 1:
            boundary_adj[a].append(b)
            boundary_adj[b].append(a)
        else:
            (i, di), (j, dj) = refs
            adjacent[i].append((j, di == dj))
            adjacent[j].append((i, di == dj))
    if not boundary_adj:
        raise ValueError('Zamknięta siatka. Wytnij otwarty płat i dodaj szew przed rozprostowaniem.')
    if any(len(x) != 2 for x in boundary_adj.values()):
        raise ValueError('Rozgałęziony brzeg. Wydziel jeden poprawny płat siatki.')
    orientation = {0: False}
    queue = deque([0])
    while queue:
        i = queue.popleft()
        for j, flip in adjacent[i]:
            wanted = orientation[i] ^ flip
            if j in orientation and orientation[j] != wanted:
                raise ValueError('Powierzchnia nieorientowalna.')
            if j not in orientation:
                orientation[j] = wanted
                queue.append(j)
    if len(orientation) != len(f):
        raise ValueError('Wybrane powierzchnie nie tworzą jednego płata połączonego krawędziami. Zaznacz także brakujące powierzchnie pomiędzy nimi.')
    for i, flip in orientation.items():
        if flip:
            f[i] = f[i, [0, 2, 1]]
    for vertex, pairs in links.items():
        graph = defaultdict(set)
        for a, b in pairs:
            graph[a].add(b)
            graph[b].add(a)
        seen, todo = set(), [next(iter(graph))]
        while todo:
            n = todo.pop()
            if n not in seen:
                seen.add(n)
                todo.extend(graph[n] - seen)
        if len(seen) != len(graph):
            raise ValueError('Siatka non-manifold w wierzchołku.')
    loop = [next(iter(boundary_adj))]
    prev, cur = None, loop[0]
    while True:
        nxt = next(n for n in boundary_adj[cur] if n != prev)
        if nxt == loop[0]:
            break
        loop.append(nxt)
        prev, cur = cur, nxt
    if len(loop) != len(boundary_adj) or len(v)-len(edge_faces)+len(f) != 1:
        remaining = set(boundary_adj)
        boundaries = 0
        while remaining:
            boundaries += 1
            todo = [next(iter(remaining))]
            while todo:
                node = todo.pop()
                if node in remaining:
                    remaining.remove(node)
                    todo.extend(boundary_adj[node])
        euler = len(v)-len(edge_faces)+len(f)
        handles = (2-boundaries-euler)//2
        raise ValueError(
            'Wspólny płat ma {} obwodów brzegowych i {} uchwytów topologicznych. '
            'Wymagany jest jeden obwód, bez otworów. '
            'Dwa obwody mogą oznaczać otwór albo pełny pas wokół modelu (np. walec). '
            'Dla pasa potrzebne jest cięcie wzdłuż; dla otworów trzeba ustalić sposób ich obsługi. '
            'Nie utworzono DXF i nie zmieniono modelu.'.format(boundaries, handles))
    if len(loop) > 3000:
        raise ValueError('Kontur ma ponad 3000 odcinków. Zredukuj siatkę.')
    return v, v0, f, extent, np.array(list(edge_faces), dtype=np.int32)


def double_area(uv, f):
    a = uv[f[:, 1]] - uv[f[:, 0]]
    b = uv[f[:, 2]] - uv[f[:, 0]]
    return a[:, 0]*b[:, 1] - a[:, 1]*b[:, 0]


def check_boundary(uv, loop):
    # A positive disk triangulation and simple boundary give a globally valid map.
    p = uv[loop]
    q = np.roll(p, -1, axis=0)
    def cross(a, b):
        return a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
    for i in range(len(p)):
        js = np.arange(i+2, len(p))
        if i == 0:
            js = js[js != len(p)-1]
        if not len(js):
            continue
        a, b, c, d = p[i], q[i], p[js], q[js]
        o1, o2 = cross(b-a, c-a), cross(b-a, d-a)
        o3, o4 = cross(d-c, a-c), cross(d-c, b-c)
        bbox = np.all(np.maximum(np.minimum(a,b), np.minimum(c,d)) <=
                      np.minimum(np.maximum(a,b), np.maximum(c,d))+1e-12, axis=1)
        if np.any((o1*o2 <= 1e-24) & (o3*o4 <= 1e-24) & bbox):
            raise ValueError('Kontur rozprostowania przecina lub dotyka sam siebie. Podziel płat.')


def flatten(vertices, faces, iterations=100):
    if not isinstance(iterations, int) or not 1 <= iterations <= 1000:
        raise ValueError('Liczba iteracji musi wynosić 1–1000.')
    v, vn, f, scale, edges = prepare(vertices, faces)
    boundary = np.asarray(igl.boundary_loop(f), dtype=np.int64)
    circle = igl.map_vertices_to_circle(vn, boundary)
    uv = igl.harmonic(vn, f.astype(np.int64), boundary, circle, 1)
    if not np.isfinite(uv).all() or np.any(double_area(uv, f) <= 1e-14):
        # Positive uniform weights provide a safer initialization on obtuse meshes.
        row = np.concatenate([edges[:, 0], edges[:, 1]])
        col = np.concatenate([edges[:, 1], edges[:, 0]])
        adj = coo_matrix((np.ones(len(row)), (row, col)), shape=(len(v), len(v))).tocsr()
        lap = diags(np.asarray(adj.sum(axis=1)).ravel())-adj
        inner = np.setdiff1d(np.arange(len(v)), boundary)
        uv = np.zeros((len(v), 2))
        uv[boundary] = circle
        if len(inner):
            uv[inner] = spsolve(lap[inner][:, inner], -lap[inner][:, boundary] @ circle)
    if not np.isfinite(uv).all() or np.any(double_area(uv, f) <= 1e-14):
        raise ValueError('Nie udało się zainicjalizować mapowania. Popraw triangulację lub podziel płat.')
    area3 = np.linalg.norm(np.cross(vn[f[:,1]]-vn[f[:,0]], vn[f[:,2]]-vn[f[:,0]]), axis=1).sum()/2
    uv *= np.sqrt(area3/(double_area(uv, f).sum()/2))
    data = igl.slim_precompute(vn, f, uv, igl.MappingEnergyType.SYMMETRIC_DIRICHLET,
                              np.empty(0, dtype=np.int32), np.empty((0, 2)))
    check_boundary(uv, boundary)
    accepted = 0
    stopped_for_overlap = False
    for _ in range(iterations):
        candidate = np.asarray(igl.slim_solve(data, iter_num=1)).copy()
        if not np.isfinite(candidate).all() or np.any(double_area(candidate, f) <= 1e-14):
            raise ValueError('Niepoprawny wynik: odwrócone lub zerowe trójkąty.')
        try:
            check_boundary(candidate, boundary)
        except ValueError:
            # SLIM is locally injective, but the free boundary can overlap.
            # Keep the last globally valid iterate, never the crossing result.
            stopped_for_overlap = True
            break
        uv = candidate
        accepted += 1
    if not accepted:
        raise ValueError('Pierwsza iteracja powoduje przecięcie konturu. Podziel płat lub zmień triangulację.')
    uv *= scale
    uv -= uv.min(axis=0)
    lengths3 = np.linalg.norm(v[edges[:,1]]-v[edges[:,0]], axis=1)
    lengths2 = np.linalg.norm(uv[edges[:,1]]-uv[edges[:,0]], axis=1)
    strain = lengths2/lengths3 - 1
    stats = {'max_edge_strain_percent': float(np.max(np.abs(strain))*100),
             'rms_edge_strain_percent': float(np.sqrt(np.mean(strain**2))*100),
             'area_change_percent': float((double_area(uv, f).sum()/2/(area3*scale**2)-1)*100),
             'triangles': len(f), 'boundary_segments': len(boundary), 'iterations': accepted,
             'requested_iterations': iterations, 'stopped_before_overlap': stopped_for_overlap,
             'removed_collapsed_triangles': len(faces)-len(f),
             'boundary_weld_tolerance_cm': WELD_TOLERANCE_CM}
    return {'uv_cm': uv.tolist(), 'faces': f.tolist(), 'boundary': boundary.tolist(),
            'edges': edges.tolist(), 'stats': stats}


def main():
    try:
        with open(sys.argv[1], encoding='utf-8') as stream:
            request = json.load(stream)
        results = []
        for item in request['meshes']:
            try:
                attempts = [item] + item.get('alternatives', [])
                last_error = None
                for index, candidate in enumerate(attempts):
                    try:
                        result = flatten(candidate['vertices'], candidate['faces'], request['iterations'])
                        result['stats']['mesh_attempt'] = index+1
                        results.append(dict(name=item['name'], **result))
                        break
                    except ValueError as error:
                        last_error = error
                else:
                    raise last_error
            except Exception as error:
                raise ValueError('{}: {}'.format(item['name'], error)) from error
        response = {'ok': True, 'results': results}
    except Exception as error:
        response = {'ok': False, 'error': str(error)}
    with open(sys.argv[2], 'w', encoding='utf-8') as stream:
        json.dump(response, stream, ensure_ascii=False, allow_nan=False)
    return 0 if response['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
