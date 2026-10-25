"""Rasterize the project's own geometric icon without external dependencies."""
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]/'FusionSquish/resources/flatten'
POLYGONS = [([(3,7),(12,3),(18,8),(10,13)], (91,199,242)),
            ([(3,7),(10,13),(10,24),(3,18)], (35,114,163)),
            ([(10,13),(18,8),(18,18),(10,24)], (50,157,207)),
            ([(18,22),(26,16),(31,20),(23,27)], (241,176,63)),
            ([(18,22),(23,27),(23,30),(18,25)], (193,121,34)),
            ([(22,5),(26,9),(24,9),(24,13),(21,13),(21,9),(19,9)], (241,176,63))]


def inside(x,y,polygon):
    result = False
    for i,(a,b) in enumerate(polygon):
        c,d = polygon[i-1]
        if (b>y)!=(d>y) and x < (c-a)*(y-b)/(d-b)+a:
            result = not result
    return result


def chunk(tag,data):
    return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data))


for size in (16,32,64):
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            hits=[]
            for sy in range(4):
                for sx in range(4):
                    px,py=(x+(sx+.5)/4)*32/size,(y+(sy+.5)/4)*32/size
                    color=None
                    for polygon,rgb in POLYGONS:
                        if inside(px,py,polygon): color=rgb
                    if color: hits.append(color)
            rows.extend([round(sum(c[i] for c in hits)/len(hits)) for i in range(3)]+[round(255*len(hits)/16)] if hits else [0,0,0,0])
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    (ROOT/f'{size}x{size}.png').write_bytes(png)
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'+''.join(
    '<polygon points="'+ ' '.join(f'{x},{y}' for x,y in poly)+'" fill="rgb('+','.join(map(str,rgb))+')"/>' for poly,rgb in POLYGONS)+'</svg>'
(ROOT/'icon.svg').write_text(svg)
