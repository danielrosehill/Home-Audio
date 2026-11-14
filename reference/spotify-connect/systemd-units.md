# Systemd unit reference

Drop-in units when a package doesn't ship one or when you want to pin behaviour.

## librespot.service (raw librespot)

```ini
[Unit]
Description=librespot Spotify Connect endpoint
After=network-online.target sound.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/librespot \
  --name "Kitchen Speaker" \
  --device plughw:CARD=D1,DEV=0 \
  --bitrate 320 \
  --initial-volume 60 \
  --enable-volume-normalisation
Restart=on-failure
RestartSec=3
User=librespot

[Install]
WantedBy=multi-user.target
```

## spotifyd.service (if not provided by package)

```ini
[Unit]
Description=spotifyd
After=network-online.target sound.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/spotifyd --no-daemon
Restart=on-failure
RestartSec=3
User=spotifyd

[Install]
WantedBy=multi-user.target
```

## snapserver (package-provided, for reference)

Config lives in `/etc/snapserver.conf`. Service is `snapserver.service`. Typical stream line:

```
[stream]
source = pipe:///tmp/snapfifo?name=Spotify&sampleformat=44100:16:2
```

## snapclient defaults

File: `/etc/default/snapclient`

```
SNAPCLIENT_OPTS="--host 192.168.1.20 --soundcard plughw:CARD=Headphones,DEV=0"
```

## User vs system services

- Desktop Linux with a logged-in user: use `systemctl --user` so audio follows the user session.
- Headless Pi: use system-level services with a dedicated user.
- EasyEffects: always `--user` (it needs a graphical session unless configured otherwise).
