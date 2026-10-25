import html
import json
import math
from pathlib import Path
import re
import getpass
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def stl(name, vertices, faces):
    rows=['solid '+name]
    for tri in faces:
        rows.extend(['facet normal 0 0 0','outer loop'])
        rows.extend('vertex '+' '.join(f'{c:.10g}' for c in vertices[i]) for i in tri)
        rows.extend(['endloop','endfacet'])
    rows.append('endsolid '+name)
    (ROOT/'examples'/f'{name}.stl').write_text('\n'.join(rows)+'\n')

stl('prostokat_100x50_mm', [[0,0,0],[100,0,0],[100,50,0],[0,50,0]], [[0,1,2],[0,2,3]])
v=[]
f=[]
for j in range(6):
    for i in range(25):
        t=i/24*math.pi/2
        v.append([100*math.sin(t),j*10,100*math.cos(t)])
for j in range(5):
    for i in range(24):
        a=j*25+i
        f.extend([[a,a+1,a+26],[a,a+26,a+25]])
stl('walec_cwiartka_R100_H50_mm',v,f)

def inline(text):
    text=html.escape(text)
    text=re.sub(r'(https://[^\s<]+)',r'<a href="\1">\1</a>',text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text)
    return re.sub(r'`(.+?)`',r'<code>\1</code>',text)

body=[]
list_type=None
for line in (ROOT/'INSTRUKCJA_PL.md').read_text().splitlines():
    match=re.match(r'^(\d+\. |\- )(.*)',line)
    kind=('ol' if match.group(1)[0].isdigit() else 'ul') if match else None
    if list_type != kind:
        if list_type: body.append(f'</{list_type}>')
        if kind: body.append(f'<{kind}>')
        list_type=kind
    if match: body.append('<li>'+inline(match.group(2))+'</li>')
    elif line.startswith('## '): body.append('<h2>'+inline(line[3:])+'</h2>')
    elif line.startswith('# '): body.append('<h1>'+inline(line[2:])+'</h1>')
    elif line: body.append('<p>'+inline(line)+'</p>')
if list_type: body.append(f'</{list_type}>')
page='''<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fusion Squish — instrukcja</title><style>
body{font:17px/1.65 system-ui,sans-serif;color:#183044;background:#eef3f7;margin:0}main{max-width:960px;margin:35px auto;background:white;padding:45px;border-radius:18px}h1{font-size:34px;line-height:1.2}h2{margin-top:42px;border-top:1px solid #dbe5eb;padding-top:25px;color:#13628a}li{margin:12px 0}a{color:#13628a;overflow-wrap:anywhere}code{background:#eef3f7;padding:3px 5px;border-radius:4px}strong{color:#113c57}.icon{width:80px;float:right}@media(max-width:650px){main{margin:0;padding:22px}h1{font-size:27px}}@media print{body{background:white}main{margin:0;padding:0}h2{break-after:avoid}li{break-inside:avoid}a{color:inherit}}
</style><main><img class="icon" src="FusionSquish/resources/flatten/icon.svg" alt="Ikona dodatku">'''+ '\n'.join(body)+'</main></html>'
(ROOT/'INSTRUKCJA_PL.html').write_text(page)
version=json.loads((ROOT/'FusionSquish/FusionSquish.manifest').read_text())['version']
(ROOT/'dist').mkdir(exist_ok=True)
archive=ROOT/'dist'/f'FusionSquish-{version}.zip'
source_archive=ROOT/'dist'/'FusionSquish-GitHub-source.zip'
excluded={'.engine','.venv','__pycache__','.vscode','.git','.idea','.diagnostics'}
allowed={'.py','.manifest','.txt','.command','.cmd','.png','.svg','.stl'}
paths=[]
for folder in ('FusionSquish','examples','tests','tools'):
    for path in sorted((ROOT/folder).rglob('*')):
        if (path.is_file() and not any(part in excluded for part in path.relative_to(ROOT).parts)
                and path.suffix in allowed and path.name!='config.json'):
            paths.append(path)
for name in ('INSTRUKCJA_PL.html','INSTRUKCJA_PL.md','README.md','LICENSE','THIRD_PARTY.md','START_TUTAJ.md','GITHUB_PL.md','RELEASE_NOTES.md','.gitignore'):
    paths.append(ROOT/name)
# Fail before producing a new release if personal paths leak into text sources.
account=getpass.getuser()
for path in paths:
    if path.suffix == '.png':
        continue
    content=path.read_text(encoding='utf-8')
    personal=(str(Path.home()) in content or
              (len(account)>=4 and account.lower() in content.lower()))
    absolute_home=re.search(r'/(?:Users|home)/[^/\s]+/|[A-Za-z]:\\Users\\[^\\\s]+',content)
    if personal or absolute_home:
        raise RuntimeError('Personal path/account found in publication file: '+str(path.relative_to(ROOT)))
for output in (archive,source_archive):
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as package:
        for path in paths:
            package.write(path,path.relative_to(ROOT))
    print(output.name)
