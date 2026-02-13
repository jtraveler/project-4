"""
NSFW Tag Audit Script
Run: python manage.py shell < audit_nsfw_tags.py

Outputs:
1. Complete unique tag inventory with usage counts
2. Hardcore NSFW tags found (should be banned)
3. Ambiguous tags found (flag for admin review)
4. Soft/artistic NSFW tags found (keep - legitimate categories)
"""

from django.db.models import Count
from taggit.models import Tag

print("=" * 70)
print("NSFW TAG AUDIT")
print("=" * 70)

# ─── CURATED LISTS ───────────────────────────────────────────────────

# HARDCORE NSFW - explicit sexual/violent terms that should NEVER be tags
# These have no legitimate non-sexual/non-violent meaning in AI art context
HARDCORE_BAN = {
    # Explicit sexual acts/terms
    'anal', 'blowjob', 'bukkake', 'creampie', 'cumshot', 'deepthroat',
    'dildo', 'doggystyle', 'ejaculation', 'fellatio', 'fingering',
    'fisting', 'gangbang', 'handjob', 'hentai', 'masturbation',
    'missionary', 'orgasm', 'orgy', 'penetration', 'pornographic',
    'pornography', 'pussy', 'rimjob', 'sex', 'sexual', 'sexually',
    'threesome', 'vaginal', 'xxx',
    # Body parts (explicit context)
    'genitals', 'genitalia', 'penis', 'testicles', 'vulva', 'anus',
    'nipples', 'areola', 'crotch', 'groin',
    # Fetish/kink (explicit)
    'bondage', 'bdsm', 'dominatrix', 'fetish', 'gimp', 'sadomasochism',
    'slave', 'submissive', 'dominance', 'whip', 'collar',
    # Violence (graphic)
    'gore', 'dismemberment', 'mutilation', 'decapitation', 'torture',
    'bloodbath', 'disembowel',
    # Exploitation
    'lolita', 'jailbait', 'underage',
}

