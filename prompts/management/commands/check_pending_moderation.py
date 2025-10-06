"""
Management command to check pending moderation status for prompts.

This command polls Cloudinary API for moderation results on prompts that are
still in 'pending' status. It should be run periodically (e.g., every 5 minutes)
to ensure prompts get published even if webhooks fail or moderation data isn't
immediately available.

Usage:
    python manage.py check_pending_moderation
    python manage.py check_pending_moderation --verbose
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging
import cloudinary.api
from prompts.models import Prompt, ContentFlag

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check pending moderation status and update prompts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--max-age-minutes',
            type=int,
            default=60,
            help='Maximum age of pending prompts to check (default: 60 minutes)',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        max_age_minutes = options['max_age_minutes']

        # Find prompts that are pending moderation
        cutoff_time = timezone.now() - timedelta(minutes=max_age_minutes)
        pending_prompts = Prompt.objects.filter(
            moderation_status='pending',
            created_on__gte=cutoff_time  # Only check recent prompts
        ).order_by('created_on')

        total_count = pending_prompts.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No pending prompts to check'))
            return

        self.stdout.write(f'Found {total_count} pending prompt(s) to check...')

        approved_count = 0
        rejected_count = 0
        still_pending_count = 0
        error_count = 0

        for prompt in pending_prompts:
            try:
                # Determine which media field to check
                if prompt.featured_image:
                    public_id = prompt.featured_image.public_id
                    resource_type = 'image'
                elif prompt.featured_video:
                    public_id = prompt.featured_video.public_id
                    resource_type = 'video'
                else:
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(f'  Prompt {prompt.id}: No media to moderate, setting to approved')
                        )
                    prompt.moderation_status = 'approved'
                    prompt.status = 1  # Published
                    prompt.save()
                    approved_count += 1
                    continue

                if verbose:
                    self.stdout.write(f'  Checking Prompt {prompt.id}: {public_id}')

                # Fetch moderation data from Cloudinary
                try:
                    resource = cloudinary.api.resource(
                        public_id,
                        resource_type=resource_type,
                        moderation=True
                    )

                    moderation_status = resource.get('moderation_status')
                    moderation_data = resource.get('moderation', [])

                    if verbose:
                        self.stdout.write(f'    Moderation status: {moderation_status}')
                        self.stdout.write(f'    Moderation data: {moderation_data}')

                    # Process based on status
                    if moderation_status == 'approved':
                        # Publish the prompt
                        prompt.status = 1  # Published
                        prompt.moderation_status = 'approved'
                        prompt.requires_manual_review = False
                        prompt.save()

                        approved_count += 1
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(f'    ✓ Approved and published')
                            )

                    elif moderation_status == 'rejected':
                        # Keep as draft and flag
                        prompt.status = 0  # Draft
                        prompt.moderation_status = 'rejected'
                        prompt.requires_manual_review = True
                        prompt.save()

                        # Extract flag details
                        flag_details = []
                        for mod in moderation_data:
                            if mod.get('kind') == 'aws_rek':
                                response = mod.get('response', {})
                                labels = response.get('moderation_labels', [])
                                for label in labels:
                                    flag_details.append(
                                        f"{label.get('Name')} ({label.get('Confidence', 0):.1f}%)"
                                    )

                        # Create ContentFlag if not exists
                        if not ContentFlag.objects.filter(
                            prompt=prompt,
                            service_type='cloudinary',
                            flag_type='aws_rekognition'
                        ).exists():
                            ContentFlag.objects.create(
                                prompt=prompt,
                                service_type='cloudinary',
                                flag_type='aws_rekognition',
                                severity='high',
                                details={
                                    'moderation_status': moderation_status,
                                    'flagged_categories': flag_details,
                                    'raw_response': moderation_data
                                }
                            )

                        rejected_count += 1
                        if verbose:
                            self.stdout.write(
                                self.style.ERROR(f'    ✗ Rejected: {", ".join(flag_details)}')
                            )

                    else:
                        # Still pending or unknown status
                        still_pending_count += 1
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(f'    ⟳ Still pending (status: {moderation_status})')
                            )

                except cloudinary.exceptions.NotFound:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ Resource not found in Cloudinary: {public_id}')
                    )
                    # Flag for manual review
                    prompt.requires_manual_review = True
                    prompt.save()

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ Error fetching moderation data: {str(e)}')
                    )
                    logger.error(f'Error checking moderation for prompt {prompt.id}: {e}', exc_info=True)

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  Error processing prompt {prompt.id}: {str(e)}')
                )
                logger.error(f'Error processing prompt {prompt.id}: {e}', exc_info=True)

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Approved and published: {approved_count}'))
        if rejected_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Rejected and flagged: {rejected_count}'))
        if still_pending_count > 0:
            self.stdout.write(self.style.WARNING(f'⟳ Still pending: {still_pending_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'⚠ Errors: {error_count}'))
        self.stdout.write('='*60)
