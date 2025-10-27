#!/bin/bash
#
# Production Rate Limiting Verification Script
# Tests that rate limiting works on Heroku production
#
# Usage: ./scripts/verify_rate_limiting_production.sh
#

echo "🔍 PRODUCTION RATE LIMITING VERIFICATION"
echo "========================================="
echo ""
echo "App: mj-project-4.herokuapp.com"
echo "Endpoint: /unsubscribe/test-token/"
echo "Expected: Requests 1-5 pass, Request 6 shows HTTP 429"
echo ""

PRODUCTION_URL="https://mj-project-4.herokuapp.com/unsubscribe/test-token/"
PASS_COUNT=0
RATE_LIMITED=false

for i in {1..6}; do
    echo "Request $i:"

    # Get HTTP status code
    STATUS=$(curl -I -s "$PRODUCTION_URL" 2>&1 | grep "^HTTP/" | awk '{print $2}')

    echo "  Status: HTTP $STATUS"

    if [ "$i" -le 5 ]; then
        # Requests 1-5 should pass (404 or 200 is OK)
        if [ "$STATUS" = "404" ] || [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then
            echo "  ✅ PASS (Request allowed)"
            ((PASS_COUNT++))
        else
            echo "  ❌ FAIL (Unexpected status: $STATUS)"
        fi
    else
        # Request 6 should be rate limited
        if [ "$STATUS" = "429" ]; then
            echo "  ✅ RATE LIMITED (HTTP 429) - SUCCESS!"
            RATE_LIMITED=true
        else
            echo "  ❌ FAIL (Expected 429, got $STATUS)"
            echo "  ⚠️  Rate limiting NOT working!"
        fi
    fi

    echo ""
    sleep 0.5
done

echo "========================================="
echo "RESULTS:"
echo "  Requests 1-5 passed: $PASS_COUNT/5"
if [ "$RATE_LIMITED" = true ]; then
    echo "  Request 6 rate limited: ✅ YES"
    echo ""
    echo "🎉 SUCCESS! Rate limiting is working in production!"
    echo ""
    echo "Next steps:"
    echo "  1. Check Heroku logs: heroku logs --tail --app mj-project-4"
    echo "  2. Verify 429.html template displays correctly in browser"
    echo "  3. Test from different IP address (should allow 5 new requests)"
    exit 0
else
    echo "  Request 6 rate limited: ❌ NO"
    echo ""
    echo "⚠️  FAIL: Rate limiting NOT working!"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check decorator is on unsubscribe_view() function"
    echo "  2. Verify RatelimitMiddleware is in MIDDLEWARE list"
    echo "  3. Check Heroku logs for errors: heroku logs --tail --app mj-project-4"
    echo "  4. Confirm latest code is deployed: git log -1 --oneline"
    exit 1
fi
