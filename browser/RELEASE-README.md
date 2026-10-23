# C-Dogs SDL browser integration

Original C-Dogs: Ronny Wester. SDL port and enhancements: Jeremy Chin, Lucas
Martin-King, Cong Xu and the contributors listed in `doc/CREDITS`. The original
Emscripten port is credited to Justin Jacobs. Browser host fixes and packaging:
Old Games Archive / CatBroDev. This is an adaptation of that existing Web port,
not a claim to have created the first browser version.

Pinned upstream: https://github.com/cxong/cdogs-sdl/tree/a388e3918c3a70e8a753a754f01ee21f8a31f28f

This package contains the two original campaigns, Ogre Rampage (16 missions)
and Bug-Eyed Monsters (3 missions), and the procedural Quick Play mode. It omits
additional community campaigns, empty deathmatch menus, UDP LAN hosting/joining
and foreign-game importers. Native game menus remain in English.

## Controls

Choose Start, Campaign and a campaign. X joins keyboard player one and
confirms choices. Use the arrow keys to move, aim and navigate. X fires; the
original default **stops movement while firing**. Z switches weapons while
stationary or slides with a direction. S throws an available grenade, A toggles
the map, Enter confirms and Esc opens the pause/back menu. Configure in the
website's shared touch controls changes the touch bindings without game-specific
UI code. In-game keyboard remapping must be matched by the touch configuration.

## Storage and audio

IndexedDB stores the native settings, player templates and campaign autosave.
Campaign progression is written by the original mission debriefing code, then
restored through Continue. This is **not a mid-mission save state** and is not
cloud storage. Clearing browser data removes it. If storage is unavailable,
play can continue without persistence. Audio starts muted; the host sound
button enables it. Pause releases input and gates audio; disposal closes SDL
audio and flushes pending native files.

Sound effects are included in the startup package without recompression.
The preload includes both WAV and Ogg effects (the previous extension filter
omitted Ogg effects). The unused upstream lmg.mp3 is not referenced by the
selected weapon data and is not part of this Ogg/WAV browser build.
Original music is downloaded separately, only for the current scene after
sound is enabled. Music downloads never hold up the game; failed downloads
leave sound effects working. Changing scenes, muting, pausing or leaving the
page cancels pending music downloads. Original tracks and credits are retained.
The .wasm.bin and .data.bin resources use explicit MIME types and immutable
edge caching. The loading indicator reports actual game-data download progress.

## Build

Install Emscripten 4.0.23 and set `CDOGS_EMSDK` to its emsdk directory. With Python
available, run `python browser/scripts/build-web.py release --host`, then
`python browser/scripts/package-release.py release`. Serve `browser/build/release` over HTTP(S).
The SDK downloads its SDL2 2.32.8, SDL2_mixer 2.8.0, libogg and libvorbis ports
on first use. The build applies checked transformations to an unchanged source
tree at the repository root; emitted changes are inspectable in `overrides`.
No test state exports or fixtures are compiled unless `--state` is explicitly
supplied. Source and resource hashes accompany the package.

The source archive contains all code and resources needed by this browser
build, the build/packaging scripts and host sources. Excluded optional MAME
sources and unused campaigns/music are not required to reproduce it. No
upstream author headers or licenses in the included files are changed.

## Changes

- Complete IDBFS restoration before native startup; initialize player templates
  before direct campaign loading.
- Serialize native JSON/config writes after file close; flush before shutdown.
- Keep the main loop and its context alive across asynchronous Web callbacks.
- Preserve the native 4:3 presentation while CSS handles responsive scaling.
- Let the host handle visibility pause; moving focus to toolbar or touch
  controls does not open an extra native pause menu or swallow the first key.
- Omit unavailable LAN/foreign import paths; select credited original assets.
- Add the existing site protocol for generic touch keys, pause, mute and disposal.

Code is GPL-2.0 with BSD-licensed components. Assets have their own CC0, CC-BY
and CC-BY-SA notices. See `notices.txt`, the unmodified source headers and
resource attribution files. Ronny's original graphics/campaigns were relicensed
to CC-BY in the correspondence preserved in `doc/README_DATA.md`.

Testing does not imply completion of every mission or physical Android/iOS
acceptance. Evidence distinguishes actual gameplay from a diagnostic save
fixture; diagnostic files are excluded from the release runtime.
