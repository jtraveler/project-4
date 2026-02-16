"""
Tests for _validate_and_fix_tags post-processing function.

Covers: compound preservation (default), stop-word splitting, lowercase
enforcement, AI tag removal, ethnicity removal, deduplication, tag count
enforcement, and gender pair warnings.
"""

import logging
from unittest import TestCase

from prompts.tasks import _validate_and_fix_tags, DEMOGRAPHIC_TAGS


# ---------------------------------------------------------------------------
# 1. Compound tags are PRESERVED by default
# ---------------------------------------------------------------------------
class TestCompoundPreservation(TestCase):
    """Test that hyphenated compound tags are preserved by default."""

    def test_soft_lighting_preserved(self):
        result = _validate_and_fix_tags(['soft-lighting', 'moody'])
        self.assertIn('soft-lighting', result)

    def test_vintage_car_preserved(self):
        result = _validate_and_fix_tags(['vintage-car', 'woman'])
        self.assertIn('vintage-car', result)

    def test_dramatic_lighting_preserved(self):
        result = _validate_and_fix_tags(['dramatic-lighting'])
        self.assertIn('dramatic-lighting', result)

    def test_cinematic_lighting_preserved(self):
        result = _validate_and_fix_tags(['cinematic-lighting'])
        self.assertIn('cinematic-lighting', result)

    def test_cute_bunny_preserved(self):
        result = _validate_and_fix_tags(['cute-bunny', 'nature'])
        self.assertIn('cute-bunny', result)

    def test_interior_design_preserved(self):
        result = _validate_and_fix_tags(['interior-design'])
        self.assertIn('interior-design', result)

    def test_professional_headshot_preserved(self):
        result = _validate_and_fix_tags(['professional-headshot'])
        self.assertIn('professional-headshot', result)

    def test_corporate_portrait_preserved(self):
        result = _validate_and_fix_tags(['corporate-portrait'])
        self.assertIn('corporate-portrait', result)

    def test_business_portrait_preserved(self):
        result = _validate_and_fix_tags(['business-portrait'])
        self.assertIn('business-portrait', result)

    def test_fisheye_portrait_preserved(self):
        result = _validate_and_fix_tags(['fisheye-portrait'])
        self.assertIn('fisheye-portrait', result)

    def test_double_exposure_preserved(self):
        result = _validate_and_fix_tags(['double-exposure', 'portrait'])
        self.assertIn('double-exposure', result)

    def test_high_contrast_preserved(self):
        result = _validate_and_fix_tags(['high-contrast', 'moody'])
        self.assertIn('high-contrast', result)

    def test_mixed_media_preserved(self):
        result = _validate_and_fix_tags(['mixed-media', 'collage'])
        self.assertIn('mixed-media', result)

    def test_warm_tones_preserved(self):
        result = _validate_and_fix_tags(['warm-tones', 'sunset'])
        self.assertIn('warm-tones', result)

    def test_cool_tones_preserved(self):
        result = _validate_and_fix_tags(['cool-tones', 'winter'])
        self.assertIn('cool-tones', result)

    def test_macro_photography_preserved(self):
        result = _validate_and_fix_tags(['macro-photography', 'nature'])
        self.assertIn('macro-photography', result)

    def test_nature_photography_preserved(self):
        result = _validate_and_fix_tags(['nature-photography', 'landscape'])
        self.assertIn('nature-photography', result)

    def test_vibrant_colors_preserved(self):
        result = _validate_and_fix_tags(['vibrant-colors', 'pop-art'])
        self.assertIn('vibrant-colors', result)

    def test_long_exposure_preserved(self):
        result = _validate_and_fix_tags(['long-exposure', 'night'])
        self.assertIn('long-exposure', result)

    def test_time_lapse_preserved(self):
        result = _validate_and_fix_tags(['time-lapse'])
        self.assertIn('time-lapse', result)

    def test_film_noir_preserved(self):
        result = _validate_and_fix_tags(['film-noir'])
        self.assertIn('film-noir', result)

    def test_pop_art_preserved(self):
        result = _validate_and_fix_tags(['pop-art'])
        self.assertIn('pop-art', result)

    def test_art_deco_preserved(self):
        result = _validate_and_fix_tags(['art-deco'])
        self.assertIn('art-deco', result)

    def test_wide_angle_preserved(self):
        result = _validate_and_fix_tags(['wide-angle'])
        self.assertIn('wide-angle', result)

    def test_hyper_realistic_preserved(self):
        result = _validate_and_fix_tags(['hyper-realistic'])
        self.assertIn('hyper-realistic', result)

    def test_street_style_preserved(self):
        result = _validate_and_fix_tags(['street-style'])
        self.assertIn('street-style', result)

    def test_hand_drawn_preserved(self):
        result = _validate_and_fix_tags(['hand-drawn'])
        self.assertIn('hand-drawn', result)

    def test_line_art_preserved(self):
        result = _validate_and_fix_tags(['line-art'])
        self.assertIn('line-art', result)

    def test_pixel_art_preserved(self):
        result = _validate_and_fix_tags(['pixel-art'])
        self.assertIn('pixel-art', result)

    def test_depth_of_field_preserved(self):
        """depth-of-field contains 'of' (stop word) but is a known photographic term."""
        result = _validate_and_fix_tags(['depth-of-field', 'portrait'])
        self.assertIn('depth-of-field', result)
        self.assertNotIn('depth', result)


