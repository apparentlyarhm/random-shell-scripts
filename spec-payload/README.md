# Weird thing with systemd that i learnt today

### Context

*This is a small reporting service that pings the backend running for my personal website v2's [specific page](https://nsfw.arhm.dev/goodstuff) to show my current system specs for.. reasons. The script uses `uv` and is expected to be platform independent. have tested it on windows 10, 11, and various linux distros. The following is just a reminder for me if i keep on distro hopping. The given `report.service` works fine on mint, needs small modification for `SELinux`*

---

## Start

Set the env:

```bash
cp .env.local .env
```

## Overview

This document records an observation regarding how **systemd services behave differently** between Fedora (with **SELinux**) and Linux Mint (with **AppArmor**).  
The difference primarily affects where executables can be placed when registered as **system services**.

---

## Issue Summary

When registering a Python-based systemd service on **Fedora**, execution failed with the following error:

```yaml
report.service: Unable to locate executable '/home/arhum/.../.venv/bin/python': Permission denied
report.service: Failed at step EXEC spawning ... Permission denied
audit[PID]: AVC avc: denied { read } ... tcontext=unconfined_u:object_r:user_home_t:s0 tclass=lnk_file permissive=0
```



However, the **same service file worked fine on Linux Mint**.

---

## Root "Cause"

Fedora uses **SELinux**, while Mint uses **AppArmor**.  
The key difference is in how these systems enforce **Mandatory Access Control (MAC)**:

| Aspect | Fedora (SELinux) | Mint (AppArmor) |
|--------|-------------------|----------------|
| Default MAC system | SELinux | AppArmor |
| Enforcement mode | Mandatory, system-wide | Per-application profiles |
| Policy granularity | Label-based (file + process contexts) | Path-based profiles |
| Execution from `/home` | ❌ Blocked for system services | ✅ Allowed (no restrictive profile) |

SELinux prevents system daemons (running under `init_t` or similar contexts) from executing binaries located in the user’s home directory (`user_home_t`), even if file permissions are open.

---

## Verification

The AVC log confirms the mismatch between service and file contexts:

```yaml
scontext=system_u:system_r:init_t:s0
tcontext=unconfined_u:object_r:user_home_t:s0
```


This means the **system service** (init_t) attempted to execute a binary labeled as **user_home_t**, which SELinux denies by default.

---

## Solutions

### Option 1: Move code outside of `/home`
Place your virtual environment and script under a trusted location like `/opt` or something. tedious. needs script update to change all locations.


### Option 1: Register as a User Service

If the service is meant to run only under your user account, create:

```yaml
~/.config/systemd/user/report.service
```

and remove the `User=` field.

then:
```bash
systemctl --user daemon-reload
systemctl --user enable report.service
systemctl --user start report.service
```
(notice the `--user` here)

