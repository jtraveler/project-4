# DESIGN: Category Taxonomy Revamp (Phase 2B)

**Author:** Claude.ai Session 74+
**Date:** February 9, 2026
**Status:** Design — Approved for Implementation
**Location:** Save to `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md`

---

## 1. Problem Statement

The current category system has critical gaps that limit content discoverability, related prompt accuracy, and SEO performance:

1. **No people descriptors** — The platform is heavily portrait-driven, yet there's no structured way to find prompts by gender, ethnicity, or age.
2. **No physical features** — Vitiligo, heterochromia, natural hair, hijab, pregnancy — all massive search trends in AI art with no structured representation.
3. **No professions** — Military, healthcare, royal/regal — stock platforms have entire filter categories for professions. We have none.
4. **No seasons** — Autumn aesthetic, summer vibes, winter portraits — huge search categories treated as an afterthought.
5. **Holidays lumped together** — "Seasonal & Holiday" treats Valentine's Day and Halloween as equivalent.
6. **No mood/atmosphere axis** — "Dark fantasy" and "bright whimsical fantasy" both land in the same category.
7. **No color-based discovery** — Users search by palette but we have no structured data for it.
8. **Missing high-demand niches** — AI Influencer/Avatar, Boudoir, Headshot, LinkedIn headshot are massive search categories with no representation.
9. **AI descriptions miss SEO synonyms** — "black woman" without "African-American" misses major search traffic. Same for Hispanic/Latino, Indian/Desi.
10. **Tag limit too low** — 5 tags can't cover subject + style + demographics + mood.
11. **Category limit too low** — 3 categories per prompt constrains scoring accuracy.

## 2. Design Goals

- **Comprehensive discoverability:** Users can find content along any axis — subject, demographics, mood, color, style, occasion, profession, physical features.
- **Rich related scoring:** More taxonomy data = more accurate "You Might Also Like" recommendations.
- **SEO coverage:** AI-generated descriptions and tags include synonym variants for maximum search engine capture.
- **Future filter UI:** Taxonomy supports multi-axis browse/filter pages.
- **Zero hallucination tolerance:** Backend validation ensures only valid taxonomy values are ever stored, regardless of what the AI returns.
- **Scalable:** Easy to add new categories/descriptors without schema changes.

## 3. Architecture: Three-Tier Taxonomy

### Tier 1: Subject Categories (WHAT the image is)

Existing `SubjectCategory` model, expanded from 25 to 46 entries. Same M2M relationship on Prompt.

**Purpose:** Primary content classification. What is this image depicting? What genre does it belong to?
**Limit per prompt:** Up to 5 (increased from 3).

### Tier 2: Subject Descriptors (WHO, HOW, WHEN, WHERE)

New `SubjectDescriptor` model with a `descriptor_type` field for grouping. Separate M2M on Prompt.

**Purpose:** Demographics, mood, color, physical features, profession, season, holiday, and setting. Used for filtering and scoring.
**Limit per prompt:** Up to 10.
**Organized into 10 descriptor types** (see Section 4.2).

### Tier 3: Tags (SEO keywords)

Existing tag system, limit increased from 5 to 10.

**Purpose:** Free-form search engine optimization. Includes synonyms and long-tail keywords.
**Limit per prompt:** Up to 10 (increased from 5).

---

## 4. Complete Taxonomy

### 4.1 Subject Categories (Tier 1) — 46 Total

#### Kept from Existing 25 (24 kept, 1 removed, 1 renamed):

| # | Category | Notes |
|---|----------|-------|
| 1 | Portrait | |
| 2 | Fashion & Style | |
| 3 | Landscape & Nature | |
| 4 | Urban & City | |
| 5 | Sci-Fi & Futuristic | |
| 6 | Fantasy & Mythical | |
| 7 | Wildlife & Nature Animals | Renamed from "Animals & Wildlife" — lions, eagles, ocean life |
| 8 | Interior & Architecture | |
| 9 | Abstract & Artistic | |
| 10 | Food & Drink | |
| 11 | Vehicles & Transport | |
| 12 | Horror & Dark | |
| 13 | Anime & Manga | |
| 14 | Photorealistic | |
| 15 | Digital Art | |
| 16 | Illustration | |
| 17 | Product & Commercial | |
| 18 | Sports & Action | |
| 19 | Music & Entertainment | |
| 20 | Retro & Vintage | |
| 21 | Minimalist | |
| 22 | Macro & Close-up | |
| 23 | Text & Typography | |
| 24 | Comedy & Humor | Renamed from "Meme & Humor" — broader comedic/satirical/parody content |

**REMOVED:** ~~Seasonal & Holiday~~ → Split into individual holidays (now in Tier 2 descriptors).

**RENAMED:** ~~Wedding & Bridal~~ → **Wedding & Engagement** (engagement shoots are a huge overlapping visual category).

**RENAMED:** ~~Animals & Wildlife~~ → **Wildlife & Nature Animals** (narrowed scope — domestic pets split into separate category).

**RENAMED:** ~~Meme & Humor~~ → **Comedy & Humor** (broader — covers parody, satire, caricature, comedic scenes, not just internet memes).

#### New Categories (22 added):

| # | Category | Description |
|---|----------|-------------|
| 25 | Wedding & Engagement | Weddings, engagement shoots, bridal, rings, proposals |
| 26 | Couple & Romance | Romantic couples, love themes, date imagery |
| 27 | Group & Crowd | Multiple people as the subject |
| 28 | Cosplay | Costume play, character recreation |
| 29 | Tattoo & Body Art | Tattoos, body paint, body modification as focus |
| 30 | Underwater | Underwater photography/art |
| 31 | Aerial & Drone View | Bird's-eye, overhead, satellite perspectives |
| 32 | Concept Art | Pre-production art, environment/character concepts |
| 33 | Wallpaper & Background | Images designed as device wallpapers or backgrounds |
| 34 | Character Design | Original character creation, character sheets |
| 35 | Pixel Art | Pixel-based art style |
| 36 | 3D Render | 3D modeled/rendered imagery |
| 37 | Watercolor & Traditional | Traditional art media (watercolor, oil, pencil, etc.) |
| 38 | Surreal & Dreamlike | Surrealism, impossible scenes, dreamscapes |
| 39 | AI Influencer / AI Avatar | Polished virtual influencer/avatar portraits |
| 40 | Headshot | Shoulders-up professional/casting portraits |
| 41 | Boudoir | Intimate, lingerie-focused photography genre |
| 42 | YouTube Thumbnail / Cover Art | Bold, eye-catching thumbnail/cover designs for YouTube, podcasts, social media |
| 43 | Pets & Domestic Animals | Pet portraits, dogs, cats, horses, domestic animal photography |
| 44 | Maternity Shoot | Styled pregnancy photography (flowing gowns, belly poses, dreamy lighting) |
| 45 | 3D Photo / Forced Perspective | Fisheye, depth-layered compositions designed for parallax/pop-out effect |
| 46 | Photo Restoration | AI-restored, colorized, or enhanced old/damaged photographs |

