"""
Tag-Description Cross-Reference Audit Script
=============================================
Run with: python manage.py shell < audit_tags_vs_descriptions.py

Checks:
1. TAG RELEVANCE - Are tags reflected in title/description?
2. MISSED KEYWORDS - Are important description words missing from tags?
3. GARBAGE SPLITS - Tags that are single generic words (likely bad splits)
4. TAG DIVERSITY - Are we over-using the same tags across all prompts?
5. GENDER PAIR CHECK - Are gender tags properly paired?
6. COMPOUND LEAKS - Any hyphenated tags that shouldn't be?
"""

from prompts.models import Prompt
from collections import Counter
import re

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Tags that are too generic to be useful (likely from bad compound splits)
GARBAGE_TAGS = {
    'working', 'class', 'style', 'art', 'scene', 'photo', 'type',
    'look', 'effect', 'shot', 'view', 'tone', 'color', 'light',
    'mode', 'set', 'piece', 'form', 'line', 'way', 'part', 'kind',
    'out', 'up', 'old', 'new', 'big', 'top',
}

# High-value SEO keywords that should appear as tags when relevant
HIGH_VALUE_KEYWORDS = {
    'portrait', 'cinematic', 'photorealistic', 'digital-art', 'fantasy',
    'anime', 'landscape', 'abstract', 'vintage', 'retro', 'futuristic',
    'cyberpunk', 'watercolor', 'oil-painting', 'sci-fi', 'surreal',
    'minimalist', 'dramatic', 'moody', 'ethereal', 'noir',
    'steampunk', 'gothic', 'baroque', 'art-deco', 'pop-art',
    'illustration', 'concept-art', 'fashion', 'editorial',
}

# Acceptable whitelist (must match tasks.py)
ACCEPTABLE_COMPOUNDS = {
    'digital-art', 'sci-fi', 'close-up', 'avant-garde', 'middle-aged',
    'high-contrast', 'full-body', '3d-render', 'golden-hour', 'high-fashion',
    'oil-painting', 'teen-boy', 'teen-girl',
    'character-design', 'fantasy-character', 'stock-photo',
    'youtube-thumbnail', 'instagram-aesthetic', 'tiktok-aesthetic',
    'linkedin-headshot', 'open-plan', 'living-room', 'comic-style',
    'coloring-book', 'colouring-book', 'pin-up', 'baby-bump',
    'cover-art', 'maternity-shoot', 'forced-perspective', '3d-photo',
    'thumbnail-design',
}

# Gender pairs
GENDER_TAGS = {'man', 'male', 'woman', 'female', 'boy', 'girl', 'teen-boy', 'teen-girl'}

# Words to ignore when checking description keywords
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
    'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'about', 'above', 'after', 'again', 'against', 'below', 'between',
    'during', 'into', 'through', 'before', 'under', 'over', 'here', 'there',
    'then', 'once', 'its', 'as', 'up', 'out', 'off', 'if', 'while',
    'image', 'features', 'creates', 'creating', 'created', 'shows',
    'showing', 'using', 'used', 'captures', 'capturing', 'evoking',
    'evokes', 'blending', 'blends', 'combines', 'combining', 'brings',
    'one', 'two', 'three', 'set', 'like', 'also', 'well', 'around',
    'their', 'them', 'his', 'her', 'him', 'make', 'makes', 'made',
    'prompt', 'prompts', 'generate', 'generated', 'ai', 'art',
    'scene', 'sense', 'feel', 'feeling', 'style', 'styled', 'gives',
    'adds', 'adding', 'where', 'within', 'along', 'across',
}

# ═══════════════════════════════════════════════════════════════
# AUDIT LOGIC
# ═══════════════════════════════════════════════════════════════

prompts = Prompt.objects.filter(deleted_at__isnull=True).order_by('id')
total = prompts.count()

all_tags = Counter()
issues = {
    'garbage_tags': [],
    'compound_leaks': [],
    'gender_incomplete': [],
    'missed_keywords': [],
    'low_tag_count': [],
    'tag_description_mismatch': [],
}

