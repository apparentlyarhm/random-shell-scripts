#!/bin/bash

# Set the path to the Steam client installation.
# Proton needs this to know where the Steam runtime and related files are.
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.steam/steam"

# Set the path for Proton's compatibility data.
# Here we reuse Legendary’s global compatdata folder so all games share the same prefix.
export STEAM_COMPAT_DATA_PATH="$HOME/.legendary/compatdata/global"

# Run Proton (Experimental build) with the arguments passed to this script.
# "$@" ensures any command-line arguments (like the path to the game exe)
# are forwarded properly to Proton.
# This lets Legendary launch games using Proton as if they were Steam games.
"/media/gamedisk2/SteamLibrary/steamapps/common/Proton - Experimental/proton" run "$@"
