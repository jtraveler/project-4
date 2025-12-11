#!/bin/bash

# ============================================================================
# 301 Redirect Verification Suite
# Complete automated testing for AI generator URL migration
# Usage: ./scripts/redirect_verification_suite.sh [environment] [url]
# Examples:
#   ./scripts/redirect_verification_suite.sh local http://localhost:8000
#   ./scripts/redirect_verification_suite.sh production https://mj-project-4-68750ca94690.herokuapp.com
# ============================================================================

set -e  # Exit on any error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Configuration
ENVIRONMENT="${1:-local}"
BASE_URL="${2:-http://localhost:8000}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_DIR="docs/redirect_logs"
LOG_FILE="$LOG_DIR/redirect_test_${ENVIRONMENT}_${TIMESTAMP}.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# AI Generators to test
declare -a GENERATORS=(
    "midjourney"
    "dalle3"
    "dalle2"
    "stable-diffusion"
    "leonardo-ai"
    "flux"
    "sora"
    "sora2"
    "veo-3"
    "adobe-firefly"
    "bing-image-creator"
)

# Test parameters for query string testing
declare -a QUERY_PARAMS=(
    ""
    "?page=1"
    "?page=2"
    "?sort=trending"
    "?sort=new"
    "?page=2&sort=trending"
)

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

