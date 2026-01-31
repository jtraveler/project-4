"""
Django management command to test Django-Q infrastructure setup.

Usage:
    python manage.py test_django_q
    python manage.py test_django_q --sync  # Run task synchronously for testing
    python manage.py test_django_q --verbose  # Show detailed output

Phase N: Optimistic Upload UX Infrastructure Verification
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test Django-Q infrastructure setup and verify configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run test task synchronously (for testing without qcluster)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed configuration output',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('Django-Q Infrastructure Test'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')

        all_passed = True

        # Test 1: Check django_q is in INSTALLED_APPS
        self.stdout.write('Test 1: Checking INSTALLED_APPS...')
        if 'django_q' in settings.INSTALLED_APPS:
            self.stdout.write(self.style.SUCCESS('  ✓ django_q is in INSTALLED_APPS'))
        else:
            self.stdout.write(self.style.ERROR('  ✗ django_q is NOT in INSTALLED_APPS'))
            all_passed = False

        # Test 2: Check Q_CLUSTER configuration exists
        self.stdout.write('Test 2: Checking Q_CLUSTER configuration...')
        if hasattr(settings, 'Q_CLUSTER'):
            self.stdout.write(self.style.SUCCESS('  ✓ Q_CLUSTER is configured'))
            if options['verbose']:
                self.stdout.write(f'    Name: {settings.Q_CLUSTER.get("name", "N/A")}')
                self.stdout.write(f'    Workers: {settings.Q_CLUSTER.get("workers", "N/A")}')
                self.stdout.write(f'    ORM: {settings.Q_CLUSTER.get("orm", "N/A")}')
                self.stdout.write(f'    Timeout: {settings.Q_CLUSTER.get("timeout", "N/A")}s')
                self.stdout.write(f'    Retry: {settings.Q_CLUSTER.get("retry", "N/A")}s')
        else:
            self.stdout.write(self.style.ERROR('  ✗ Q_CLUSTER is NOT configured'))
            all_passed = False

        # Test 3: Check ORM broker is using default database
        self.stdout.write('Test 3: Checking ORM broker configuration...')
        if hasattr(settings, 'Q_CLUSTER'):
            orm_setting = settings.Q_CLUSTER.get('orm')
            if orm_setting == 'default':
                self.stdout.write(
                    self.style.SUCCESS('  ✓ Using Postgres ORM as broker (zero extra cost)')
                )
            elif orm_setting:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Using ORM broker: {orm_setting}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('  ⚠ ORM broker not specified (may use Redis)')
                )
        else:
            self.stdout.write(self.style.ERROR('  ✗ Cannot check - Q_CLUSTER missing'))
            all_passed = False

        # Test 4: Check Django-Q tables exist
        self.stdout.write('Test 4: Checking Django-Q database tables...')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_name LIKE 'django_q%'"
                )
                tables = [row[0] for row in cursor.fetchall()]

            if tables:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Found {len(tables)} Django-Q table(s)'))
                if options['verbose']:
                    for table in tables:
                        self.stdout.write(f'    - {table}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '  ⚠ No Django-Q tables found. Run: python manage.py migrate'
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Database check failed: {e}'))
            all_passed = False

        # Test 5: Check task module can be imported
        self.stdout.write('Test 5: Checking task module import...')
        try:
            from prompts.tasks import (
                test_task,
                placeholder_nsfw_moderation,
                placeholder_ai_generation,
                placeholder_variant_generation,
            )
            self.stdout.write(self.style.SUCCESS('  ✓ All task functions imported successfully'))
            if options['verbose']:
                self.stdout.write('    - test_task')
                self.stdout.write('    - placeholder_nsfw_moderation')
                self.stdout.write('    - placeholder_ai_generation')
                self.stdout.write('    - placeholder_variant_generation')
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Import failed: {e}'))
            all_passed = False

        # Test 6: Run test task (sync or async)
        self.stdout.write('Test 6: Running test task...')
        if options['sync']:
            # Synchronous execution for testing
            try:
                result = test_task('Sync test from management command')
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Sync task completed: {result}')
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Sync task failed: {e}'))
                all_passed = False
        else:
            # Async execution via Django-Q
            try:
                from django_q.tasks import async_task
                task_id = async_task(
                    'prompts.tasks.test_task',
                    'Async test from management command'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Async task queued with ID: {task_id}')
                )
                self.stdout.write(
                    self.style.WARNING(
                        '    Note: Task will execute when qcluster is running'
                    )
                )
                self.stdout.write(
                    '    To run qcluster: python manage.py qcluster'
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Async task failed: {e}'))
                all_passed = False

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        if all_passed:
            self.stdout.write(
                self.style.SUCCESS('All tests passed! Django-Q infrastructure is ready.')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Some tests failed. Please review the output above.')
            )
        self.stdout.write(self.style.HTTP_INFO('=' * 60))

        # Next steps
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Next steps:'))
        self.stdout.write('  1. Run migrations: python manage.py migrate')
        self.stdout.write('  2. Start qcluster: python manage.py qcluster')
        self.stdout.write('  3. Test async: python manage.py test_django_q')
        self.stdout.write('  4. Test sync:  python manage.py test_django_q --sync')
