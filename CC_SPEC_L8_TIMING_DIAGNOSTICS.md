# CC_SPEC_L8_TIMING_DIAGNOSTICS

---

## ⛔ STOP - READ THIS FIRST ⛔

**BEFORE starting this task, Claude Code MUST:**

1. **Read `docs/CC_COMMUNICATION_PROTOCOL.md`** - Contains mandatory agent usage requirements
2. **Read this entire specification** - Don't skip sections
3. **Use required agents** - Minimum 2 agents for this task
4. **Report agent usage** - Include ratings and findings in completion summary

**⚠️ Work will be REJECTED if agent ratings are below 8/10 or agents are not consulted.**

---

## 📋 OVERVIEW

### Task: Upload Timing Diagnostics & Quick Fix

**Problem:** After the `/api/upload/b2/complete/` endpoint returns (~847ms), there's an 11-second delay before the user is redirected to Step 2. Only 2 seconds of this is intentional - we need to find where the other 9 seconds are going.

**Goals:**
1. Remove the intentional 2-second delay (quick win)
2. Add timing diagnostics to identify bottlenecks
3. Run connection tests for B2 and OpenAI APIs

---

## 🎯 OBJECTIVES

### Primary Goals

1. **Remove 2-second delay** - Eliminate intentional wait in JavaScript
2. **Add timing markers** - Console.log timestamps at each step
3. **Connection diagnostics** - Test B2 and OpenAI response times
4. **Identify bottleneck** - Find where 9 extra seconds are spent

### Success Criteria

- ✅ 2-second intentional delay removed
- ✅ Timing markers show milliseconds for each upload phase
- ✅ Connection test results documented
- ✅ Root cause of 9-second delay identified (or ruled out)

---

## 📝 TASK 1: Remove 2-Second Delay

### File: `prompts/templates/prompts/upload_step1.html`

### Location: Lines 944-952 (approximately)

**Find this code:**
```javascript
// L8-PROGRESS-ANIMATE: Start animated finalizing state with rotating messages
const redirectUrl = `/upload/details?${params.toString()}`;
ProgressUI.startFinalizing();

// Wait for at least one message rotation cycle (2 seconds) for better UX
await new Promise(resolve => setTimeout(resolve, 2000));

// Clean up and redirect
ProgressUI.completeAndRedirect(redirectUrl);
```

**Replace with:**
```javascript
// L8-PROGRESS-ANIMATE: Start animated finalizing state with rotating messages
const redirectUrl = `/upload/details?${params.toString()}`;
ProgressUI.startFinalizing();

// Redirect immediately - animation will show briefly during redirect
// Removed 2-second intentional delay for faster perceived performance
ProgressUI.completeAndRedirect(redirectUrl);
```

---

## 📝 TASK 2: Add Timing Diagnostics

### File: `prompts/templates/prompts/upload_step1.html`

### Add timing object at the START of the `<script>` block (after line 328):

```javascript
// L8-DIAGNOSTICS: Timing tracker for upload performance analysis
const UploadTiming = {
    markers: {},
    
    mark(name) {
        this.markers[name] = performance.now();
        console.log(`⏱️ [TIMING] ${name}: ${new Date().toISOString()}`);
    },
    
    measure(startMark, endMark) {
        const start = this.markers[startMark];
        const end = this.markers[endMark] || performance.now();
        const duration = end - start;
        console.log(`📊 [TIMING] ${startMark} → ${endMark}: ${duration.toFixed(2)}ms`);
        return duration;
    },
    
    summary() {
        console.log('═══════════════════════════════════════');
        console.log('📊 UPLOAD TIMING SUMMARY');
        console.log('═══════════════════════════════════════');
        
        const phases = [
            ['upload_start', 'presign_start', 'Initial Setup'],
            ['presign_start', 'presign_complete', 'Presign API'],
            ['presign_complete', 'b2_upload_start', 'Pre-Upload'],
            ['b2_upload_start', 'b2_upload_complete', 'B2 Upload'],
            ['b2_upload_complete', 'complete_api_start', 'Post-Upload'],
            ['complete_api_start', 'complete_api_done', 'Complete API'],
            ['complete_api_done', 'redirect_start', 'Post-Complete JS'],
            ['upload_start', 'redirect_start', 'TOTAL']
        ];
        
        phases.forEach(([start, end, label]) => {
            if (this.markers[start] && this.markers[end]) {
                const duration = this.markers[end] - this.markers[start];
                console.log(`  ${label}: ${duration.toFixed(2)}ms`);
            }
        });
        
        console.log('═══════════════════════════════════════');
    }
};
```