# ---------------------------------------------------------------------------
# 2. Legacy whitelist compounds also preserved (subset check)
# ---------------------------------------------------------------------------
class TestLegacyWhitelistPreserved(TestCase):
    """Compounds that were on the old whitelist are still preserved."""

    def test_digital_art_preserved(self):
        result = _validate_and_fix_tags(['digital-art', 'portrait'])
        self.assertIn('digital-art', result)

    def test_sci_fi_preserved(self):
        result = _validate_and_fix_tags(['sci-fi', 'futuristic'])
        self.assertIn('sci-fi', result)

    def test_close_up_preserved(self):
        result = _validate_and_fix_tags(['close-up', 'macro'])
        self.assertIn('close-up', result)

    def test_middle_aged_preserved(self):
        result = _validate_and_fix_tags(['middle-aged', 'man'])
        self.assertIn('middle-aged', result)

    def test_oil_painting_preserved(self):
        result = _validate_and_fix_tags(['oil-painting'])
        self.assertIn('oil-painting', result)

    def test_golden_hour_preserved(self):
        result = _validate_and_fix_tags(['golden-hour'])
        self.assertIn('golden-hour', result)

    def test_teen_boy_preserved(self):
        result = _validate_and_fix_tags(['teen-boy', 'male'])
        self.assertIn('teen-boy', result)

    def test_teen_girl_preserved(self):
        result = _validate_and_fix_tags(['teen-girl', 'female'])
        self.assertIn('teen-girl', result)

    def test_3d_render_preserved(self):
        result = _validate_and_fix_tags(['3d-render'])
        self.assertIn('3d-render', result)

    def test_character_design_preserved(self):
        result = _validate_and_fix_tags(['character-design'])
        self.assertIn('character-design', result)

    def test_youtube_thumbnail_preserved(self):
        result = _validate_and_fix_tags(['youtube-thumbnail'])
        self.assertIn('youtube-thumbnail', result)

    def test_baby_bump_preserved(self):
        result = _validate_and_fix_tags(['baby-bump'])
        self.assertIn('baby-bump', result)

    def test_open_plan_preserved(self):
        result = _validate_and_fix_tags(['open-plan'])
        self.assertIn('open-plan', result)

    def test_living_room_preserved(self):
        result = _validate_and_fix_tags(['living-room'])
        self.assertIn('living-room', result)

    def test_comic_style_preserved(self):
        result = _validate_and_fix_tags(['comic-style'])
        self.assertIn('comic-style', result)

    def test_stock_photo_preserved(self):
        result = _validate_and_fix_tags(['stock-photo'])
        self.assertIn('stock-photo', result)

    def test_cover_art_preserved(self):
        result = _validate_and_fix_tags(['cover-art'])
        self.assertIn('cover-art', result)

    def test_maternity_shoot_preserved(self):
        result = _validate_and_fix_tags(['maternity-shoot'])
        self.assertIn('maternity-shoot', result)

    def test_forced_perspective_preserved(self):
        result = _validate_and_fix_tags(['forced-perspective'])
        self.assertIn('forced-perspective', result)

    def test_3d_photo_preserved(self):
        result = _validate_and_fix_tags(['3d-photo'])
        self.assertIn('3d-photo', result)

    def test_thumbnail_design_preserved(self):
        result = _validate_and_fix_tags(['thumbnail-design'])
        self.assertIn('thumbnail-design', result)

    def test_coloring_book_preserved(self):
        result = _validate_and_fix_tags(['coloring-book'])
        self.assertIn('coloring-book', result)

    def test_colouring_book_preserved(self):
        result = _validate_and_fix_tags(['colouring-book'])
        self.assertIn('colouring-book', result)

    def test_pin_up_preserved(self):
        result = _validate_and_fix_tags(['pin-up'])
        self.assertIn('pin-up', result)

    def test_fantasy_character_preserved(self):
        result = _validate_and_fix_tags(['fantasy-character'])
        self.assertIn('fantasy-character', result)

    def test_instagram_aesthetic_preserved(self):
        result = _validate_and_fix_tags(['instagram-aesthetic'])
        self.assertIn('instagram-aesthetic', result)

    def test_tiktok_aesthetic_preserved(self):
        result = _validate_and_fix_tags(['tiktok-aesthetic'])
        self.assertIn('tiktok-aesthetic', result)

    def test_linkedin_headshot_preserved(self):
        result = _validate_and_fix_tags(['linkedin-headshot'])
        self.assertIn('linkedin-headshot', result)

    def test_high_fashion_preserved(self):
        result = _validate_and_fix_tags(['high-fashion'])
        self.assertIn('high-fashion', result)

    def test_full_body_preserved(self):
        result = _validate_and_fix_tags(['full-body'])
        self.assertIn('full-body', result)

    def test_avant_garde_preserved(self):
        result = _validate_and_fix_tags(['avant-garde'])
        self.assertIn('avant-garde', result)

    def test_linkedin_profile_photo_preserved(self):
        """3-part compound with no stop words is naturally preserved."""
        result = _validate_and_fix_tags(['linkedin-profile-photo'])
        self.assertIn('linkedin-profile-photo', result)
        self.assertNotIn('linkedin', result)
        self.assertNotIn('profile', result)
        self.assertNotIn('photo', result)

    def test_restore_old_photo_preserved(self):
        """3-part compound with no stop words is naturally preserved."""
        result = _validate_and_fix_tags(['restore-old-photo'])
        self.assertIn('restore-old-photo', result)
        self.assertNotIn('restore', result)
        self.assertNotIn('old', result)
        self.assertNotIn('photo', result)

    def test_pop_out_effect_preserved(self):
        """3-part compound with no stop words is naturally preserved."""
        result = _validate_and_fix_tags(['pop-out-effect'])
        self.assertIn('pop-out-effect', result)
        self.assertNotIn('pop', result)
        self.assertNotIn('out', result)
        self.assertNotIn('effect', result)

    def test_xray_preserved(self):
        """x-ray is a real word and should not be split."""
        result = _validate_and_fix_tags(['x-ray', 'medical', 'portrait'])
        self.assertIn('x-ray', result)

    def test_3d_render_preserved(self):
        """3d-render is a real term and should not be split."""
        result = _validate_and_fix_tags(['3d-render', 'digital', 'art'])
        self.assertIn('3d-render', result)

    def test_3d_photo_preserved(self):
        """3d-photo is a real term and should not be split."""
        result = _validate_and_fix_tags(['3d-photo', 'portrait'])
        self.assertIn('3d-photo', result)

    def test_kpop_preserved(self):
        """k-pop is a real word and should not be split."""
        result = _validate_and_fix_tags(['k-pop', 'music', 'portrait'])
        self.assertIn('k-pop', result)

    def test_tshirt_preserved(self):
        """t-shirt is a real word and should not be split."""
        result = _validate_and_fix_tags(['t-shirt', 'fashion', 'portrait'])
        self.assertIn('t-shirt', result)

    def test_unknown_single_char_compound_still_split(self):
        """Random single-char compounds not in preserve list should still split."""
        result = _validate_and_fix_tags(['z-thing', 'portrait'])
        self.assertNotIn('z-thing', result)