print_header() {
    local title="$1"
    echo "" | tee -a "$LOG_FILE"
    echo "╔════════════════════════════════════════════════════════════════╗" | tee -a "$LOG_FILE"
    echo "║ $title" | tee -a "$LOG_FILE"
    echo "╚════════════════════════════════════════════════════════════════╝" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

print_section() {
    local title="$1"
    echo "" | tee -a "$LOG_FILE"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}$title${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

print_pass() {
    local message="$1"
    echo -e "${GREEN}✓${NC} $message" | tee -a "$LOG_FILE"
    ((PASSED_TESTS++))
}

print_fail() {
    local message="$1"
    echo -e "${RED}✗${NC} $message" | tee -a "$LOG_FILE"
    ((FAILED_TESTS++))
}

print_warning() {
    local message="$1"
    echo -e "${YELLOW}⚠${NC} $message" | tee -a "$LOG_FILE"
    ((WARNING_TESTS++))
}

increment_test() {
    ((TOTAL_TESTS++))
}

# ============================================================================
# MAIN TEST FUNCTIONS
# ============================================================================

test_connectivity() {
    print_section "TEST 0: Connectivity Check"

    log "INFO" "Testing connectivity to $BASE_URL"

    if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL" > /dev/null 2>&1; then
        print_pass "Server is reachable"
        return 0
    else
        print_fail "Server is not reachable"
        log "ERROR" "Cannot reach $BASE_URL - please check URL or server status"
        exit 1
    fi
}

test_http_status() {
    print_section "TEST 1: HTTP 301 Status Code Verification"

    log "INFO" "Verifying all old URLs return HTTP 301 status code"

    for gen in "${GENERATORS[@]}"; do
        increment_test
        URL="$BASE_URL/ai/$gen/"

        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
        FULL_RESPONSE=$(curl -s -I "$URL")

        if [ "$STATUS" = "301" ]; then
            print_pass "$gen: HTTP 301 ✓"
        else
            print_fail "$gen: HTTP $STATUS (expected 301)"
            log "DEBUG" "Full response:\n$FULL_RESPONSE"
        fi
    done
}

test_redirect_destination() {
    print_section "TEST 2: Redirect Destination Verification"

    log "INFO" "Verifying all redirects point to correct new URLs"

    for gen in "${GENERATORS[@]}"; do
        increment_test
        URL="$BASE_URL/ai/$gen/"

        LOCATION=$(curl -s -I "$URL" | grep -i "^Location:" | cut -d' ' -f2- | tr -d '\r\n')
        EXPECTED="/inspiration/ai/$gen/"

        if [ "$LOCATION" = "$EXPECTED" ]; then
            print_pass "$gen → $LOCATION ✓"
        else
            print_fail "$gen → $LOCATION (expected $EXPECTED)"
            log "DEBUG" "URL: $URL, Got: $LOCATION"
        fi
    done
}

test_query_string_preservation() {
    print_section "TEST 3: Query String Preservation"

    log "INFO" "Testing query parameter preservation in redirects"

    # Test with subset of generators to avoid too much output
    local TEST_GENERATORS=("midjourney" "dalle3" "stable-diffusion")

    for gen in "${TEST_GENERATORS[@]}"; do
        for params in "${QUERY_PARAMS[@]}"; do
            increment_test
            URL="$BASE_URL/ai/$gen/$params"
            EXPECTED_LOCATION="/inspiration/ai/$gen/$params"

            LOCATION=$(curl -s -I "$URL" | grep -i "^Location:" | cut -d' ' -f2- | tr -d '\r\n')

            if [ "$LOCATION" = "$EXPECTED_LOCATION" ]; then
                print_pass "$gen$params → ✓"
            else
                print_fail "$gen$params"
                log "DEBUG" "Expected: $EXPECTED_LOCATION, Got: $LOCATION"
            fi
        done
    done
}

test_new_url_accessibility() {
    print_section "TEST 4: New URL Accessibility"

    log "INFO" "Verifying all new /inspiration/ai/* URLs are accessible"

    for gen in "${GENERATORS[@]}"; do
        increment_test
        URL="$BASE_URL/inspiration/ai/$gen/"

        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")

        if [ "$STATUS" = "200" ]; then
            print_pass "$gen: HTTP 200 ✓"
        else
            print_fail "$gen: HTTP $STATUS (expected 200)"
        fi
    done
}

test_no_redirect_chains() {
    print_section "TEST 5: Redirect Chain Detection"

    log "INFO" "Verifying no redirect chains exist (should be exactly 2 HTTP requests)"

    local TEST_GENERATORS=("midjourney" "dalle3" "stable-diffusion")

    for gen in "${TEST_GENERATORS[@]}"; do
        increment_test
        URL="$BASE_URL/ai/$gen/"

        # Create temp file for headers
        HEADERS_FILE=$(mktemp)
        trap "rm -f $HEADERS_FILE" RETURN

        # Follow redirect and save all headers
        curl -s -L "$URL" -D "$HEADERS_FILE" > /dev/null 2>&1

        # Count HTTP status lines
        HTTP_COUNT=$(grep -c "^HTTP" "$HEADERS_FILE" || echo 0)

        if [ "$HTTP_COUNT" = "2" ]; then
            print_pass "$gen: 2 requests (no chain) ✓"
        else
            print_fail "$gen: $HTTP_COUNT HTTP requests (expected 2 - indicates redirect chain)"
            log "DEBUG" "Headers from $gen:\n$(cat $HEADERS_FILE)"
        fi
    done
}

test_cache_headers() {
    print_section "TEST 6: Cache Headers for 301 Redirects"

    log "INFO" "Verifying 301 redirects have proper cache headers"

    # Test just one generator to avoid spam
    increment_test
    URL="$BASE_URL/ai/midjourney/"

    RESPONSE=$(curl -s -I "$URL")

    # Check for Cache-Control header
    if echo "$RESPONSE" | grep -q -i "^Cache-Control:"; then
        CACHE_CONTROL=$(echo "$RESPONSE" | grep -i "^Cache-Control:" | cut -d' ' -f2-)
        print_pass "Cache headers present: $CACHE_CONTROL ✓"
    else
        print_warning "No explicit Cache-Control header (may use defaults)"
    fi
}

test_ssl_https() {
    print_section "TEST 7: HTTPS/SSL Verification"

    log "INFO" "Verifying HTTPS is working properly"

    if [[ "$BASE_URL" == https://* ]]; then
        increment_test

        # Test SSL certificate validity
        DOMAIN=$(echo "$BASE_URL" | cut -d'/' -f3)
        if curl -s -I "https://$DOMAIN/ai/midjourney/" > /dev/null 2>&1; then
            print_pass "HTTPS connection successful ✓"
        else
            print_fail "HTTPS connection failed"
        fi
    else
        log "INFO" "Skipping HTTPS test (not testing HTTPS URL)"
    fi
}

test_heroku_specific() {
    print_section "TEST 8: Heroku-Specific Checks (Production Only)"

    if [[ "$BASE_URL" == *"herokuapp.com"* ]]; then
        increment_test
        log "INFO" "Running Heroku-specific checks"

        # Check Heroku-specific headers
        RESPONSE=$(curl -s -I "$BASE_URL/ai/midjourney/")

        if echo "$RESPONSE" | grep -q "X-Powered-By: Express"; then
            print_warning "Detected Express.js (might be proxy)"
        elif echo "$RESPONSE" | grep -q "Heroku"; then
            print_pass "Heroku infrastructure headers present ✓"
        fi

        # Check for common Heroku errors
        if echo "$RESPONSE" | grep -q "502\|503\|504"; then
            print_fail "Heroku error response detected"
        fi
    else
        log "INFO" "Skipping Heroku checks (not a Heroku URL)"
    fi
}

test_trailing_slash() {
    print_section "TEST 9: Trailing Slash Handling"

    increment_test
    log "INFO" "Testing redirect behavior with/without trailing slash"

    URL_WITH_SLASH="$BASE_URL/ai/midjourney/"
    URL_WITHOUT_SLASH="$BASE_URL/ai/midjourney"

    # Both should work
    STATUS_WITH=$(curl -s -o /dev/null -w "%{http_code}" "$URL_WITH_SLASH")
    STATUS_WITHOUT=$(curl -s -o /dev/null -w "%{http_code}" "$URL_WITHOUT_SLASH")

    if [ "$STATUS_WITH" = "301" ] && [ "$STATUS_WITHOUT" = "301" ]; then
        print_pass "Both work: with and without trailing slash ✓"
    else
        print_warning "Trailing slash behavior: with=$STATUS_WITH, without=$STATUS_WITHOUT"
    fi
}

test_invalid_generator() {
    print_section "TEST 10: Invalid Generator Handling"

    increment_test
    log "INFO" "Testing behavior with invalid generator slug"

    URL="$BASE_URL/ai/invalid-generator/"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")

    # Should either redirect or 404, but not 500
    if [ "$STATUS" = "301" ] || [ "$STATUS" = "404" ]; then
        print_pass "Invalid generator handled gracefully (HTTP $STATUS) ✓"
    else
        print_fail "Invalid generator returned HTTP $STATUS (expected 301 or 404)"
    fi
}

# ============================================================================
# REPORTING FUNCTIONS
# ============================================================================

generate_report() {
    print_header "REDIRECT MIGRATION TEST SUITE RESULTS"

    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Base URL: $BASE_URL"
    log "INFO" "Test timestamp: $TIMESTAMP"
    log "INFO" "Log file: $LOG_FILE"

    echo "" | tee -a "$LOG_FILE"
    echo "╔════════════════════════════════════════════════════════════════╗" | tee -a "$LOG_FILE"
    echo "║                     TEST SUMMARY                                ║" | tee -a "$LOG_FILE"
    echo "╚════════════════════════════════════════════════════════════════╝" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    echo "Total tests:    $TOTAL_TESTS" | tee -a "$LOG_FILE"
    echo -e "Passed:         ${GREEN}$PASSED_TESTS${NC}" | tee -a "$LOG_FILE"
    echo -e "Failed:         ${RED}$FAILED_TESTS${NC}" | tee -a "$LOG_FILE"
    echo -e "Warnings:       ${YELLOW}$WARNING_TESTS${NC}" | tee -a "$LOG_FILE"

    echo "" | tee -a "$LOG_FILE"

    # Calculate pass rate
    if [ $TOTAL_TESTS -gt 0 ]; then
        PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        echo "Pass rate:      ${PASS_RATE}%" | tee -a "$LOG_FILE"
    fi

    echo "" | tee -a "$LOG_FILE"

    # Final verdict
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✓ ALL TESTS PASSED${NC}" | tee -a "$LOG_FILE"
        echo -e "${GREEN}Migration is ready for deployment${NC}" | tee -a "$LOG_FILE"
        RETURN_CODE=0
    else
        echo -e "${RED}✗ $FAILED_TESTS TEST(S) FAILED${NC}" | tee -a "$LOG_FILE"
        echo -e "${RED}Please fix issues before proceeding${NC}" | tee -a "$LOG_FILE"
        RETURN_CODE=1
    fi

    echo "" | tee -a "$LOG_FILE"
    echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    return $RETURN_CODE
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    print_header "301 REDIRECT MIGRATION TEST SUITE"

    log "INFO" "Starting redirect verification tests"
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Base URL: $BASE_URL"
    log "INFO" "Generators to test: ${#GENERATORS[@]}"
    log "INFO" "Test started: $(date)"

    # Run all tests
    test_connectivity
    test_http_status
    test_redirect_destination
    test_query_string_preservation
    test_new_url_accessibility
    test_no_redirect_chains
    test_cache_headers
    test_ssl_https
    test_heroku_specific
    test_trailing_slash
    test_invalid_generator

    # Generate final report
    generate_report
    EXIT_CODE=$?

    log "INFO" "Test completed: $(date)"

    exit $EXIT_CODE
}

# Run main function
main
