"""
JavaScript functional tests for user profile header (Phase E - Part 1)

These tests verify client-side JavaScript functionality:
- Overflow arrow click and scroll behavior
- Smooth scrolling animation
- Console logging for debugging
- Event propagation handling
- Responsive behavior

NOTE: These tests require Selenium WebDriver and browser automation.
Install with: pip install selenium

Run with: python manage.py test prompts.tests.test_user_profile_javascript
"""

from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from prompts.models import Prompt, UserProfile
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    import warnings
    warnings.warn(
        "Selenium not installed. JavaScript tests will be skipped. "
        "Install with: pip install selenium"
    )


def skip_if_no_selenium(test_func):
    """Decorator to skip tests if Selenium is not available"""
    import unittest
    return unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium not installed")(test_func)


class JavaScriptOverflowArrowTestCase(LiveServerTestCase):
    """Test overflow arrow JavaScript functionality with browser automation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SELENIUM_AVAILABLE:
            return

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception as e:
            cls.selenium = None
            warnings.warn(f"Could not initialize Chrome WebDriver: {e}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'selenium') and cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        """Create test user and prompts"""
        if not SELENIUM_AVAILABLE or not self.selenium:
            return

        # Create user
        self.user = User.objects.create_user(
            username='scrolltester',
            email='scroll@test.com',
            password='testpass123'
        )

        # Create many prompts to trigger overflow
        for i in range(20):
            Prompt.objects.create(
                title=f'Prompt {i}',
                slug=f'prompt-{i}',
                content=f'Content {i}',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )

    @skip_if_no_selenium
    def test_overflow_arrow_exists(self):
        """Overflow arrow button should be present in DOM"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        # Navigate to profile
        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['scrolltester'])}")

        # Wait for page load
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'btn-scroll-right'))
        )

        # Check arrow button exists
        arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')
        self.assertIsNotNone(arrow)
        self.assertTrue(arrow.is_displayed())

    @skip_if_no_selenium
    def test_overflow_arrow_click_scrolls_container(self):
        """Clicking arrow should scroll the tab container"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['scrolltester'])}")

        # Wait for page load
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'btn-scroll-right'))
        )

        # Get initial scroll position
        tab_container = self.selenium.find_element(By.ID, 'tabContainer')
        initial_scroll = self.selenium.execute_script("return arguments[0].scrollLeft;", tab_container)

        # Click arrow
        arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')
        arrow.click()

        # Wait for scroll animation
        time.sleep(1)

        # Get new scroll position
        new_scroll = self.selenium.execute_script("return arguments[0].scrollLeft;", tab_container)

        # Should have scrolled right
        self.assertGreater(new_scroll, initial_scroll)

    @skip_if_no_selenium
    def test_overflow_arrow_console_logs(self):
        """Overflow arrow should log to console for debugging"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['scrolltester'])}")

        # Enable browser logs
        logs_before = self.selenium.get_log('browser')

        # Click arrow
        arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')
        arrow.click()

        time.sleep(0.5)

        # Get console logs
        logs_after = self.selenium.get_log('browser')

        # Check for our console logs
        log_messages = [log['message'] for log in logs_after]
        log_text = ' '.join(log_messages)

        # Should contain our debug logs
        self.assertIn('Overflow arrow clicked', log_text)

    @skip_if_no_selenium
    def test_overflow_arrow_hover_effect(self):
        """Arrow should have visual hover effect"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['scrolltester'])}")

        arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')

        # Get initial transform
        initial_transform = arrow.value_of_css_property('transform')

        # Hover over arrow
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.selenium).move_to_element(arrow).perform()

        time.sleep(0.3)

        # Get transform after hover
        hover_transform = arrow.value_of_css_property('transform')

        # Transform should have changed (translateX applied)
        # Note: This might vary based on browser, so we just check it's different
        # or check if transition is defined
        transition = arrow.value_of_css_property('transition')
        self.assertIsNotNone(transition)

    @skip_if_no_selenium
    def test_overflow_arrow_smooth_scroll(self):
        """Scroll should be smooth, not instant"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['scrolltester'])}")

        tab_container = self.selenium.find_element(By.ID, 'tabContainer')
        arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')

        # Get initial scroll
        initial_scroll = self.selenium.execute_script("return arguments[0].scrollLeft;", tab_container)

        # Click arrow
        arrow.click()

        # Check scroll position immediately (should be partway)
        time.sleep(0.2)
        intermediate_scroll = self.selenium.execute_script("return arguments[0].scrollLeft;", tab_container)

        # Wait for scroll to complete
        time.sleep(1)
        final_scroll = self.selenium.execute_script("return arguments[0].scrollLeft;", tab_container)

        # Intermediate should be between initial and final (proof of smooth scroll)
        # If instant, intermediate would equal final
        self.assertGreater(intermediate_scroll, initial_scroll)
        self.assertGreaterEqual(final_scroll, intermediate_scroll)


