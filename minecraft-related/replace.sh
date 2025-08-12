#!/bin/bash


# one of the native dependencies of the mod, the `so` file highlighted is getting overwritten automatically and the jvm arguments are not taking effect
# so in order to force mc to use the file i downloaded, we set up a watch and copy if write is detected (and finished)


WATCH_DIR="/home/arhum/.minecraft/versions/Prominence II RPG Hasturian Era Prominence II Hasturian Era-v3.1.53hf2/natives"
PATCHED_FILE="/home/arhum/Downloads/libglfw.so"
TARGET_FILE="libglfw.so"


echo "[Watcher] Waiting for $TARGET_FILE to be fully written..."

inotifywait -e close_write "$WATCH_DIR/$TARGET_FILE"

# Once closed, replace it
cp -f "$PATCHED_FILE" "$WATCH_DIR/$TARGET_FILE"
echo "[Watcher] Replacement complete."