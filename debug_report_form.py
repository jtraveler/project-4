#!/usr/bin/env python
"""
Django shell debugging script for PromptReportForm
Run with: python manage.py shell < debug_report_form.py

This will help diagnose where the comment field data is being lost.
"""

from prompts.models import Prompt, PromptReport
from prompts.forms import PromptReportForm
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*60)
print("DEBUGGING PromptReportForm Comment Field")
print("="*60 + "\n")

# Get test data
try:
    prompt = Prompt.objects.filter(status=1).first()
    user = User.objects.exclude(id=prompt.author.id).first()

    print(f"✓ Test Prompt: {prompt.title}")
    print(f"✓ Test User: {user.username}")
    print()
except Exception as e:
    print(f"✗ Error getting test data: {e}")
    exit(1)

# Test 1: Form with comment data
print("TEST 1: Form with comment data")
print("-" * 60)

test_data = {
    'reason': 'inappropriate',
    'comment': 'This is a test comment with actual content'
}

print(f"Input data: {test_data}")
print()

form = PromptReportForm(data=test_data)

print(f"form.is_valid(): {form.is_valid()}")
if not form.is_valid():
    print(f"Errors: {form.errors}")
    exit(1)

print(f"form.cleaned_data['comment']: '{form.cleaned_data.get('comment')}'")
print(f"Length: {len(form.cleaned_data.get('comment', ''))}")
print()

# Save and check
report = form.save(commit=False)
report.prompt = prompt
report.reported_by = user

print("BEFORE save():")
print(f"  report.comment: '{report.comment}'")
print(f"  Length: {len(report.comment)}")
print()

report.save()

print("AFTER save():")
print(f"  report.id: {report.id}")
print(f"  report.comment: '{report.comment}'")
print(f"  Length: {len(report.comment)}")
print()

# Verify in database
fresh_report = PromptReport.objects.get(id=report.id)
print("FRESH from database:")
print(f"  fresh_report.comment: '{fresh_report.comment}'")
print(f"  Length: {len(fresh_report.comment)}")
print()

# Clean up
report.delete()
print("✓ Test report deleted\n")


# Test 2: Form with empty comment
print("TEST 2: Form with empty comment")
print("-" * 60)

test_data_empty = {
    'reason': 'spam',
    'comment': ''
}

print(f"Input data: {test_data_empty}")
print()

form2 = PromptReportForm(data=test_data_empty)

print(f"form.is_valid(): {form2.is_valid()}")
print(f"form.cleaned_data['comment']: '{form2.cleaned_data.get('comment')}'")
print(f"Length: {len(form2.cleaned_data.get('comment', ''))}")
print()


# Test 3: Form with only whitespace comment
print("TEST 3: Form with whitespace-only comment")
print("-" * 60)

test_data_whitespace = {
    'reason': 'spam',
    'comment': '    \n\n   '
}

print(f"Input data: {repr(test_data_whitespace)}")
print()

form3 = PromptReportForm(data=test_data_whitespace)

print(f"form.is_valid(): {form3.is_valid()}")
print(f"form.cleaned_data['comment']: '{form3.cleaned_data.get('comment')}'")
print(f"Length: {len(form3.cleaned_data.get('comment', ''))}")
print()


# Test 4: Simulate POST data from browser
print("TEST 4: Simulating browser POST data")
print("-" * 60)

from django.http import QueryDict

# This simulates what Django receives from the browser
post_data = QueryDict('', mutable=True)
post_data['reason'] = 'inappropriate'
post_data['comment'] = 'Browser comment with special chars: <>&"'

print(f"POST data: {dict(post_data)}")
print()

form4 = PromptReportForm(data=post_data)

print(f"form.is_valid(): {form4.is_valid()}")
if form4.is_valid():
    print(f"form.cleaned_data['comment']: '{form4.cleaned_data.get('comment')}'")
    print(f"Length: {len(form4.cleaned_data.get('comment', ''))}")
else:
    print(f"Errors: {form4.errors}")
print()


print("="*60)
print("DEBUG COMPLETE")
print("="*60)
print("\nIf TEST 1 shows empty comment, the issue is in clean_comment()")
print("If TEST 1 succeeds but browser fails, check AJAX/template")
print("If all tests succeed, check view logic after form.save()")