# ---------------------------------------------------------------------------
# 3. Stop-word compounds are SPLIT
# ---------------------------------------------------------------------------
class TestStopWordSplitting(TestCase):
    """Test that compounds containing stop/filler words are split."""

    def test_the_sunset_splits(self):
        result = _validate_and_fix_tags(['the-sunset'])
        self.assertNotIn('the', result)
        self.assertIn('sunset', result)
        self.assertNotIn('the-sunset', result)

    def test_a_portrait_splits(self):
        result = _validate_and_fix_tags(['a-portrait'])
        self.assertNotIn('a', result)
        self.assertIn('portrait', result)
        self.assertNotIn('a-portrait', result)

    def test_very_nice_splits(self):
        """Both parts are stop words — neither should survive."""
        result = _validate_and_fix_tags(['very-nice'])
        self.assertNotIn('very', result)
        self.assertNotIn('nice', result)
        self.assertNotIn('very-nice', result)

    def test_in_studio_splits(self):
        result = _validate_and_fix_tags(['in-studio'])
        self.assertNotIn('in', result)
        self.assertIn('studio', result)

    def test_with_flowers_splits(self):
        result = _validate_and_fix_tags(['with-flowers'])
        self.assertNotIn('with', result)
        self.assertIn('flowers', result)

    def test_big_portrait_splits(self):
        result = _validate_and_fix_tags(['big-portrait'])
        self.assertNotIn('big', result)
        self.assertIn('portrait', result)

    def test_good_lighting_splits(self):
        result = _validate_and_fix_tags(['good-lighting'])
        self.assertNotIn('good', result)
        self.assertIn('lighting', result)

    def test_single_char_part_splits(self):
        """Compounds with single-character parts: the single char is discarded."""
        result = _validate_and_fix_tags(['z-test'])
        # 'z' is single char, so it's discarded
        self.assertNotIn('z', result)
        self.assertIn('test', result)

    def test_art_for_kids_discards_stop_word(self):
        """'for' is a stop word — only 'art' and 'kids' survive."""
        result = _validate_and_fix_tags(['art-for-kids'])
        self.assertIn('art', result)
        self.assertIn('kids', result)
        self.assertNotIn('for', result)
        self.assertNotIn('art-for-kids', result)

    def test_people_in_the_city_discards_stop_words(self):
        """'in' and 'the' are stop words — only 'people' and 'city' survive."""
        result = _validate_and_fix_tags(['people-in-the-city'])
        self.assertIn('people', result)
        self.assertIn('city', result)
        self.assertNotIn('in', result)
        self.assertNotIn('the', result)
        self.assertNotIn('people-in-the-city', result)

    def test_day_of_the_dead_discards_stop_words(self):
        """'of' and 'the' are stop words — only 'day' and 'dead' survive."""
        result = _validate_and_fix_tags(['day-of-the-dead'])
        self.assertIn('day', result)
        self.assertIn('dead', result)
        self.assertNotIn('of', result)
        self.assertNotIn('the', result)
        self.assertNotIn('day-of-the-dead', result)

    def test_a_big_portrait_all_stop_words_except_portrait(self):
        """'a' and 'big' are stop words — only 'portrait' survives."""
        result = _validate_and_fix_tags(['a-big-portrait'])
        self.assertIn('portrait', result)
        self.assertNotIn('a', result)
        self.assertNotIn('big', result)
        self.assertNotIn('a-big-portrait', result)

    def test_three_part_cinematic_urban_portrait_preserved(self):
        """3-part compound with no stop words is naturally preserved."""
        result = _validate_and_fix_tags(['cinematic-urban-portrait'])
        self.assertIn('cinematic-urban-portrait', result)
        self.assertNotIn('cinematic', result)
        self.assertNotIn('urban', result)
        self.assertNotIn('portrait', result)

    def test_three_part_moody_dark_fantasy_preserved(self):
        """3-part compound with no stop words is naturally preserved."""
        result = _validate_and_fix_tags(['moody-dark-fantasy'])
        self.assertIn('moody-dark-fantasy', result)
        self.assertNotIn('moody', result)
        self.assertNotIn('dark', result)
        self.assertNotIn('fantasy', result)

    def test_three_part_elegant_evening_gown_preserved(self):
        """3-part compound with no stop words is naturally preserved."""
        result = _validate_and_fix_tags(['elegant-evening-gown'])
        self.assertIn('elegant-evening-gown', result)
        self.assertNotIn('elegant', result)
        self.assertNotIn('evening', result)
        self.assertNotIn('gown', result)


