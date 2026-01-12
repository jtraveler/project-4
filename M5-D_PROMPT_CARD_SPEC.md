# M5-D: Add Aspect Ratio to _prompt_card.html

## Context
Phase M5 prevents Cumulative Layout Shift. This spec adds CSS aspect-ratio to gallery videos and thumbnails.

## File
`prompts/templates/prompts/partials/_prompt_card.html`

---

## Edit 1: Video Element (Lines ~129-140)

**Find:**
```html
                {% if prompt.is_video %}
                    <!-- Video element (hidden initially, B2 first, Cloudinary fallback) -->
                    <video class="gallery-video"
                           muted
                           loop
                           playsinline
                           preload="none"
                           width="440"
                           height="auto"
                           data-src="{{ prompt.display_video_url|default:prompt.get_video_url }}">
                        <source data-src="{{ prompt.display_video_url|default:prompt.get_video_url }}" type="video/mp4">
                    </video>
```

**Replace with:**
```html
                {% if prompt.is_video %}
                    <!-- Video element (hidden initially, B2 first, Cloudinary fallback) -->
                    <video class="gallery-video"
                           muted
                           loop
                           playsinline
                           preload="none"
                           {% if prompt.video_width and prompt.video_height %}
                           style="aspect-ratio: {{ prompt.video_width }} / {{ prompt.video_height }};"
                           width="{{ prompt.video_width }}"
                           height="{{ prompt.video_height }}"
                           {% else %}
                           width="440"
                           height="auto"
                           {% endif %}
                           data-src="{{ prompt.display_video_url|default:prompt.get_video_url }}">
                        <source data-src="{{ prompt.display_video_url|default:prompt.get_video_url }}" type="video/mp4">
                    </video>
```

---

## Edit 2: Video Thumbnail (Lines ~142-155)

**Find:**
```html
                    <!-- Video thumbnail (B2 first, Cloudinary fallback) -->
                    <img class="video-thumbnail"
                         src="{{ prompt.display_video_thumb_url|default:prompt.get_thumbnail_url }}"
                         srcset="{{ prompt.display_thumb_url|default:prompt.display_video_thumb_url }} 300w,
                                 {{ prompt.display_medium_url|default:prompt.display_video_thumb_url }} 600w"
                         sizes="(max-width: 500px) 100vw,
                                (max-width: 800px) 50vw,
                                (max-width: 1100px) 33vw,
                                25vw"
                         alt="{{ prompt.title }}"
                         width="440"
                         height="auto"
                         {% if forloop.first %}loading="eager"{% else %}loading="lazy"{% endif %}
                         decoding="async">
```

**Replace with:**
```html
                    <!-- Video thumbnail (B2 first, Cloudinary fallback) -->
                    <img class="video-thumbnail"
                         src="{{ prompt.display_video_thumb_url|default:prompt.get_thumbnail_url }}"
                         srcset="{{ prompt.display_thumb_url|default:prompt.display_video_thumb_url }} 300w,
                                 {{ prompt.display_medium_url|default:prompt.display_video_thumb_url }} 600w"
                         sizes="(max-width: 500px) 100vw,
                                (max-width: 800px) 50vw,
                                (max-width: 1100px) 33vw,
                                25vw"
                         alt="{{ prompt.title }}"
                         {% if prompt.video_width and prompt.video_height %}
                         style="aspect-ratio: {{ prompt.video_width }} / {{ prompt.video_height }};"
                         width="{{ prompt.video_width }}"
                         height="{{ prompt.video_height }}"
                         {% else %}
                         width="440"
                         height="auto"
                         {% endif %}
                         {% if forloop.first %}loading="eager"{% else %}loading="lazy"{% endif %}
                         decoding="async">
```

---

## Verification
Browse homepage with video prompts, inspect elements - both video and thumbnail should have:
- `style="aspect-ratio: X / Y;"` (when dimensions exist)
- Fallback to `width="440" height="auto"` (for old videos without dimensions)

## Done
M5 Phase Complete! Run full test:
1. Upload new video
2. Check dimensions in database
3. Verify no layout shift on detail page and gallery
