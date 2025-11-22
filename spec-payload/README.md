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

When registering the service on **Fedora**, execution failed with the following error:

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


### Option 2: Register as a User Service

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


### Option 3: Wrappers

If the above doesnt work, we can sort of hack it by creating a wrapper in a trusted place that is out of `/home` (could be `/usr/local/bin`)

so, we could do something like in a `.sh` file in `/usr/local/bin`:

```bash
#!/bin/bash
# Wrapper to launch the real Python script inside the project
exec /home/user/path/to/project/.venv/bin/python /home/user/path/to/project/main.py
```

and `chmod +x` it.

now, we can modify our `.service` as:

```
───────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: /etc/systemd/system/system-report.service
───────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ [Unit]
   2   │ Description=System Report (requires internet)
   3   │ After=network-online.target
   4   │ Wants=network-online.target
   5   │ 
   6   │ [Service]
   7   │ Type=simple
   8   │ ExecStart= ## <-- path to wrapper
   9   │ User=arhum
  10   │ WorkingDirectory= ## <-- will probably be needed if .envs are used.
  11   │ Restart=on-failure
  12   │ Environment=PYTHONUNBUFFERED=1
  13   │ 
  14   │ [Install]
  15   │ WantedBy=multi-user.target

```

Then, the traditional setup:

```bash
sudo systemctl daemon-reload
sudo systemctl start system-report.service
sudo systemctl enable system-report.service
```

and read logs:

```bash
journalctl -u system-report.service -f
```

This way we get to keep our git setup simple and no sync needed.

## About shutdown scripts

The key to understanding how to get a service to stop at shutdown prior to losing the network is knowing that the shutdown order is the reverse startup order. Therefore, your service should start after `network-online.target` while also having a dependency on `network-online.target`, because it requires the network to be up. Furthermore, there are `ExecStart=` and `ExecStop=` actions that you can define. Since you want the script to run at shutdown, which is when the service stops, you want to define `ExecStop=` pointing to your script.

To set this up, do the following:

- In the `[Unit]` section, create a `Requires=network-online.target` dependency
- Set the order to After=network-online.target.
- In the `[Service]` section, don't define an `ExecStart=` action.
- Set `RemainAfterExit=true`, because we didn't create an `ExecStart=` action.
- Finally, create an `ExecStop=` action pointing to your script, such as `ExecStop=/home/username/bin/testscript.sh.`

Remember, the shutdown order is the reverse startup order. Therefore, when your service is stopped, your script, which is placed in `ExecStop=`, will be run. And because we started this service after `network-online.target`, it will be shutdown before any services in `network-online.target` are shutdown