# ---------------------------------------------------------------------------
# 4. Single-word tags are unchanged
# ---------------------------------------------------------------------------
class TestSingleWordTags(TestCase):
    """Test that plain single-word tags pass through unchanged."""

    def test_portrait_unchanged(self):
        result = _validate_and_fix_tags(['portrait'])
        self.assertIn('portrait', result)

    def test_cinematic_unchanged(self):
        result = _validate_and_fix_tags(['cinematic'])
        self.assertIn('cinematic', result)

    def test_moody_unchanged(self):
        result = _validate_and_fix_tags(['moody'])
        self.assertIn('moody', result)

    def test_woman_unchanged(self):
        result = _validate_and_fix_tags(['woman'])
        self.assertIn('woman', result)


# ---------------------------------------------------------------------------
# 5. Lowercase enforcement
# ---------------------------------------------------------------------------
class TestLowercaseEnforcement(TestCase):
    """Test uppercase tags get lowercased."""

    def test_capitalized_tag(self):
        result = _validate_and_fix_tags(['Portraits', 'Cinematic'])
        self.assertIn('portraits', result)
        self.assertIn('cinematic', result)

    def test_space_separated_uppercase(self):
        result = _validate_and_fix_tags(['Modern Architecture'])
        self.assertIn('modern', result)
        self.assertIn('architecture', result)

    def test_all_caps(self):
        result = _validate_and_fix_tags(['PORTRAIT'])
        self.assertIn('portrait', result)


# ---------------------------------------------------------------------------
# 6. AI tag removal
# ---------------------------------------------------------------------------
class TestAITagRemoval(TestCase):
    """Test AI-related tags are removed."""

    def test_ai_art_removed(self):
        result = _validate_and_fix_tags(['ai-art', 'portrait', 'cinematic'])
        self.assertNotIn('ai-art', result)
        self.assertIn('portrait', result)
        self.assertIn('cinematic', result)

    def test_ai_generated_removed(self):
        result = _validate_and_fix_tags(['ai-generated', 'woman'])
        self.assertNotIn('ai-generated', result)
        self.assertIn('woman', result)

    def test_ai_prompt_removed(self):
        result = _validate_and_fix_tags(['ai-prompt'])
        self.assertNotIn('ai-prompt', result)

    def test_ai_influencer_kept(self):
        """ai-influencer is in ALLOWED_AI_TAGS and should pass through."""
        result = _validate_and_fix_tags(['ai-influencer', 'woman'])
        self.assertIn('ai-influencer', result)
        self.assertIn('woman', result)

    def test_ai_colorize_removed(self):
        result = _validate_and_fix_tags(['ai-colorize'])
        self.assertNotIn('ai-colorize', result)

    def test_ai_prefix_catchall(self):
        result = _validate_and_fix_tags(['ai-portrait', 'portrait'])
        self.assertNotIn('ai-portrait', result)
        self.assertIn('portrait', result)

    def test_ai_restoration_removed(self):
        """ai-restoration has ai- prefix and must be caught by AI tag ban."""
        result = _validate_and_fix_tags(['ai-restoration', 'portrait'])
        self.assertNotIn('ai-restoration', result)
        self.assertIn('portrait', result)


