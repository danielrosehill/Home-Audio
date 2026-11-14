# Zeroconf / mDNS notes

Spotify Connect discovery runs over mDNS (service type `_spotify-connect._tcp`). Most "device missing from picker" problems are zeroconf problems.

## Check the device is advertising

From any host on the same subnet:

```bash
avahi-browse -rt _spotify-connect._tcp
```

You should see a record per advertising device with its IP, port, and TXT fields (`CPath`, `VERSION`, `Stack`).

## Common breakage

| Symptom | Cause |
|---|---|
| `avahi-browse` shows nothing | `avahi-daemon` not running on the advertising host — `systemctl status avahi-daemon`. |
| Device advertises but phone doesn't see it | Phone is on **guest Wi-Fi** (isolated) or a different VLAN. |
| Device appears briefly then vanishes | IP changed (DHCP lease expired) — static IP violated. |
| Windows Spotify app can't see Linux librespot | Bonjour / iTunes mDNS service not installed on Windows. |
| Two devices with the same name | Two players running on the same host (raspotify + spotifyd both installed). |

## Avahi on minimal Pi builds

Raspberry Pi OS Lite sometimes ships without avahi-daemon running. Fix:

```bash
sudo apt install avahi-daemon
sudo systemctl enable --now avahi-daemon
```

## Firewall

mDNS uses UDP 5353. Spotify Connect itself uses a dynamic port advertised in the mDNS record. If `ufw` / `firewalld` is enabled, allow:

- UDP 5353 (mDNS)
- The TCP port librespot/spotifyd picks (check `ss -tlnp | grep librespot`), or simply allow the LAN subnet inbound.

## Librespot-family ACL reality check

There is **no** per-user ACL in librespot, spotifyd, or raspotify. If the device is on the LAN and discoverable, every Premium user on that LAN can see and cast to it. Tell the user this when they ask about privacy.
