# Reproduce the browser build

Use this branch's source tree (upstream base `a388e3918c3a70e8a753a754f01ee21f8a31f28f`),
Python 3, and an activated Emscripten **4.0.23** SDK. Set `CDOGS_EMSDK` to the
absolute emsdk directory. No Old Games Archive credentials or private site code are needed.

From the repository root:

```sh
python browser/scripts/build-web.py release --host
python browser/scripts/package-release.py release
node browser/scripts/check-music-loader.mjs
python -m http.server 8080 --directory browser/build/release
```

Open `http://localhost:8080`. Use the visible Start button; the standalone host
starts muted. The existing host message protocol supplies input/pause/sound in
the live site; physical keyboard controls also work in the standalone build.
Do not add `--state` to a public build (it enables diagnostic exports).

PowerShell SDK example:

```powershell
$env:CDOGS_EMSDK = 'C:/tools/emsdk'
python browser/scripts/build-web.py release --host
```

On first use, emcc fetches SDL2 2.32.8, SDL2_mixer 2.8.0, libogg and libvorbis.
The script compiles 166 C translation units and writes inspectable Web-only
overrides under `browser/build/release/overrides`. It keeps native render targets
at 640×480 and lets CSS scale the canvas, restores IDBFS before native startup,
serializes writes, handles host focus/pause/disposal, and defers six original
music tracks. All 330 selected original WAV/Ogg effects are unchanged.

Serve `.wasm.bin` with `application/wasm`, `.data.bin` with
`application/octet-stream` and `.ogg` with `audio/ogg` in production. Compression
must match the HTTP Content-Encoding. Use a new versioned resource path whenever
bytes change. Music files must remain at their manifest URLs; source.zip is a
separate download and never required to start the game.

The public packaging script emits a full Fork source archive; its ZIP bytes will
differ from the earlier deployed subset archive. Runtime source, original effects
and native build inputs are preserved. `RUNTIME-SOURCE-MANIFEST.json` records the
browser source hashes corresponding to the accepted deployed release.

Actual acceptance: menu into a mission, movement/fire, audio PCM with music still
absent, optional-music 503 isolation, pause/resume/exit, IndexedDB file restore,
three fresh preview browser starts, bilingual page/SEO and responsive layouts.
Tests were muted at the browser output. This is not full-campaign or physical
phone certification. Details and current limitations: [release notes](RELEASE-README.md).
