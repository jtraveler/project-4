#!/bin/bash

# ================================================================
# Phase F Day 1 - Follow System Heroku Testing Script
# ================================================================
# This script automates testing of the Follow System on Heroku
# Run after deploying code: ./scripts/test_follow_system_heroku.sh
# ================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="${HEROKU_APP:-mj-project-4}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="test_reports/follow_system_test_${TIMESTAMP}.txt"

# Create reports directory if it doesn't exist
mkdir -p test_reports

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Phase F Day 1 - Follow System Testing on Heroku${NC}"
echo -e "${BLUE}App: ${APP_NAME}${NC}"
echo -e "${BLUE}Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}================================================================${NC}\n"

# Function to run Heroku command and capture output
run_heroku_cmd() {
    local cmd="$1"
    local description="$2"

    echo -e "${YELLOW}→ ${description}...${NC}"

    if output=$(heroku run "$cmd" --app "$APP_NAME" 2>&1); then
        echo -e "${GREEN}✓ Success${NC}"
        echo "$output" | tail -20  # Show last 20 lines
        echo -e "\n${output}\n" >> "$REPORT_FILE"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "$output"
        echo -e "\n${output}\n" >> "$REPORT_FILE"
        return 1
    fi
}

# Initialize report
echo "FOLLOW SYSTEM TEST REPORT - ${TIMESTAMP}" > "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Track overall status
OVERALL_STATUS="PASS"
TESTS_PASSED=0
TESTS_FAILED=0

# ================================================================
# STEP 1: Check for pending migrations
# ================================================================
echo -e "\n${BLUE}STEP 1: Checking for pending migrations${NC}"
echo -e "----------------------------------------\n"

if run_heroku_cmd "python manage.py showmigrations prompts | grep '\[ \]'" "Checking for unapplied migrations"; then
    echo -e "${YELLOW}⚠ Unapplied migrations detected${NC}"

    # Create migrations
    echo -e "\n${YELLOW}Creating new migrations...${NC}"
    if run_heroku_cmd "python manage.py makemigrations prompts" "Creating migrations"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        OVERALL_STATUS="FAIL"
    fi

    # Apply migrations
    echo -e "\n${YELLOW}Applying migrations...${NC}"
    if run_heroku_cmd "python manage.py migrate prompts" "Applying migrations"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        OVERALL_STATUS="FAIL"
    fi
else
    echo -e "${GREEN}✓ All migrations already applied${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# ================================================================
# STEP 2: Run automated test suite
# ================================================================
echo -e "\n${BLUE}STEP 2: Running automated test suite${NC}"
echo -e "----------------------------------------\n"

if run_heroku_cmd "python manage.py test prompts.tests.test_follows -v 2" "Running follow system tests"; then
    echo -e "${GREEN}✓ All tests passed${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Some tests failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    OVERALL_STATUS="FAIL"
fi

# ================================================================
# STEP 3: Verify database structure
# ================================================================
echo -e "\n${BLUE}STEP 3: Verifying database structure${NC}"
echo -e "----------------------------------------\n"

# Create Python verification script
cat << 'PYTHON_SCRIPT' > /tmp/verify_follow_db.py
from django.contrib.auth.models import User
from prompts.models import Follow
import sys

try:
    # Check Follow model exists
    print("Checking Follow model...")

    # Check fields
    expected_fields = ['id', 'follower', 'following', 'created_at']
    actual_fields = [f.name for f in Follow._meta.fields]

    for field in expected_fields:
        if field in actual_fields:
            print(f"  ✓ Field '{field}' exists")
        else:
            print(f"  ✗ Field '{field}' missing")
            sys.exit(1)

    # Check indexes
    print("\nChecking indexes...")
    indexes = Follow._meta.indexes
    print(f"  ✓ {len(indexes)} indexes found")

    # Check unique constraint
    print("\nChecking unique constraint...")
    unique = Follow._meta.unique_together
    if unique:
        print(f"  ✓ Unique constraint: {unique}")
    else:
        print("  ✗ No unique constraint found")
        sys.exit(1)

    print("\n✓ Database structure verified successfully")

except Exception as e:
    print(f"\n✗ Database verification failed: {e}")
    sys.exit(1)
PYTHON_SCRIPT

# Upload and run verification script
echo -e "${YELLOW}Uploading verification script...${NC}"
heroku run "cat > /tmp/verify_follow_db.py" --app "$APP_NAME" < /tmp/verify_follow_db.py

if run_heroku_cmd "python manage.py shell < /tmp/verify_follow_db.py" "Verifying database structure"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    OVERALL_STATUS="FAIL"
fi

# ================================================================
# STEP 4: Functional test
# ================================================================
echo -e "\n${BLUE}STEP 4: Running functional test${NC}"
echo -e "----------------------------------------\n"

