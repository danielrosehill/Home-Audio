---
name: sleep-and-alarms
description: Sleep timers, bedtime fade-outs and wake-up music. Use on "stop in 30 minutes", "fade out the bedroom", "wake me with X at 7", "cancel the sleep timer".
---

# Sleep timers and alarms

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` and `installation.json` (rooms -> player names). Run calls through the user's
secrets route if `profile.env` names one. `A="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`.
Resolve rooms to players by name; `$A ma-players` lists them. Never guess IDs.

## Sleep timer (Music Assistant native)

`$A sleep <minutes> -p "<room>"`; `0` clears. Output gives `ends_at` and `minutes_left`.
Commands: `players/sleep_timer/set {"player_id","seconds"}`, `/get` (epoch end or null),
`/clear` (confirmed live, 2.10.11).

## Fade out now

Step the volume down, then pause, then put the volume back so the next play is not silent:
read `volume_level` (`players/get`), loop `players/cmd/volume_set` down by ~5 every
10-20 s, `players/cmd/pause`, then `volume_set` to the saved level.

## Wake-up music (Home Assistant automation)

MA has no alarm command. Create an automation through the `home-assistant` skill
(`POST /api/config/automation/config/<id>`, then `automation.reload`):

```yaml
alias: Wake-up music (<room>)
triggers: [{trigger: time, at: "07:00:00"}]
conditions: [{condition: time, weekday: [sun, mon, tue, wed, thu]}]
actions:
  - action: media_player.volume_set
    target: {entity_id: media_player.<room>}
    data: {volume_level: 0.1}
  - action: music_assistant.play_media
    target: {entity_id: media_player.<room>}
    data: {media_id: "<playlist or uri>", media_type: playlist, enqueue: replace}
  - repeat:
      count: 10
      sequence:
        - delay: "00:00:30"
        - action: media_player.volume_up
          target: {entity_id: media_player.<room>}
```

Show the YAML and get a yes before saving; note the automation id in the overlay
`changelog.md`. Weekdays follow the user's week (check the profile).

## Data storage

`changelog.md` line for each automation created.
