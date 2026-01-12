# M5-A: Extract Video Dimensions in api_views.py

## Context
Phase M5 adds video dimension extraction to prevent Cumulative Layout Shift (CLS). The model fields and migration are already complete. This spec adds dimension extraction to `b2_upload_complete()`.

## File
`prompts/views/api_views.py`

## Function
`b2_upload_complete()` (starts around line 780)

---

## Edit 1: Update Import (Line ~841)

**Find:**
```python
from prompts.services.video_processor import extract_thumbnail
```

**Replace with:**
```python
from prompts.services.video_processor import extract_thumbnail, get_video_metadata
```

---

## Edit 2: Extract Dimensions After Writing Video (After line ~857)

**Find this block:**
```python
                # Write video to temp file
                with open(temp_video_path, 'wb') as f:
                    f.write(response.content)

                # Extract thumbnail
```

**Replace with:**
```python
                # Write video to temp file
                with open(temp_video_path, 'wb') as f:
                    f.write(response.content)

                # Phase M5: Extract video dimensions for CLS prevention
                video_width = None
                video_height = None
                try:
                    metadata = get_video_metadata(temp_video_path)
                    video_width = metadata.get('width')
                    video_height = metadata.get('height')
                    logger.info(f"Extracted video dimensions: {video_width}x{video_height}")
                except Exception as e:
                    logger.warning(f"Failed to extract video dimensions: {e}")

                # Extract thumbnail
```

---

## Edit 3: Store Dimensions in Session (Lines ~891-897)

**Find:**
```python
    # VIDEO FIX: Set video-specific session keys that upload_submit expects
    if is_video:
        request.session['upload_b2_video'] = urls['original']  # Original video URL
        request.session['upload_b2_video_thumb'] = urls.get('thumb', '')  # Video thumbnail
        request.session['upload_is_b2'] = True  # Mark as B2 upload
        logger.info(f"Video upload session keys set - video: {urls['original'][:50]}, thumb: {urls.get('thumb', '')[:50] if urls.get('thumb') else 'None'}")
```

**Replace with:**
```python
    # VIDEO FIX: Set video-specific session keys that upload_submit expects
    if is_video:
        request.session['upload_b2_video'] = urls['original']  # Original video URL
        request.session['upload_b2_video_thumb'] = urls.get('thumb', '')  # Video thumbnail
        request.session['upload_is_b2'] = True  # Mark as B2 upload
        # Phase M5: Store video dimensions in session
        request.session['upload_video_width'] = video_width
        request.session['upload_video_height'] = video_height
        logger.info(f"Video upload session keys set - video: {urls['original'][:50]}, thumb: {urls.get('thumb', '')[:50] if urls.get('thumb') else 'None'}, dimensions: {video_width}x{video_height}")
```

---

## Edit 4: Add Dimensions to JSON Response (Lines ~912-918)

**Find:**
```python
    return JsonResponse({
        'success': True,
        'filename': filename,
        'urls': urls,
        'is_video': is_video,
        'variants_pending': variants_pending,
    })
```

**Replace with:**
```python
    return JsonResponse({
        'success': True,
        'filename': filename,
        'urls': urls,
        'is_video': is_video,
        'variants_pending': variants_pending,
        'video_width': video_width if is_video else None,
        'video_height': video_height if is_video else None,
    })
```

---

## Verification
After edits, search the file for "video_width" - should appear 4 times:
1. In metadata extraction block
2. In session storage
3. In logger.info message  
4. In JSON response

## Done
Proceed to M5-B (upload_views.py) after this spec is complete.
