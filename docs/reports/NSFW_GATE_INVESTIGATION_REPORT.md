# NSFW Gate Investigation Report

**Investigation Date:** January 3, 2026
**Working Commit:** `d0951f643ce01d4d681e87da1e78516f7c374604`
**Current Commit:** HEAD
**Status:** ✅ ROOT CAUSE IDENTIFIED

---

## Executive Summary

This investigation examined why hardcore NSFW content is no longer being blocked during uploads. The root cause has been identified: **L8-TIMEOUT exception handlers in `cloudinary_moderation.py` return `status: 'pending_review'` on API timeout, which does NOT trigger the blocking logic that only checks for `status: 'rejected'`**.

---

## User's 3 Questions - ANSWERED

### Question 1: Was `include_moderation=True` at the working commit? What is it now?

**Answer: NO - It was `False` in BOTH versions.**

This was NOT the breaking change. The `include_moderation` parameter has always been `False`:

```python
# upload_views.py - BOTH versions (working commit AND current)
result = ContentGenerationService.generate_content(
    image_bytes,
    filename,
    include_moderation=False  # <-- Always False
)
```

**Why this isn't the issue:** The `include_moderation` parameter in `ContentGenerationService` is for *early warning* during Step 2 form display. The actual blocking happens during form submission via `ModerationOrchestrator`.

---

### Question 2: Was there code that BLOCKED hardcore NSFW (not just warned)?

**Answer: YES - The orchestrator's `_determine_overall_status()` method blocks on `'rejected'` status.**

Location: `prompts/services/orchestrator.py` (lines 265-280)

```python
def _determine_overall_status(
    self,
    results: Dict[str, Any],
    has_errors: bool = False
) -> Tuple[str, bool]:
    """Determine overall moderation status from all service results."""
    statuses = [r.get('status', 'approved') for r in results.values() if r]

    # BLOCKING LOGIC - Only triggers on 'rejected'
    if 'rejected' in statuses:
        overall_status = 'rejected'
        requires_review = True
        logger.info("Overall status: REJECTED (at least one service rejected)")
    elif 'flagged' in statuses or has_errors:
        overall_status = 'flagged'
        requires_review = True
        logger.info("Overall status: FLAGGED")
    else:
        overall_status = 'approved'
        requires_review = False
        logger.info("Overall status: APPROVED")

    return overall_status, requires_review
```

**The orchestrator.py file is UNCHANGED from the working commit.** The blocking logic is intact.

---

### Question 3: What specific change broke the NSFW gate?

**Answer: L8-TIMEOUT exception handlers in `cloudinary_moderation.py` return `status: 'pending_review'` instead of `status: 'rejected'`.**

The L8-TIMEOUT feature added graceful degradation for API timeouts. However, the chosen status bypasses the blocking logic:

#### Git Diff Excerpt - cloudinary_moderation.py

**Location 1: `moderate_image_url()` method (lines 159-174)**

```diff
+        except (APITimeoutError, APIConnectionError) as e:
+            # L8-TIMEOUT: Graceful degradation on timeout
+            logger.warning(f"Vision moderation timeout: {str(e)}")
+            return {
+                'timeout': True,
+                'is_safe': False,
+                'status': 'pending_review',  # <-- BUG: Should be 'rejected' for safety
+                'flagged_categories': ['timeout'],
+                'severity': 'low',
+                'confidence_score': 0.0,
+                'explanation': 'Moderation service timed out - flagged for manual review',
+            }
```

**Location 2: `moderate_visual_content()` method (lines 329-344)**

```diff
+        except (APITimeoutError, APIConnectionError) as e:
+            # L8-TIMEOUT: Graceful degradation on timeout
+            logger.warning(f"Visual content moderation timeout: {str(e)}")
+            return {
+                'timeout': True,
+                'is_safe': False,
+                'status': 'pending_review',  # <-- BUG: Should be 'rejected' for safety
+                'flagged_categories': ['timeout'],
+                'severity': 'low',
+                'confidence_score': 0.0,
+                'explanation': 'Moderation service timed out - flagged for manual review',
+            }
```

#### Why This Breaks NSFW Blocking

1. **Orchestrator only blocks on `'rejected'`**: The `_determine_overall_status()` method checks `if 'rejected' in statuses:`
2. **Timeout returns `'pending_review'`**: This status is NOT in the blocking check
3. **Result**: Content that times out during moderation passes through as 'flagged' instead of being blocked

---

## Moderation Flow Analysis

### Step 2 (Form Display) - WARNING ONLY
```
User uploads image
    ↓
ContentGenerationService.generate_content(include_moderation=False)
    ↓
VisionModerationService.moderate_image() called separately for early warning
    ↓
If flagged: Sets `image_warning` in session (user sees WARNING, not blocked)
    ↓
User can still proceed to submit
```

### Form Submission (Actual Blocking)
```
User clicks Submit
    ↓
upload_submit() view
    ↓
ModerationOrchestrator.moderate_prompt(prompt)
    ↓
3 layers: profanity → openai text → openai_vision
    ↓
_determine_overall_status() checks for 'rejected' in statuses
    ↓
If 'rejected': Content is BLOCKED
If 'pending_review': Content is FLAGGED but NOT blocked  ← BUG
If 'approved': Content is published
```

---

## Breaking Change Timeline

| Version | Behavior |
|---------|----------|
| Working commit (`d0951f6`) | Timeouts would raise exception, handled differently |
| L8-TIMEOUT changes | Added graceful degradation with `status: 'pending_review'` |
| Current | Timeouts bypass blocking logic, NSFW can slip through |

---

## Recommended Fix

**Option A: Change timeout status to 'rejected' (Conservative - Recommended)**

```python
except (APITimeoutError, APIConnectionError) as e:
    logger.warning(f"Vision moderation timeout: {str(e)}")
    return {
        'timeout': True,
        'is_safe': False,
        'status': 'rejected',  # BLOCK on timeout for safety
        'flagged_categories': ['timeout'],
        'severity': 'high',    # Changed from 'low'
        'confidence_score': 0.0,
        'explanation': 'Moderation service timed out - content blocked for safety',
    }
```

**Option B: Update orchestrator to also block on 'pending_review'**

```python
if 'rejected' in statuses or 'pending_review' in statuses:
    overall_status = 'rejected'
    requires_review = True
```

**Recommendation:** Option A is preferred because:
1. Maintains separation of concerns
2. "Fail closed" security principle - if moderation can't verify, block
3. Users can re-upload if legitimate content times out

---

## Files Examined

| File | Status | Notes |
|------|--------|-------|
| `prompts/views/upload_views.py` | ✅ No change | `include_moderation=False` in both versions |
| `prompts/services/orchestrator.py` | ✅ No change | Blocking logic intact |
| `prompts/services/cloudinary_moderation.py` | ⚠️ **BREAKING CHANGE** | Timeout returns `pending_review` |
| `prompts/services/content_generation.py` | ✅ No change | Not involved in blocking |

---

## Conclusion

**Root Cause:** The L8-TIMEOUT feature introduced exception handlers that return `status: 'pending_review'` when the OpenAI Vision API times out. Since the orchestrator's blocking logic only checks for `status: 'rejected'`, content that times out during moderation is NOT blocked.

**Impact:** Hardcore NSFW content can slip through if:
1. The moderation API times out (30 second timeout)
2. Network issues cause connection errors

**Fix Priority:** HIGH - This is a security issue affecting content moderation.

**Estimated Fix Time:** 15 minutes (change two return statements)

---

**Report Generated:** January 3, 2026
**Investigation Type:** NSFW Gate Analysis
**Status:** Ready for implementation
