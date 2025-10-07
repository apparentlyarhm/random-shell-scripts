#!/bin/bash

# Sum all sizes in bytes
bytes=$(gcloud artifacts files list \
  --repository="arhum-s-spotistats" \
  --location="asia-south2" \
  --format="value(sizeBytes)" \
  | awk '{s+=$1} END {print s}')

# If nothing returned
if [ -z "$bytes" ]; then
  echo "No files found or repository is empty."
  exit 0
fi

# Print in bytes, MB, GB (using awk for floats)
echo "Total size:"
echo "$bytes bytes"
echo "$(awk "BEGIN {print $bytes/1024/1024}") MB"
echo "$(awk "BEGIN {print $bytes/1024/1024/1024}") GB"

