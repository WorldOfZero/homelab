# Monitoring stack

Grafana, Loki, Prometheus, Alloy, cAdvisor and node-exporter for minerva.

| Data | Source | Coverage |
|---|---|---|
| Container logs | Alloy reads the Docker API | All containers, with no label on the service |
| Roon log file | Alloy reads `RoonServer_log.txt` | Roon stream errors do not go to the container log |
| Container metrics | cAdvisor | All containers: CPU, memory, restarts, IO |
| Host metrics | node-exporter | minerva: CPU, memory, pressure, disks, NICs, ZFS |
| Docker state | `docker-state-exporter` | All containers: state, health, restarts, OOM kills, exit code |
| Tailnet paths | Tailscale client metrics | Bytes on each path (direct, DERP, peer relay) for each sidecar and the minerva node |
| Media metrics | exportarr, `jellyfin-exporter`, Jellyfin `/metrics` | Sonarr, Radarr, Bazarr, Jellyfin |
| Other application metrics | Not configured | See [[add-app-metrics-exporters]] |

The Alloy, Prometheus and Loki configuration is in the `configs` block of
`docker-compose.yaml`, so a redeploy applies it. The Grafana provisioning in
`grafana/provisioning` is in the Grafana image, so a redeploy with a build applies it too. Copy no
files to the host for any of them.

## Access

Grafana is at `https://grafana.comet-stork.ts.net` on the tailnet, and at port 3001 on the LAN. A
Tailscale sidecar gives Grafana its name. Set `TS_AUTHKEY` in the Portainer stack variables before
you deploy. The `tailnet-local` network must exist. See `ENVIRONMENT.md`.

## Login

Grafana uses tsidp for Tailscale login. The browser must be on the tailnet. The local login form
stays as a way in when tsidp is down. Service account tokens do not use tsidp.

The role comes from the `groups` claim that tsidp sends. The tailnet policy (in homelab-private)
gives each Grafana group a `tailscale.com/cap/tsidp` grant with that claim:

| Tailscale group | Claim | Grafana role |
|---|---|---|
| `group:grafana-admins` | `grafana-admins` | Admin |
| `group:grafana-editors` | `grafana-editors` | Editor |
| `group:grafana-viewers` | `grafana-viewers` | Viewer |

A user in more than one group gets the highest role. A user in no group cannot log in with
Tailscale. Grafana sets the role at each login, so a change in a group applies at the next login
of that user. The grants must go to the node that runs tsidp (`idp`, with `tag:tsidp`). If they do
not, tsidp sends no groups, and nobody can log in with Tailscale.

Do these steps before the deploy:

1. In the tsidp UI at `https://idp.comet-stork.ts.net`, create a client with this redirect URI:
   `https://grafana.comet-stork.ts.net/login/generic_oauth`
2. In the Portainer stack variables, set `GRAFANA_OIDC_CLIENT_ID` and `GRAFANA_OIDC_CLIENT_SECRET`.
   The stack does not deploy without them.

If Tailscale login fails with a role error, check that the `idp` node has `tag:tsidp`, and that
your user is in one of the groups in the table above. Use the local login form to get in meanwhile.

## Deploy

Run these steps on minerva before the first deploy of this version.

1. Find the containerd socket:

   ```bash
   sudo ls -l /run/containerd/containerd.sock
   ```

   If the file does not exist, run `sudo find /run -name containerd.sock`. Then change the
   `source` of the cAdvisor socket mount to that path. If the path is wrong, the deploy stops with
   `bind source path does not exist`.

2. Create the dataset in the TrueNAS web UI, not with the `zfs` command. TrueNAS must manage
   the dataset. In **Datasets**, select `Fast`, then select **Add Dataset**:

   - Name: `Telemetry`
   - Quota for this dataset: 100 GiB
   - Atime: off

   Then check the dataset, and create the data directories:

   ```bash
   sudo zfs get -H -o value mounted,exec Fast/Telemetry  # Must print yes and on
   cd /mnt/Fast/Telemetry
   sudo mkdir -p loki prometheus alloy
   sudo chown 10001:10001 loki
   sudo chown 65534:65534 prometheus
   ```

   Make sure that the snapshot and replication tasks for `Fast/Configuration` do not include
   `Fast/Telemetry`. A recursive task on `Fast` includes it.

3. Look at the old configuration on the host. This deploy does not read these files, so a change
   that is only on the host stops working:

   ```bash
   cd /mnt/Fast/Configuration/grafana
   sudo cat prometheus/prometheus-docker-scraper.yaml loki/local-config.yaml promtail/docker-config.yaml
   ```

