#!/bin/bash

# Test Runner Script for Profile Header Tests (Phase E - Part 1)
# Usage: ./run_profile_tests.sh [option]
# Options: all, django, selenium, coverage, specific

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Profile Header Test Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to run Django tests
run_django_tests() {
    echo -e "${YELLOW}Running Django tests (no Selenium)...${NC}"
    python manage.py test prompts.tests.test_user_profile_header --verbosity=2

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Django tests passed!${NC}"
    else
        echo -e "${RED}✗ Django tests failed!${NC}"
        exit 1
    fi
}

# Function to run Selenium tests
run_selenium_tests() {
    echo -e "${YELLOW}Running Selenium tests (requires ChromeDriver)...${NC}"

    # Check if selenium is installed
    python -c "import selenium" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}Selenium not installed. Install with: pip install selenium${NC}"
        exit 1
    fi

    python manage.py test prompts.tests.test_user_profile_javascript --verbosity=2

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Selenium tests passed!${NC}"
    else
        echo -e "${RED}✗ Selenium tests failed!${NC}"
        exit 1
    fi
}

# Function to run all tests
run_all_tests() {
    echo -e "${YELLOW}Running all profile header tests...${NC}"
    python manage.py test prompts.tests.test_user_profile_header prompts.tests.test_user_profile_javascript --verbosity=2

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
    else
        echo -e "${RED}✗ Some tests failed!${NC}"
        exit 1
    fi
}

# Function to run with coverage
run_with_coverage() {
    echo -e "${YELLOW}Running tests with coverage report...${NC}"

    # Check if coverage is installed
    python -c "import coverage" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}Coverage not installed. Install with: pip install coverage${NC}"
        exit 1
    fi

    coverage run --source='prompts' manage.py test prompts.tests.test_user_profile_header
    coverage report
    coverage html

    echo -e "${GREEN}✓ Coverage report generated!${NC}"
    echo -e "${YELLOW}View HTML report: open htmlcov/index.html${NC}"
}

# Function to run specific test
run_specific_test() {
    echo -e "${YELLOW}Enter full test path (e.g., prompts.tests.test_user_profile_header.ProfileHeaderVisibilityTestCase.test_edit_button_visible_to_owner):${NC}"
    read test_path

    python manage.py test "$test_path" --verbosity=2

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Test passed!${NC}"
    else
        echo -e "${RED}✗ Test failed!${NC}"
        exit 1
    fi
}

# Main menu
if [ -z "$1" ]; then
    echo "Usage: ./run_profile_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  all       - Run all tests (Django + Selenium)"
    echo "  django    - Run only Django tests"
    echo "  selenium  - Run only Selenium tests"
    echo "  coverage  - Run Django tests with coverage report"
    echo "  specific  - Run a specific test (interactive)"
    echo ""
    echo "Examples:"
    echo "  ./run_profile_tests.sh all"
    echo "  ./run_profile_tests.sh django"
    echo "  ./run_profile_tests.sh coverage"
    echo ""
    exit 0
fi

case "$1" in
    all)
        run_all_tests
        ;;
    django)
        run_django_tests
        ;;
    selenium)
        run_selenium_tests
        ;;
    coverage)
        run_with_coverage
        ;;
    specific)
        run_specific_test
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        echo "Use: all, django, selenium, coverage, or specific"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test run complete!${NC}"
echo -e "${GREEN}========================================${NC}"
