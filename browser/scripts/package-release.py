from pathlib import Path
import hashlib,json,shutil,sys,zipfile
lab=Path(__file__).resolve().parents[1];root=lab.parent;build=lab/'build'/sys.argv[1]
assert build.resolve().is_relative_to((lab/'build').resolve())
assert '_oga_state' not in (build/'cdogs.js').read_text()
shutil.copy2(root/'COPYING',build/'COPYING.txt')
shutil.copy2(lab/'RELEASE-README.md',build/'README.txt')
shutil.copy2(lab/'notices.txt',build/'notices.txt')
items=[p for p in root.rglob('*') if p.is_file() and not set(p.relative_to(root).parts)&{'.git','node_modules','__pycache__'} and not p.is_relative_to(lab/'build') and not p.is_relative_to(lab/'emsdk')]
manifest=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(items)]
with zipfile.ZipFile(build/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(items):z.write(p,p.relative_to(root).as_posix())
 z.writestr('SOURCE-MANIFEST.json',json.dumps(manifest,indent=2))
names=['index.html','cdogs.js','cdogs.wasm.bin','cdogs.data.bin','bridge.js','input.js','persistence.js','music.js','music-manifest.js','COPYING.txt','README.txt','notices.txt','source.zip']+[x['url'] for x in json.loads((build/'assets-manifest.json').read_text()) if x.get('deferred')]
(build/'release-manifest.json').write_text(json.dumps({'files':[{'path':n,'bytes':(build/n).stat().st_size,'sha256':hashlib.sha256((build/n).read_bytes()).hexdigest()} for n in names]},indent=2))
print('Packaged',len(names),'runtime/source files')
