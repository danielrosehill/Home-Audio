# Home Assistant patterns for audio

REST basics: `Authorization: Bearer <token>`; `GET /api/states`, `GET /api/states/<entity>`,
`POST /api/services/<domain>/<service>` (append `?return_response` when the action returns
data), config entries under `/api/config/config_entries/*`, automations under
`/api/config/automation/config/<id>`.

`music_assistant` actions (integration docs, checked 2026-11-14): `play_media`
(`media_id`, `media_type`, `artist`, `album`, `enqueue`, `radio_mode`), `search`,
`get_library`, `get_queue`, `transfer_queue` (`source_player`, `auto_play`),
`play_announcement` (`url`, `use_pre_announce`, `announce_volume`). Needs MA server 2.4+.

## Automation patterns

Announcement that restores what was playing (MA handles resume itself):

```yaml
alias: Doorbell announcement
triggers: [{trigger: state, entity_id: binary_sensor.doorbell, to: "on"}]
actions:
  - action: music_assistant.play_announcement
    target: {entity_id: media_player.kitchen}
    data: {url: "http://<host>/doorbell.mp3", announce_volume: 40}
```

Night volume cap:

```yaml
alias: Night volume cap
triggers: [{trigger: time, at: "21:00:00"}]
actions:
  - action: media_player.volume_set
    target: {entity_id: [media_player.bedroom, media_player.nursery]}
    data: {volume_level: 0.2}
```

Play a playlist in a room from a button:

```yaml
actions:
  - action: music_assistant.play_media
    target: {entity_id: media_player.living_room}
    data: {media_id: "Morning", media_type: playlist, enqueue: replace}
```
