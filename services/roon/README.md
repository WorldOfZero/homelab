# Roon Server

RoonServer in Docker, with its database on the Fast NVMe pool (`/mnt/Fast/Configuration/roon`)
and music read from `/mnt/Vault/Media/Music`.

## Why macvlan and not host networking

Roon bundles its own .NET runtime, and that runtime's network-interface enumeration crashes
the whole server with `System.ArgumentException: An invalid IP address was specified`
([dotnet/runtime#49515](https://github.com/dotnet/runtime/issues/49515)) when interfaces
change during enumeration. With `network_mode: host` on minerva (~40 containers creating and
destroying veth interfaces), that race fired constantly: the server crash-looped and every
Roon remote disconnected on each crash. See [[diagnose-roon-disconnects]].

On a macvlan network the container has its own MAC and IP directly on the LAN, so:

- Roon's runtime sees only `eth0` + `lo` — stable, no crash trigger.
- Multicast discovery and RAAT streaming keep working (macvlan is plain L2 on the LAN).

## Deploying

The network values are in the compose file. They are not secret, so they are in git and
Portainer needs no environment variables for this stack:

| Value | Setting | How to check it |
|---|---|---|
| LAN interface | `parent: eno1` | `ip route get 192.168.1.1` on minerva, the `dev` field |
| Subnet and gateway | `192.168.1.0/24`, `192.168.1.1` | the same command, the `src` address |
| Container address | `ipv4_address: 192.168.1.212` | must be outside the UniFi DHCP range (see below) |

Roon remotes connect to `192.168.1.212`, not to the address of minerva.

## UniFi

The container has its own MAC address on the LAN, so UniFi shows it as a separate client. The
compose file pins the MAC to `02:52:4f:4f:4e:01`. Without a fixed MAC, each container recreate
can create a new MAC, and UniFi shows a new unknown client each time. `02` marks the address as
locally administered, so it cannot be the same as the MAC of real hardware.

Configure the router once:

1. In **Settings → Networks → (LAN) → DHCP**, make sure that the DHCP range does not include
   `192.168.1.212`. For example, end the range at `.199`. UniFi never gives an address outside
   the range to a client.
2. After the first deploy, find the client with MAC `02:52:4f:4f:4e:01` in the client list.
   Name it "Roon Core", and set **Fixed IP Address** to `192.168.1.212`. This records the
   address in UniFi, so that nobody gives it to a different device.

## Known limitations

- **IPv6 is off in the container.** The macvlan network has only IPv4. With IPv6 on, Roon
  tried to connect to the IPv6 addresses of Qobuz, failed with `Network is unreachable`, and
  did not try IPv4, so Qobuz tracks stopped. The `sysctls` in the compose file turn IPv6 off,
  so Roon uses only IPv4. To use IPv6, configure an IPv6 subnet on the macvlan network first.

- **minerva itself cannot reach the container** (kernel macvlan isolation). Roon doesn't
  need it — remotes and audio endpoints are other LAN devices, and music arrives through the
  bind mount. Remember it when debugging: `curl` from the host will fail while every other
  machine on the LAN connects fine. To test from the host, add a macvlan shim interface, or
  just test from another device.
- After the switch, Roon remotes may need one manual reconnect ("Find my Roon Core" →
  the new IP).

## Image note

The `debian-12-slim` image lacks `procps`; Roon's wrapper logs `ps: command not found` and
its stale-process handling does not work. Harmless but worth fixing if the image publisher
offers a fuller tag.
