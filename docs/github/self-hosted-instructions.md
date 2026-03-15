1 reference

Copilot said: ### 4 concurrent jobs on a 32-thread
4 concurrent jobs on a 32-thread / 64GB Ubuntu 24.04 VM: recommended layout

You can do this cleanly by running 4 separate runner instances on the same VM, each with its own work directory and service.
1) Labeling scheme (keep it simple + future-proof)

Use one shared “pool” label that workflows target:

    big → “any big self-hosted runner”

Optionally add informational labels (not required for routing):

    threadripper, tr32, ram64

Workflow target (standard across all repos/orgs):
YAML

runs-on: [self-hosted, linux, x64, big]

That will spread jobs across all runners that have big.
2) Install 4 runner instances (one host, four directories)

On the VM:
bash

sudo useradd -m -s /bin/bash github-runner || true
sudo apt-get update
sudo apt-get install -y curl ca-certificates tar gzip jq git podman python3 python3-venv
sudo su - github-runner

Create four directories:
bash

mkdir -p ~/runners
cd ~/runners
for i in 1 2 3 4; do
  mkdir -p "actions-runner-$i"
done

For each runner i, download/extract the runner tarball into that directory (you can reuse the same tarball):
bash

# Download once
cd ~/runners
curl -L -o actions-runner-linux-x64.tar.gz <URL_FROM_GITHUB_UI>

for i in 1 2 3 4; do
  cd ~/runners/actions-runner-$i
  tar xzf ../actions-runner-linux-x64.tar.gz
done

Now configure each runner (use the exact --url + token GitHub gives you; names must be unique):
bash

for i in 1 2 3 4; do
  cd ~/runners/actions-runner-$i
  ./config.sh \
    --url <URL_FROM_GITHUB_UI> \
    --token <REGISTRATION_TOKEN> \
    --name tr-vm-01-$i \
    --labels self-hosted,linux,x64,big,threadripper,tr32,ram64 \
    --work _work-$i \
    --unattended
done

Install/start each as a service:
bash

for i in 1 2 3 4; do
  cd ~/runners/actions-runner-$i
  sudo ./svc.sh install
  sudo ./svc.sh start
done

Check status:
bash

for i in 1 2 3 4; do
  cd ~/runners/actions-runner-$i
  sudo ./svc.sh status
done

You should now see 4 separate runners in the Enterprise UI, all in your big-machines runner group.
3) Resource sanity check (so 4 jobs don’t thrash)

With 64GB RAM, 4 concurrent jobs usually works great if your jobs aren’t extreme memory hogs. If you run very heavy builds/tests, consider:

    setting job-level parallelism limits (don’t run “make -j32” in four jobs at once)
    using smaller internal parallelism per job (e.g., -j8), since 4 jobs × 8 threads ≈ 32 threads total

4) Nice-to-have hardening for persistent runners

Add a periodic cleanup workflow (or a cron on the VM) to prune Podman and old work dirs. For example on the VM:
bash

podman system prune -af --volumes

(Only do this if you’re sure you won’t break caches you care about.)
5) Smoke test workflow (run in each org once)

In a repo allowed to use big-machines, add:
YAML

name: self-hosted-smoke
on: workflow_dispatch
jobs:
  smoke:
    runs-on: [self-hosted, linux, x64, big]
    steps:
      - run: |
          echo "host=$(hostname)"
          nproc
          free -h
          podman --version

If you tell me your enterprise slug (what shows in the runner registration --url), I can give you a copy/paste script that installs all 4 runners in one go and prompts only for the registration token.
TeamHG-Memex Instructions
You said: Sure it's Hyperion Gray LLC
Sure it's Hyperion Gray LLC
1 reference

1 reference

Copilot said: I can’t derive the enterprise registration URL

I can’t derive the enterprise registration URL from the display name “Hyperion Gray LLC” (GitHub uses an enterprise slug, and it may differ). Here’s how to get the exact value and then a safe one-shot setup.
1) Find your enterprise “slug” / runner URL (authoritative)

Go to:

    Enterprise account → Settings → Actions → Runners → New self-hosted runner

On that page, GitHub will show a command like:
bash

./config.sh --url https://github.com/enterprises/<SLUG> --token <TOKEN> ...

Copy the --url exactly. That’s the only URL you should use.
2) One-shot installer for 4 runners (Ubuntu 24.04)

Paste this as your github-runner user (it will prompt you for the URL and token once). This creates 4 runner instances in ~/runners/actions-runner-{1..4} with separate work dirs.
bash

set -euo pipefail

read -r -p "Enterprise runner URL (from GitHub UI, e.g. https://github.com/enterprises/SLUG): " GH_URL
read -r -p "Registration token (from GitHub UI): " GH_TOKEN

RUNNER_NAME_PREFIX="tr-vm-01"
LABELS="self-hosted,linux,x64,big,threadripper,tr32,ram64"

mkdir -p ~/runners
cd ~/runners

if [ ! -f actions-runner-linux-x64.tar.gz ]; then
  echo "Download the runner tarball URL from GitHub UI and place it here as:"
  echo "  ~/runners/actions-runner-linux-x64.tar.gz"
  echo "Then re-run this script."
  exit 1
fi

