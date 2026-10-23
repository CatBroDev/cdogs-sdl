/* Browser save queue. GPL-2.0-or-later. Old Games Archive / CatBroDev. */
(() => {
  let dirty=false, writer=null, shutdown=null;
  const status=value=>{Module.storageState=value;Module.onStorageState?.(value);};
  const write=()=>new Promise(resolve=>{
    try {Module.FS.syncfs(false,error=>{status(error?'unavailable':'available');resolve(!error);});}
    catch {status('unavailable');resolve(false);}
  });
  Module.queueSave=()=>{
    dirty=true;
    return writer??=(Promise.resolve().then(async()=>{
      let ok=true;
      while(dirty){dirty=false;ok=(await write())&&ok;}
      return ok;
    }).finally(()=>{writer=null;}));
  };
  Module.flushSaves=()=>shutdown??Module.queueSave();
  Module.preRun=[()=>{
    const {FS,IDBFS}=Module;
    FS.mkdirTree('/persistent_data');FS.mount(IDBFS,{autoPersist:false},'/persistent_data');
    const close=IDBFS.quit.bind(IDBFS);
    Module.shutdownSaves=()=>shutdown??=(async()=>{
      await writer;const ok=await Module.queueSave();close();return ok;
    })();
    IDBFS.quit=()=>{Module.shutdownSaves();};
    status('loading');Module.addRunDependency('cdogs-saves');
    FS.syncfs(true,error=>{status(error?'unavailable':'available');Module.removeRunDependency('cdogs-saves');});
  }];
})();