# ---------------------------------------------------------------------------
# 6b. ALLOWED_AI_TAGS exceptions
# ---------------------------------------------------------------------------
class TestAllowedAITags(TestCase):
    """Test that AI product-category tags in ALLOWED_AI_TAGS pass through."""

    def test_allowed_ai_tag_influencer(self):
        """ai-influencer is a legitimate niche tag and should be kept."""
        result = _validate_and_fix_tags(['ai-influencer', 'woman', 'portrait'])
        self.assertIn('ai-influencer', result)

    def test_allowed_ai_tag_avatar(self):
        """ai-avatar is a legitimate niche tag and should be kept."""
        result = _validate_and_fix_tags(['ai-avatar', 'character-design'])
        self.assertIn('ai-avatar', result)

    def test_allowed_ai_tag_headshot(self):
        """ai-headshot is a legitimate niche tag and should be kept."""
        result = _validate_and_fix_tags(['ai-headshot', 'professional'])
        self.assertIn('ai-headshot', result)

    def test_allowed_ai_tag_girlfriend(self):
        """ai-girlfriend is a legitimate niche tag and should be kept."""
        result = _validate_and_fix_tags(['ai-girlfriend'])
        self.assertIn('ai-girlfriend', result)

    def test_allowed_ai_tag_boyfriend(self):
        """ai-boyfriend is a legitimate niche tag and should be kept."""
        result = _validate_and_fix_tags(['ai-boyfriend'])
        self.assertIn('ai-boyfriend', result)

    def test_banned_ai_art_still_removed(self):
        """ai-art is NOT in ALLOWED_AI_TAGS and must still be removed."""
        result = _validate_and_fix_tags(['ai-art', 'portrait'])
        self.assertNotIn('ai-art', result)
        self.assertIn('portrait', result)

    def test_unknown_ai_prefix_still_removed(self):
        """ai-portrait is not in ALLOWED_AI_TAGS; startswith('ai-') ban catches it."""
        result = _validate_and_fix_tags(['ai-portrait', 'cinematic'])
        self.assertNotIn('ai-portrait', result)
        self.assertIn('cinematic', result)


# ---------------------------------------------------------------------------
# 7. Ethnicity removal
# ---------------------------------------------------------------------------
class TestEthnicityRemoval(TestCase):
    """Test ethnicity tags are removed."""

    def test_caucasian_removed(self):
        result = _validate_and_fix_tags(['caucasian', 'man', 'portrait'])
        self.assertNotIn('caucasian', result)
        self.assertIn('man', result)
        self.assertIn('portrait', result)

    def test_african_american_removed(self):
        result = _validate_and_fix_tags(['african-american', 'woman'])
        self.assertNotIn('african-american', result)
        self.assertIn('woman', result)

    def test_asian_removed(self):
        result = _validate_and_fix_tags(['asian', 'portrait'])
        self.assertNotIn('asian', result)

    def test_black_woman_compound_removes_black(self):
        """Compound 'black-woman' should split and remove 'black' (ethnicity)."""
        result = _validate_and_fix_tags(['black-woman', 'portrait'])
        self.assertNotIn('black', result)
        self.assertIn('woman', result)
        self.assertIn('portrait', result)

    def test_white_man_compound_removes_white(self):
        """Compound 'white-man' should split and remove 'white' (ethnicity)."""
        result = _validate_and_fix_tags(['white-man', 'portrait'])
        self.assertNotIn('white', result)
        self.assertIn('man', result)

    def test_asian_girl_compound_removes_asian(self):
        """Compound 'asian-girl' should split and remove 'asian' (ethnicity)."""
        result = _validate_and_fix_tags(['asian-girl', 'child'])
        self.assertNotIn('asian', result)
        self.assertIn('girl', result)

    def test_space_separated_ethnicity_removed(self):
        """Space-separated 'black portrait' should remove 'black'."""
        result = _validate_and_fix_tags(['black portrait', 'cinematic'])
        self.assertNotIn('black', result)
        self.assertIn('portrait', result)
        self.assertIn('cinematic', result)

    def test_hispanic_removed(self):
        result = _validate_and_fix_tags(['hispanic'])
        self.assertNotIn('hispanic', result)

    def test_black_removed(self):
        result = _validate_and_fix_tags(['black', 'man'])
        self.assertNotIn('black', result)

    def test_white_removed(self):
        result = _validate_and_fix_tags(['white', 'woman'])
        self.assertNotIn('white', result)


# ---------------------------------------------------------------------------
# 8. Deduplication
# ---------------------------------------------------------------------------
class TestDeduplication(TestCase):
    """Test duplicate tags are removed."""

    def test_exact_duplicates(self):
        result = _validate_and_fix_tags(['portrait', 'portrait', 'cinematic'])
        self.assertEqual(result.count('portrait'), 1)

    def test_compound_and_part_coexist(self):
        """warm-tones (preserved) and warm (separate) both appear; no dedup clash."""
        result = _validate_and_fix_tags(['warm-tones', 'warm', 'portrait'])
        self.assertIn('warm-tones', result)
        self.assertIn('warm', result)
        self.assertEqual(result.count('warm'), 1)

    def test_stop_word_split_dedup(self):
        """Splitting a stop-word compound may create a duplicate."""
        result = _validate_and_fix_tags(['the-portrait', 'portrait', 'moody'])
        # 'the-portrait' splits to 'the' + 'portrait'; 'portrait' already exists
        self.assertEqual(result.count('portrait'), 1)


