#!/bin/bash

# MarketMindAI Application Test Script
# This script runs comprehensive tests on all components

echo "🧪 MarketMindAI Application Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
TOTAL=0

# Function to print colored output
print_status() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    ((TOTAL++))
}

# Function to test API endpoint
test_api() {
    local name=$1
    local url=$2
    local expected=$3
    local method=${4:-GET}
    local data=$5
    
    print_test "Testing $name..."
    
    if [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s --max-time 10 -X POST "$url" -H "Content-Type: application/json" -d "$data")
        else
            response=$(curl -s --max-time 10 -X POST "$url")
        fi
    else
        response=$(curl -s --max-time 10 "$url")
    fi
    
    if echo "$response" | grep -q "$expected"; then
        print_status "$name endpoint working"
        echo "  Response: $(echo "$response" | head -c 100)..."
    else
        print_fail "$name endpoint failed"
        echo "  Response: $(echo "$response" | head -c 100)..."
    fi
}

echo ""
echo "🔍 Starting Test Suite..."
echo ""

# Test 1: PostgreSQL Container
print_test "Checking PostgreSQL container..."
if docker ps --filter "name=marketmindai-postgres" --filter "status=running" --quiet | grep -q .; then
    print_status "PostgreSQL container is running"
    
    # Test database connectivity
    if docker exec marketmindai-postgres pg_isready -U marketmindai_user -d marketmindai >/dev/null 2>&1; then
        print_status "PostgreSQL is accepting connections"
    else
        print_fail "PostgreSQL is not accepting connections"
    fi
else
    print_fail "PostgreSQL container is not running"
fi

# Test 2: Backend Health
test_api "Backend Health" "http://localhost:8001/api/health" "healthy"

# Test 3: Database Connectivity via API
test_api "Database Connectivity" "http://localhost:8001/api/debug/connectivity" "success"

# Test 4: Authentication - SuperAdmin Login
test_api "SuperAdmin Login" "http://localhost:8001/api/auth/login" "access_token" "POST" '{"email":"superadmin@marketmindai.com","password":"superadmin123"}'

# Test 5: Authentication - Admin Login
test_api "Admin Login" "http://localhost:8001/api/auth/login" "access_token" "POST" '{"email":"admin@marketmindai.com","password":"admin123"}'

# Test 6: Authentication - User Login
test_api "User Login" "http://localhost:8001/api/auth/login" "access_token" "POST" '{"email":"user@marketmindai.com","password":"password123"}'

# Test 7: Tools API
test_api "Tools API" "http://localhost:8001/api/tools" "tools"

# Test 8: Categories API
test_api "Categories API" "http://localhost:8001/api/categories" "categories"

# Test 9: Blogs API
test_api "Blogs API" "http://localhost:8001/api/blogs" "blogs"

# Test 10: Frontend Server
print_test "Testing Frontend server..."
if curl -s --max-time 10 "http://localhost:3000" > /dev/null; then
    print_status "Frontend server is responding"
else
    print_fail "Frontend server is not responding"
fi

# Test 11: SuperAdmin Analytics (requires authentication)
print_test "Testing SuperAdmin analytics..."
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"superadmin@marketmindai.com","password":"superadmin123"}' | \
    grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    if curl -s --max-time 10 -H "Authorization: Bearer $TOKEN" \
        "http://localhost:8001/api/admin/analytics/advanced" | grep -q "user_stats"; then
        print_status "SuperAdmin analytics working"
    else
        print_fail "SuperAdmin analytics failed"
    fi
else
    print_fail "Could not get authentication token for SuperAdmin analytics"
fi

# Test 12: Database Tables
print_test "Testing database tables..."
TABLE_COUNT=$(docker exec marketmindai-postgres psql -U marketmindai_user -d marketmindai -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
if [ "$TABLE_COUNT" -gt 0 ]; then
    print_status "Database tables created ($TABLE_COUNT tables)"
else
    print_fail "No database tables found"
fi

# Test 13: User Data
print_test "Testing user data..."
USER_COUNT=$(docker exec marketmindai-postgres psql -U marketmindai_user -d marketmindai -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
if [ "$USER_COUNT" -eq 3 ]; then
    print_status "User data seeded correctly (3 users)"
else
    print_fail "User data not seeded correctly (found $USER_COUNT users, expected 3)"
fi

# Test 14: Port Availability
print_test "Testing port availability..."
PORTS_IN_USE=0
for port in 3000 8001 5432; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        ((PORTS_IN_USE++))
    fi
done
if [ $PORTS_IN_USE -eq 3 ]; then
    print_status "All required ports are in use (3000, 8001, 5432)"
else
    print_fail "Not all required ports are in use ($PORTS_IN_USE/3)"
fi

# Test 15: Log Files
print_test "Testing log files..."
LOG_COUNT=0
[ -f "/tmp/backend.log" ] && ((LOG_COUNT++))
[ -f "/tmp/frontend.log" ] && ((LOG_COUNT++))
if [ $LOG_COUNT -eq 2 ]; then
    print_status "Log files are present"
else
    print_fail "Log files are missing ($LOG_COUNT/2)"
fi

echo ""
echo "🎯 Test Results Summary"
echo "======================"
echo "Total Tests: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Success Rate: $(($PASSED * 100 / $TOTAL))%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! MarketMindAI is fully functional.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the application status.${NC}"
    echo ""
    echo "🔧 Troubleshooting commands:"
    echo "  ./status_marketmindai.sh    # Check component status"
    echo "  tail -f /tmp/backend.log    # View backend logs"
    echo "  tail -f /tmp/frontend.log   # View frontend logs"
    echo "  docker logs marketmindai-postgres  # View database logs"
    exit 1
fi