### Add timing markers throughout `uploadToB2()` function:

**At the START of uploadToB2 function (after `try {`):**
```javascript
UploadTiming.mark('upload_start');
```

**BEFORE presign fetch (around line 797):**
```javascript
UploadTiming.mark('presign_start');
```

**AFTER presign response parsed (after `const presignData = ...`):**
```javascript
UploadTiming.mark('presign_complete');
```

**BEFORE B2 upload XHR send (before `uploadXhr.send(file)`):**
```javascript
UploadTiming.mark('b2_upload_start');
```

**AFTER uploadPromise resolves (after `await uploadPromise`):**
```javascript
UploadTiming.mark('b2_upload_complete');
```

**BEFORE complete API fetch (before the `completeResponse = await fetch` line):**
```javascript
UploadTiming.mark('complete_api_start');
```

**AFTER completeData is parsed (after `completeData = await completeResponse.json()`):**
```javascript
UploadTiming.mark('complete_api_done');
```

**BEFORE redirect (before `ProgressUI.completeAndRedirect`):**
```javascript
UploadTiming.mark('redirect_start');
UploadTiming.summary();
```

---

## 📝 TASK 3: Connection Diagnostics Script

### Create new file: `prompts/management/commands/test_api_latency.py`

```python
"""
Management command to test API connection latency for B2 and OpenAI.

Usage:
    python manage.py test_api_latency
    python manage.py test_api_latency --iterations 5
"""

import time
import statistics
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test connection latency to B2 and OpenAI APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=3,
            help='Number of test iterations (default: 3)'
        )

    def handle(self, *args, **options):
        iterations = options['iterations']
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('API LATENCY DIAGNOSTICS'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        
        # Test B2 connection
        self.test_b2_latency(iterations)
        
        self.stdout.write('')
        
        # Test OpenAI connection
        self.test_openai_latency(iterations)
        
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.SUCCESS('Diagnostics complete'))

    def test_b2_latency(self, iterations):
        """Test B2 API response time"""
        self.stdout.write(self.style.HTTP_INFO('Testing B2 Connection...'))
        
        try:
            import boto3
            from botocore.config import Config
            
            # Get B2 credentials from settings
            b2_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            b2_app_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            b2_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
            b2_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            
            if not all([b2_key_id, b2_app_key, b2_endpoint, b2_bucket]):
                self.stdout.write(self.style.ERROR('  B2 credentials not configured'))
                return
            
            s3_client = boto3.client(
                's3',
                endpoint_url=b2_endpoint,
                aws_access_key_id=b2_key_id,
                aws_secret_access_key=b2_app_key,
                config=Config(signature_version='s3v4')
            )
            
            latencies = []
            for i in range(iterations):
                start = time.time()
                # Simple HEAD request to check bucket exists
                s3_client.head_bucket(Bucket=b2_bucket)
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                self.stdout.write(f'  Iteration {i+1}: {latency:.2f}ms')
            
            self.stdout.write(self.style.SUCCESS(
                f'  B2 Average: {statistics.mean(latencies):.2f}ms '
                f'(min: {min(latencies):.2f}ms, max: {max(latencies):.2f}ms)'
            ))
            
        except ImportError:
            self.stdout.write(self.style.ERROR('  boto3 not installed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  B2 test failed: {e}'))

    def test_openai_latency(self, iterations):
        """Test OpenAI API response time"""
        self.stdout.write(self.style.HTTP_INFO('Testing OpenAI Connection...'))
        
        try:
            from openai import OpenAI
            import os
            
            api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            
            if not api_key:
                self.stdout.write(self.style.ERROR('  OpenAI API key not configured'))
                return
            
            client = OpenAI(api_key=api_key)
            
            latencies = []
            for i in range(iterations):
                start = time.time()
                # Minimal API call - list models (lightweight)
                client.models.list()
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                self.stdout.write(f'  Iteration {i+1}: {latency:.2f}ms')
            
            self.stdout.write(self.style.SUCCESS(
                f'  OpenAI Average: {statistics.mean(latencies):.2f}ms '
                f'(min: {min(latencies):.2f}ms, max: {max(latencies):.2f}ms)'
            ))
            
        except ImportError:
            self.stdout.write(self.style.ERROR('  openai package not installed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  OpenAI test failed: {e}'))
```

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

