# Ship This First — pf-runner CLI

This archive contains a standalone CLI for PacketFS called **pf**.

## Install (dev)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Quick smoke
- Tail commit events (blocks):  
  `pf events-tail commit`
- Create + commit an iprog:  
  `pf iprog-run x1 --refs '[]' --meta '{}' --wait`
- Enqueue a pGPU job and follow:  
  `pf pgpu-run x1 --profile fast --follow`

Set `PF_ROOT=/mnt/pf` if running inside a container with `/pf` bind-mounted.

## Container (Quadlet) example
```ini
# /etc/containers/systemd/pf-dispatch.container
[Container]
Image=registry.fedoraproject.org/fedora:41
Volume=/pf:/mnt/pf:Z
Exec=/usr/bin/bash -lc 'python3 -m pip install pf-runner && PF_ROOT=/mnt/pf pf dispatch --topic commit'
Restart=always
```