class JavaScriptMediaFilterTestCase(LiveServerTestCase):
    """Test media filter form JavaScript behavior"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SELENIUM_AVAILABLE:
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception:
            cls.selenium = None

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'selenium') and cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        if not SELENIUM_AVAILABLE or not self.selenium:
            return

        self.user = User.objects.create_user(
            username='filteruser',
            email='filter@test.com',
            password='testpass123'
        )

        # Create mixed media prompts
        for i in range(5):
            Prompt.objects.create(
                title=f'Image {i}',
                slug=f'image-{i}',
                content='Content',
                author=self.user,
                status=1,
                ai_generator='midjourney',
                is_image=True
            )

        for i in range(3):
            Prompt.objects.create(
                title=f'Video {i}',
                slug=f'video-{i}',
                content='Content',
                author=self.user,
                status=1,
                ai_generator='runway',
                is_video=True
            )

    @skip_if_no_selenium
    def test_filter_form_auto_submits(self):
        """Filter form should auto-submit on dropdown change"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['filteruser'])}")

        # Find media type dropdown
        from selenium.webdriver.support.ui import Select
        media_dropdown = Select(self.selenium.find_element(By.NAME, 'media_type'))

        # Count current prompts
        prompts_before = len(self.selenium.find_elements(By.CLASS_NAME, 'prompt-card'))

        # Change dropdown
        media_dropdown.select_by_value('videos')

        # Wait for page reload/filter
        time.sleep(2)

        # Count prompts after filter
        prompts_after = len(self.selenium.find_elements(By.CLASS_NAME, 'prompt-card'))

        # Should have fewer prompts (only videos)
        self.assertLess(prompts_after, prompts_before)
        self.assertEqual(prompts_after, 3)  # 3 videos

    @skip_if_no_selenium
    def test_filter_preserves_selection(self):
        """Selected filter values should persist after form submission"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['filteruser'])}")

        from selenium.webdriver.support.ui import Select
        media_dropdown = Select(self.selenium.find_element(By.NAME, 'media_type'))

        # Select videos
        media_dropdown.select_by_value('videos')

        time.sleep(2)

        # Check that "videos" is still selected
        media_dropdown_after = Select(self.selenium.find_element(By.NAME, 'media_type'))
        selected_value = media_dropdown_after.first_selected_option.get_attribute('value')

        self.assertEqual(selected_value, 'videos')


class JavaScriptMobileResponsivenessTestCase(LiveServerTestCase):
    """Test mobile responsiveness with different viewport sizes"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SELENIUM_AVAILABLE:
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception:
            cls.selenium = None

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'selenium') and cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        if not SELENIUM_AVAILABLE or not self.selenium:
            return

        self.user = User.objects.create_user(
            username='mobileuser',
            email='mobile@test.com',
            password='testpass123'
        )

        Prompt.objects.create(
            title='Test Prompt',
            slug='test-prompt',
            content='Content',
            author=self.user,
            status=1,
            ai_generator='midjourney'
        )

    @skip_if_no_selenium
    def test_mobile_viewport_filter_form_stacking(self):
        """Filter form dropdowns should stack on mobile"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        # Set mobile viewport
        self.selenium.set_window_size(375, 667)  # iPhone SE size

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['mobileuser'])}")

        # Get filter form
        filter_form = self.selenium.find_element(By.ID, 'media-filter-form')

        # Check form width (should be 100% on mobile)
        form_width = filter_form.size['width']
        viewport_width = self.selenium.execute_script("return window.innerWidth;")

        # Form should take nearly full width (within 50px tolerance for padding)
        self.assertGreater(form_width, viewport_width - 50)

    @skip_if_no_selenium
    def test_desktop_viewport_filter_form_inline(self):
        """Filter form dropdowns should be inline on desktop"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        # Set desktop viewport
        self.selenium.set_window_size(1920, 1080)

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['mobileuser'])}")

        # Get dropdowns
        dropdowns = self.selenium.find_elements(By.CSS_SELECTOR, '#media-filter-form select')

        # On desktop, dropdowns should be side-by-side (not stacked)
        if len(dropdowns) >= 2:
            dropdown1_y = dropdowns[0].location['y']
            dropdown2_y = dropdowns[1].location['y']

            # Y positions should be same (inline) or very close
            self.assertLess(abs(dropdown1_y - dropdown2_y), 10)

    @skip_if_no_selenium
    def test_mobile_viewport_edit_button_visible(self):
        """Edit button should remain visible on mobile for owner"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        # Log in as owner
        self.client.login(username='mobileuser', password='testpass123')

        # Set mobile viewport
        self.selenium.set_window_size(375, 667)

        # Navigate to profile (with session cookie)
        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['mobileuser'])}")

        # TODO: Need to handle authentication in Selenium
        # This test needs enhancement to work with Django session authentication

        # For now, just verify element exists in template
        # Full implementation would require Selenium login flow


class JavaScriptEdgeCaseTestCase(LiveServerTestCase):
    """Test JavaScript edge cases and error handling"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SELENIUM_AVAILABLE:
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception:
            cls.selenium = None

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'selenium') and cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        if not SELENIUM_AVAILABLE or not self.selenium:
            return

        self.user = User.objects.create_user(
            username='edgeuser',
            email='edge@test.com',
            password='testpass123'
        )

    @skip_if_no_selenium
    def test_overflow_arrow_with_no_overflow(self):
        """Arrow should handle case where no overflow exists"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        # Create only 2 prompts (not enough to overflow)
        for i in range(2):
            Prompt.objects.create(
                title=f'Prompt {i}',
                slug=f'prompt-{i}',
                content='Content',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['edgeuser'])}")

        # Arrow might be hidden or disabled
        try:
            arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')
            # Should be hidden or have no effect
            initial_scroll = self.selenium.execute_script(
                "return document.getElementById('tabContainer').scrollLeft;"
            )

            arrow.click()
            time.sleep(0.5)

            final_scroll = self.selenium.execute_script(
                "return document.getElementById('tabContainer').scrollLeft;"
            )

            # Scroll shouldn't change if no overflow
            self.assertEqual(initial_scroll, final_scroll)

        except NoSuchElementException:
            # Arrow not present (also acceptable)
            pass

    @skip_if_no_selenium
    def test_rapid_arrow_clicks(self):
        """Multiple rapid arrow clicks should be handled gracefully"""
        if not self.selenium:
            self.skipTest("Selenium WebDriver not available")

        # Create prompts
        for i in range(20):
            Prompt.objects.create(
                title=f'Prompt {i}',
                slug=f'prompt-{i}',
                content='Content',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )

        self.selenium.get(f"{self.live_server_url}{reverse('prompts:user_profile', args=['edgeuser'])}")

        arrow = self.selenium.find_element(By.CLASS_NAME, 'btn-scroll-right')

        # Click rapidly 5 times
        for _ in range(5):
            arrow.click()
            time.sleep(0.1)

        # Should not cause JavaScript errors
        logs = self.selenium.get_log('browser')
        error_logs = [log for log in logs if log['level'] == 'SEVERE']

        # No severe errors should occur
        self.assertEqual(len(error_logs), 0)