print("=" * 80)
print(f"TAG-DESCRIPTION CROSS-REFERENCE AUDIT — {total} prompts")
print("=" * 80)

for p in prompts:
    tags = list(p.tags.names())
    tag_set = set(tags)
    all_tags.update(tags)

    title = p.title or ''
    desc = p.excerpt or ''
    full_text = f"{title} {desc}".lower()

    prompt_issues = []

    # ─── CHECK 1: Garbage tags (likely bad splits) ───
    garbage_found = tag_set & GARBAGE_TAGS
    if garbage_found:
        prompt_issues.append(f"🗑️  GARBAGE TAGS: {sorted(garbage_found)}")
        issues['garbage_tags'].append((p.id, sorted(garbage_found)))

    # ─── CHECK 2: Compound leaks (hyphenated tags not on whitelist) ───
    compound_leaks = [t for t in tags if '-' in t and t not in ACCEPTABLE_COMPOUNDS]
    if compound_leaks:
        prompt_issues.append(f"🔗 COMPOUND LEAKS: {compound_leaks}")
        issues['compound_leaks'].append((p.id, compound_leaks))

    # ─── CHECK 3: Gender pair check ───
    gender_in_tags = tag_set & GENDER_TAGS
    if gender_in_tags:
        if 'man' in tag_set and 'male' not in tag_set:
            prompt_issues.append("⚠️  GENDER: 'man' without 'male'")
            issues['gender_incomplete'].append((p.id, 'man without male'))
        if 'woman' in tag_set and 'female' not in tag_set:
            prompt_issues.append("⚠️  GENDER: 'woman' without 'female'")
            issues['gender_incomplete'].append((p.id, 'woman without female'))
        if 'girl' in tag_set and 'female' not in tag_set:
            prompt_issues.append("⚠️  GENDER: 'girl' without 'female'")
            issues['gender_incomplete'].append((p.id, 'girl without female'))
        if 'boy' in tag_set and 'male' not in tag_set:
            prompt_issues.append("⚠️  GENDER: 'boy' without 'male'")
            issues['gender_incomplete'].append((p.id, 'boy without male'))

    # ─── CHECK 4: Low tag count ───
    if len(tags) < 10:
        prompt_issues.append(f"📉 LOW COUNT: only {len(tags)} tags (expected 10)")
        issues['low_tag_count'].append((p.id, len(tags)))

    # ─── CHECK 5: Missed high-value keywords ───
    # Extract meaningful words from description
    desc_words = set(re.findall(r'[a-z]+(?:-[a-z]+)*', full_text))
    desc_words -= STOP_WORDS

    # Check if description mentions concepts that should be tags
    missed = []
    for kw in HIGH_VALUE_KEYWORDS:
        # Check if keyword (or its parts) appear in description but not in tags
        kw_parts = kw.split('-')
        kw_in_desc = any(part in desc_words for part in kw_parts) or kw in desc_words
        kw_in_tags = kw in tag_set or any(part in tag_set for part in kw_parts)
        if kw_in_desc and not kw_in_tags:
            missed.append(kw)

    if missed:
        prompt_issues.append(f"🔍 MISSED KEYWORDS: {sorted(missed)}")
        issues['missed_keywords'].append((p.id, sorted(missed)))

    # ─── CHECK 6: Tag-description relevance ───
    # How many tags appear somewhere in the title or description?
    tags_in_desc = 0
    for tag in tags:
        tag_parts = tag.split('-')
        if any(part in full_text for part in tag_parts):
            tags_in_desc += 1
    relevance_pct = (tags_in_desc / len(tags) * 100) if tags else 0

    if relevance_pct < 30:
        prompt_issues.append(f"📊 LOW RELEVANCE: only {tags_in_desc}/{len(tags)} tags ({relevance_pct:.0f}%) found in title/description")
        issues['tag_description_mismatch'].append((p.id, tags_in_desc, len(tags), relevance_pct))

    # ─── OUTPUT PER PROMPT ───
    status = "❌ ISSUES" if prompt_issues else "✅ PASS"
    print(f"\n{'─' * 70}")
    print(f"ID:{p.id} | {status} | {title[:60]}")
    print(f"  TAGS: {', '.join(sorted(tags))}")
    print(f"  DESC: {desc[:150]}...")
    print(f"  RELEVANCE: {tags_in_desc}/{len(tags)} tags in text ({relevance_pct:.0f}%)")

    if prompt_issues:
        for issue in prompt_issues:
            print(f"  {issue}")


