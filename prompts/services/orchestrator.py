"""
Moderation orchestrator that coordinates all moderation services.

This module runs all three layers of moderation:
1. AWS Rekognition (via Cloudinary)
2. Cloudinary AI Vision (custom checks)
3. OpenAI Moderation API (text content)

And creates ModerationLog and ContentFlag records for tracking.
"""

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction

from ..models import Prompt, ModerationLog, ContentFlag
from .openai_moderation import OpenAIModerationService
from .cloudinary_moderation import CloudinaryModerationService
from .profanity_filter import ProfanityFilterService

logger = logging.getLogger(__name__)


class ModerationOrchestrator:
    """
    Orchestrates all moderation checks and updates the database.

    Usage:
        orchestrator = ModerationOrchestrator()
        result = orchestrator.moderate_prompt(prompt)
    """

    def __init__(self):
        """Initialize all moderation services."""
        try:
            self.openai_service = OpenAIModerationService()
            self.openai_enabled = True
        except (ValueError, Exception) as e:
            logger.warning(f"OpenAI service disabled: {str(e)}")
            self.openai_enabled = False

        self.cloudinary_service = CloudinaryModerationService()
        self.profanity_service = ProfanityFilterService()
        logger.info("Moderation Orchestrator initialized")

    def moderate_prompt(self, prompt: Prompt, force: bool = False) -> Dict:
        """
        Run all moderation checks on a prompt.

        This method:
        1. Runs all three moderation layers
        2. Creates ModerationLog entries for each check
        3. Creates ContentFlag entries for violations
        4. Updates the Prompt moderation status
        5. Returns a summary of results

        Args:
            prompt: Prompt instance to moderate
            force: If True, re-run moderation even if already completed

        Returns:
            Dict with:
            - overall_status: 'approved', 'rejected', 'flagged', or 'pending'
            - requires_review: bool
            - checks_completed: int
            - checks_failed: int
            - summary: dict of each service's result
        """
        # Check if already moderated
        if prompt.moderation_status != 'pending' and not force:
            logger.info(f"Prompt {prompt.id} already moderated: {prompt.moderation_status}")
            return {
                'overall_status': prompt.moderation_status,
                'requires_review': prompt.requires_manual_review,
                'checks_completed': prompt.moderation_logs.count(),
                'checks_failed': 0,
                'message': 'Already moderated (use force=True to re-run)',
            }

        logger.info(f"Starting moderation for Prompt {prompt.id}: {prompt.title}")

        results = {
            'profanity': None,
            'openai': None,
            'rekognition': None,
            'cloudinary_ai': None,
        }

        # Layer 0: Custom profanity filter (runs first, cheapest)
        try:
            results['profanity'] = self._run_profanity_check(prompt)
        except Exception as e:
            logger.error(f"Profanity filter failed: {str(e)}", exc_info=True)
            results['profanity'] = {'status': 'flagged', 'error': str(e)}

        # Layer 3: OpenAI text moderation
        if self.openai_enabled:
            try:
                results['openai'] = self._run_openai_moderation(prompt)
            except Exception as e:
                logger.error(f"OpenAI moderation failed: {str(e)}", exc_info=True)
                results['openai'] = {'status': 'flagged', 'error': str(e)}

        # Layers 1 & 2: Cloudinary (Rekognition + AI Vision)
        # SKIP during initial creation - results will come via webhook
        # Only run if force=True (e.g., manual re-moderation from admin)
        if force and (prompt.featured_image or prompt.featured_video):
            try:
                cloudinary_result = self.cloudinary_service.moderate_image(prompt)
                # Note: Cloudinary service combines both Rekognition and AI Vision
                # We'll log it as 'cloudinary_ai' for now but it includes both layers
                results['cloudinary_ai'] = cloudinary_result
            except Exception as e:
                logger.error(f"Cloudinary moderation failed: {str(e)}", exc_info=True)
                results['cloudinary_ai'] = {'status': 'flagged', 'error': str(e)}
        else:
            # Cloudinary moderation happens asynchronously via webhook
            logger.info(f"Skipping Cloudinary check for Prompt {prompt.id} - will be handled by webhook")
            results['cloudinary_ai'] = {
                'status': 'pending',
                'message': 'AWS Rekognition moderation pending (webhook)',
                'is_safe': True  # Assume safe for now, webhook will update
            }

        # Determine overall status
        overall_result = self._determine_overall_status(results)

        # Update prompt with results
        with transaction.atomic():
            # Save moderation logs
            self._save_moderation_logs(prompt, results)

            # Update prompt moderation status
            prompt.moderation_status = overall_result['status']
            prompt.requires_manual_review = overall_result['requires_review']
            prompt.moderation_completed_at = timezone.now()

            # Set prompt publication status based on moderation result
            # Only publish if fully approved (no pending checks)
            old_status = prompt.status
            if overall_result['status'] == 'approved':
                prompt.status = 1  # Published
                logger.info(f"Setting prompt {prompt.id} status to PUBLISHED (1) - was {old_status}")
            elif overall_result['status'] == 'pending':
                # Keep as draft while waiting for async moderation (webhook)
                prompt.status = 0  # Draft
                logger.info(f"Keeping prompt {prompt.id} as DRAFT (0) - waiting for webhook moderation results")
            else:
                # Flagged or rejected content should remain as draft
                prompt.status = 0  # Draft
                logger.info(f"Keeping prompt {prompt.id} as DRAFT (0) - moderation status: {overall_result['status']}")

            prompt.save(update_fields=[
                'moderation_status',
                'requires_manual_review',
                'moderation_completed_at',
                'status'
            ])

            logger.info(f"Prompt {prompt.id} saved - status in DB: {prompt.status}, moderation_status: {prompt.moderation_status}")

        logger.info(
            f"Moderation complete for Prompt {prompt.id}: "
            f"{overall_result['status']} (review: {overall_result['requires_review']})"
        )

        return {
            'overall_status': overall_result['status'],
            'requires_review': overall_result['requires_review'],
            'checks_completed': sum(1 for r in results.values() if r is not None),
            'checks_failed': sum(
                1 for r in results.values()
                if r and r.get('status') in ['rejected', 'flagged']
            ),
            'summary': results,
        }

    def _run_profanity_check(self, prompt: Prompt) -> Dict:
        """
        Run custom profanity filter and return results.

        Args:
            prompt: Prompt instance

        Returns:
            Dict with profanity check results
        """
        logger.info(f"Running profanity check for Prompt {prompt.id}")
        result = self.profanity_service.check_prompt(prompt)
        return result

    def _run_openai_moderation(self, prompt: Prompt) -> Dict:
        """
        Run OpenAI text moderation and return results.

        Args:
            prompt: Prompt instance

        Returns:
            Dict with OpenAI moderation results
        """
        logger.info(f"Running OpenAI moderation for Prompt {prompt.id}")
        result = self.openai_service.moderate_prompt(prompt)
        return result

    def _determine_overall_status(self, results: Dict) -> Dict:
        """
        Determine overall moderation status from all service results.

        Logic:
        - If ANY service is 'pending' -> overall = 'pending' (wait for webhook)
        - If ANY service rejects -> overall = 'rejected'
        - If ANY service flags (and none reject) -> overall = 'flagged'
        - If ALL services approve -> overall = 'approved'
        - If ANY service has error -> flag for manual review

        Args:
            results: Dict of service results

        Returns:
            Dict with 'status' and 'requires_review'
        """
        statuses = []
        has_pending = False
        has_errors = False

        for service_name, result in results.items():
            if result is None:
                continue

            status = result.get('status', 'pending')
            statuses.append(status)

            if status == 'pending':
                has_pending = True

            if 'error' in result:
                has_errors = True

        # Determine overall status
        logger.info(f"Determining overall status from all checks: {statuses}")
        logger.info(f"Has pending: {has_pending}, Has errors: {has_errors}")

        # CRITICAL: If ANY service is pending, overall must be pending
        if has_pending:
            overall_status = 'pending'
            requires_review = False  # No review needed, just waiting for webhook
            logger.info("Overall status: PENDING (waiting for async webhook results)")
        elif 'rejected' in statuses:
            overall_status = 'rejected'
            requires_review = True
            logger.info("Overall status: REJECTED (at least one service rejected)")
        elif 'flagged' in statuses or has_errors:
            overall_status = 'flagged'
            requires_review = True
            logger.info(f"Overall status: FLAGGED (flagged services or errors)")
        elif all(s == 'approved' for s in statuses) and len(statuses) > 0:
            overall_status = 'approved'
            requires_review = False
            logger.info(f"Overall status: APPROVED (all {len(statuses)} services approved)")
        else:
            overall_status = 'pending'
            requires_review = True
            logger.info(f"Overall status: PENDING (default fallback, statuses: {statuses})")

        logger.info(f"Final determination: status={overall_status}, requires_review={requires_review}")

        return {
            'status': overall_status,
            'requires_review': requires_review,
        }

    def _save_moderation_logs(self, prompt: Prompt, results: Dict) -> None:
        """
        Save ModerationLog and ContentFlag entries for all checks.

        Args:
            prompt: Prompt instance
            results: Dict of service results
        """
        # Map service names to model choices
        service_map = {
            'profanity': 'profanity',
            'openai': 'openai',
            'rekognition': 'rekognition',
            'cloudinary_ai': 'cloudinary_ai',
        }

        for service_key, result in results.items():
            if result is None:
                continue

            service_name = service_map.get(service_key)
            if not service_name:
                continue

            # Create ModerationLog
            log = ModerationLog.objects.create(
                prompt=prompt,
                service=service_name,
                status=result.get('status', 'pending'),
                confidence_score=result.get('confidence_score', 0.0),
                flagged_categories=result.get('flagged_categories', []),
                raw_response=result.get('raw_response', {}),
                notes=result.get('error', '') if 'error' in result else ''
            )

            # Create ContentFlag entries for violations
            self._save_content_flags(log, result)

            logger.info(f"Saved {service_name} moderation log for Prompt {prompt.id}")

    def _save_content_flags(self, log: ModerationLog, result: Dict) -> None:
        """
        Create ContentFlag entries for flagged categories.

        Args:
            log: ModerationLog instance
            result: Service result dict
        """
        raw_response = result.get('raw_response', {})

        # Handle OpenAI format
        if 'flagged_details' in raw_response:
            for detail in raw_response['flagged_details']:
                ContentFlag.objects.create(
                    moderation_log=log,
                    category=detail['category'],
                    confidence=detail['confidence'],
                    severity=detail['severity'],
                    details={'source': 'openai'}
                )

        # Handle Cloudinary format
        elif 'combined_flags' in raw_response:
            for flag in raw_response['combined_flags']:
                if isinstance(flag, dict):
                    ContentFlag.objects.create(
                        moderation_log=log,
                        category=flag.get('category', 'unknown'),
                        confidence=flag.get('confidence', 0.0),
                        severity=flag.get('severity', 'medium'),
                        details={
                            'source': 'cloudinary',
                            'parent': flag.get('parent'),
                            'matching_tags': flag.get('matching_tags', []),
                        }
                    )

    def bulk_moderate_prompts(
        self,
        prompts: Optional[List[Prompt]] = None,
        status_filter: str = 'pending'
    ) -> Dict:
        """
        Run moderation on multiple prompts.

        Args:
            prompts: List of Prompt instances (if None, queries based on status)
            status_filter: Only moderate prompts with this status

        Returns:
            Dict with:
            - total_processed: int
            - approved: int
            - rejected: int
            - flagged: int
            - errors: int
        """
        if prompts is None:
            prompts = Prompt.objects.filter(moderation_status=status_filter)

        logger.info(f"Starting bulk moderation of {prompts.count()} prompts")

        stats = {
            'total_processed': 0,
            'approved': 0,
            'rejected': 0,
            'flagged': 0,
            'errors': 0,
        }

        for prompt in prompts:
            try:
                result = self.moderate_prompt(prompt)
                stats['total_processed'] += 1

                status = result['overall_status']
                if status == 'approved':
                    stats['approved'] += 1
                elif status == 'rejected':
                    stats['rejected'] += 1
                elif status == 'flagged':
                    stats['flagged'] += 1

            except Exception as e:
                logger.error(f"Error moderating prompt {prompt.id}: {str(e)}")
                stats['errors'] += 1

        logger.info(f"Bulk moderation complete: {stats}")
        return stats
