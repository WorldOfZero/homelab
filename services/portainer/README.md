# Portainer

Portainer deploys the stacks in this repo from Git.

## Automatic Git updates

Turn on automatic updates once for each stack. Then a push to `main` reaches minerva without a redeploy in Portainer.

In the stack, select **Editor**, then turn on **GitOps updates**:

- Mechanism: **Polling**
- Fetch interval: `5m`
- Force redeployment: off. If it is on, each poll deploys again, and each poll rebuilds the `build:` services.

The menu names can change between Portainer versions. These results are from a test on Portainer CE 2.45.1:

| Change in Git | Result of the Git update |
|---|---|
| Image, command or other service setting | Portainer recreates only that service |
| Inline `configs` content, with the label below | Portainer recreates only that service |
| Inline `configs` content, without the label | No change to the container, and the old config stays |
| Any commit, for a service with `build:` | Portainer builds the image again and recreates the service |
| A file that no service uses | Other services do not restart |

A commit anywhere in the repo starts an update of all stacks that use automatic updates. Each update also pulls all images, so a service with a mutable tag such as `:latest` can change after an unrelated commit. Pin the tag of a service that must not change.

## Inline configs

Compose does not recreate a container when only the content of a config changes. **Pull and redeploy** in the Portainer UI recreates all containers of the stack, but a Git update does not.

To make a Git update apply a config, put the content in a label of the service that uses it:

```yaml
configs:
  my-exporter:
    content: &my-exporter |
      print("my exporter")

services:
  exporter:
    labels:
      config-content: *my-exporter
    configs:
      - source: my-exporter
        target: /exporter.py
```

The label changes the service when the config changes. The content is visible in `docker inspect`, like an environment variable. cAdvisor does not export this label, because `-store_container_labels=false` is set.

The `ts-serve` configs do not have the label. A change to one recreates nothing, so use **Pull and redeploy** for that stack. With a label, the sidecar and all services that share its network would restart when the label is first added.
