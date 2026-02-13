"""
Tests for _validate_and_fix_tags post-processing function.

Covers: compound preservation (default), stop-word splitting, lowercase
enforcement, AI tag removal, ethnicity removal, deduplication, tag count
enforcement, and gender pair warnings.
"""

import logging
from unittest import TestCase

from prompts.tasks import _validate_and_fix_tags


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
        self.assertIn('the', result)
        self.assertIn('sunset', result)
        self.assertNotIn('the-sunset', result)

    def test_a_portrait_splits(self):
        result = _validate_and_fix_tags(['a-portrait'])
        self.assertIn('a', result)
        self.assertIn('portrait', result)
        self.assertNotIn('a-portrait', result)

    def test_very_nice_splits(self):
        result = _validate_and_fix_tags(['very-nice'])
        self.assertIn('very', result)
        self.assertIn('nice', result)
        self.assertNotIn('very-nice', result)

    def test_in_studio_splits(self):
        result = _validate_and_fix_tags(['in-studio'])
        self.assertIn('in', result)
        self.assertIn('studio', result)

    def test_with_flowers_splits(self):
        result = _validate_and_fix_tags(['with-flowers'])
        self.assertIn('with', result)
        self.assertIn('flowers', result)

    def test_big_portrait_splits(self):
        result = _validate_and_fix_tags(['big-portrait'])
        self.assertIn('big', result)
        self.assertIn('portrait', result)

    def test_good_lighting_splits(self):
        result = _validate_and_fix_tags(['good-lighting'])
        self.assertIn('good', result)
        self.assertIn('lighting', result)

    def test_single_char_part_splits(self):
        """Compounds with single-character parts should be split."""
        result = _validate_and_fix_tags(['z-test'])
        # 'z' is single char, so it splits
        self.assertIn('z', result)
        self.assertIn('test', result)

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
# 10. Gender pair warnings
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
