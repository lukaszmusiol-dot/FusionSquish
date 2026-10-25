from solver import flatten

result = flatten([[0,0,0],[10,0,0],[10,5,0],[0,5,0]], [[0,1,2],[0,2,3]], 100)
assert result['stats']['max_edge_strain_percent'] < 0.1, result['stats']
print('OK: silnik SLIM, prostokąt 100 x 50 mm, błąd długości < 0.1%.')
