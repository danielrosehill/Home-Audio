---
name: set-speaker
description: Change the output device (default speaker, sink, sound card) a Squeezelite or snapclient endpoint plays to.
---

# Change the speaker on one endpoint

## Inputs

Endpoint host; the new device (a name, "the USB speaker", "HDMI"), or "list".

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`installation.json` (this endpoint's client, unit, current device), `set-speaker.md` and
`endpoints/<host>.md`.

## Steps

1. **List what the endpoint can play to**, over SSH:
   - ALSA: `aplay -l` and `aplay -L | grep -E '^(plughw|hw|sysdefault|front):'`
   - Squeezelite's own view: `squeezelite -l`
   - snapclient's view: `snapclient -l` (or `--list`)
   - PipeWire/Pulse: `pactl list short sinks`; current default `pactl get-default-sink`
2. **Pick a stable identifier.** ALSA: `plughw:CARD=<CardName>,DEV=<n>` (name, not index;
   `plughw` resamples, `hw` does not). PipeWire: the sink name
   `alsa_output.usb-<vendor>_<model>-00.analog-stereo`. USB devices that only do 48 kHz
   need `plughw` or Squeezelite `-r 48000`.
3. **Which layer to change** (read the unit first: `systemctl cat <unit>`):
   - Client opens ALSA directly (`-o plughw:...`, `--soundcard plughw:...`): edit the
     client's device: `SL_SOUNDCARD` / `-o` for Squeezelite, `--soundcard` for snapclient.
   - Client goes through PipeWire (`-o pulse`, `--player pulse`): either set the system
     default sink (`pactl set-default-sink <sink>`; WirePlumber remembers it) or pin the
     client (`--soundcard <sink>` for snapclient, `PULSE_SINK=<sink>` in the unit's
     `Environment=` for Squeezelite). Pinning is better on a desktop where the default moves.
   - Second speaker, not a replacement: run a second instance (`snapclient --instance 2`,
     or a second squeezelite unit with its own `-n`, `-m` and `-o`).
4. Stop the client, test the device: `speaker-test -D <device> -c 2 -t sine -l 1`.
5. Apply the change, `daemon-reload`, restart the unit, confirm the server still lists the
   player under the same name, then play something.
6. Set the volume baseline: hardware mixer `amixer -c <card> scontrols` /
   `amixer -c <card> sset <control> 80%`; Squeezelite `-V <control>` hands volume to the
   hardware mixer.
7. Record the new device in `installation.json` and `endpoints/<host>.md` (old -> new, date).

## Notes

Restarts the endpoint's client. Ask the user whether they heard it; report ALSA-only
verification as that.

## Data storage

Updates `installation.json`, `endpoints/<host>.md` and `changelog.md` in the overlay.
