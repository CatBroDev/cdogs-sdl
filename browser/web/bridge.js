/* Optional Old Games Archive protocol v1, GPL-2.0-or-later. */
(() => {
  const q=new URLSearchParams(location.search);let origin;
  if(q.get('embedded')==='1'&&parent!==window){
    try{const u=new URL(q.get('host'));
      if(['https://oldgamesarchive.org','https://preview.oldgamesarchive.org'].includes(u.origin)||
        (u.protocol==='http:'&&['localhost','127.0.0.1'].includes(u.hostname)))origin=u.origin;
    }catch{}
  }
  if(origin)document.documentElement.classList.add('embedded');
  const send=(type,extra={})=>{if(origin)parent.postMessage({source:'oldgames-native',version:1,type,...extra},origin);};
  const keys={263:37,265:38,262:39,264:40,256:27,257:13,32:32,341:17,345:17,342:18,346:18,340:16,344:16,260:45,
    258:9,259:8,261:46,266:33,267:34,268:36,269:35,280:20,281:145,282:144,284:19,
    44:188,45:189,46:190,47:191,59:186,61:187,91:219,92:220,93:221,96:192,39:222,335:13};
  for(let n=65;n<=90;n++)keys[n]=n;for(let n=48;n<=57;n++)keys[n]=n;
  for(let n=0;n<12;n++)keys[290+n]=112+n;for(let n=0;n<10;n++)keys[320+n]=96+n;
  let ready=false,stopped=false,started=false,muted=true,paused=false,helpOpen=false;
  const status=text=>{document.querySelector('#status').textContent=text;};
  const release=()=>{Module.browserInput.release();if(ready&&!stopped)Module._oga_release();};
  const audio=()=>{if(!ready||stopped)return;Module._oga_mute(muted?1:0);
    Module.setMusicEnabled(!muted&&!paused&&!helpOpen);
    if(!muted&&!paused&&!helpOpen)Module.SDL2?.audioContext?.resume().catch(()=>{});};
  const checkpoint=()=>{if(ready&&!stopped)Module._oga_checkpoint();return Module.flushSaves?.();};
  const pause=value=>{if(!ready||stopped)return;release();paused=value;Module._oga_pause(paused?1:0);audio();
    if(value)checkpoint();send(value?'paused':'running');};
  Module.setHelpOpen=value=>{helpOpen=value;if(ready&&!stopped){release();Module._oga_pause(paused?1:0);audio();}};
  Module.onGameReady=()=>{ready=true;document.querySelector('#loading').hidden=true;audio();status('Ready');send('ready');send('storage',{state:Module.storageState});if(document.hidden)pause(true);};
  Module.onStorageState=state=>send('storage',{state});
  Module.onRuntimeInitialized=()=>{window.runtimeReady=true;status('Press Start');if(origin)start();};
  function start(){if(started){if(paused)pause(false);return;}if(!window.runtimeReady)return;started=true;Module.canvas.focus();Module.callMain(Module.arguments);}
  Module.onAbort=reason=>{stopped=true;Module.disposeMusic();clearInterval(timer);status('Unable to start');send('error');console.error(reason);};
  Module.onExit=()=>{stopped=true;Module.disposeMusic();clearInterval(timer);status('Game stopped');
    Module.shutdownSaves().finally(()=>{send('stopped');window.gameStopped=true;});};
  const timer=setInterval(()=>{if(ready&&!stopped)checkpoint();},5000);
  document.querySelector('#start').onclick=start;
  document.querySelector('#sound').onclick=()=>{muted=!muted;audio();document.querySelector('#sound').textContent=muted?'Sound: off':'Sound: on';};
  addEventListener('message',event=>{
    const m=event.data;
    if(!origin||event.source!==parent||event.origin!==origin||!m||m.source!=='oldgames-player'||m.version!==1||!ready||stopped)return;
    if(m.type==='key'&&!paused&&!helpOpen&&Number.isInteger(m.key)&&typeof m.down==='boolean'&&keys[m.key]!==undefined)
      Module.browserInput.key(keys[m.key],m.down,[344,345,346].includes(m.key)?2:m.key>=320&&m.key<=335?3:0);
    if(m.type==='release')release();if(m.type==='focus'&&!helpOpen)Module.canvas.focus();
    if(m.type==='pause')pause(true);if(m.type==='resume'&&!document.hidden)pause(false);
    if(m.type==='sound'&&typeof m.muted==='boolean'){muted=m.muted;audio();}
    if(m.type==='dispose'){Module.disposeMusic();release();checkpoint();Module._oga_stop();}
  });
  addEventListener('blur',release);
  addEventListener('pagehide',()=>{Module.disposeMusic();release();if(ready&&!stopped){checkpoint();Module._oga_stop();}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pause(true);else if(!origin&&paused){status('Paused: press Start to continue');}});
})();
