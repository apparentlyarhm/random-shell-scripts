#!/bin/bash

# This script compares cold start times between two of my Google Cloud Run services
# it is assumed that the gcloud cli is installed and conifigured with the correct project

# based on a little research, the cost implications of redeploying multiple times is negligible
:<<INFO
Because we change the configuration (dummy var), Cloud Run is forced to create a new, distinct revision.

-- Why This Guarantees a Cold Start--

A Cloud Run Revision is the fundamental unit of deployment.

    - The previous revision (-rev-00001) might have warm instances sitting around.
    - Your new revision (-rev-00002) has zero instances running. It's brand new.
    - When your curl command hits the service URL, Cloud Run routes the request to the latest revision, which is now -rev-00002.
    - Since -rev-00002 has no running instances, Cloud Run must start a new container from scratch. This is your guaranteed cold start.
INFO

# --- Configuration ---
REGION="asia-south2"
EXPRESS_SERVICE="spotify-proxy"
GO_SERVICE="go-prxy"
ITERATIONS=20

EXPRESS_RESULTS_FILE="eres.txt"
GO_RESULTS_FILE="gres.txt"

echo "--- Testing Express App ---"
for i in $(seq 1 $ITERATIONS); do
  echo "Iteration $i..."
  
  # Deploy a new revision by changing an environment variable to force a cold start
  # The value of DUMMY_VAR doesn't matter, it just needs to change.
  gcloud run services update $EXPRESS_SERVICE --region=$REGION --update-env-vars="DUMMY_VAR=$i" --quiet
  SERVICE_URL=$(gcloud run services describe $EXPRESS_SERVICE --region=$REGION --format='value(status.url)')

  echo "Pinging $SERVICE_URL..."
  curl -o /dev/null -s -w "Express Cold Start TTFB dep #$i: %{time_starttransfer}s\n" "$SERVICE_URL/ping" >> $EXPRESS_RESULTS_FILE
  
  sleep 3
done


echo -e "\n--- Testing Go App ---"
for i in $(seq 1 $ITERATIONS); do
  echo "Iteration $i..."
  
  gcloud run services update $GO_SERVICE --region=$REGION --update-env-vars="DUMMY_VAR=$i" --quiet
  SERVICE_URL=$(gcloud run services describe $GO_SERVICE --region=$REGION --format='value(status.url)')

  echo "Pinging $SERVICE_URL..."
  curl -o /dev/null -s -w "Go Cold Start TTFB dep #$i: %{time_starttransfer}s\n" "$SERVICE_URL/ping" >> $GO_RESULTS_FILE

  sleep 3
done