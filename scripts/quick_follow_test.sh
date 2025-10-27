#!/bin/bash

# Quick test of follow system on Heroku
APP_NAME="${HEROKU_APP:-mj-project-4}"

echo "Quick Follow System Test"
echo "========================"

# Test 1: Check migrations
echo -n "1. Migrations applied: "
if heroku run "python manage.py showmigrations prompts | grep prompts.0031" --app "$APP_NAME" > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗ (run: heroku run python manage.py migrate)"
    exit 1
fi

# Test 2: Run one test
echo -n "2. Basic test passing: "
if heroku run "python manage.py test prompts.tests.test_follows.FollowSystemTestCase.test_follow_user -v 0" --app "$APP_NAME" > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗"
    exit 1
fi

# Test 3: Check model exists
echo -n "3. Follow model exists: "
if heroku run "python manage.py shell -c 'from prompts.models import Follow; print(\"OK\")'" --app "$APP_NAME" 2>&1 | grep -q "OK"; then
    echo "✓"
else
    echo "✗"
    exit 1
fi

echo -e "\n✓ Follow System is working!"