4. Turn on the Jellyfin metrics. Stop the Jellyfin stack, and set `<EnableMetrics>true</EnableMetrics>`
   in `/mnt/Fast/Configuration/jellyfin/config/config/system.xml`.

5. In Portainer, add these stack variables. A stack does not deploy without its value:

   | Stack | Variable | Value |
   |---|---|---|
   | sonarr | `SONARR_APIKEY` | Settings -> General in Sonarr |
   | radarr | `RADARR_APIKEY` | Settings -> General in Radarr |
   | bazarr | `BAZARR_APIKEY` | Settings -> General in Bazarr |

   The jellyfin stack uses the `JELLYFIN_APIKEY` value that it has now.

6. Redeploy the monitoring, jellyfin, sonarr, radarr and bazarr stacks in Portainer. Remove the old
   `promtail` container if Portainer keeps it.

## Check the deploy

```bash
# Each target must show "up".
curl -s http://localhost:9090/api/v1/targets | grep -o '"scrapeUrl":"[^"]*"\|"health":"[^"]*"'

# The number must be about the same as the result of: sudo docker ps -q | wc -l
curl -s -G http://localhost:9090/api/v1/query --data-urlencode 'query=count(container_memory_working_set_bytes{name=~".+"})'

# The result must not be empty. It shows ZFS and pressure metrics.
curl -s -G http://localhost:9090/api/v1/query --data-urlencode 'query=node_zfs_arc_size'
curl -s -G http://localhost:9090/api/v1/query --data-urlencode 'query=node_pressure_io_waiting_seconds_total'
```

Loki has no published port. To check the logs, open Grafana -> Explore and select the Loki data
source. The `container` label must list the containers of all stacks.

## Dashboards

The dashboards are in the **Homelab** folder in Grafana. Change them in the repo, not in Grafana,
because Grafana does not save changes to a provisioned dashboard. A dashboard change reaches Grafana
when the stack updates from Git and the image builds again. See `services/portainer/README.md`.

| Dashboard | Shows |
|---|---|
| Container Health | State, health, restarts and resources of all containers, host pressure, memory, disks, network, and error logs |
| Media Stack | Service health, each stream with its buffer and speed, playback errors, group playback, host load, library, Sonarr, Radarr and Bazarr counts and issues, and error logs |
| Overview | Anything wrong now, applications, load, and links to the other dashboards |
| Security | UniFi threats, unusual container behaviour, signs of compromise, and logins |
| Storage and Backups | Pool state, free space, disk activity and backups |
| GPU and Ollama | T400 memory and use, transcodes and Ollama requests |
| Network | minerva traffic, tailnet paths, traffic through Tailscale DERP relays, Wi-Fi clients and Roon symptoms |
| Flights | Status, tailnet probe, backups, resources and logs |
| Tandoor | Status, tailnet probe, backups, resources and logs |
| Karakeep | Status, tailnet probe, bookmarks, job queues, API errors and logs |
| Kavita | Status, tailnet probe, backups, warnings, resources and logs |
| GameScores | Rooms, players and games played, games that people asked for, status, tailnet probe, response time, restarts, errors, resources and logs |
| tsidp | Status, tailnet probe, logins for each service, errors, resources and logs |
| Media Interest | Watch time, top titles, directors, studios, genres, artists and albums, and watch history for the last 30 days. All Grafana users can see the watch history of each person. |
| Roon | Core starts, stream problems, Bluesound device connections and errors, core resources, host load, and logs |

The Media Stack, GPU and Ollama, and Network dashboards show Jellyfin events as marks on their panels: stream starts and stops, SyncPlay group waits, and library scans. To hide a type of mark, use the switches at the top of the dashboard.

The Tailnet path row on the Media Stack dashboard shows what Jellyfin sends over direct and DERP paths. It does not show which client. To find the client, run `tailscale status` on it, and look for `relay` on the `jellyfin` line.

Roon does not use the tailnet, so it does not use DERP.

To debug a watch party, open the Group playback row on the Media Stack dashboard, and select the time of the problem. Compare Group waits with SyncPlay events by person. The person and device with the most Kept the group waiting, Out of sync, Paused to catch up or Buffering events slow the group down. Then look at their stream in Now playing, and at the Buffer ahead panel. The table gets the person from `jellyfin_stream_info`, so a session that never played anything shows no person.

When a stream has a problem, look at the Streaming problems row, then compare the time with the Host row. The Roon dashboard has the same Host row. The core can restart in the Roon container, so use Core starts, not the container restart count.

`jellyfin_stream_info` has stream titles and user names in its labels. All LAN devices can read them from Prometheus.

