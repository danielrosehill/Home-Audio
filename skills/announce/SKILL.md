---
name: announce
description: Speak a message or play a sound on one speaker, several or a group, through Music Assistant TTS or Home Assistant. Use on "announce dinner is ready", "say X in the kitchen", "tell everyone".
---

# Announce

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` and `installation.json` (rooms -> player names). Run calls through the user's
secrets route if `profile.env` names one. `A="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`.
Resolve rooms to players by name; `$A ma-players` lists them. Never guess IDs.

## Steps

1. Pick the engine once: `$A ma players/tts_engines` lists `uid`s (`hass/tts.<entity>` when
   TTS comes from Home Assistant). Record the user's choice as `HOME_AUDIO_TTS_ENGINE` in
   `profile.env`, and pass it with `--engine`.
2. `$A announce "<text>" -p "<room>" [-p ...] [--engine <uid>] [--language en] [--volume 50] [--no-chime]`.
   A sound file instead of speech: `--url <http url MA can reach>`. MA ducks or pauses what
   is playing and resumes it afterwards.
3. This makes sound in someone's room: say where before sending, unless asked directly.
4. MA unreachable or no engine: Home Assistant `tts.speak`
   (`{"entity_id":"tts.<engine>","media_player_entity_id":"media_player.<x>","message"}`) or
   `music_assistant.play_announcement` (`message`, `tts_entity_id`, `url`, `use_pre_announce`,
   `announce_volume`); see the `home-assistant` skill.

## Commands underneath

`players/cmd/play_announcement {"player_id","message"|"url","tts_engine?","language?",
"volume_level?","pre_announce?","pre_announce_url?"}` (source: 2.10.11; `message` and
`tts_engine` are newer than the `url`-only form). Player config keys `announce_volume`,
`announce_volume_strategy`, `announce_volume_min/max` set the default level.

## Data storage

`HOME_AUDIO_TTS_ENGINE` in `profile.env`, only on the user's choice.
