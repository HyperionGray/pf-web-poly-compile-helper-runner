#!/usr/bin/env bash
set -euo pipefail

echo "Creating MirrorOS container for continuous system snapshots..."

cat > /tmp/Dockerfile.mirror-os <<'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    rsync \
    btrfs-progs \
    zfsutils-linux \
    cron \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/*

RUN cat > /usr/local/bin/mirror-snapshot <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

snapshot_dir="/snapshots"
timestamp="$(date +%Y%m%d-%H%M%S)"

echo "Creating snapshot at $timestamp"

if [ -f /.btrfs ]; then
  btrfs subvolume snapshot /host "$snapshot_dir/btrfs-$timestamp"
elif [ -f /.zfs ]; then
  zfs snapshot rpool/ROOT/ubuntu@mirror-"$timestamp"
else
  rsync -aAX --delete /host/ "$snapshot_dir/rsync-$timestamp/"
fi

ls -t "$snapshot_dir" | tail -n +11 | xargs -r rm -rf

echo "Snapshot $timestamp completed"
SCRIPT

RUN chmod +x /usr/local/bin/mirror-snapshot
RUN echo "*/30 * * * * /usr/local/bin/mirror-snapshot" | crontab -

CMD ["cron", "-f"]
EOF

podman build -t localhost/pf-mirror-os:latest -f /tmp/Dockerfile.mirror-os .

echo "OK MirrorOS container created"
snap_root="${PF_SNAPSHOTS_ROOT:-/opt/pf-snapshots}"
echo "Start with: podman run -d --name mirror-os --volume /:/host:ro --volume ${snap_root}:/snapshots localhost/pf-mirror-os:latest"