Seerr and Themearr have no metrics endpoint. The Media Stack dashboard shows only their container
state, resources and logs.

## Storage and retention

The data is in the `Fast/Telemetry` dataset, mounted at `/mnt/Fast/Telemetry`.

| Store | Directory | Limit |
|---|---|---|
| Prometheus | `prometheus` | 30 days or 20 GB |
| Loki | `loki` | 30 days |
| Alloy read positions | `alloy` | Small |

The dataset has a 100 GB quota, because Loki has no size limit of its own. The quota stops
telemetry from filling the Fast pool, which also holds the Roon database. If the dataset reaches
the quota, Loki writes fail. Do not make this dataset part of the nightly replication. The data
has no backup, and a loss of `Fast` loses it.

## Tailnet probes

The `blackbox` service checks each application at its tailnet address each minute, so a failure can come from DNS, Tailscale, TLS or the application. The tailnet policy must allow access from the `grafana` node to each application. To add a target, change the `blackbox` job in `docker-compose.yaml`.

## Alerts

`grafana/provisioning/alerting/rules.yaml` defines the alerts, and Discord receives them. To change a threshold, change this file, and deploy again.

| Alert | Fires when |
|---|---|
| Container unhealthy | The health check fails for 15 minutes |
| Container crash loop | A container starts more than 2 times in 15 minutes, for 5 minutes |
| Container high CPU | A container uses more than 4 cores for 1 hour |
| Host high CPU | minerva uses more than 50% for 30 minutes |
| Low on space | Vault has under 2 TB, Fast under 100 GB, Fast/Telemetry under 10 GB, or boot-pool under 20 GB |
| Backup is old | Flights, Tandoor or Kavita has no backup in 26 hours |
| Jellyfin stream uses DERP | With a stream on, Jellyfin sends more than 10 kB/s through DERP for 3 minutes |

## UniFi logs

Alloy receives syslog on port 1514 of minerva, on UDP and TCP, and sends the lines to Loki.

Configure UniFi once. In **Settings -> Control Plane -> Integrations -> Activity Logging**, select **SIEM Server**, and enter `192.168.1.43` and port `1514`. The menu names can change between versions. Select only the log categories that you need, because all of the lines go to Loki and use the quota of `Fast/Telemetry`.

| Question | LogQL query |
|---|---|
| All UniFi lines | `{service="unifi-siem"}` |
| UniFi Network events | `{service="unifi-siem", product="UniFi Network"}` |
| Traffic to an address | `{service="unifi-siem"} \|= "85.11.167.7"` |

Loki uses the time that Alloy receives each line, because UniFi timestamps change between versions.

## Network exposure

Loki has no authentication, and it holds the logs of all containers. A log line can contain a
secret. Thus Loki has no published port. Only containers on the stack network can connect to it.
Use Grafana to read the logs.

Prometheus (9090) and node-exporter (9100) have no authentication, and all LAN devices can connect
to them. They hold metrics, not logs.

The exportarr exporters (9707) and `jellyfin-exporter` (9711) share the network of their Tailscale
sidecars. Tailnet devices can read them if the tailnet policy allows it. They show library counts
and health messages, and they show no API keys.

Port 1514 has no authentication, so all LAN devices can send lines to Loki through it. Treat these lines as a guide, not as proof. Do not forward this port from the internet.

The Tailscale sidecars serve health and metrics on all interfaces, at port 41234 in most stacks, so Prometheus can read them on `tailnet-local`. Tailnet devices can read them if the tailnet policy allows it. The minerva node has host networking, so all LAN devices can read port 41235. These ports show traffic counts, and no secrets.

`docker-state-exporter` reads the Docker socket. It makes only GET calls and it publishes no port.

## Agent access

Agents use a Grafana service account token for Loki and Prometheus. They do not connect to those
services directly. Create the token in Grafana: Administration -> Users and access -> Service
accounts. Give the service account the Viewer role, and give the token an expiry date.

## Useful queries

| Question | Query |
|---|---|
| Logs of a stack (LogQL) | `{stack="roon"}` |
| Roon stream errors (LogQL) | `{service="roonserver", logstream="file"} \|~ "media_slow\|NetworkUnreachable"` |
| Container restarts | `changes(container_start_time_seconds{name=~".+"}[1h]) > 0` |
| Top CPU containers | `topk(5, rate(container_cpu_usage_seconds_total{name=~".+"}[5m]))` |
| Top memory containers | `topk(5, container_memory_working_set_bytes{name=~".+"})` |
| Host IO pressure | `rate(node_pressure_io_waiting_seconds_total[5m])` |
| Host OOM kills | `increase(node_vmstat_oom_kill[1h])` |