# AMBIGUOUS - terms with BOTH innocent and NSFW meanings
# These should trigger admin review but NOT block the post
AMBIGUOUS_TERMS = {
    # Could be skincare OR sexual
    'facial': 'skincare treatment vs sexual act',
    'cream': 'cosmetics/food vs sexual slang',
    'cream-pie': 'dessert vs sexual act',
    
    # Could be fashion/art OR sexual
    'nude': 'art nude/color vs pornographic',
    'naked': 'artistic nudity vs pornographic',
    'topless': 'fashion/artistic vs pornographic',
    'bare': 'minimalist/exposed vs nudity',
    'exposed': 'photography term vs nudity',
    'strip': 'comic strip/pattern vs striptease',
    'stripped': 'pattern/texture vs undressing',
    
    # Could be anatomy/art OR suggestive
    'breasts': 'anatomical/maternal vs sexual',
    'chest': 'anatomy/furniture vs sexual',
    'thigh': 'anatomy/fashion vs sexual',
    'curves': 'design/body shape vs sexual',
    'curvy': 'body type vs sexual objectification',
    'thick': 'texture/style vs body sexualization',
    'juicy': 'food/color vs sexual slang',
    
    # Could be fashion OR suggestive
    'corset': 'historical fashion vs fetish',
    'stockings': 'fashion vs fetish',
    'garter': 'fashion accessory vs fetish',
    'leather': 'material/fashion vs fetish',
    'latex': 'material vs fetish',
    'fishnet': 'pattern/fashion vs fetish',
    'sheer': 'fabric type vs revealing',
    'see-through': 'fabric type vs revealing',
    'tight': 'fit/composition vs suggestive',
    'wet': 'water/rain vs suggestive',
    'dripping': 'liquid/paint vs suggestive',
    
    # Could be pose/composition OR suggestive
    'spread': 'layout/wings vs sexual pose',
    'mounting': 'horse riding vs sexual',
    'riding': 'equestrian/vehicle vs sexual',
    'straddling': 'pose vs sexual',
    'bent': 'posture/shape vs suggestive pose',
    'arched': 'architecture/pose vs suggestive',
    'kneeling': 'prayer/pose vs suggestive',
    'sprawled': 'relaxed pose vs suggestive',
    
    # Could be emotion/art OR suggestive
    'sensual': 'artistic mood vs sexual',
    'seductive': 'fashion/mood vs sexual',
    'provocative': 'art/fashion vs sexual',
    'intimate': 'close/personal vs sexual',
    'passionate': 'emotion/art vs sexual',
    'erotic': 'art genre vs pornographic',
    'sultry': 'mood/weather vs sexual',
    'steamy': 'steam/hot vs sexual',
    'lusty': 'vibrant vs sexual',
    'tempting': 'food/fashion vs sexual',
    'alluring': 'fashion/beauty vs sexual',
    'naughty': 'playful vs sexual',
    
    # Could be body description OR objectifying
    'busty': 'body type vs sexual objectification',
    'voluptuous': 'body type/art vs sexual',
    'hourglass': 'shape/time vs body objectification',
    'cleavage': 'geology/fashion vs sexual',
    'plump': 'food/style vs body commentary',
    'petite': 'size descriptor vs fetishization',
    
    # Could be activity OR suggestive
    'licking': 'food/animal vs sexual',
    'sucking': 'candy/baby vs sexual',
    'swallowing': 'food/drink vs sexual',
    'blowing': 'wind/bubbles vs sexual',
    'stroking': 'petting/painting vs sexual',
    'grinding': 'coffee/skate vs sexual',
    'moaning': 'wind/emotion vs sexual',
    'panting': 'exhaustion/dog vs sexual',
    'throbbing': 'pain/music vs sexual',
    
    # Could be restraint/art OR violent/fetish
    'chains': 'jewelry/industrial vs bondage',
    'rope': 'nautical/craft vs bondage',
    'tied': 'bow/rope vs bondage',
    'bound': 'book/travel vs bondage',
    'caged': 'bird/art vs imprisonment',
    'chained': 'industrial vs bondage',
    'handcuffs': 'police/costume vs fetish',
    'gagged': 'comedy vs fetish',
    
    # Could be innocent OR substance-related
    'smoking': 'atmosphere/cooking vs tobacco/drugs',
    'injection': 'medical/art vs drugs',
    'high': 'altitude/fashion vs drugs',
    'wasted': 'apocalyptic vs intoxication',
    
    # Could be age descriptor OR problematic
    'innocent': 'mood/style vs infantilization',
    'virgin': 'nature/cocktail vs sexual',
    'schoolgirl': 'uniform/costume vs fetishization',
    'daddy': 'family vs sexual slang',
    'baby': 'infant/term of endearment vs infantilization',
}

# SOFT/ARTISTIC NSFW - legitimate categories on AI art platforms (KEEP)
SOFT_NSFW_KEEP = {
    'lingerie', 'boudoir', 'pin-up', 'burlesque', 'glamour',
    'swimwear', 'bikini', 'underwear', 'bodysuit',
    'figure-drawing', 'life-drawing', 'classical-nude',
    'maternity', 'pregnancy', 'breastfeeding',
    'romantic', 'love', 'kiss', 'kissing', 'embrace', 'cuddle',
    'muscular', 'athletic', 'fitness', 'bodybuilder',
    'tattoo', 'piercing', 'body-art',
}

# ─── AUDIT ───────────────────────────────────────────────────────────

# Get all unique tags with usage counts
all_tags = (
    Tag.objects
    .filter(taggit_taggeditem_items__content_type__model='prompt')
    .annotate(usage=Count('taggit_taggeditem_items'))
    .order_by('-usage')
)