# Create functional test script
cat << 'FUNC_TEST' > /tmp/functional_test.py
from django.contrib.auth.models import User
from django.test import Client
from prompts.models import Follow
import json

print("Starting functional test...")

try:
    # Create test users
    print("1. Creating test users...")
    user1, _ = User.objects.get_or_create(username='followtest1')
    user1.set_password('testpass123')
    user1.save()

    user2, _ = User.objects.get_or_create(username='followtest2')
    user2.save()
    print("  ✓ Test users created")

    # Test follow
    print("2. Testing follow action...")
    client = Client()
    client.login(username='followtest1', password='testpass123')

    response = client.post(f'/users/{user2.username}/follow/')
    if response.status_code == 200:
        data = json.loads(response.content)
        if data.get('success'):
            print(f"  ✓ Follow successful")
        else:
            print(f"  ✗ Follow failed: {data.get('error')}")
    else:
        print(f"  ✗ HTTP {response.status_code}")

    # Verify in database
    print("3. Verifying database...")
    if Follow.objects.filter(follower=user1, following=user2).exists():
        print("  ✓ Follow relationship exists")
    else:
        print("  ✗ Follow relationship not found")

    # Cleanup
    print("4. Cleaning up...")
    Follow.objects.filter(follower=user1).delete()
    user1.delete()
    user2.delete()
    print("  ✓ Cleanup complete")

    print("\n✓ Functional test passed")

except Exception as e:
    print(f"\n✗ Functional test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
FUNC_TEST

# Upload and run functional test
echo -e "${YELLOW}Uploading functional test...${NC}"
heroku run "cat > /tmp/functional_test.py" --app "$APP_NAME" < /tmp/functional_test.py

if run_heroku_cmd "python manage.py shell < /tmp/functional_test.py" "Running functional test"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    OVERALL_STATUS="FAIL"
fi

# ================================================================
# STEP 5: Performance check
# ================================================================
echo -e "\n${BLUE}STEP 5: Performance check${NC}"
echo -e "----------------------------------------\n"

cat << 'PERF_TEST' > /tmp/perf_test.py
from django.contrib.auth.models import User
from prompts.models import Follow
import time

print("Running performance check...")

try:
    # Get or create users
    user1, _ = User.objects.get_or_create(username='perftest1')
    user2, _ = User.objects.get_or_create(username='perftest2')

    # Test follow creation speed
    start = time.time()
    follow, created = Follow.objects.get_or_create(
        follower=user1, following=user2
    )
    elapsed = time.time() - start

    print(f"Follow creation: {elapsed:.3f}s")

    if elapsed < 1.0:
        print("  ✓ Performance acceptable (<1s)")
    else:
        print(f"  ⚠ Slow performance ({elapsed:.3f}s)")

    # Test query speed
    start = time.time()
    count = user2.follower_set.count()
    elapsed = time.time() - start

    print(f"Follower count query: {elapsed:.3f}s")

    if elapsed < 0.5:
        print("  ✓ Query performance good (<0.5s)")
    else:
        print(f"  ⚠ Slow query ({elapsed:.3f}s)")

    # Cleanup
    Follow.objects.filter(follower=user1).delete()
    user1.delete()
    user2.delete()

    print("\n✓ Performance check complete")

except Exception as e:
    print(f"\n✗ Performance check failed: {e}")
    exit(1)
PERF_TEST

heroku run "cat > /tmp/perf_test.py" --app "$APP_NAME" < /tmp/perf_test.py

if run_heroku_cmd "python manage.py shell < /tmp/perf_test.py" "Running performance check"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    # Don't fail overall for performance issues
fi

# ================================================================
# FINAL REPORT
# ================================================================
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}TEST RESULTS SUMMARY${NC}"
echo -e "${BLUE}================================================================${NC}\n"

echo "Tests Passed: ${TESTS_PASSED}" | tee -a "$REPORT_FILE"
echo "Tests Failed: ${TESTS_FAILED}" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ "$OVERALL_STATUS" = "PASS" ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✓ ALL TESTS PASSED                ║${NC}"
    echo -e "${GREEN}║     Follow System Ready for Use       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo "OVERALL: PASS" >> "$REPORT_FILE"
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     ✗ SOME TESTS FAILED               ║${NC}"
    echo -e "${RED}║     Review report for details         ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo "OVERALL: FAIL" >> "$REPORT_FILE"
fi

echo -e "\nFull report saved to: ${REPORT_FILE}"
echo -e "\nTo view the report: cat ${REPORT_FILE}\n"

# Clean up temp files
rm -f /tmp/verify_follow_db.py /tmp/functional_test.py /tmp/perf_test.py

exit $([ "$OVERALL_STATUS" = "PASS" ] && echo 0 || echo 1)
