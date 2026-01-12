# M5-C: Add Aspect Ratio to prompt_detail.html

## Context
Phase M5 prevents Cumulative Layout Shift by providing video dimensions upfront. This spec adds CSS aspect-ratio to the detail page video.

## File
`prompts/templates/prompts/prompt_detail.html`

---

## Edit 1: Add Dimensions to Video Element (Lines ~55-65)

**Find:**
```html
                    {% if prompt.display_video_url %}
                        <!-- Video Display (B2 or Cloudinary) -->
                        <video controls class="hero-video"
                            poster="{{ prompt.display_video_thumb_url|default:prompt.get_thumbnail_url }}"
                            preload="metadata"
                            autoplay
                            loop
                            muted>
                            <source src="{{ prompt.display_video_url }}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
```

**Replace with:**
```html
                    {% if prompt.display_video_url %}
                        <!-- Video Display (B2 or Cloudinary) -->
                        <video controls class="hero-video"
                            poster="{{ prompt.display_video_thumb_url|default:prompt.get_thumbnail_url }}"
                            preload="metadata"
                            autoplay
                            loop
                            muted
                            {% if prompt.video_width and prompt.video_height %}
                            style="aspect-ratio: {{ prompt.video_width }} / {{ prompt.video_height }};"
                            width="{{ prompt.video_width }}"
                            height="{{ prompt.video_height }}"
                            {% endif %}>
                            <source src="{{ prompt.display_video_url }}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
```

---

## Verification
View a video prompt in browser, inspect the `<video>` element - should have:
- `style="aspect-ratio: X / Y;"`
- `width` and `height` attributes

## Done
Proceed to M5-D (_prompt_card.html) after this spec is complete.
