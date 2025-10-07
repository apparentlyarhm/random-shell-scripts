#!/bin/bash

USERNAME="name"
SUBNET="192.168.0.*"

echo "[+] Scanning for 'archserver' in subnet $SUBNET..."

MATCH=$(nmap -sL $SUBNET 2>/dev/null | grep archserver)

if [ -z "$MATCH" ]; then
    echo "[-] No device with hostname containing 'archserver' found."
    exit 1
fi

# Extract IP from the match
IP=$(echo "$MATCH" | awk -F '[()]' '{print $2}')

echo "[+] Found host: $MATCH"
echo "[+] Attempting to SSH into $IP as '$USERNAME'..."
echo

ssh "$USERNAME@$IP"