### Required Agents (Minimum 2)

**1. @javascript-expert or @frontend**
- Task: Review timing marker placement and JavaScript changes
- Focus: Ensure markers capture all phases accurately
- Rating requirement: 8+/10

**2. @django-expert**
- Task: Review management command and API testing approach
- Focus: Proper error handling, settings access
- Rating requirement: 8+/10

---

## 🧪 TESTING CHECKLIST

### After Implementation:

- [ ] 2-second delay code removed from upload_step1.html
- [ ] Timing markers added at all specified points
- [ ] Management command created and runs without errors
- [ ] Upload an image and check browser console for timing output
- [ ] Run `python manage.py test_api_latency` and document results

### Expected Console Output Format:
```
⏱️ [TIMING] upload_start: 2026-01-02T12:00:00.000Z
⏱️ [TIMING] presign_start: 2026-01-02T12:00:00.100Z
...
═══════════════════════════════════════
📊 UPLOAD TIMING SUMMARY
═══════════════════════════════════════
  Initial Setup: 100.00ms
  Presign API: 250.00ms
  ...
  TOTAL: 5000.00ms
═══════════════════════════════════════
```

---

## 📊 CC COMPLETION REPORT FORMAT

**After implementation, provide:**

```markdown
═══════════════════════════════════════════════════════════════
L8 TIMING DIAGNOSTICS - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

| Agent | Rating | Key Finding |
|-------|--------|-------------|
| [Agent] | X/10 | [finding] |
| [Agent] | X/10 | [finding] |

## 📝 CHANGES MADE

| File | Change |
|------|--------|
| upload_step1.html | Removed 2s delay, added timing markers |
| test_api_latency.py | Created new management command |

## 🧪 TESTING PERFORMED

- [ ] 2-second delay removed - verified in code
- [ ] Timing markers output to console
- [ ] Management command runs successfully
- [ ] API latency test results:
  - B2: XXXms average
  - OpenAI: XXXms average

## ✅ SUCCESS CRITERIA MET

- [ ] 2-second delay removed
- [ ] Timing diagnostics added
- [ ] Connection test command created

═══════════════════════════════════════════════════════════════
```

---

## ⚠️ DO NOT

- ❌ Change any AI moderation logic
- ❌ Modify the upload flow sequence
- ❌ Remove or change the `startFinalizing()` call (animation is fine)
- ❌ Modify Step 2 code
- ❌ Change any backend API endpoints

## ✅ DO

- ✅ Remove ONLY the 2-second setTimeout delay
- ✅ Add timing markers as specified
- ✅ Create the diagnostic management command
- ✅ Test that uploads still work correctly after changes

---

## 🔁 CRITICAL REMINDERS

1. **Agent ratings must be 8+/10** - Work rejected otherwise
2. **Only remove the 2-second delay** - Don't change other timing/flow
3. **Test an actual upload** - Verify timing output appears in console
4. **Run the management command** - Document the API latency results

---

**END OF SPECIFICATION**
