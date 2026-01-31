"""
Django management command to test API latency for B2 and OpenAI services.

L8-TIMING-DIAGNOSTICS: Server-side latency testing
This command measures API response times to help diagnose upload delays.

Usage:
    python manage.py test_api_latency                    # Run all tests
    python manage.py test_api_latency --b2-only         # Test B2 only
    python manage.py test_api_latency --openai-only     # Test OpenAI only
    python manage.py test_api_latency --iterations 5    # Run 5 iterations

Created: January 2026 (CC_SPEC_L8_TIMING_DIAGNOSTICS)
"""

import time
import os
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test API latency for B2 and OpenAI services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--b2-only',
            action='store_true',
            help='Only test B2 API latency',
        )
        parser.add_argument(
            '--openai-only',
            action='store_true',
            help='Only test OpenAI API latency',
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=3,
            help='Number of test iterations (default: 3)',
        )

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('L8-TIMING-DIAGNOSTICS: API Latency Test')
        self.stdout.write('=' * 70)

        b2_only = options.get('b2_only', False)
        openai_only = options.get('openai_only', False)
        iterations = options.get('iterations', 3)

        results = {
            'b2': [],
            'openai': []
        }

        # Test B2 if not openai-only
        if not openai_only:
            self.stdout.write(f'\n📦 Testing B2 API ({iterations} iterations)...')
            results['b2'] = self._test_b2_latency(iterations)

        # Test OpenAI if not b2-only
        if not b2_only:
            self.stdout.write(f'\n🤖 Testing OpenAI API ({iterations} iterations)...')
            results['openai'] = self._test_openai_latency(iterations)

        # Print summary
        self._print_summary(results)

    def _test_b2_latency(self, iterations):
        """Test B2 bucket list operation latency."""
        try:
            from prompts.storage_backends import B2MediaStorage
        except ImportError:
            self.stdout.write(self.style.ERROR('  ❌ B2MediaStorage not available'))
            return []

        latencies = []

        for i in range(iterations):
            try:
                start_time = time.perf_counter()

                # Initialize storage backend (tests B2 connection)
                storage = B2MediaStorage()

                # Test bucket existence check (lightweight operation)
                # This is similar to what happens during presign URL generation
                _ = storage.bucket_name

                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000

                latencies.append(latency_ms)
                self.stdout.write(f'  Iteration {i + 1}: {latency_ms:.2f}ms')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Iteration {i + 1}: ERROR - {str(e)}'))
                latencies.append(None)

        return [lat for lat in latencies if lat is not None]

    def _test_openai_latency(self, iterations):
        """Test OpenAI API latency with a minimal request."""
        try:
            import openai
        except ImportError:
            self.stdout.write(self.style.ERROR('  ❌ OpenAI library not available'))
            return []

        api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('  ❌ OPENAI_API_KEY not configured'))
            return []

        latencies = []
        client = openai.OpenAI(api_key=api_key)

        for i in range(iterations):
            try:
                start_time = time.perf_counter()

                # Minimal API call - just list models (very lightweight)
                # This tests the connection overhead without expensive compute
                _ = client.models.list()

                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000

                latencies.append(latency_ms)
                self.stdout.write(f'  Iteration {i + 1}: {latency_ms:.2f}ms')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Iteration {i + 1}: ERROR - {str(e)}'))
                latencies.append(None)

        return [lat for lat in latencies if lat is not None]

    def _print_summary(self, results):
        """Print a summary of all latency test results."""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 70)

        for service, latencies in results.items():
            if latencies:
                avg = sum(latencies) / len(latencies)
                min_lat = min(latencies)
                max_lat = max(latencies)

                self.stdout.write(f'\n{service.upper()}:')
                self.stdout.write(f'  Average: {avg:.2f}ms')
                self.stdout.write(f'  Min:     {min_lat:.2f}ms')
                self.stdout.write(f'  Max:     {max_lat:.2f}ms')

                # Performance assessment
                if avg < 200:
                    self.stdout.write(self.style.SUCCESS('  Status:  ✅ Good (< 200ms)'))
                elif avg < 500:
                    self.stdout.write(self.style.WARNING('  Status:  ⚠️ Moderate (200-500ms)'))
                else:
                    self.stdout.write(self.style.ERROR('  Status:  ❌ Slow (> 500ms)'))
            else:
                self.stdout.write(f'\n{service.upper()}: No successful tests')

        # Upload delay analysis
        self.stdout.write('\n' + '-' * 70)
        self.stdout.write('UPLOAD DELAY ANALYSIS:')
        self.stdout.write('-' * 70)

        total_api_latency = 0
        b2_avg = sum(results['b2']) / len(results['b2']) if results['b2'] else 0
        openai_avg = sum(results['openai']) / len(results['openai']) if results['openai'] else 0
        total_api_latency = b2_avg + openai_avg

        self.stdout.write(f'\nExpected server-side latency: ~{total_api_latency:.0f}ms')
        self.stdout.write(f'  B2 connection:    ~{b2_avg:.0f}ms')
        self.stdout.write(f'  OpenAI API:       ~{openai_avg:.0f}ms')

        self.stdout.write('\nIf upload takes longer than expected:')
        self.stdout.write('  1. Check browser console for UploadTiming output')
        self.stdout.write('  2. Look for delays in "complete_api" segment')
        self.stdout.write('  3. Network latency may add 100-500ms')
        self.stdout.write('  4. Image processing adds ~100-500ms per variant')

        self.stdout.write('\n' + '=' * 70)
