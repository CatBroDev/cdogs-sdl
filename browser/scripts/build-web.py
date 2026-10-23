"""C-Dogs browser candidate. Keep the pinned source intact; apply Web-only overrides."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, sys, time

lab=Path(__file__).resolve().parents[1]
src=lab.parent
sdk=Path(os.environ.get('CDOGS_EMSDK',str(lab/'emsdk')))
name=sys.argv[1] if len(sys.argv)>1 else 'web-01'
assert re.fullmatch(r'[a-z0-9-]+',name)
out=lab/'build'/name
out.mkdir(parents=True,exist_ok=False)
(out/'tmp').mkdir()
def read(rel): return (src/rel).read_text(encoding='utf-8')
def override(rel,text):
 p=out/'overrides'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8');return p
def change(text,old,new):
 assert old in text, old[:100]
 return text.replace(old,new)
def cmake_sources(folder,var):
 section=re.search(r'set\('+var+r'\s+(.*?)\)',(folder/'CMakeLists.txt').read_text(),re.S).group(1)
 return [folder/p for p in re.findall(r'[\w/.-]+\.c\b',section)]
files=cmake_sources(src/'src','CDOGS_SDL_SOURCES')+cmake_sources(src/'src/cdogs','CDOGS_SOURCES')
files=[p for p in files if p.name!='map_wolf.c']
for rel in ['src/json','src/cdogs/c_hashmap','src/cdogs/SDL_JoystickButtonNames','src/cdogs/yajl','src/cdogs/enet']:
 files+=list((src/rel).glob('*.c'))
files += [src/'src/proto/msg.pb.c']+list((src/'src/proto/nanopb').glob('*.c'))
patches={}
main=read('src/cdogs.c')
main=change(main,'\tLoopRunner l = LoopRunnerNew();','\tstatic LoopRunner l;\n\tl = LoopRunnerNew();')
begin=main.index('#ifdef __EMSCRIPTEN__\n\t// initialize IDBFS')
end=main.index('\n\t// Set config options',begin)
main=main[:begin]+'''// IDBFS has completed its initial read in preRun before main is called.
\tSetupConfigDir();
\tgConfig = ConfigLoad(GetConfigFilePath(CONFIG_FILE));
'''+main[end:]
main=change(main,'#ifndef __EMSCRIPTEN__\n\tAutosaveLoad(&gAutosave, GetConfigFilePath(AUTOSAVE_FILE));\n#endif','\tAutosaveLoad(&gAutosave, GetConfigFilePath(AUTOSAVE_FILE));')
main=change(main,'#ifndef __EMSCRIPTEN__\n\tLoadingScreenDraw(&gLoadingScreen, "Loading player templates...", 0.75f);\n\tPlayerTemplatesLoad(&gPlayerTemplates, &gCharacterClasses);\n#endif','\tLoadingScreenDraw(&gLoadingScreen, "Loading player templates...", 0.75f);\n\tPlayerTemplatesLoad(&gPlayerTemplates, &gCharacterClasses);')
main=change(main,'\tSoundInitialize(&gSoundDevice, "sounds");','\tSoundInitialize(&gSoundDevice, "sounds");\n\textern void oga_audio_install(void); oga_audio_install();')
main=change(main,'\t// Set config options that are only set via command line','\tConfigSetInt(&gConfig, "Graphics.WindowWidth", 640);\n\tConfigSetInt(&gConfig, "Graphics.WindowHeight", 480);\n\t// Set config options that are only set via command line')
main=change(main,'\tConfigSetInt(&gConfig, "Graphics.WindowWidth", 640);','\tConfigGet(&gConfig, "StartServer")->u.Bool.Value = false;\n\tConfigSetInt(&gConfig, "Graphics.WindowWidth", 640);')
patches['src/cdogs.c']=main
loop=read('src/game_loop.c')
a=loop.index('bool emscripten_fs_ready = false;');b=loop.index('\n#endif',a)
loop=loop[:a]+'// IDBFS startup is completed by the browser preRun dependency.\n'+loop[b:]
loop=change(loop,'\tif (!emscriptenPersistData())\n\t\treturn;\n','')
loop=change(loop,'\tLoopRunnerRunInner((LoopRunInnerData *)arg);','''\textern int oga_tick(void);
\tconst int state = oga_tick();
\tif (state == 1) return;
\tif (state == 2 || !LoopRunnerRunInner((LoopRunInnerData *)arg)) {
\t\textern void oga_checkpoint(void); oga_checkpoint();
\t\temscripten_cancel_main_loop();
\t\tSoundTerminate(&gSoundDevice, true); SDL_Quit();
\t\temscripten_force_exit(0);
\t}''')
loop=change(loop,'\tLoopRunInnerData ctx;','\tstatic LoopRunInnerData ctx;')
patches['src/game_loop.c']=loop
for rel in ['src/cdogs/yajl_utils.c','src/cdogs/player_template.c','src/autosave.c']:
 t=read(rel)
 if '#include <emscripten.h>' not in t:t='#include <emscripten.h>\n'+t
 t,n=re.subn(r'EM_ASM\(\s*// persist changes\s*FS\.syncfs\(\s*false, function\(err\) \{ assert\(!err\); \}\);\);','EM_ASM(Module.queueSave(););',t)
 assert n==1,(rel,n)
 # queueSave schedules its writer in a microtask, after fclose has returned.
 patches[rel]=t
t=read('src/cdogs/config_json.c')
a=t.index('#ifdef __EMSCRIPTEN__',t.index('void ConfigSaveJSON('));b=t.index('#endif',a)+len('#endif')
t=t[:a]+'#ifdef __EMSCRIPTEN__\n    EM_ASM(Module.queueSave(););\n#endif'+t[b:]
patches['src/cdogs/config_json.c']=t
# A CSS-resized browser canvas is not a native window resize. Keep native
# render targets at 640x480; CSS letterboxing scales without reinitializing them.
t=read('src/cdogs/grafx.c').replace('SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI','0')
patches['src/cdogs/grafx.c']=t
t=read('src/cdogs/events.c')
# The host owns page-visibility pause. Moving focus to a touch/menu/toolbar
# button is not leaving the game and must not open a second native pause menu.
# Keep input release on focus loss, but neither pause music nor drop the first
# key when focus returns from a host control.
t=change(t,'\t\t\t\tregainedFocus = true;','\t\t\t\t// Browser host controls share focus with the canvas.')
t=change(t,'\t\t\t\t\tMusicSetPlaying(&gSoundDevice.music, false);\n\t\t\t\t\thandlers->HasLostFocus = true;','\t\t\t\t\t// Visibility and explicit pause are handled by the browser host.')
t=change(t,'\t\t\tcase SDL_WINDOWEVENT_SIZE_CHANGED: {','\t\t\tcase SDL_WINDOWEVENT_SIZE_CHANGED: {\n\t\t\t\tbreak; // CSS handles browser resize; retain native render targets.')
patches['src/cdogs/events.c']=t
# Omit optional foreign-engine importers entirely, including old MAME code.
for rel in ['src/cdogs/campaign_entry.c','src/cdogs/map_new.c']:
 t=read(rel)
 t=t.replace('#include <cdogs/cwolfmap/cwolfmap.h>','')
 a=t.index('\tint spearMission = 1;')
 b=t.index('\n\treturn false;',a) if rel.endswith('campaign_entry.c') else t.index('\n\t// try to load the new map format',a)
 t=t[:a]+t[b:];patches[rel]=t
t=read('src/cdogs/campaigns.c')
for s in ['\tMapWolfInit();','\tMapWolfTerminate();','\tMapWolfLoadCampaignsFromSystem(&campaigns->campaignList);']:
 t=change(t,s,'\t// Foreign-game import is not included in this browser package.')
patches['src/cdogs/campaigns.c']=t
t=read('src/prep.c')
t=t.replace('\t\tI("StartServer");','\t\t// UDP server hosting is unavailable in this browser edition.')
t=change(t,'\t\tMapWolfN3DCheckAndLoadCustomQuiz(\n\t\t\tgCampaign.Setting.Title, &gPlayerDatas);','\t\t// Optional foreign-game quiz importer omitted.')
patches['src/prep.c']=t
t=read('src/mainmenu.c')
a=t.index('\tMenuAddSubmenu(\n\t\tmenu, MenuCreateCampaigns(\n\t\t\t\t  "Dogfight"')
b=t.index('\n\treturn menu;',a)
t=t[:a]+'\tMenuAddSubmenu(menu, MenuCreateSeparator(""));\n\tMenuAddSubmenu(menu, MenuCreateBack("Back"));\n'+t[b:]
patches['src/mainmenu.c']=t
# Missing first-run scores are an empty table, not malformed JSON.
t=read('src/hiscores.c')
needle='\tconst char *path = GetConfigFilePath(SCORES_FILE);\n\tyajl_val node = YAJLReadFile(path);'
t=change(t,needle,'\tconst char *path = GetConfigFilePath(SCORES_FILE);\n\tFILE *existing = fopen(path, "r");\n\tif (!existing) return highScores;\n\tfclose(existing);\n\tyajl_val node = YAJLReadFile(path);')
patches['src/hiscores.c']=t
# Keep music out of the blocking preload. The browser fetches only the current
# scene's original track after audio is enabled. A failed track never blocks play.
t=read('src/cdogs/music.c')
t=change(t,'#include "music.h"','#include "music.h"\n#include <emscripten.h>\n#include "sounds.h"\nstatic int ogaMusicType = -1;')
t=change(t,'void MusicPlayGeneral(MusicPlayer *mp, const MusicType type)\n{','void MusicPlayGeneral(MusicPlayer *mp, const MusicType type)\n{\n\togaMusicType = type;\n\tEM_ASM(if (Module.requestMusic) Module.requestMusic($0);, type);')
t+='''
// Called only after the browser has placed an intact Ogg in the virtual FS.
EMSCRIPTEN_KEEPALIVE int oga_music_ready(int type)
{
    if (type < 0 || type >= MUSIC_COUNT) return 0;
    static const char *paths[] = {"music/menu", "music/briefing", "music/game",
        "music/end", "music/lose", "music/victory"};
    MusicPlayer *mp = &gSoundDevice.music;
    CArray *tracks = &mp->generalTracks[type];
    if (tracks->size == 0) {
        CArrayTerminate(tracks);
        LoadMusic(tracks, paths[type]);
    }
    if (tracks->size && ogaMusicType == type && mp->type == MUSIC_SRC_GENERAL)
        MusicPlayGeneral(mp, (MusicType)type);
    return (int)tracks->size;
}
'''
patches['src/cdogs/music.c']=t
for rel,t in patches.items():
 p=override(rel,t);files=[p if x==src/rel else x for x in files]

config=read('src/cdogs/sys_config.h.cmake').replace('@VERSION@','2.4.0').replace('@CDOGS_DATA_DIR@','/').replace('@CDOGS_CFG_DIR@','.config/cdogs-sdl/')
for rel in ['sys_config.h','cdogs/sys_config.h']:
 p=out/rel;p.parent.mkdir(exist_ok=True);p.write_text(config)
(out/'yajl').mkdir()
for h in (src/'src/cdogs/yajl/api').glob('*.h'):shutil.copy2(h,out/'yajl'/h.name)
v=read('src/cdogs/yajl/api/yajl_version.h.cmake')
for key,val in [('YAJL_MAJOR','2'),('YAJL_MINOR','1'),('YAJL_MICRO','1')]:v=v.replace('@'+key+'@',val).replace('${'+key+'}',val)
(out/'yajl/yajl_version.h').write_text(v)

assets=out/'assets';assets.mkdir()
selected=[]
for directory in ['data','graphics','sounds','doc']:
 for p in (src/directory).rglob('*'):
  if not p.is_file() or any(part.startswith('.') for part in p.relative_to(src).parts):continue
  if p.suffix.lower() not in ['.png','.bmp','.wav','.json','.txt','.md'] and not (directory=='sounds' and p.suffix.lower()=='.ogg') and p.name!='CREDITS':continue
  selected.append(p)
for campaign in ['ogre.cdogscpn','bem.cdogscpn']:
 p=src/'missions'/campaign
 selected+=list(p.rglob('*')) if p.is_dir() else [p]
for rel in ['music/game/space_dimensions_8bit','music/menu/space_0.ogg','music/briefing/A Really Tense Moment FULL','music/end/The 9th Circle V2','music/lose/CrashedShip','music/victory/low-fi']:
 audio=src/(rel if rel.endswith('.ogg') else rel+'.ogg')
 credit=src/(rel+'.txt')
 assert audio.is_file() and credit.is_file(),rel
 selected.extend([audio,credit])
manifest=[]
music=[]
for p in selected:
 if not p.is_file():continue
 deferred=p.suffix.lower()=='.ogg' and p.relative_to(src).parts[0]=='music'
 relative=p.relative_to(src)
 deploy_path='/'.join(relative.parts[:2])+'/track.ogg' if deferred else relative.as_posix()
 dest=(out/deploy_path) if deferred else (assets/relative);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 item={'path':p.relative_to(src).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'deferred':deferred}
 manifest.append(item)
 if deferred:
  item['url']=deploy_path
  music.append(item)
for d in ['missions','dogfights','music/game','music/menu','music/briefing']:
 (assets/d).mkdir(parents=True,exist_ok=True)
 (assets/d/'README.txt').write_text('Selected original campaigns and credited music. Foreign imports and extra campaigns omitted.\n')
(out/'assets-manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'music-manifest.js').write_text('Module.musicFiles = '+json.dumps({x['path'].split('/')[1]:x for x in music})+';\n')
flags=(['-O1','-g2'] if '--state' in sys.argv else ['-O2','-g0'])+['-std=gnu99','-fsigned-char','-DSTATIC','-DPB_FIELD_16BIT=1']
files.append(lab/'web/browser.c')
if '--state' in sys.argv:flags+=['-DOGA_DIAGNOSTIC']
flags+=['-I'+str(p) for p in [out,out/'overrides/src',out/'overrides/src/cdogs',src/'src',src/'src/cdogs',src/'src/proto/nanopb',src/'src/cdogs/enet/include',src/'src/cdogs/include',src/'src/cdogs/yajl/src',src/'src/cdogs/yajl/src/api']]
flags+=['-sUSE_SDL=2','-sUSE_SDL_MIXER=2','-sSDL2_MIXER_FORMATS=["ogg"]','-sASYNCIFY','-sASYNCIFY_STACK_SIZE=131072','-sSTACK_SIZE=1048576','-sALLOW_MEMORY_GROWTH=1','-sINITIAL_MEMORY=134217728','-sFORCE_FILESYSTEM=1','-sEXIT_RUNTIME=1','-lidbfs.js','-sEXPORTED_RUNTIME_METHODS=["FS","IDBFS","UTF8ToString","addRunDependency","removeRunDependency","callMain"]']
for directory in ['data','graphics','sounds','doc','missions','dogfights','music']:flags+=['--preload-file',str(assets/directory)+'@/'+directory]
flags+=['-o',str(out/'cdogs.js')]
(out/'compile.rsp').write_text('\n'.join(json.dumps(a) for a in [str(p) for p in files]+flags))
env=dict(os.environ,EM_CONFIG=str(sdk/'.emscripten'),EMSDK_PYTHON=sys.executable,EMCC_CORES='4',TEMP=str(out/'tmp'),TMP=str(out/'tmp'))
started=time.monotonic();print('Compiling',len(files),'units; assets',sum(i['bytes'] for i in manifest),flush=True)
with (out/'build.log').open('w') as log:
 result=subprocess.run([sys.executable,str(sdk/'upstream/emscripten/emcc.py'),'@'+str(out/'compile.rsp')],cwd=src,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
report={'exitCode':result.returncode,'seconds':round(time.monotonic()-started,1),'translationUnits':len(files),'assetBytes':sum(i['bytes'] for i in manifest),'foreignImportersIncluded':False}
(out/'build-result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if result.returncode:print((out/'build.log').read_text()[-6000:]);sys.exit(result.returncode)
# .bin has Cloudflare's default immutable edge caching; MIME remains explicit.
for filename in ['cdogs.wasm','cdogs.data']:(out/filename).rename(out/(filename+'.bin'))
shutil.copy2(lab/'web/persistence.js',out/'persistence.js')
(out/'index.html').write_text('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>C-Dogs source candidate</title><style>body{margin:0;background:#08101b;color:white}canvas{display:block;max-width:100%;width:960px;height:auto;image-rendering:pixelated}button{min-height:44px}</style></head><body><button id="start">Start (test audio muted)</button><canvas id="canvas" width="640" height="480" tabindex="0"></canvas><script>window.logs=[];window.errors=[];var Module={noInitialRun:true,canvas:document.querySelector('canvas'),arguments:[],print:s=>logs.push(s),printErr:s=>errors.push(s),onRuntimeInitialized:()=>window.ready=true};document.querySelector('#start').onclick=()=>{if(window.ready){Module.canvas.focus();Module.callMain([]);}};</script><script src="persistence.js"></script><script src="cdogs.js"></script></body></html>''')
if '--host' in sys.argv:
 for filename in ['index.html','input.js','bridge.js','music.js']:shutil.copy2(lab/'web'/filename,out/filename)