# ═══════════════════════════════════════════════════════════════
# SUMMARY REPORT
# ═══════════════════════════════════════════════════════════════

print("\n\n" + "=" * 80)
print("SUMMARY REPORT")
print("=" * 80)

# Issue counts
print(f"\n📊 ISSUE BREAKDOWN ({total} prompts):")
print(f"  🗑️  Garbage tags:           {len(issues['garbage_tags'])} prompts")
print(f"  🔗 Compound leaks:          {len(issues['compound_leaks'])} prompts")
print(f"  ⚠️  Gender incomplete:       {len(issues['gender_incomplete'])} prompts")
print(f"  🔍 Missed keywords:         {len(issues['missed_keywords'])} prompts")
print(f"  📉 Low tag count (<10):     {len(issues['low_tag_count'])} prompts")
print(f"  📊 Low relevance (<30%):    {len(issues['tag_description_mismatch'])} prompts")

pass_count = total - len(set(
    [i[0] for i in issues['garbage_tags']] +
    [i[0] for i in issues['compound_leaks']] +
    [i[0] for i in issues['gender_incomplete']] +
    [i[0] for i in issues['low_tag_count']] +
    [i[0] for i in issues['tag_description_mismatch']]
))
print(f"\n  ✅ Clean prompts: {pass_count}/{total} ({pass_count/total*100:.0f}%)")

# Tag frequency (top 30)
print(f"\n📈 TOP 30 MOST USED TAGS (across {total} prompts):")
for tag, count in all_tags.most_common(30):
    bar = "█" * count
    pct = count / total * 100
    print(f"  {tag:20s} {count:3d} ({pct:4.0f}%) {bar}")

# Tag frequency (least used)
print(f"\n📉 TAGS USED ONLY ONCE (potential waste):")
singles = [(tag, count) for tag, count in all_tags.items() if count == 1]
singles.sort(key=lambda x: x[0])
for tag, count in singles:
    print(f"  {tag}")
print(f"  Total unique-once tags: {len(singles)}")

# Diversity check
total_tag_slots = total * 10  # 51 prompts * 10 tags each
unique_tags = len(all_tags)
print(f"\n📊 DIVERSITY METRICS:")
print(f"  Total tag slots: {total_tag_slots}")
print(f"  Unique tags used: {unique_tags}")
print(f"  Diversity ratio: {unique_tags/total_tag_slots*100:.1f}% (higher = more diverse)")

# Over-concentrated tags (used in >50% of prompts)
print(f"\n⚠️  OVER-CONCENTRATED TAGS (>50% of prompts):")
for tag, count in all_tags.most_common():
    pct = count / total * 100
    if pct > 50:
        print(f"  {tag}: {count}/{total} ({pct:.0f}%)")
    else:
        break

# Specific issue details
if issues['garbage_tags']:
    print(f"\n🗑️  GARBAGE TAG DETAILS:")
    for pid, tags in issues['garbage_tags']:
        print(f"  Prompt {pid}: {tags}")

if issues['compound_leaks']:
    print(f"\n🔗 COMPOUND LEAK DETAILS:")
    for pid, tags in issues['compound_leaks']:
        print(f"  Prompt {pid}: {tags}")

if issues['gender_incomplete']:
    print(f"\n⚠️  GENDER PAIR DETAILS:")
    for pid, detail in issues['gender_incomplete']:
        print(f"  Prompt {pid}: {detail}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
