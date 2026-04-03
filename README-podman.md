# Podman Dev Workflow for cdr-aws-local

This guide walks through a Podman-first workflow for this repository:
1. Manually build the devcontainer image.
2. Start the devcontainer and supporting services with Podman Compose.
3. Attach to the running devcontainer from VS Code.
4. Clone a desired PySpark project from GitHub inside the devcontainer.

## Prerequisites

- Podman installed (Podman Desktop or CLI)
- VS Code installed
- VS Code extension: Dev Containers (`ms-vscode-remote.remote-containers`)

If you are on macOS, make sure the Podman VM is running:

```bash
podman machine init   # run once if needed
podman machine start
podman info
```

## 1) Build the devcontainer image manually

From the repository root:

```bash
podman build -f Dockerfile.devcontainer -t cdr-aws-developer .
```

This must succeed before starting Compose, because the `devcontainer` service uses the local image tag `cdr-aws-developer`.

## 2) Start the devcontainer and all supporting services

From the same repository root:

```bash
podman compose up -d
```

This starts:
- moto
- glue
- trino
- opensearch
- opensearch-dashboards
- devcontainer

Check status:

```bash
podman compose ps
```

Optional logs:

```bash
podman compose logs -f devcontainer
```

## 3) Attach to the running devcontainer from VS Code

1. Open VS Code.
2. Press `Cmd+Shift+P` and run: **Dev Containers: Attach to Running Container...**
3. Select the running container for the `devcontainer` service.
   - The name usually contains `devcontainer` and the project folder name.
4. After VS Code attaches, open folder path:
   - `/workspace/cdr-aws-local`

You are now in the containerized development environment.

## 4) Clone a desired PySpark project from GitHub

Inside the VS Code terminal in the attached container:

```bash
cd /workspace
git clone https://github.com/<org>/<pyspark-project>.git
cd <pyspark-project>
```

If your repo requires SSH:

```bash
git clone git@github.com:<org>/<pyspark-project>.git
```

## Useful lifecycle commands

Stop everything:

```bash
podman compose down
```

Stop and remove volumes:

```bash
podman compose down -v
```

Rebuild only the devcontainer image after Dockerfile changes:

```bash
podman build -f Dockerfile.devcontainer -t cdr-aws-developer .
podman compose up -d
```
