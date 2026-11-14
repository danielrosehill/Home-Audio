---
name: podcasts-radio
description: Podcasts and radio in Music Assistant: add feeds (one or a whole OPML), list and play the latest episode, resume, add radio streams, remove. Use on "add this podcast", "play the latest episode of X", "add this radio station".
---

# Podcasts and radio

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` and `installation.json` (rooms -> player names). Run calls through the user's
secrets route if `profile.env` names one. `A="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`.
Resolve rooms to players by name; `$A ma-players` lists them. Never guess IDs.

## Podcasts

- **Add:** `$A ma-add-podcast <feed url>... ` or `--opml <url>` for every feed in an OPML.
  Each feed becomes one `podcastfeed` provider instance through the setup flow
  (`config/providers/setup` + `config/flows/submit {"values":{"feed_url"}}`). It does not
  dedupe: list titles first with `$A ma music/podcasts/library_items '{"limit":1000}'`.
- **Episodes:** `$A episodes "<podcast title or part>" [--limit 5]`: newest first, with
  duration, resume point and played flag. `--play "<room>"` plays the newest.
  Underneath: `music/podcasts/podcast_episodes {"item_id","provider_instance_id_or_domain":"library"}`.
- **Resume:** `$A now-playing --history 10` shows `in_progress` items; play one by `uri`
  with `player_queues/play_media`.
- **Remove a feed** (destructive, confirm): delete its provider instance
  (`config/providers/remove {"instance_id"}`); `$A providers --domain podcastfeed` maps
  instances, and `music/podcasts/library_items` `provider_mappings` maps titles to instances.

## Radio

- Library stations: `music/radios/library_items`; search `music/search {"search_query","media_types":["radio"]}`.
- Add a stream URL: `$A ma builtin/add_radio '{"url":"<stream>","name":"<name>","image_url":"<optional>"}'`
  (source 2.10.11; not yet run live).
- Play: `player_queues/play_media {"queue_id","media":"<radio uri>"}`.

## Data storage

House record of which feeds were added: the user's notebook or overlay `changelog.md`.
