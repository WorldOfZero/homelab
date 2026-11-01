# Monitoring stack

Grafana, Loki, Prometheus, Alloy, cAdvisor and node-exporter for minerva.

| Data | Source | Coverage |
|---|---|---|
| Container logs | Alloy reads the Docker API | All containers, with no label on the service |
| Roon log file | Alloy reads `RoonServer_log.txt` | Roon stream errors do not go to the container log |
| Container metrics | cAdvisor | All containers: CPU, memory, restarts, IO |
| Host metrics | node-exporter | minerva: CPU, memory, pressure, disks, NICs, ZFS |
| Docker state | `docker-state-exporter` | All containers: state, health, restarts, OOM kills, exit code |
| Media metrics | exportarr, `jellyfin-exporter`, Jellyfin `/metrics` | Sonarr, Radarr, Bazarr, Jellyfin |
| Other application metrics | Not configured | See [[add-app-metrics-exporters]] |

The Alloy, Prometheus and Loki configuration is in the `configs` block of
`docker-compose.yaml`, so a redeploy applies it. Copy no files to the host for them. Grafana
provisioning still comes from `/mnt/Fast/Configuration/grafana/grafana/provisioning`.

## Access

Grafana is at `https://grafana.comet-stork.ts.net` on the tailnet, and at port 3001 on the LAN. A
Tailscale sidecar gives Grafana its name. Set `TS_AUTHKEY` in the Portainer stack variables before
you deploy. The `tailnet-local` network must exist. See `ENVIRONMENT.md`.

## Login

Grafana uses tsidp for Tailscale login. The browser must be on the tailnet. The local login form
stays as a way in when tsidp is down. Service account tokens do not use tsidp.

The configured `GRAFANA_ADMIN_EMAIL` user gets the Admin role, and all other tailnet users get the
Viewer role.

Do these steps before the deploy:

1. In the tsidp UI at `https://idp.comet-stork.ts.net`, create a client with this redirect URI:
   `https://grafana.comet-stork.ts.net/login/generic_oauth`
2. In the Portainer stack variables, set `GRAFANA_OIDC_CLIENT_ID`, `GRAFANA_OIDC_CLIENT_SECRET` and
   `GRAFANA_ADMIN_EMAIL`. The stack does not deploy without them.

If you get the Viewer role, read your email in Grafana -> Profile. Set `GRAFANA_ADMIN_EMAIL` to that
value, and deploy again.

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

4. Copy the dashboards to the host. Grafana reads them from the host, not from the compose file.
   Repeat this step when a dashboard changes:

   ```bash
   sudo cp -r services/grafana/grafana/provisioning/dashboards /mnt/Fast/Configuration/grafana/grafana/provisioning/
   sudo chown -R 472:472 /mnt/Fast/Configuration/grafana/grafana/provisioning/dashboards
   ```

5. Turn on the Jellyfin metrics. Stop the Jellyfin stack, and set `<EnableMetrics>true</EnableMetrics>`
   in `/mnt/Fast/Configuration/jellyfin/config/config/system.xml`.

6. In Portainer, add these stack variables. A stack does not deploy without its value:

   | Stack | Variable | Value |
   |---|---|---|
   | sonarr | `SONARR_APIKEY` | Settings -> General in Sonarr |
   | radarr | `RADARR_APIKEY` | Settings -> General in Radarr |
   | bazarr | `BAZARR_APIKEY` | Settings -> General in Bazarr |

   The jellyfin stack uses the `JELLYFIN_APIKEY` value that it has now.

7. Redeploy the monitoring, jellyfin, sonarr, radarr and bazarr stacks in Portainer. Remove the old
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
because Grafana does not save changes to a provisioned dashboard.

| Dashboard | Shows |
|---|---|
| Container Health | State, health, restarts and resources of all containers, host pressure, memory, disks, network, and error logs |
| Media Stack | Service health, Jellyfin streams and library, Sonarr, Radarr and Bazarr counts and issues, resources, and error logs |

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

## Network exposure

Loki has no authentication, and it holds the logs of all containers. A log line can contain a
secret. Thus Loki has no published port. Only containers on the stack network can connect to it.
Use Grafana to read the logs.

Prometheus (9090) and node-exporter (9100) have no authentication, and all LAN devices can connect
to them. They hold metrics, not logs.

The exportarr exporters (9707) and `jellyfin-exporter` (9711) share the network of their Tailscale
sidecars. Tailnet devices can read them if the tailnet policy allows it. They show library counts
and health messages, and they show no API keys.

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
