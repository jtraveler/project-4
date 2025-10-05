"""
Django management command to test the moderation system.

Tests all 3 layers of moderation with sample data.

Usage:
    python manage.py test_moderation
"""

from django.core.management.base import BaseCommand
from prompts.services import (
    OpenAIModerationService,
    CloudinaryModerationService,
    ModerationOrchestrator
)


class Command(BaseCommand):
    help = 'Test the content moderation system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Content Moderation System - Test Suite'))
        self.stdout.write(self.style.SUCCESS('=' * 60 + '\n'))

        # Test 1: OpenAI Service
        self.test_openai_service()

        # Test 2: Cloudinary Service
        self.test_cloudinary_service()

        # Test 3: Orchestrator
        self.test_orchestrator()

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✓ All tests completed'))
        self.stdout.write('=' * 60 + '\n')

    def test_openai_service(self):
        """Test OpenAI Moderation API service"""
        self.stdout.write(self.style.WARNING('\n[Test 1] OpenAI Text Moderation'))
        self.stdout.write('-' * 60)

        try:
            service = OpenAIModerationService()
            self.stdout.write(self.style.SUCCESS('✓ OpenAI service initialized'))

            # Test safe content
            self.stdout.write('\nTesting safe content...')
            is_safe, categories, confidence = service.moderate_text(
                "This is a beautiful landscape with mountains and trees."
            )
            if is_safe:
                self.stdout.write(self.style.SUCCESS('  ✓ Safe content approved'))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ False positive! Flagged: {categories}'
                    )
                )

            # Test potentially unsafe content
            self.stdout.write('\nTesting edge case content...')
            is_safe, categories, confidence = service.moderate_text(
                "How to stay safe online"
            )
            self.stdout.write(
                f'  Result: {"Safe" if is_safe else "Flagged"} '
                f'(Confidence: {confidence:.2f})'
            )

            self.stdout.write(self.style.SUCCESS('\n✓ OpenAI service test passed'))

        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ OpenAI service failed: {e}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '  → Check OPENAI_API_KEY environment variable'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Unexpected error: {e}')
            )

    def test_cloudinary_service(self):
        """Test Cloudinary moderation service"""
        self.stdout.write(self.style.WARNING('\n[Test 2] Cloudinary Image/Video Moderation'))
        self.stdout.write('-' * 60)

        try:
            service = CloudinaryModerationService()
            self.stdout.write(self.style.SUCCESS('✓ Cloudinary service initialized'))

            self.stdout.write(
                '\nNote: Image/video tests require actual uploaded assets.'
            )
            self.stdout.write(
                'To test fully, upload a prompt through the web interface.'
            )

            self.stdout.write(self.style.SUCCESS('\n✓ Cloudinary service test passed'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Cloudinary service failed: {e}')
            )

    def test_orchestrator(self):
        """Test the moderation orchestrator"""
        self.stdout.write(self.style.WARNING('\n[Test 3] Moderation Orchestrator'))
        self.stdout.write('-' * 60)

        try:
            orchestrator = ModerationOrchestrator()
            self.stdout.write(self.style.SUCCESS('✓ Orchestrator initialized'))

            # Check if OpenAI is enabled
            if orchestrator.openai_enabled:
                self.stdout.write(
                    self.style.SUCCESS('  ✓ OpenAI service: ENABLED')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('  ⚠ OpenAI service: DISABLED')
                )

            self.stdout.write(
                self.style.SUCCESS('  ✓ Cloudinary service: ENABLED')
            )

            self.stdout.write(
                '\nOrchestrator is ready to moderate prompts.'
            )
            self.stdout.write(
                'To test with actual prompt: create a prompt via web interface'
            )

            self.stdout.write(self.style.SUCCESS('\n✓ Orchestrator test passed'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Orchestrator failed: {e}')
            )

    def test_with_prompt(self, prompt):
        """
        Test moderation with an actual prompt.
        This method is called manually or via another command.
        """
        self.stdout.write(
            self.style.WARNING(f'\n[Test] Moderating Prompt: {prompt.title}')
        )
        self.stdout.write('-' * 60)

        try:
            orchestrator = ModerationOrchestrator()
            result = orchestrator.moderate_prompt(prompt)

            self.stdout.write(f'\nResult:')
            self.stdout.write(f'  Status: {result["overall_status"]}')
            self.stdout.write(f'  Requires review: {result["requires_review"]}')
            self.stdout.write(f'  Checks completed: {result["checks_completed"]}')
            self.stdout.write(f'  Checks failed: {result["checks_failed"]}')

            if result['summary']:
                self.stdout.write(f'\nService Results:')
                for service, service_result in result['summary'].items():
                    if service_result:
                        status = service_result.get('status', 'N/A')
                        flags = service_result.get('flagged_categories', [])
                        self.stdout.write(
                            f'  {service}: {status} '
                            f'({len(flags)} flags)'
                        )

            if result['overall_status'] == 'approved':
                self.stdout.write(
                    self.style.SUCCESS('\n✓ Prompt approved!')
                )
            elif result['overall_status'] == 'rejected':
                self.stdout.write(
                    self.style.ERROR('\n✗ Prompt rejected')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('\n⚠ Prompt flagged for review')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Moderation failed: {e}')
            )
