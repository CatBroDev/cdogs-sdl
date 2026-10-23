/* GPL-2.0-or-later. Browser integration: Old Games Archive / CatBroDev.
 * Original C-Dogs: Ronny Wester; C-Dogs SDL: its credited contributors. */
#include <emscripten.h>
#include <SDL.h>
#include <SDL_mixer.h>
#include <string.h>
#include <cdogs/events.h>
#include <cdogs/config_io.h>
#include <cdogs/files.h>
#include <cdogs/player_template.h>
#include <autosave.h>
static int paused=0, stopping=0, muted=1, ready=0, ticks=0;
EMSCRIPTEN_KEEPALIVE void oga_release(void){SDL_ResetKeyboard();SDL_FlushEvents(SDL_KEYDOWN,SDL_MOUSEWHEEL);EventReset(&gEventHandlers);}
EMSCRIPTEN_KEEPALIVE void oga_pause(int value){oga_release();paused=value!=0;}
EMSCRIPTEN_KEEPALIVE int oga_paused(void){return paused;}
EMSCRIPTEN_KEEPALIVE void oga_mute(int value){muted=value!=0;}
EMSCRIPTEN_KEEPALIVE void oga_stop(void){stopping=1;paused=0;}
EMSCRIPTEN_KEEPALIVE void oga_checkpoint(void){if(ready){ConfigSave(&gConfig,GetConfigFilePath(CONFIG_FILE));PlayerTemplatesSave(&gPlayerTemplates);AutosaveSave(&gAutosave,GetConfigFilePath(AUTOSAVE_FILE));}}
static void gate(void *unused,Uint8 *stream,int length){if(muted||paused||stopping)memset(stream,0,length);}
void oga_audio_install(void){Mix_SetPostMix(gate,NULL);}
int oga_tick(void){if(!ready){ready=1;EM_ASM(if(Module.onGameReady)Module.onGameReady(););}if(stopping)return 2;if(paused)return 1;ticks++;return 0;}
#ifdef OGA_DIAGNOSTIC
#include <stdio.h>
#include <cdogs/actors.h>
#include <cdogs/gamedata.h>
#include <cdogs/grafx.h>
EMSCRIPTEN_KEEPALIVE const char *oga_state(void){
 static char buf[900];const PlayerData *p=GetFirstPlayer(true,true,true);
 const TActor *a=p?ActorGetByUID(p->ActorUID):NULL;
 snprintf(buf,sizeof(buf),"{\"ticks\":%d,\"loaded\":%d,\"begun\":%d,\"mission\":%d,\"players\":%d,\"x\":%.3f,\"y\":%.3f,\"hp\":%d,\"resX\":%d,\"resY\":%d,\"savedCampaigns\":%d,\"time\":%d,\"device\":%d,\"deviceIndex\":%d,\"cmd\":%d,\"shot\":%d}",ticks,gCampaign.IsLoaded,gMission.HasBegun,gCampaign.MissionIndex,(int)gPlayerDatas.size,a?a->thing.Pos.x:0,a?a->thing.Pos.y:0,p?p->HP:0,gGraphicsDevice.cachedConfig.Res.x,gGraphicsDevice.cachedConfig.Res.y,(int)gAutosave.Campaigns.size,gMission.time,p?p->inputDevice:-1,p?p->deviceIndex:-1,a?a->lastCmd:0,a?a->hasShot:0);return buf;
}
/* Explicit test fixture: exercise the same save API used by debriefing.
 * Does not claim a naturally completed mission. Never compiled in releases. */
EMSCRIPTEN_KEEPALIVE int oga_fixture_save_next(void){
 if(!gMission.HasBegun)return 0;
 AutosaveAdd(&gAutosave,&gCampaign.Entry,gMission.index,gMission.index+1,&gPlayerDatas);
 AutosaveSave(&gAutosave,GetConfigFilePath(AUTOSAVE_FILE));return 1;
}
#endif
