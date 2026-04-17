# pf-runner Installation Guide

pf-runner installation is now standardized on **Debian `.deb` packages only**.

## 1) Build the package

```bash
./deb/build-deb.sh 1.0.0
```

## 2) Install the package

```bash
sudo dpkg -i deb/build/pf-runner_1.0.0.deb
sudo apt-get install -f -y
```

## 3) Verify

```bash
pf --version
pf list
pf --help
```

## Uninstall

```bash
sudo dpkg -r pf-runner
```

## Support

For issues and questions, open an issue in this repository.
