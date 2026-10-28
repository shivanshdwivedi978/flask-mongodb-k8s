#!/bin/bash
# HPA Load Test Script
# Generates continuous concurrent requests to trigger CPU utilization > 70%
# and verify scaling from 2 to up to 5 replicas.

TARGET_URL="${1:-http://localhost:5000}"
DURATION_SECONDS="${2:-120}"

echo "=========================================================="
echo "Starting HPA High-Load Simulation against: $TARGET_URL"
echo "Duration: ${DURATION_SECONDS}s"
echo "Open another terminal and watch autoscaling with:"
echo "  kubectl get hpa flask-hpa --watch"
echo "  kubectl get pods -l app=flask-app --watch"
echo "=========================================================="

END_TIME=$((SECONDS + DURATION_SECONDS))

# Function to spam requests
spam_requests() {
  while [ $SECONDS -lt $END_TIME ]; do
    curl -s "$TARGET_URL/" > /dev/null
    curl -s -X POST -H "Content-Type: application/json" -d '{"load_test":true}' "$TARGET_URL/data" > /dev/null
    curl -s "$TARGET_URL/data" > /dev/null
  done
}

echo "Launching 20 concurrent load workers..."
for i in {1..20}; do
  spam_requests &
done

# Wait for all background workers to finish
wait
echo ""
echo "=========================================================="
echo "Load test completed! Check 'kubectl get hpa' and 'kubectl get pods' to view scaled replicas."
echo "=========================================================="
