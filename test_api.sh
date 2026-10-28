#!/bin/bash
set -e

# Default URL is http://localhost:5000, or user can pass URL as first argument
TARGET_URL="${1:-http://localhost:5000}"

echo "=========================================================="
echo "Testing Application Endpoints at: $TARGET_URL"
echo "=========================================================="

# 1. Test Root Endpoint
echo ""
echo "[Test 1] Testing Root '/' Endpoint..."
ROOT_RESPONSE=$(curl -s "$TARGET_URL/")
echo "Response: $ROOT_RESPONSE"
if [[ "$ROOT_RESPONSE" == *"Welcome to the Flask app"* ]]; then
    echo "✅ Root endpoint test passed!"
else
    echo "❌ Root endpoint test failed!"
fi

# 2. Test Healthz Endpoint
echo ""
echo "[Test 2] Testing Health '/healthz' Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$TARGET_URL/healthz")
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tail -n 1 | cut -d':' -f2)
echo "Status: $HEALTH_STATUS"
echo "Body: $HEALTH_BODY"
if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo "✅ Health check test passed!"
else
    echo "❌ Health check test failed!"
fi

# 3. Test POST /data
echo ""
echo "[Test 3] Testing POST '/data' Endpoint..."
TIMESTAMP=$(date +"%Y-%m-%d %T")
POST_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "{\"candidate\":\"Shivansh Dwivedi\",\"role\":\"Intern Assignment\",\"timestamp\":\"$TIMESTAMP\"}" \
  "$TARGET_URL/data")
POST_BODY=$(echo "$POST_RESPONSE" | sed '$d')
POST_STATUS=$(echo "$POST_RESPONSE" | tail -n 1 | cut -d':' -f2)
echo "Status: $POST_STATUS"
echo "Body: $POST_BODY"
if [ "$POST_STATUS" -eq 201 ]; then
    echo "✅ POST /data test passed!"
else
    echo "❌ POST /data test failed!"
fi

# 4. Test GET /data
echo ""
echo "[Test 4] Testing GET '/data' Endpoint..."
GET_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$TARGET_URL/data")
GET_BODY=$(echo "$GET_RESPONSE" | sed '$d')
GET_STATUS=$(echo "$GET_RESPONSE" | tail -n 1 | cut -d':' -f2)
echo "Status: $GET_STATUS"
echo "Body: $GET_BODY"
if [ "$GET_STATUS" -eq 200 ] && [[ "$GET_BODY" == *"Shivansh Dwivedi"* ]]; then
    echo "✅ GET /data test passed (Data verified in MongoDB)!"
else
    echo "❌ GET /data test failed!"
fi

echo ""
echo "=========================================================="
echo "All functional tests finished successfully! 🎉"
echo "=========================================================="
