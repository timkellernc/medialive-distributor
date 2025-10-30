#!/bin/bash

# MediaLive Distributor - Testing & Validation Script
# Tests the application deployment and basic functionality

set -e

echo "=== MediaLive Distributor Test Suite ==="
echo

API_URL="http://localhost:8000"
PASSED=0
FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=$4
    local data=$5
    
    echo -n "Testing: $name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $http_code)"
        echo "Response: $body"
        ((FAILED++))
        return 1
    fi
}

# Check if application is running
echo "Checking if application is running..."
if ! curl -s "$API_URL/api/health" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Application is not responding at $API_URL${NC}"
    echo "Please start the application first:"
    echo "  Docker: docker-compose up -d"
    echo "  Systemd: sudo systemctl start medialive-distributor"
    exit 1
fi
echo -e "${GREEN}✓ Application is running${NC}"
echo

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/api/health" 200

# Test 2: List Channels (empty)
test_endpoint "List Channels (empty)" "GET" "/api/channels" 200

# Test 3: Create Channel
echo -n "Creating test channel... "
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/api/channels" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Channel",
        "rtp_ip": "127.0.0.1",
        "rtp_port": 15000,
        "outputs": []
    }')

if echo "$CREATE_RESPONSE" | grep -q '"id"'; then
    CHANNEL_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ PASS${NC} (Channel ID: $CHANNEL_ID)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $CREATE_RESPONSE"
    ((FAILED++))
    exit 1
fi

# Test 4: Get Channel Details
test_endpoint "Get Channel Details" "GET" "/api/channels/$CHANNEL_ID" 200

# Test 5: Add Output to Channel
echo -n "Adding SRT output... "
OUTPUT_RESPONSE=$(curl -s -X POST "$API_URL/api/channels/$CHANNEL_ID/outputs" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test SRT Output",
        "protocol": "srt",
        "url": "srt://127.0.0.1:9000?streamid=test"
    }')

if echo "$OUTPUT_RESPONSE" | grep -q '"output_id"'; then
    OUTPUT_ID=$(echo "$OUTPUT_RESPONSE" | grep -o '"output_id":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ PASS${NC} (Output ID: $OUTPUT_ID)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $OUTPUT_RESPONSE"
    ((FAILED++))
fi

# Test 6: Add RTMP Output
echo -n "Adding RTMP output... "
OUTPUT2_RESPONSE=$(curl -s -X POST "$API_URL/api/channels/$CHANNEL_ID/outputs" \
    -H "Content-Type: application/json" \
    -d '{
        "protocol": "rtmp",
        "url": "rtmp://127.0.0.1:1935/live/test"
    }')

if echo "$OUTPUT2_RESPONSE" | grep -q '"output_id"'; then
    OUTPUT2_ID=$(echo "$OUTPUT2_RESPONSE" | grep -o '"output_id":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ PASS${NC} (Output ID: $OUTPUT2_ID)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $OUTPUT2_RESPONSE"
    ((FAILED++))
fi

# Test 7: Remove Output
test_endpoint "Remove Output" "DELETE" "/api/channels/$CHANNEL_ID/outputs/$OUTPUT_ID" 200

# Test 8: Delete Channel
test_endpoint "Delete Channel" "DELETE" "/api/channels/$CHANNEL_ID" 200

# Test 9: Verify Channel Deleted
test_endpoint "Verify Channel Deleted" "GET" "/api/channels/$CHANNEL_ID" 404

# Test 10: Web Interface
echo -n "Testing Web Interface... "
WEB_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/")
WEB_CODE=$(echo "$WEB_RESPONSE" | tail -n1)
WEB_BODY=$(echo "$WEB_RESPONSE" | head -n-1)

if [ "$WEB_CODE" -eq 200 ] && echo "$WEB_BODY" | grep -q "MediaLive Distributor"; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP 200, content valid)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $WEB_CODE)"
    ((FAILED++))
fi

# Summary
echo
echo "=== Test Results ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"
echo

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