# ---------------------------------------------------------------------------
# 9. Tag count enforcement
# ---------------------------------------------------------------------------
class TestTagCountEnforcement(TestCase):
    """Test tag count is enforced to max 10."""

    def test_more_than_10_trimmed(self):
        tags = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(len(result), 10)

    def test_exactly_10_unchanged(self):
        tags = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(len(result), 10)

    def test_fewer_than_10_not_padded(self):
        tags = ['portrait', 'cinematic', 'moody']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(len(result), 3)

    def test_compounds_preserved_count(self):
        """Preserved compounds count as 1 tag each, not split into multiple."""
        tags = [
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
            'soft-lighting', 'dramatic-lighting'
        ]
        result = _validate_and_fix_tags(tags)
        # 8 single + 2 preserved compounds = 10, no trimming
        self.assertEqual(len(result), 10)
        self.assertIn('soft-lighting', result)
        self.assertIn('dramatic-lighting', result)


# ---------------------------------------------------------------------------
# 10. Demographic tag reordering
# ---------------------------------------------------------------------------
class TestDemographicTagReordering(TestCase):
    """Test that demographic/gender tags are moved to end of tag list."""

    def test_demographic_tags_moved_to_end(self):
        """Demographic tags should appear after all content tags."""
        tags = ['man', 'male', 'cinematic', 'portrait', 'warm-tones',
                'soft-light', 'beard', 'photorealistic', 'middle-aged', 'thoughtful-expression']
        result = _validate_and_fix_tags(tags)
        # man and male should be at the end
        self.assertIn(result[-1], ('male', 'man'))
        self.assertIn(result[-2], ('male', 'man'))
        # Content tags should be before demographic tags
        man_idx = result.index('man')
        male_idx = result.index('male')
        cinematic_idx = result.index('cinematic')
        self.assertLess(cinematic_idx, man_idx)
        self.assertLess(cinematic_idx, male_idx)

    def test_demographic_reorder_preserves_all_tags(self):
        """Reordering should not add or remove any tags."""
        tags = ['woman', 'female', 'portrait', 'fashion', 'elegant',
                'studio', 'lighting', 'model', 'glamour', 'photorealistic']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(len(result), 10)
        self.assertIn('woman', result)
        self.assertIn('female', result)
        self.assertIn('portrait', result)

    def test_no_demographic_tags_order_unchanged(self):
        """When no demographic tags present, order should be unchanged."""
        tags = ['landscape', 'mountain', 'sunset', 'golden-hour', 'panoramic',
                'nature', 'clouds', 'dramatic', 'wilderness', 'scenic']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(result[0], 'landscape')
        self.assertEqual(result[1], 'mountain')

    def test_multiple_demographic_tags_all_at_end(self):
        """Multiple demographic tags (e.g., couple) should all be at end."""
        tags = ['man', 'male', 'woman', 'female', 'couple', 'romantic',
                'sunset', 'beach', 'silhouette', 'warm-tones']
        result = _validate_and_fix_tags(tags)
        # All 5 demographic tags at end
        content_section = result[:5]
        demo_section = result[5:]
        for tag in demo_section:
            self.assertIn(tag, DEMOGRAPHIC_TAGS)
        for tag in content_section:
            self.assertNotIn(tag, DEMOGRAPHIC_TAGS)

    def test_child_tags_moved_to_end(self):
        """Child-related demographic tags should also move to end."""
        tags = ['boy', 'male', 'child', 'playground', 'happy',
                'outdoor', 'colorful', 'summer', 'candid', 'portrait']
        result = _validate_and_fix_tags(tags)
        boy_idx = result.index('boy')
        playground_idx = result.index('playground')
        self.assertLess(playground_idx, boy_idx)

    def test_male_always_after_man(self):
        """'male' must be the very last tag when both 'man' and 'male' present."""
        tags = ['portrait', 'male', 'man', 'cinematic', 'warm-tones',
                'soft-light', 'beard', 'photorealistic', 'moody', 'dramatic']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(result[-1], 'male')
        man_idx = result.index('man')
        male_idx = result.index('male')
        self.assertLess(man_idx, male_idx)

    def test_female_always_after_woman(self):
        """'female' must be the very last tag when both 'woman' and 'female' present."""
        tags = ['portrait', 'female', 'woman', 'warm-tones', 'elegant',
                'soft-light', 'fashion', 'photorealistic', 'glamour', 'studio']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(result[-1], 'female')
        woman_idx = result.index('woman')
        female_idx = result.index('female')
        self.assertLess(woman_idx, female_idx)

    def test_no_gender_tag_demo_still_at_end(self):
        """When no male/female present, other demographic tags still go to end."""
        tags = ['portrait', 'man', 'cinematic', 'warm-tones', 'soft-light',
                'beard', 'photorealistic', 'moody', 'dramatic', 'editorial']
        result = _validate_and_fix_tags(tags)
        self.assertEqual(result[-1], 'man')
        # All content tags before 'man'
        man_idx = result.index('man')
        for tag in result[:man_idx]:
            self.assertNotIn(tag, DEMOGRAPHIC_TAGS)

    def test_multiple_demo_with_male_female_last(self):
        """With multiple demographic tags, male/female are absolute last."""
        tags = ['man', 'male', 'woman', 'female', 'couple', 'romantic',
                'sunset', 'beach', 'silhouette', 'warm-tones']
        result = _validate_and_fix_tags(tags)
        # male and female should be the last two (distinct)
        self.assertIn(result[-1], ('male', 'female'))
        self.assertIn(result[-2], ('male', 'female'))
        self.assertNotEqual(result[-1], result[-2])
        # man, woman, couple should be before male/female
        male_idx = result.index('male')
        female_idx = result.index('female')
        man_idx = result.index('man')
        woman_idx = result.index('woman')
        couple_idx = result.index('couple')
        self.assertLess(man_idx, male_idx)
        self.assertLess(woman_idx, female_idx)
        self.assertLess(couple_idx, male_idx)


