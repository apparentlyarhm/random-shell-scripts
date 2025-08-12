#!/bin/bash

NATIVES="$HOME/.minecraft/versions/Prominence II RPG Hasturian Era Prominence II Hasturian Era-v3.1.53hf2/natives"

# 1) Display / session type
env | egrep 'DISPLAY|WAYLAND_DISPLAY|XDG_SESSION_TYPE' || true
echo "DISPLAY='$DISPLAY'  XDG_SESSION_TYPE='${XDG_SESSION_TYPE:-unset}'"

# 2) Kernel / OS info
uname -a

# 3) Check GL driver / renderer (may ask to install mesa-utils if missing)
if ! command -v glxinfo >/dev/null; then
  echo "glxinfo missing — install mesa-utils (sudo apt install mesa-utils) and re-run glxinfo -B"
else
  glxinfo -B
  glxinfo | egrep -i 'vendor|renderer|version|direct rendering'
fi

# 4) See if libglfw has unresolved deps
ldd "$NATIVES/libglfw.so" 2>/dev/null | egrep -i 'not found|undefined' || true

# 5) See what backends the libglfw mentions (quick clue if it was built for Wayland/EGL/etc)
strings "$NATIVES/libglfw.so" | egrep -i 'wayland|egl|glx|x11|wl_display|xcb' || true

# 6) Quick test: attempt to load the .so with python's ctypes to see immediate errors
python3 - <<'PY'
import ctypes,sys
p = "/home/arhum/.minecraft/versions/Prominence II RPG Hasturian Era Prominence II Hasturian Era-v3.1.53hf2/natives/libglfw.so"
try:
    ctypes.CDLL(p)
    print("python: loaded OK")
except OSError as e:
    print("python: failed to load:", e)
PY
