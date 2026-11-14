---
name: library-providers
description: Music Assistant sources and library health: which providers exist, which are failing, add a source through the setup flow, resync. Use on "what music sources do I have", "why isn't X syncing", "add a source", "rescan the library".
---

# Library and providers

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` and `installation.json` (rooms -> player names). Run calls through the user's
secrets route if `profile.env` names one. `A="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py"`.
Resolve rooms to players by name; `$A ma-players` lists them. Never guess IDs.

## Steps

1. **Health:** `$A providers` (domain, instance, enabled, loaded, last_error);
   `--problems` keeps only enabled ones that failed or are not loaded; `--domain <d>` filters.
2. **What can be added:** `$A ma providers/manifests` (`domain`, `multi_instance`,
   `has_setup_flow`, `documentation`).
3. **Add** (a change; confirm first): `$A ma config/providers/setup '{"provider_domain":"<d>"}'`
   returns a step. `form`: fill its `entries` and `$A ma config/flows/submit '{"flow_id":"<id>","values":{...}}'`;
   repeat until `type` is `finish` (`result.instance_id`). `external` (OAuth): give the user
   the `url` and poll `config/flows/get`. `abort`: read `reason`. `config/providers/save`
   refuses new providers.
4. **Fix:** `config/providers/reload {"instance_id"}`; credentials changed:
   `config/providers/reconfigure {"instance_id"}` (same flow).
5. **Resync:** `$A ma music/sync '{"media_types":["track"],"providers":["<instance>"]}'`
   (both optional). Counts: `music/<type>s/count`.
6. Errors come back as HTTP 500; the reason is in `$A ma logging/get` (admin token).

## Data storage

Nothing written; record source changes in the overlay `changelog.md`.