# ---------------------------------------------------------------------------
# 11. Gender pair warnings
# ---------------------------------------------------------------------------
class TestGenderPairWarnings(TestCase):
    """Test gender pair warnings are logged (no auto-fix)."""

    def test_man_without_male_warns(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _validate_and_fix_tags(['man', 'portrait', 'cinematic'])
        self.assertTrue(any("'man' without 'male'" in msg for msg in cm.output))

    def test_woman_without_female_warns(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _validate_and_fix_tags(['woman', 'portrait'])
        self.assertTrue(any("'woman' without 'female'" in msg for msg in cm.output))

    def test_girl_without_female_warns(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _validate_and_fix_tags(['girl', 'child'])
        self.assertTrue(any("'girl' without 'female'" in msg for msg in cm.output))

    def test_boy_without_male_warns(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _validate_and_fix_tags(['boy', 'child'])
        self.assertTrue(any("'boy' without 'male'" in msg for msg in cm.output))

    def test_teen_boy_without_male_warns(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _validate_and_fix_tags(['teen-boy', 'sports'])
        self.assertTrue(any("'teen-boy' without 'male'" in msg for msg in cm.output))

    def test_teen_girl_without_female_warns(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _validate_and_fix_tags(['teen-girl', 'fashion'])
        self.assertTrue(any("'teen-girl' without 'female'" in msg for msg in cm.output))

    def test_correct_pair_no_warning(self):
        """man + male should not produce a gender warning."""
        result = _validate_and_fix_tags(['man', 'male', 'portrait'])
        self.assertIn('man', result)
        self.assertIn('male', result)

    def test_girl_female_no_warning(self):
        """girl + female should not produce a gender warning for girl."""
        result = _validate_and_fix_tags(['girl', 'female', 'child'])
        self.assertIn('girl', result)
        self.assertIn('female', result)


# ---------------------------------------------------------------------------
# 11. Edge cases
# ---------------------------------------------------------------------------
class TestEdgeCases(TestCase):
    """Test edge cases and combined scenarios."""

    def test_empty_input(self):
        result = _validate_and_fix_tags([])
        self.assertEqual(result, [])

    def test_whitespace_tags(self):
        result = _validate_and_fix_tags(['  ', '', '  portrait  '])
        self.assertIn('portrait', result)

    def test_combined_rules(self):
        """Multiple rules applied together."""
        result = _validate_and_fix_tags([
            'ai-art',           # removed (AI tag)
            'caucasian',        # removed (ethnicity)
            'soft-lighting',    # preserved (compound)
            'digital-art',      # preserved (compound)
            'Portrait',         # lowercased
            'warm-tones',       # preserved (compound)
        ])
        self.assertNotIn('ai-art', result)
        self.assertNotIn('caucasian', result)
        self.assertIn('soft-lighting', result)
        self.assertIn('digital-art', result)
        self.assertIn('portrait', result)
        self.assertIn('warm-tones', result)

    def test_prompt_id_in_logs(self):
        """Prompt ID should appear in log messages."""
        # Use a stop-word compound to trigger a split log
        with self.assertLogs('prompts.tasks', level='INFO') as cm:
            _validate_and_fix_tags(['the-sunset'], prompt_id=42)
        self.assertTrue(any('Prompt 42' in msg for msg in cm.output))

    def test_mixed_stop_and_real_compounds(self):
        """Mix of stop-word compounds (split) and real compounds (preserved)."""
        result = _validate_and_fix_tags([
            'double-exposure',   # preserved
            'the-portrait',      # split
            'high-contrast',     # preserved
            'with-lighting',     # split
        ])
        self.assertIn('double-exposure', result)
        self.assertIn('high-contrast', result)
        self.assertNotIn('the-portrait', result)
        self.assertIn('portrait', result)
        self.assertNotIn('with-lighting', result)
        self.assertIn('lighting', result)


# ---------------------------------------------------------------------------
# 14. reorder_tags management command
# ---------------------------------------------------------------------------
from io import StringIO

from django.core.management import call_command
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from taggit.models import Tag


class TestReorderTagsCommand(DjangoTestCase):
    """Tests for the reorder_tags management command."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='reorder_test_user', password='testpass'
        )

    def _make_prompt(self, tag_names):
        """Create a published prompt with tags in the given order."""
        from prompts.models import Prompt
        prompt = Prompt(
            author=self.user,
            title='Test Prompt',
            content='test content',
            excerpt='test excerpt',
            status=1,
            b2_image_url='https://example.com/test.jpg',
        )
        prompt.save()
        # Add tags one at a time to guarantee insertion order
        for name in tag_names:
            tag_obj, _ = Tag.objects.get_or_create(name=name)
            prompt.tags.add(tag_obj)
        return prompt

    def test_reorder_command_fixes_demographic_order(self):
        """Command should reorder tags so demographics are last, male/female very last."""
        # Create prompt with male/man BEFORE content tags (wrong order)
        prompt = self._make_prompt([
            'male', 'man', 'portrait', 'cinematic', 'warm-tones',
            'soft-light', 'photorealistic', 'moody', 'dramatic', 'editorial',
        ])

        out = StringIO()
        call_command('reorder_tags', f'--prompt-id={prompt.pk}', stdout=out)

        # Verify tags are reordered in the database
        from taggit.models import TaggedItem
        ordered_tags = list(
            TaggedItem.objects
            .filter(
                content_type__app_label='prompts',
                content_type__model='prompt',
                object_id=prompt.pk,
            )
            .order_by('id')
            .values_list('tag__name', flat=True)
        )

        # male should be last, man second-to-last
        self.assertEqual(ordered_tags[-1], 'male')
        self.assertEqual(ordered_tags[-2], 'man')

        # Content tags should precede demographics
        man_idx = ordered_tags.index('man')
        for tag in ordered_tags[:man_idx]:
            self.assertNotIn(tag, DEMOGRAPHIC_TAGS)

        self.assertIn('reordered', out.getvalue())

    def test_reorder_command_dry_run_no_changes(self):
        """--dry-run should preview changes without modifying the database."""
        prompt = self._make_prompt([
            'male', 'man', 'portrait', 'cinematic', 'warm-tones',
            'soft-light', 'photorealistic', 'moody', 'dramatic', 'editorial',
        ])

        # Record original TaggedItem IDs
        from taggit.models import TaggedItem
        original_ids = list(
            TaggedItem.objects
            .filter(
                content_type__app_label='prompts',
                content_type__model='prompt',
                object_id=prompt.pk,
            )
            .order_by('id')
            .values_list('id', flat=True)
        )

        out = StringIO()
        call_command('reorder_tags', f'--prompt-id={prompt.pk}', '--dry-run', stdout=out)

        # TaggedItem IDs should be unchanged (no DB modification)
        after_ids = list(
            TaggedItem.objects
            .filter(
                content_type__app_label='prompts',
                content_type__model='prompt',
                object_id=prompt.pk,
            )
            .order_by('id')
            .values_list('id', flat=True)
        )
        self.assertEqual(original_ids, after_ids)

        output = out.getvalue()
        self.assertIn('WOULD reorder', output)
        self.assertIn('DRY RUN', output)


# ---------------------------------------------------------------------------
# Tag Display Ordering Tests
# ---------------------------------------------------------------------------
from django.test import Client


class TestOrderedTagsModelMethod(DjangoTestCase):
    """Tests for the Prompt.ordered_tags() model method."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='tag_order_user', password='testpass'
        )

    def test_ordered_tags_model_method(self):
        """ordered_tags() returns tags ordered by TaggedItem.id ascending."""
        from prompts.models import Prompt
        prompt = Prompt(
            author=self.user,
            title='Ordered Tags Test',
            content='test content',
            excerpt='test excerpt',
            status=1,
            b2_image_url='https://example.com/test.jpg',
        )
        prompt.save()

        # Add tags in specific order: content first, demographics last
        for name in ['cinematic', 'warm-tones', 'portrait', 'man', 'male']:
            tag_obj, _ = Tag.objects.get_or_create(name=name)
            prompt.tags.add(tag_obj)

        result = list(prompt.ordered_tags().values_list('name', flat=True))
        self.assertEqual(
            result,
            ['cinematic', 'warm-tones', 'portrait', 'man', 'male'],
        )


class TestPromptDetailTagOrder(DjangoTestCase):
    """Tests for tag ordering in prompt detail and list views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='view_tag_user', password='testpass'
        )

    def _make_prompt(self, title, tag_names):
        from prompts.models import Prompt
        prompt = Prompt(
            author=self.user,
            title=title,
            slug=title.lower().replace(' ', '-'),
            content='test content',
            excerpt='test excerpt',
            status=1,
            b2_image_url='https://example.com/test.jpg',
        )
        prompt.save()
        for name in tag_names:
            tag_obj, _ = Tag.objects.get_or_create(name=name)
            prompt.tags.add(tag_obj)
        return prompt

    def test_prompt_detail_tags_ordered_by_insertion(self):
        """Prompt detail page renders tags in insertion order (demographics last)."""
        prompt = self._make_prompt('Detail Order Test', [
            'cinematic', 'portrait', 'moody', 'man', 'male',
        ])

        response = self.client.get(f'/prompt/{prompt.slug}/')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Verify tag badges appear in correct order in the tags section
        # Template renders tags inside <a class="tag-badge"> elements
        import re
        tag_badges = re.findall(
            r'class="tag-badge"[^>]*>\s*(\S+)\s*</a>', content
        )
        self.assertEqual(
            tag_badges,
            ['cinematic', 'portrait', 'moody', 'man', 'male'],
            'Tag badges should appear in insertion order',
        )

    def test_prompt_list_tags_still_present(self):
        """Prompt list page still includes tags after ordering refactor (regression check)."""
        prompt = self._make_prompt('List Order Test', [
            'photorealistic', 'dramatic', 'woman', 'female',
        ])

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        # Verify prompt card exists with tags
        self.assertIn('photorealistic', content)
        self.assertIn('dramatic', content)