total_tags = all_tags.count()
print(f"\nTotal unique tags in database: {total_tags}")
print(f"Checking against: {len(HARDCORE_BAN)} hardcore terms, "
      f"{len(AMBIGUOUS_TERMS)} ambiguous terms, "
      f"{len(SOFT_NSFW_KEEP)} soft/artistic terms")

# ─── CHECK 1: Hardcore NSFW found ────────────────────────────────────
print("\n" + "=" * 70)
print("🚫 HARDCORE NSFW TAGS FOUND (should be BANNED)")
print("=" * 70)

hardcore_found = []
for tag in all_tags:
    name_lower = tag.name.lower()
    if name_lower in HARDCORE_BAN:
        hardcore_found.append((tag.name, tag.usage))
        
    # Also check if any hardcore term appears as part of a compound
    for term in HARDCORE_BAN:
        if term in name_lower and name_lower != term:
            hardcore_found.append((tag.name, tag.usage, f"contains '{term}'"))

if hardcore_found:
    for item in hardcore_found:
        if len(item) == 3:
            print(f"  ❌ '{item[0]}' (used {item[1]}x) — {item[2]}")
        else:
            print(f"  ❌ '{item[0]}' (used {item[1]}x)")
else:
    print("  ✅ No hardcore NSFW tags found!")

# ─── CHECK 2: Ambiguous tags found ──────────────────────────────────
print("\n" + "=" * 70)
print("⚠️  AMBIGUOUS TAGS FOUND (flag for admin review)")
print("=" * 70)

ambiguous_found = []
for tag in all_tags:
    name_lower = tag.name.lower()
    if name_lower in AMBIGUOUS_TERMS:
        ambiguous_found.append((tag.name, tag.usage, AMBIGUOUS_TERMS[name_lower]))

if ambiguous_found:
    for name, usage, reason in ambiguous_found:
        print(f"  ⚠️  '{name}' (used {usage}x) — {reason}")
else:
    print("  ✅ No ambiguous tags found!")

# ─── CHECK 3: Soft/artistic NSFW found ──────────────────────────────
print("\n" + "=" * 70)
print("✅ SOFT/ARTISTIC NSFW TAGS FOUND (keep — legitimate categories)")
print("=" * 70)

soft_found = []
for tag in all_tags:
    name_lower = tag.name.lower()
    if name_lower in SOFT_NSFW_KEEP:
        soft_found.append((tag.name, tag.usage))

if soft_found:
    for name, usage in soft_found:
        print(f"  ✅ '{name}' (used {usage}x)")
else:
    print("  (none currently in use)")

# ─── FULL TAG INVENTORY ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("📋 COMPLETE TAG INVENTORY (sorted by usage)")
print("=" * 70)

for tag in all_tags:
    flag = ""
    name_lower = tag.name.lower()
    if name_lower in HARDCORE_BAN:
        flag = " 🚫 HARDCORE"
    elif name_lower in AMBIGUOUS_TERMS:
        flag = " ⚠️  AMBIGUOUS"
    elif name_lower in SOFT_NSFW_KEEP:
        flag = " 🔸 SOFT-NSFW"
    print(f"  {tag.name:30s} ({tag.usage}x){flag}")

# ─── SUMMARY ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"  Total unique tags:     {total_tags}")
print(f"  Hardcore NSFW found:   {len(hardcore_found)}")
print(f"  Ambiguous found:       {len(ambiguous_found)}")
print(f"  Soft/artistic found:   {len(soft_found)}")
print(f"  Clean tags:            {total_tags - len(hardcore_found) - len(ambiguous_found) - len(soft_found)}")

if hardcore_found:
    print(f"\n  🚨 ACTION REQUIRED: Add {len(hardcore_found)} hardcore terms to validator ban list")
if ambiguous_found:
    print(f"\n  📝 DECISION NEEDED: Review {len(ambiguous_found)} ambiguous tags")
    print(f"     Options per tag: keep, ban, or flag for admin review")
