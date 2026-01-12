# M5-B: Save Video Dimensions in upload_views.py

## Context
Phase M5 adds video dimension extraction. M5-A stored dimensions in session. This spec reads them and saves to the Prompt model.

## File
`prompts/views/upload_views.py`

## Function
`upload_submit()` (starts around line 400)

---

## Edit 1: Read Dimensions from Session (Around line ~430)

**Find these lines (in the B2 video URL section):**
```python
        b2_video = request.session.get('upload_b2_video', '')
        b2_video_thumb = request.session.get('upload_b2_video_thumb', '')
```

**Add immediately after:**
```python
        # Phase M5: Get video dimensions from session
        video_width = request.session.get('upload_video_width')
        video_height = request.session.get('upload_video_height')
```

---

## Edit 2: Save Dimensions to Model (Around lines ~597-599)

**Find:**
```python
            prompt.b2_video_url = b2_video or b2_original
            prompt.b2_video_thumb_url = b2_video_thumb
            logger.info(f"Set B2 video URL: {prompt.b2_video_url[:50]}..." if prompt.b2_video_url else "No B2 video URL")
```

**Replace with:**
```python
            prompt.b2_video_url = b2_video or b2_original
            prompt.b2_video_thumb_url = b2_video_thumb
            # Phase M5: Save video dimensions to model
            if video_width and video_height:
                prompt.video_width = video_width
                prompt.video_height = video_height
            logger.info(f"Set B2 video URL: {prompt.b2_video_url[:50]}..., dimensions: {video_width}x{video_height}" if prompt.b2_video_url else "No B2 video URL")
```

---

## Verification
After edits, search the file for "video_width" - should appear 3 times:
1. Reading from session
2. Saving to prompt.video_width
3. In logger.info message

## Done
Proceed to M5-C (prompt_detail.html) after this spec is complete.