#### Category Detection Criteria — Special Cases

**AI Influencer / AI Avatar (Category #39):**

ASSIGN when ALL of these are true:
- Single person is the clear subject
- Polished, idealized, or glamorous appearance
- Fashion-conscious styling (designer clothes, accessories, makeup)
- At least one of: luxury setting, aspirational lifestyle elements, professional-grade lighting, social media-ready framing (selfie angle, eye contact, confident pose)

DO NOT ASSIGN when:
- The person looks average/everyday without styling emphasis
- It's a character design or fantasy character (use "Character Design" instead)
- It's a gritty/raw/documentary-style portrait
- The mood is dark, horror, or unsettling
- Multiple people are the focus (use "Couple & Romance" or "Group & Crowd")

**Headshot (Category #40):**

ASSIGN when:
- Framing is shoulders-up or head-and-shoulders
- Single person is the subject
- Relatively clean or simple background
- Professional, casting, or profile-photo intent

DO NOT ASSIGN when:
- Full-body or environmental portrait (use "Portrait")
- Fantasy/cosplay character (use "Character Design" or "Cosplay")

**LinkedIn Profile Photo Detection (NOT a separate category — SEO only):**
This is triggered by professional styling, NOT by framing. A LinkedIn photo can be a headshot, half-body, or environmental portrait — users crop to fit.

Include "LinkedIn headshot," "LinkedIn profile photo," and "professional headshot" in the AI description and tags when ALL of these are true:
- A person is the clear subject (any framing — headshot, half-body, environmental)
- The person wears business, smart-casual, or professional attire
- The mood is "Professional / Corporate" OR the profession is "Business / Executive"

Add tags: `linkedin-headshot`, `linkedin-profile-photo`, `professional-headshot`, `corporate-portrait`, `business-portrait`

Examples that SHOULD trigger LinkedIn SEO terms:
- Shoulders-up headshot in a blazer with studio background ✅
- Half-body shot in business attire at a coffee shop ✅
- Environmental portrait of an executive in a boardroom ✅
- Outdoor portrait in smart-casual with bokeh background ✅

Examples that should NOT trigger:
- Headshot of an actor/model for a casting portfolio (professional but not corporate)
- Fashion editorial in a suit (styled for fashion, not LinkedIn)
- Military uniform portrait (professional but not corporate — different niche)

**Boudoir (Category #41):**

ASSIGN when the image shows the boudoir photography genre — at least 2-3 of:
- Lingerie, swimwear, or revealing clothing as the focal point
- Intimate setting (bedroom, boudoir, bath, silk/satin fabrics)
- Sensual posing (reclining, over-shoulder gaze, body-emphasis composition)
- Soft/dramatic lighting designed to highlight physical form
- Pin-up or burlesque styling/costume

CRITICAL: Boudoir is about **intent and styling**, not body type or fitness level. The image must be deliberately styled to be alluring through lighting, pose, and composition.

DO NOT ASSIGN based on:
- Body type or fitness level alone
- Casual clothing in non-sensual context
- Beach/pool scenes without sensual styling (that's "Beach / Coastal" setting descriptor)
- Couples in intimate embrace (use "Couple & Romance" category + "Sensual / Alluring" mood descriptor)
- Medical or anatomical imagery

**YouTube Thumbnail / Cover Art (Category #42):**

ASSIGN when the image is a designed composition intended as a clickable cover or preview — at least 2 of:
- Bold text overlay as a key visual element
- Exaggerated facial expression (shock, excitement, curiosity, pointing)
- Bright, saturated, attention-grabbing colors
- Landscape orientation (16:9 or similar widescreen)
- Split composition (before/after, vs, reaction format)
- Arrow, circle, or highlight graphics drawing attention to elements
- Clear "click-bait" design intent — composed to grab attention at small sizes

DO NOT ASSIGN when:
- A raw photograph with no design elements (even if landscape orientation)
- Text & Typography that's artistic/decorative rather than click-oriented
- A regular portrait that happens to show an expressive face
- Wallpaper/background designs (use "Wallpaper & Background" instead)

Often pairs with: "Text & Typography" (text overlays), "Portrait" (featured face), "Bright & Cheerful" or "Energetic" mood, "Neon / Vibrant" or "High Contrast" color.

SEO terms to include in description when assigned: "YouTube thumbnail," "video thumbnail," "thumbnail design," "cover art," "podcast cover," "social media graphic," "click-worthy"

Tags when assigned: `youtube-thumbnail`, `thumbnail-design`, `cover-art`, `video-thumbnail`, `podcast-cover`, `social-media-graphic`

**Maternity Shoot (Category #44):**

ASSIGN when the image is styled as a deliberate maternity photoshoot — the pregnant subject is the focus AND at least 2 of:
- Flowing, elegant, or sheer clothing (gowns, draped fabric, bodycon dress)
- Hands cradling or framing the belly
- Soft, dreamy, or golden hour lighting
- Nature or studio backdrop specifically chosen for the shoot
- Partner tenderly involved (hands on belly, embracing from behind)
- Baby-related props (ultrasound, tiny shoes, letter board, nursery setting)

CRITICAL: Maternity Shoot is about the *photoshoot genre*, not just "a pregnant person is visible." A pregnant woman in a grocery store is NOT a maternity shoot — that prompt gets only the "Pregnancy / Maternity" physical feature descriptor.

DO NOT ASSIGN when:
- Pregnant person in a casual/everyday scene (assign "Pregnancy / Maternity" descriptor only)
- Medical or clinical pregnancy imagery
- A person who appears pregnant but the pregnancy isn't the subject of the shot

Often pairs with: "Portrait", "Couple & Romance" (partner shots), "Boudoir" (maternity boudoir sub-genre), "Dreamy / Ethereal" mood, "Outdoor / Nature" or "Studio / Indoor" setting. ALWAYS paired with "Pregnancy / Maternity" physical feature descriptor.

SEO terms to include in description: "maternity shoot," "maternity photography," "pregnancy photoshoot," "baby bump," "expecting mother," "maternity portrait"

Tags when assigned: `maternity-shoot`, `maternity-photography`, `pregnancy-photoshoot`, `baby-bump`, `expecting-mother`, `maternity-portrait`

**3D Photo / Forced Perspective (Category #45):**

ASSIGN when the image uses deliberate depth manipulation for a pop-out or immersive effect — at least 2 of:
- Visible wide-angle or fisheye lens distortion (10-16mm effect)
- Object or body part projected toward the viewer in extreme foreground (hand, foot, fist, bottle)
- Strong three-layer depth separation (distinct foreground, midground, background planes)
- Subject or objects appear to "break" a frame boundary (phone screen, portal, circular opening)
- Counter-angle or worm's-eye perspective shooting upward
- Dramatic scale distortion from forced perspective (giant hand, tiny buildings/people)
- Levitating objects or debris creating radial depth layers

DO NOT ASSIGN when:
- A standard wide-angle landscape with no intentional depth play
- Normal portrait with shallow depth of field (bokeh ≠ forced perspective)
- Aerial/drone shots (that's "Aerial & Drone View")
- Regular fisheye photo without intentional depth layering for 3D effect

Often pairs with: "Portrait" (most are people-focused), "Surreal & Dreamlike" (levitation, destruction), "Urban & City" (urban canyon backgrounds), "Cinematic" or "Dramatic" mood, "High Contrast" or "Neon / Vibrant" color.

SEO terms to include in description: "3D photo," "forced perspective," "fisheye portrait," "depth photography," "pop-out effect," "immersive photography," "Facebook 3D," "parallax photo"

Tags when assigned: `3d-photo`, `forced-perspective`, `facebook-3d`, `3d-effect`, `fisheye-portrait`, `depth-photography`, `pop-out-effect`, `parallax-photo`

**Photo Restoration (Category #46):**

ASSIGN when the image shows evidence of AI restoration, colorization, or enhancement of an old/damaged photograph — at least 2 of:
- Before/after split or comparison layout
- Colorized black-and-white photograph with period-specific clothing/settings
- Visibly enhanced old photograph (sharper faces, cleaner backgrounds than original era)
- Historical/period-specific context (clothing, hairstyles, settings) with modern image clarity
- Old photographic formats (daguerreotype borders, scalloped edges, studio backdrops) with enhanced quality
- Visible repair of damage (scratches, tears, water damage, fading restored)

DO NOT ASSIGN when:
- A newly created image in vintage style (that's "Retro & Vintage")
- An aged/deteriorated effect applied to modern content (that's "Vintage / Aged Film" mood descriptor)
- A regular old photograph with no restoration evident
- A sepia-toned new photo designed to look old

Often pairs with: "Portrait" (most restored photos are family portraits), "Retro & Vintage" (period content), "Vintage / Aged Film" mood (retains some aged quality).

SEO terms to include in description: "photo restoration," "AI restoration," "restored old photo," "colorized photo," "photo enhancement," "vintage restoration," "AI colorize"

Tags when assigned: `photo-restoration`, `ai-restoration`, `restore-old-photo`, `colorized-photo`, `photo-enhancement`, `old-photo-restored`, `ai-colorize`, `vintage-restoration`

**Comedy & Humor (Category #24, renamed from "Meme & Humor"):**

ASSIGN when the image is intentionally comedic, satirical, or humorous:
- Internet memes, meme formats, meme templates
- Parody or satirical art
- Intentionally comedic compositions or scenarios
- Caricatures and exaggerated humor
- Funny juxtapositions or absurdist comedy scenes
- Slapstick or physical comedy depictions

DO NOT ASSIGN when:
- Merely colorful or playful (that's "Whimsical" mood)
- Strange or weird but not intentionally funny (that might be "Surreal & Dreamlike")
- A character smiling or laughing (that's just a happy portrait)

SEO terms when applicable: "funny AI art," "AI meme," "comedy art," "parody," "satirical art"

Tags when assigned: `meme`, `funny`, `comedy`, `humor`, `parody`, `satirical-art`, `ai-meme`

---

### 4.2 Subject Descriptors (Tier 2) — 10 Types, ~109 Total

Each descriptor belongs to exactly one `descriptor_type`. The AI assigns descriptors organized by type, with per-type rules.

---

#### Type 1: Gender Presentation (`gender`) — 3 descriptors

**Per-prompt limit:** 0-1. Only assign if a person is clearly visible.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 1 | Male | man, male, masculine, guy, boy |
| 2 | Female | woman, female, feminine, girl, lady |
| 3 | Androgynous | androgynous, non-binary, gender-neutral, unisex |

---

#### Type 2: Ethnicity / Heritage (`ethnicity`) — 11 descriptors

**Per-prompt limit:** 0-1. Only assign if a person is clearly visible AND ethnicity is identifiable with HIGH confidence (>90%). If ambiguous, DO NOT assign. It is always better to omit than to guess wrong.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 4 | African-American / Black | african-american, black, afro, black woman, black man |
| 5 | African | african, west african, east african, nigerian, ethiopian, kenyan |
| 6 | Hispanic / Latino | hispanic, latino, latina, latinx, mexican, colombian, brazilian |
| 7 | East Asian | east asian, chinese, japanese, korean, taiwanese |
| 8 | South Asian / Indian / Desi | south asian, indian, desi, pakistani, bangladeshi, sri lankan |
| 9 | Southeast Asian | southeast asian, thai, vietnamese, filipino, indonesian, malaysian |
| 10 | Middle Eastern / Arab | middle eastern, arab, persian, turkish, iranian |
| 11 | Caucasian / White | caucasian, white, european, scandinavian |
| 12 | Indigenous / Native | indigenous, native american, first nations, aboriginal, maori |
| 13 | Pacific Islander | pacific islander, polynesian, hawaiian, samoan |
| 14 | Mixed / Multiracial | mixed race, multiracial, biracial, multicultural |

---

#### Type 3: Age Range (`age`) — 6 descriptors

**Per-prompt limit:** 0-1. Only assign if a person is clearly visible.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 15 | Baby / Infant | baby, infant, newborn, toddler |
| 16 | Child | child, kid, young, little, elementary |
| 17 | Teen | teen, teenager, adolescent, youth |
| 18 | Young Adult | young adult, 20s, millennial, young woman, young man |
| 19 | Middle-Aged | middle-aged, mature, 40s, 50s |
| 20 | Senior / Elderly | senior, elderly, old, aging, grandparent, wise |

---

#### Type 4: Physical Features (`features`) — 17 descriptors

**Per-prompt limit:** 0-3. Only assign features that are visually prominent and intentionally part of the image's aesthetic. Do NOT assign every minor detail — only features that a user would search for.

| # | Name | Why It's Included |
|---|------|-------------------|
| 21 | Vitiligo | Trending AI art aesthetic, representation, high search volume |
| 22 | Albinism | Unique visual aesthetic, representation |
| 23 | Heterochromia | Extremely popular in AI art (different colored eyes) |
| 24 | Freckles | Major AI art aesthetic trend |
| 25 | Natural Hair / Afro | Massive search category, cultural significance |
| 26 | Braids / Locs | High demand, especially in fashion AI art |
| 27 | Hijab / Headscarf | Representation, huge global market |
| 28 | Bald / Shaved Head | Common search filter on stock photography sites |
| 29 | Glasses / Eyewear | High search volume as a style element |
| 30 | Beard / Facial Hair | Common portrait modifier |
| 31 | Colorful / Dyed Hair | Huge in AI art — pink hair, blue hair, rainbow, etc. |
| 32 | Wheelchair User | Disability representation |
| 33 | Prosthetic | Trending in sci-fi/cyberpunk crossover and representation |
| 34 | Scarring | Both representation and artistic/warrior aesthetic |
| 35 | Plus Size / Curvy | Body positivity movement, very high search demand |
| 36 | Athletic / Muscular | Fitness content, physique art |
| 37 | Pregnancy / Maternity | Enormous stock photography category |

---

#### Type 5: Profession / Role (`profession`) — 17 descriptors

**Per-prompt limit:** 0-2. Only assign if the person is clearly depicted in a professional role through uniform, equipment, or setting context. These are visual identifiers, not assumptions.

| # | Name | Why It's Included |
|---|------|-------------------|
| 38 | Military / Armed Forces | Uniforms, patriotic content, very high demand |
| 39 | Healthcare / Medical | Doctor, nurse, scrubs — massive commercial use |
| 40 | First Responder | Police, firefighter, EMT — patriotic and commercial |
| 41 | Chef / Culinary | Food content crossover, restaurant industry |
| 42 | Business / Executive | Corporate portraits, LinkedIn content |
| 43 | Scientist / Lab | Education and tech content |
| 44 | Artist / Creative | Meta-popular in AI art communities |
| 45 | Teacher / Education | Commercial use, back-to-school content |
| 46 | Athlete / Sports | Sports & Action category crossover |
| 47 | Construction / Blue Collar | Representation, commercial use |
| 48 | Pilot / Aviation | Aspirational, uniform aesthetic |
| 49 | Musician / Performer | Entertainment crossover |
| 50 | Royal / Regal | Huge AI art niche — queens, kings, crowns, thrones |
| 51 | Warrior / Knight | Fantasy crossover, extremely popular in AI art |
| 52 | Astronaut | Sci-fi crossover, aspirational |
| 53 | Cowboy / Western | Strong niche aesthetic |
| 54 | Ninja / Samurai | Anime and fantasy crossover |

---

#### Type 6: Mood / Atmosphere (`mood`) — 15 descriptors

**Per-prompt limit:** 1-2. Almost every image has a mood. Assign the 1-2 most dominant moods.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 55 | Dark & Moody | dark, moody, noir, shadow, low-key, brooding |
| 56 | Bright & Cheerful | bright, cheerful, sunny, happy, upbeat, vibrant |
| 57 | Dreamy / Ethereal | dreamy, ethereal, soft, hazy, otherworldly, fairytale |
| 58 | Cinematic | cinematic, film, movie-like, widescreen, theatrical |
| 59 | Dramatic | dramatic, intense, bold, powerful, striking |
| 60 | Peaceful / Serene | peaceful, serene, calm, tranquil, zen, meditative |
| 61 | Romantic | romantic, love, intimate, tender, affectionate |
| 62 | Mysterious | mysterious, enigmatic, hidden, fog, suspense, cryptic |
| 63 | Energetic | energetic, dynamic, action, movement, fast, explosive |
| 64 | Melancholic | melancholic, sad, somber, nostalgic, lonely, wistful |
| 65 | Whimsical | whimsical, playful, quirky, cute, charming, lighthearted |
| 66 | Eerie / Unsettling | eerie, unsettling, creepy, uncanny, disturbing, haunting |
| 67 | Sensual / Alluring | sensual, alluring, seductive, intimate, sultry, sexy |
| 68 | Professional / Corporate | professional, corporate, business, executive, polished, formal |
| 69 | Vintage / Aged Film | vintage photo, aged, film grain, sepia, faded, old photograph, antique, analog, daguerreotype |

**Note on "Sensual / Alluring":** This is a MOOD, independent of the "Boudoir" category. It can pair with ANY category:
- Solo lingerie shoot → Category: Boudoir + Mood: Sensual / Alluring
- Couple in intimate embrace → Category: Couple & Romance + Mood: Sensual / Alluring
- Sexy fashion editorial → Category: Fashion & Style + Mood: Sensual / Alluring
- Seductive dark portrait → Category: Portrait + Mood: Sensual / Alluring + Dark & Moody

**Note on "Professional / Corporate":** Covers LinkedIn profile photos, business portraits, corporate settings. This mood is a key trigger for LinkedIn SEO terms — when combined with a person in business attire, it triggers "LinkedIn headshot" and related tags regardless of whether the image is a headshot, half-body, or environmental portrait.

---

#### Type 7: Color Palette (`color`) — 10 descriptors

**Per-prompt limit:** 1-2. Almost every image has a dominant color palette. Assign the 1-2 most prominent.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 70 | Warm Tones | warm, golden, amber, sunset, orange, red tones |
| 71 | Cool Tones | cool, blue, teal, ice, frost, ocean tones |
| 72 | Monochrome | monochrome, black and white, grayscale, b&w |
| 73 | Neon / Vibrant | neon, vibrant, electric, fluorescent, glowing, saturated |
| 74 | Pastel | pastel, soft colors, light, baby pink, lavender, mint |
| 75 | Earth Tones | earth tones, brown, olive, terracotta, forest, natural |
| 76 | High Contrast | high contrast, stark, bold colors, shadow play |
| 77 | Muted / Desaturated | muted, desaturated, faded, washed out, subdued |
| 78 | Dark / Low-Key | dark palette, black, shadow, underexposed, noir |
| 79 | Gold & Luxury | gold, luxury, metallic, rich, opulent, gilded |

---

#### Type 8: Holiday / Occasion (`holiday`) — 17 descriptors

**Per-prompt limit:** 0-1. Only assign if the image is CLEARLY related to a specific holiday through visual elements (decorations, symbols, colors, costumes). Do NOT assign based on vague seasonal vibes — use the Season type instead.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 80 | Valentine's Day | valentine, valentines day, hearts, february 14, cupid |
| 81 | Christmas | christmas, xmas, santa, december 25, ornaments, tree |
| 82 | Halloween | halloween, spooky, trick or treat, costume, october 31 |
| 83 | Easter | easter, easter eggs, bunny, resurrection, spring celebration |
| 84 | Thanksgiving | thanksgiving, gratitude, harvest, turkey, fall feast |
| 85 | New Year | new year, new years eve, countdown, fireworks, january 1 |
| 86 | Independence Day | independence day, 4th of july, patriotic, fireworks, american |
| 87 | St. Patrick's Day | st patricks day, irish, shamrock, leprechaun, march 17 |
| 88 | Lunar New Year | lunar new year, chinese new year, spring festival, lantern |
| 89 | Día de los Muertos | dia de los muertos, day of the dead, sugar skull, calavera |
| 90 | Mother's Day | mothers day, mom, mother, maternal, motherhood |
| 91 | Father's Day | fathers day, dad, father, paternal, fatherhood |
| 92 | Pride | pride, lgbtq, rainbow, pride month, june, equality |
| 93 | Holi | holi, festival of colors, rang, gulal, spring festival india |
| 94 | Diwali | diwali, deepavali, festival of lights, rangoli, diyas |
| 95 | Eid | eid, eid mubarak, ramadan, eid al-fitr, eid al-adha |
| 96 | Hanukkah | hanukkah, chanukah, menorah, dreidel, jewish holiday |

---

#### Type 9: Season (`season`) — 4 descriptors

**Per-prompt limit:** 0-1. Assign when the image has clear seasonal visual cues (foliage, weather, clothing, light quality). Separate from holidays — a winter portrait is not necessarily Christmas.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 97 | Spring | spring, bloom, blossom, fresh, green, renewal |
| 98 | Summer | summer, sunshine, warm, bright, vacation, tropical |
| 99 | Autumn / Fall | autumn, fall, leaves, golden, harvest, cozy, pumpkin |
| 100 | Winter | winter, snow, cold, frost, icy, cozy, fireplace |

---

#### Type 10: Setting / Environment (`setting`) — 9 descriptors

**Per-prompt limit:** 0-1. Assign the primary setting if clearly determinable.

| # | Name | Search Terms Covered |
|---|------|---------------------|
| 101 | Studio / Indoor | studio, indoor, controlled lighting, backdrop |
| 102 | Outdoor / Nature | outdoor, nature, natural light, outside |
| 103 | Urban / Street | urban, street, city, downtown, alley, metropolitan |
| 104 | Beach / Coastal | beach, coastal, ocean, seaside, tropical, shore |
| 105 | Mountain | mountain, alpine, hiking, peak, summit, highland |
| 106 | Desert | desert, sand, arid, dune, sahara, dry |
| 107 | Forest / Woodland | forest, woodland, trees, enchanted, moss, canopy |
| 108 | Space / Cosmic | space, cosmic, galaxy, stars, nebula, universe |
| 109 | Underwater | underwater, deep sea, ocean, aquatic, diving, coral |

---

### 4.3 Final Summary Table

| Tier | Model | Count | Per-Prompt Limit | Purpose |
|------|-------|-------|-----------------|---------|
| 1 - Subject Categories | `SubjectCategory` | 46 | Up to 5 | What is it? |
| 2 - Subject Descriptors | `SubjectDescriptor` | ~109 | Up to 10 | Who/how/when/where? |
| 3 - Tags | Existing tag system | Open | Up to 10 | SEO keywords |

### 4.4 Per-Type Descriptor Limits (within the overall 10 limit)

These are GUIDELINES for the AI, not hard database constraints:

| Descriptor Type | Per-Type Limit | When to Assign |
|-----------------|---------------|----------------|
| `gender` | 0-1 | Only if person clearly visible |
| `ethnicity` | 0-1 | Only if >90% confidence. OMIT if unsure. |
| `age` | 0-1 | Only if person clearly visible |
| `features` | 0-3 | Only visually prominent, intentional features |
| `profession` | 0-2 | Only if identifiable through uniform/equipment/context |
| `mood` | 1-2 | Almost every image has a mood |
| `color` | 1-2 | Almost every image has a color palette |
| `holiday` | 0-1 | Only if clearly holiday-specific |
| `season` | 0-1 | Only if clear seasonal visual cues |
| `setting` | 0-1 | If primary setting is determinable |

**Maximum possible per prompt:** gender(1) + ethnicity(1) + age(1) + features(3) + profession(2) + mood(2) + color(2) + holiday(1) + season(1) + setting(1) = 15. But the overall cap is 10, so the AI must prioritize the most relevant.

---

## 5. Data Model Changes

### 5.1 New Model: SubjectDescriptor

```python
class SubjectDescriptor(models.Model):
    DESCRIPTOR_TYPES = [
        ('gender', 'Gender Presentation'),
        ('ethnicity', 'Ethnicity / Heritage'),
        ('age', 'Age Range'),
        ('features', 'Physical Features'),
        ('profession', 'Profession / Role'),
        ('mood', 'Mood / Atmosphere'),
        ('color', 'Color Palette'),
        ('holiday', 'Holiday / Occasion'),
        ('season', 'Season'),
        ('setting', 'Setting / Environment'),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    descriptor_type = models.CharField(max_length=20, choices=DESCRIPTOR_TYPES, db_index=True)

    class Meta:
        ordering = ['descriptor_type', 'name']
        indexes = [
            models.Index(fields=['descriptor_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_descriptor_type_display()})"
```

### 5.2 Updated Prompt Model

```python
class Prompt(models.Model):
    # Existing field (no change)
    categories = models.ManyToManyField('SubjectCategory', blank=True, related_name='prompts')

    # NEW field
    descriptors = models.ManyToManyField('SubjectDescriptor', blank=True, related_name='prompts')
```

### 5.3 Migrations Required

| Migration | Type | Description |
|-----------|------|-------------|
| `0048_create_subject_descriptor` | Schema | Create `SubjectDescriptor` model + `descriptors` M2M on Prompt |
| `0049_populate_descriptors` | Data | Insert all ~109 descriptors with correct `descriptor_type` and `slug` |
| `0050_update_subject_categories` | Data | Add 22 new categories, remove "Seasonal & Holiday", rename "Wedding & Bridal" → "Wedding & Engagement", rename "Animals & Wildlife" → "Wildlife & Nature Animals", rename "Meme & Humor" → "Comedy & Humor" |

### 5.4 Admin Registration

```python
@admin.register(SubjectDescriptor)
class SubjectDescriptorAdmin(admin.ModelAdmin):
    list_display = ['name', 'descriptor_type', 'prompt_count']
    list_filter = ['descriptor_type']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def prompt_count(self, obj):
        return obj.prompts.count()
    prompt_count.short_description = 'Prompts'
```

---

## 6. Updated Scoring Algorithm

### Related Prompts Scoring (new weights)

```python
Total = (
    tag_score         * 0.20    # Was 0.35
    category_score    * 0.25    # Was 0.35
    descriptor_score  * 0.25    # NEW
    generator_score   * 0.10    # Unchanged
    engagement_score  * 0.10    # Unchanged
    recency_score     * 0.10    # Unchanged
)
```

**`descriptor_score`:** Jaccard similarity across ALL assigned descriptors (regardless of type). Two portraits of young African-American women in warm tones with cinematic mood would have high Jaccard overlap, scoring ~0.8+ on this component.

**`category_score`:** Jaccard similarity on subject categories only. Same formula as current implementation.

**Combined effect:** A prompt matching on both category AND descriptors gets up to 50% of total score from taxonomy, producing highly relevant recommendations.

---

## 7. AI Prompt — Anti-Hallucination Design

### 7.1 The Problem

Long prompts with large choice lists increase hallucination risk:
- AI invents descriptors not on the list (e.g., returns "Gladiator" instead of "Warrior / Knight")
- AI over-assigns to seem thorough
- AI guesses ethnicity incorrectly on ambiguous faces

### 7.2 Four-Layer Anti-Hallucination Strategy

**Layer 1: Structured Sectioned Prompt**

Instead of one massive wall of options, the prompt is split into clearly labeled sections with small per-section choice lists (3-17 options each). This reduces cognitive load on the model.

**Layer 2: Per-Section Rules and Limits**

Each section has explicit rules: when to assign, when NOT to assign, confidence thresholds, and maximum count per section. These are embedded directly alongside the options.

**Layer 3: Explicit Validation Instruction**

The prompt includes a hard constraint:
```
VALIDATION RULE: You MUST only return values that appear EXACTLY as written in the
lists above. Do NOT invent, modify, combine, or abbreviate values. If you are unsure
about any assignment, OMIT it. An omission is always better than an incorrect assignment.
```

**Layer 4: Backend Database Validation (Safety Net)**

Regardless of what the AI returns, the backend code validates every value against the database:
```python
# Categories
requested_categories = ai_result.get('categories', [])
valid_categories = SubjectCategory.objects.filter(name__in=requested_categories)
prompt.categories.set(valid_categories)
# Any hallucinated category name silently dropped — not in DB, not stored.

# Descriptors
requested_descriptors = []
for desc_type, names in ai_result.get('descriptors', {}).items():
    requested_descriptors.extend(names)
valid_descriptors = SubjectDescriptor.objects.filter(name__in=requested_descriptors)
prompt.descriptors.set(valid_descriptors)
# Any hallucinated descriptor name silently dropped — not in DB, not stored.
```

This means even if Layers 1-3 all fail and the AI hallucinates a value, it NEVER makes it into the database.

### 7.3 Complete AI Prompt (for tasks.py)

This is the exact prompt to send to OpenAI Vision API. It replaces the current category-only prompt.

```
Analyze this image and return a JSON object with the following fields.

VALIDATION RULE: You MUST only return values that appear EXACTLY as written in the
lists below. Do NOT invent, modify, combine, or abbreviate any value. If you are unsure
about any assignment, OMIT it entirely. An omission is always better than an incorrect
assignment.

═══════════════════════════════════════════════
FIELD 1: "title" (string)
═══════════════════════════════════════════════
A concise, SEO-optimized title for this image. Max 60 characters. 
Include the most important subject and style keywords.

═══════════════════════════════════════════════
FIELD 2: "description" (string)
═══════════════════════════════════════════════
A detailed, SEO-optimized description. 2-4 sentences. Follow these CRITICAL SEO RULES:

ETHNICITY SYNONYMS — when describing ethnicity, ALWAYS include multiple search terms:
  * "Black" → also include "African-American" (or "African" if clearly African context)
  * "Hispanic" → also include "Latino" or "Latina"
  * "Indian" → also include "South Asian" and "Desi"
  * "Asian" → specify "East Asian," "Southeast Asian," etc. when identifiable
  * "Arab" → also include "Middle Eastern"
  * "White" → also include "Caucasian" or "European" if contextually appropriate

GENDER SYNONYMS — include both specific and general:
  * Include "woman" AND "female," "man" AND "male"

NICHE TERMS — include when applicable:
  * AI Influencer images: "AI influencer," "AI avatar," "virtual influencer," "digital influencer"
  * Person + business/smart-casual attire + professional mood: "LinkedIn headshot," "LinkedIn profile photo,"
    "professional headshot," "corporate portrait" (any framing — not limited to headshots)
  * Boudoir: "boudoir photography," "intimate portrait," "sensual portrait"
  * Styled portraits: naturally mention "virtual photoshoot" when applicable
  * Holiday images: include holiday name AND season AND mood keywords

SPELLING VARIANTS — always include both US and UK spellings in descriptions and tags:
  * "coloring book" AND "colouring book"
  * "watercolor" AND "watercolour"
  * "color" AND "colour" (when color is a key term)
  * "gray" AND "grey"
  * "center" AND "centre" (when relevant)
  * "favor" AND "favour" (when relevant)

Naturally weave in 2-3 synonym variants of key terms without keyword stuffing.

═══════════════════════════════════════════════
FIELD 3: "tags" (array of strings, up to 10)
═══════════════════════════════════════════════
SEO-optimized keyword tags. Use hyphens for multi-word tags (e.g., "african-american").

Include:
- Primary subject (e.g., "portrait", "landscape")
- Demographic synonyms (e.g., both "african-american" AND "black-woman")
- Mood/atmosphere keywords
- Art style (e.g., "photorealistic", "oil-painting")
- Specific elements (e.g., "coffee", "red-car", "neon-lights")
- LinkedIn photos: include "linkedin-headshot", "linkedin-profile-photo", "professional-headshot",
  "corporate-portrait", "business-portrait" (triggered by professional attire + corporate mood,
  ANY framing — not limited to shoulders-up headshots)
- Other niche terms when applicable: "ai-influencer", "ai-avatar", "virtual-photoshoot",
  "boudoir", "burlesque", "pin-up", "glamour-photography"
- YouTube thumbnails: include "youtube-thumbnail", "thumbnail-design", "cover-art",
  "video-thumbnail", "podcast-cover", "social-media-graphic"
- Maternity shoots: include "maternity-shoot", "maternity-photography", "pregnancy-photoshoot",
  "baby-bump", "expecting-mother", "maternity-portrait"
- 3D/forced perspective: include "3d-photo", "forced-perspective", "facebook-3d", "3d-effect",
  "fisheye-portrait", "pop-out-effect", "parallax-photo"
- Photo restoration: include "photo-restoration", "ai-restoration", "restore-old-photo",
  "colorized-photo", "ai-colorize", "vintage-restoration"
- US/UK spelling variants: include BOTH spellings when applicable, e.g. "coloring-book" AND
  "colouring-book", "watercolor" AND "watercolour"

═══════════════════════════════════════════════
FIELD 4: "categories" (array of strings, up to 5)
═══════════════════════════════════════════════
Choose from this EXACT list only:

Portrait, Fashion & Style, Landscape & Nature, Urban & City, Sci-Fi & Futuristic,
Fantasy & Mythical, Wildlife & Nature Animals, Interior & Architecture, Abstract & Artistic,
Food & Drink, Vehicles & Transport, Horror & Dark, Anime & Manga, Photorealistic,
Digital Art, Illustration, Product & Commercial, Sports & Action, Music & Entertainment,
Retro & Vintage, Minimalist, Macro & Close-up, Text & Typography, Comedy & Humor,
Wedding & Engagement, Couple & Romance, Group & Crowd, Cosplay, Tattoo & Body Art,
Underwater, Aerial & Drone View, Concept Art, Wallpaper & Background, Character Design,
Pixel Art, 3D Render, Watercolor & Traditional, Surreal & Dreamlike,
AI Influencer / AI Avatar, Headshot, Boudoir, YouTube Thumbnail / Cover Art,
Pets & Domestic Animals, Maternity Shoot, 3D Photo / Forced Perspective,
Photo Restoration

SPECIAL RULES:
- "AI Influencer / AI Avatar": ONLY if single person + polished/glamorous + fashion-styled
  + luxury/aspirational setting or social-media-ready framing.
- "Headshot": Shoulders-up + single person + clean background.
- "Boudoir": Lingerie/revealing clothing + intimate setting + sensual posing/lighting.
  Based on styling, NOT body type.
- "YouTube Thumbnail / Cover Art": Designed composition with at least 2 of: bold text overlay,
  exaggerated expression, bright saturated colors, landscape orientation, split composition,
  arrow/circle graphics. Must be intentionally designed as a clickable cover/preview.
- "Maternity Shoot": Pregnant subject + styled photoshoot elements (flowing gowns, belly poses,
  dreamy lighting, partner involvement, baby props). Genre intent, not just pregnancy visible.
- "3D Photo / Forced Perspective": At least 2 of: fisheye/wide-angle distortion, object projected
  toward viewer in extreme foreground, three-layer depth separation, breaking frame boundaries,
  worm's-eye perspective, dramatic scale distortion.
- "Photo Restoration": At least 2 of: before/after layout, colorized B&W, enhanced old photo
  with period-specific context, old format borders with modern clarity, visible damage repair.
  NOT new images in vintage style (that's "Retro & Vintage").
- "Comedy & Humor": Intentionally comedic — memes, parody, satire, caricature, absurd humor,
  funny juxtapositions. NOT merely playful or whimsical.

═══════════════════════════════════════════════
FIELD 5: "descriptors" (object with typed arrays)
═══════════════════════════════════════════════
Return an object with these EXACT keys. Each value is an array of strings.
Choose ONLY from the options listed under each key.
Leave an array empty [] if nothing applies or if you are not confident.

"gender" (0-1 values, ONLY if person clearly visible):
  Male, Female, Androgynous

"ethnicity" (0-1 values, ONLY if >90% confident — OMIT if ANY doubt):
  African-American / Black, African, Hispanic / Latino, East Asian,
  South Asian / Indian / Desi, Southeast Asian, Middle Eastern / Arab,
  Caucasian / White, Indigenous / Native, Pacific Islander, Mixed / Multiracial

"age" (0-1 values, ONLY if person clearly visible):
  Baby / Infant, Child, Teen, Young Adult, Middle-Aged, Senior / Elderly

"features" (0-3 values, ONLY visually prominent intentional features):
  Vitiligo, Albinism, Heterochromia, Freckles, Natural Hair / Afro,
  Braids / Locs, Hijab / Headscarf, Bald / Shaved Head, Glasses / Eyewear,
  Beard / Facial Hair, Colorful / Dyed Hair, Wheelchair User, Prosthetic,
  Scarring, Plus Size / Curvy, Athletic / Muscular, Pregnancy / Maternity

"profession" (0-2 values, ONLY if identifiable through uniform/equipment/context):
  Military / Armed Forces, Healthcare / Medical, First Responder,
  Chef / Culinary, Business / Executive, Scientist / Lab, Artist / Creative,
  Teacher / Education, Athlete / Sports, Construction / Blue Collar,
  Pilot / Aviation, Musician / Performer, Royal / Regal, Warrior / Knight,
  Astronaut, Cowboy / Western, Ninja / Samurai

"mood" (1-2 values, almost every image has a mood):
  Dark & Moody, Bright & Cheerful, Dreamy / Ethereal, Cinematic, Dramatic,
  Peaceful / Serene, Romantic, Mysterious, Energetic, Melancholic, Whimsical,
  Eerie / Unsettling, Sensual / Alluring, Professional / Corporate,
  Vintage / Aged Film

"color" (1-2 values, almost every image has a color palette):
  Warm Tones, Cool Tones, Monochrome, Neon / Vibrant, Pastel, Earth Tones,
  High Contrast, Muted / Desaturated, Dark / Low-Key, Gold & Luxury

"holiday" (0-1 values, ONLY if clearly related to a specific holiday):
  Valentine's Day, Christmas, Halloween, Easter, Thanksgiving, New Year,
  Independence Day, St. Patrick's Day, Lunar New Year, Día de los Muertos,
  Mother's Day, Father's Day, Pride, Holi, Diwali, Eid, Hanukkah

"season" (0-1 values, ONLY if clear seasonal visual cues):
  Spring, Summer, Autumn / Fall, Winter

"setting" (0-1 values, if primary setting is determinable):
  Studio / Indoor, Outdoor / Nature, Urban / Street, Beach / Coastal,
  Mountain, Desert, Forest / Woodland, Space / Cosmic, Underwater

═══════════════════════════════════════════════
EXAMPLE RESPONSE
═══════════════════════════════════════════════
{
  "title": "Cinematic African-American Woman Golden Hour Portrait",
  "description": "A stunning cinematic portrait of a young African-American woman bathed in golden hour light. This photorealistic image captures the Black female subject with natural afro hair, wearing elegant gold jewelry against a warm urban backdrop. The dramatic lighting and rich warm tones create a powerful, aspirational mood perfect for AI avatar and virtual photoshoot inspiration. Ideal for creators seeking diverse, high-quality portrait prompts featuring African-American beauty and cinematic photography techniques.",
  "tags": ["african-american", "black-woman", "portrait", "cinematic", "golden-hour", "photorealistic", "natural-hair", "afro", "urban-portrait", "ai-avatar"],
  "categories": ["Portrait", "AI Influencer / AI Avatar", "Photorealistic"],
  "descriptors": {
    "gender": ["Female"],
    "ethnicity": ["African-American / Black"],
    "age": ["Young Adult"],
    "features": ["Natural Hair / Afro"],
    "profession": [],
    "mood": ["Cinematic", "Dramatic"],
    "color": ["Warm Tones", "Gold & Luxury"],
    "holiday": [],
    "season": [],
    "setting": ["Urban / Street"]
  }
}

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no backticks, no preamble.
```

---

## 8. Migration Plan

### Phase 2B-1: Model + Data Setup (1 CC session)
1. Create `SubjectDescriptor` model with all fields
2. Add `descriptors` M2M to Prompt model
3. Populate all ~109 descriptors via data migration (exact names and slugs from Section 4.2)
4. Add 22 new subject categories (exact names from Section 4.1)
5. Remove "Seasonal & Holiday" category
6. Rename "Wedding & Bridal" → "Wedding & Engagement" (if it exists)
7. Rename "Animals & Wildlife" → "Wildlife & Nature Animals"
8. Rename "Meme & Humor" → "Comedy & Humor"
9. Register `SubjectDescriptorAdmin`

### Phase 2B-2: AI Prompt Updates (1 CC session)
1. Replace current OpenAI prompt in `tasks.py` with Section 7.3 prompt
2. Update `tasks.py` to parse `descriptors` object from AI response
3. Update `tasks.py` to clean/validate descriptor names
4. Update `tasks.py` to store descriptors in cache alongside categories
5. Update tag limit from 5 to 10 in `tasks.py`

### Phase 2B-3: Upload Flow (1 CC session)
1. Update `upload_views.py` to read descriptors from cache
2. Update `upload_views.py` to assign descriptors to prompt (same pattern as categories)
3. Update tag limit validation from 5 to 10
4. Add backend validation: `SubjectDescriptor.objects.filter(name__in=...)` (Layer 4 safety net)

### Phase 2B-4: Scoring Update (1 CC session)
1. Update `prompts/utils/related.py` with new weights (20/25/25/10/10/10)
2. Add descriptor Jaccard similarity calculation
3. Update pre-filter to include descriptor overlap as candidate criteria
4. Update `DESIGN_RELATED_PROMPTS.md` to reflect new weights

### Phase 2B-5: Backfill (1 CC session + ~30 min runtime)
1. Update backfill command to assign categories AND descriptors AND regenerate tags (10-tag limit)
2. Optionally regenerate descriptions for SEO synonym coverage
3. Run on all existing prompts (~800)
4. Estimated cost: ~$8-24 (one OpenAI Vision call per prompt)

### Phase 2B-6: Future — Browse/Filter UI (2-3 CC sessions)
1. Filter sidebar with checkbox groups by descriptor type
2. URL-based filtering: `/browse/?gender=female&ethnicity=african-american&mood=cinematic`
3. Category landing pages: `/categories/portrait/`
4. Descriptor landing pages: `/browse/african-american/`

---

## 9. Performance Considerations

- Descriptor M2M adds one JOIN for related scoring — mitigate with `prefetch_related`
- ~109 descriptors × up to 10 per prompt = more pivot table rows — index on both FK columns
- Cache descriptor lookups (they rarely change)
- Pre-filter optimization: include descriptor overlap in candidate selection
- OpenAI prompt is ~1,500-2,000 tokens — well within GPT-4 Vision's reliable accuracy range
- Per-section choice lists are 3-17 options each — small enough for consistent accuracy

## 10. Content Sensitivity Notes

- Ethnicity detection by AI is imperfect — the >90% confidence threshold prevents misassignment
- Gender presentation is based on visual presentation, not assumed identity
- Holiday descriptors are culturally inclusive (Diwali, Eid, Hanukkah alongside Christmas)
- Boudoir/sensual classification is based on styling intent, not body type or fitness level
- Physical features (vitiligo, wheelchair, prosthetic) are assigned only when visually prominent and intentionally part of the image aesthetic — never as incidental observations
- Admin can override/correct any AI assignments
- Backend validation (Layer 4) guarantees no hallucinated values are ever stored
- NSFW moderation remains completely separate — Boudoir category is for content that passes NSFW checks

---

## 11. Estimated Total Effort

| Phase | Task | Effort |
|-------|------|--------|
| 2B-1 | Model + migrations + admin | 1 CC session |
| 2B-2 | AI prompt updates | 1 CC session |
| 2B-3 | Upload flow (cache/session/assign) | 1 CC session |
| 2B-4 | Scoring algorithm update | 1 CC session |
| 2B-5 | Backfill command + run | 1 CC session + ~30 min |
| 2B-6 | Browse/filter UI | 2-3 CC sessions |

**Total: ~5-6 CC sessions before UI, ~8-9 with filter UI**

---

**END OF DESIGN DOCUMENT**
