/* GPL-2.0-or-later. Non-blocking original music: Old Games Archive / CatBroDev. */
(() => {
  const scenes = ['menu', 'briefing', 'game', 'end', 'lose', 'victory'];
  const loaded = new Set(), failed = new Set();
  let wanted = -1, enabled = false, disposed = false, active;
  const state = Module.musicState = { requested: [], loaded: [], failed: [] };
  function cancel() {
    if (!active) return;
    clearTimeout(active.timer); active.controller.abort(); active = undefined;
  }
  async function pump() {
    if (!enabled || disposed || wanted < 0 || loaded.has(wanted) || failed.has(wanted) || active?.type === wanted) return;
    cancel();
    const type = wanted, file = Module.musicFiles[scenes[type]];
    if (!file) return;
    const job = active = { type, controller: new AbortController() };
    job.timer = setTimeout(() => job.controller.abort('timeout'), 30000);
    state.requested.push(type);
    try {
      const response = await fetch(file.url, { signal: job.controller.signal });
      if (!response.ok) throw new Error('Music HTTP ' + response.status);
      const bytes = await response.arrayBuffer();
      if (bytes.byteLength !== file.bytes) throw new Error('Music size mismatch');
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
      if (hash !== file.sha256) throw new Error('Music integrity mismatch');
      if (disposed || active !== job || !enabled) return;
      Module.FS.writeFile('/' + file.path, new Uint8Array(bytes));
      // Mark first: native activation may request this same scene again.
      loaded.add(type);
      if (!Module._oga_music_ready(type)) throw new Error('Music decode failed');
      state.loaded.push(type);
    } catch (error) {
      if (job.controller.signal.aborted && job.controller.signal.reason !== 'timeout') return;
      failed.add(type); state.failed.push({ type, reason: String(error) });
      // Optional music failure is intentionally non-fatal and not retried.
    } finally {
      clearTimeout(job.timer);
      if (active === job) active = undefined;
    }
  }
  Module.requestMusic = type => {
    if (!Number.isInteger(type) || type < 0 || type >= scenes.length) return;
    if (wanted !== type) cancel();
    wanted = type; void pump();
  };
  Module.setMusicEnabled = value => { enabled = !!value; if (!enabled) cancel(); else void pump(); };
  Module.disposeMusic = () => { disposed = true; enabled = false; cancel(); };
})();