for i in 1 2 3 4; do
  dir="actions-runner-$i"
  mkdir -p "$dir"
  cd "$dir"

  # Extract only if it doesn't look installed
  if [ ! -f ./config.sh ]; then
    tar xzf ../actions-runner-linux-x64.tar.gz
  fi

  ./config.sh \
    --url "$GH_URL" \
    --token "$GH_TOKEN" \
    --name "${RUNNER_NAME_PREFIX}-${i}" \
    --labels "$LABELS" \
    --work "_work-${i}" \
    --unattended

  sudo ./svc.sh install
  sudo ./svc.sh start

  cd ..
done

echo "Done. Check Enterprise → Actions → Runners for 4 online runners."

Before running that script

Do these once (as root):
bash

sudo apt-get update
sudo apt-get install -y curl ca-certificates tar gzip jq git podman
sudo useradd -m -s /bin/bash github-runner || true
sudo usermod -aG sudo github-runner   # optional; only needed because svc.sh uses sudo

Then switch to the runner user:
bash

sudo su - github-runner

And download the runner tarball (use the URL from GitHub UI):
bash

mkdir -p ~/runners
cd ~/runners
curl -L -o actions-runner-linux-x64.tar.gz <RUNNER_TARBALL_URL_FROM_GITHUB_UI>

3) Enterprise-wide usage across your orgs

Once those runners appear in the enterprise UI:

    Put them in runner group big-machines
    Set runner group access to the repos across:
        P4X-ng
        hyp3ri0n-ng
        HyperionGray
        TeamHG-Memex

Then any workflow can target:
YAML

runs-on: [self-hosted, linux, x64, big]

4) Quick note about tokens

The registration token is short-lived and only used for registration. After runners are registered, they keep working without you re-entering it.

If you paste the exact --url ... line GitHub shows you on the “New self-hosted runner” page (just the URL part, no token), I can tailor the script to your exact enterprise URL and recommended label/group names.
TeamHG-Memex Instructions
You said: https://github.com/enterprises/hyperion-gray-llc
https://github.com/enterprises/hyperion-gray-llc 
1 reference

1 reference

Copilot said: Perfect — that’s the enterprise URL you’ll

Perfect — that’s the enterprise URL you’ll use:

https://github.com/enterprises/hyperion-gray-llc

Below is a copy/paste setup for 4 concurrent self-hosted runners on Ubuntu 24.04 (persistent runners, systemd services), labeled so all your repos can target them as big.
0) On GitHub (Enterprise UI)

Enterprise → Settings → Actions → Runners → New self-hosted runner (Linux)

Grab:

    the runner tarball download URL (or just follow their commands)
    the registration token (short-lived)

Also create/confirm your Runner group big-machines and allow the repos from:

    P4X-ng
    hyp3ri0n-ng
    HyperionGray
    TeamHG-Memex

1) On the Ubuntu VM: install prerequisites
bash

sudo apt-get update
sudo apt-get install -y curl ca-certificates tar gzip jq git podman
sudo useradd -m -s /bin/bash github-runner || true

Switch to the runner user:
bash

sudo su - github-runner

2) Download the runner package once

Use the tarball URL GitHub shows on the runner setup page:
bash

mkdir -p ~/runners
cd ~/runners
curl -L -o actions-runner-linux-x64.tar.gz <TARBALL_URL_FROM_GITHUB_UI>

3) Configure + install 4 runner instances

This script will prompt for the registration token once, then register 4 runners:
bash

set -euo pipefail

ENTERPRISE_URL="https://github.com/enterprises/hyperion-gray-llc"
read -r -p "Registration token (from GitHub UI): " REG_TOKEN

RUNNER_NAME_PREFIX="tr-vm-01"
LABELS="self-hosted,linux,x64,big,threadripper,tr32,ram64"

mkdir -p ~/runners
cd ~/runners

if [ ! -f actions-runner-linux-x64.tar.gz ]; then
  echo "Missing ~/runners/actions-runner-linux-x64.tar.gz"
  exit 1
fi

for i in 1 2 3 4; do
  dir="actions-runner-$i"
  mkdir -p "$dir"
  cd "$dir"

  if [ ! -f ./config.sh ]; then
    tar xzf ../actions-runner-linux-x64.tar.gz
  fi

  ./config.sh \
    --url "$ENTERPRISE_URL" \
    --token "$REG_TOKEN" \
    --name "${RUNNER_NAME_PREFIX}-${i}" \
    --labels "$LABELS" \
    --work "_work-${i}" \
    --unattended

  sudo ./svc.sh install
  sudo ./svc.sh start

  cd ..
done

echo "Done. Verify in Enterprise → Actions → Runners."

    You’ll be asked for your sudo password when installing services. If you’d rather avoid granting sudo to github-runner, you can run the svc.sh install/start lines as root instead.

4) Target these runners from workflows

In any repo that’s allowed to use the big-machines runner group:
YAML

runs-on: [self-hosted, linux, x64, big]

5) Quick smoke test workflow (recommended)

Add this to a test repo:
YAML

name: self-hosted-smoke
on: workflow_dispatch
jobs:
  smoke:
    runs-on: [self-hosted, linux, x64, big]
    steps:
      - run: |
          echo "host=$(hostname)"
          nproc
          free -h
          podman --version

If you tell me whether the VM hostname should appear in the runner name (e.g. tr-$(hostname)-1), I can adjust the script so it auto-names runners uniquely without manual edits.