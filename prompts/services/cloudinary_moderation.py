"""
Cloudinary moderation integration for image/video content.

This service handles:
1. AWS Rekognition (Layer 1) - via Cloudinary add-on
2. Cloudinary AI Vision (Layer 2) - custom moderation checks

Checks performed:
- AWS Rekognition: General content moderation, unsafe content detection
- Cloudinary AI: Custom checks for minors, gore, satanic imagery, NSFW
"""

import logging
from typing import Dict, List, Tuple, Optional
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings

logger = logging.getLogger(__name__)


class CloudinaryModerationService:
    """
    Service for moderating images and videos using Cloudinary's
    AWS Rekognition integration and AI Vision moderation.

    Usage:
        service = CloudinaryModerationService()
        result = service.moderate_image(prompt_obj)
    """

    # Rekognition categories that should auto-reject
    REKOGNITION_CRITICAL = [
        'Explicit Nudity',
        'Violence',
        'Visually Disturbing',
        'Drugs',
        'Tobacco',
        'Alcohol',
        'Gambling',
        'Hate Symbols',
    ]

    # Rekognition categories that need review
    REKOGNITION_HIGH = [
        'Suggestive',
        'Revealing Clothes',
        'Rude Gestures',
    ]

    # Custom Cloudinary AI checks for specific violations
    CUSTOM_CHECKS = {
        'minors': {
            'severity': 'critical',
            'tags': ['child', 'minor', 'kid', 'baby', 'toddler', 'teenager'],
        },
        'gore': {
            'severity': 'critical',
            'tags': ['blood', 'gore', 'injury', 'wound', 'corpse'],
        },
        'satanic': {
            'severity': 'high',
            'tags': ['demon', 'devil', 'satanic', 'occult', 'pentagram'],
        },
        'weapons': {
            'severity': 'high',
            'tags': ['gun', 'weapon', 'knife', 'sword', 'rifle'],
        },
    }

    def __init__(self):
        """Initialize Cloudinary configuration."""
        # Cloudinary should already be configured in settings.py
        logger.info("Cloudinary Moderation Service initialized")

    def moderate_image(self, prompt_obj) -> Dict:
        """
        Moderate image/video content using Cloudinary services.

        Runs both:
        1. AWS Rekognition moderation
        2. Cloudinary AI Vision custom checks

        Args:
            prompt_obj: Prompt model instance with featured_image or featured_video

        Returns:
            Dict with combined moderation results
        """
        if not prompt_obj.featured_image and not prompt_obj.featured_video:
            logger.warning(f"Prompt {prompt_obj.id} has no media to moderate")
            return {
                'is_safe': True,
                'status': 'approved',
                'flagged_categories': [],
                'confidence_score': 1.0,
                'raw_response': {'error': 'No media found'},
            }

        # Get the media public_id
        if prompt_obj.is_video():
            public_id = prompt_obj.featured_video.public_id
            resource_type = 'video'
        else:
            public_id = prompt_obj.featured_image.public_id
            resource_type = 'image'

        logger.info(f"Moderating {resource_type}: {public_id}")

        # Run both moderation checks
        rekognition_result = self._check_rekognition(public_id, resource_type)
        ai_vision_result = self._check_custom_ai(public_id, resource_type)

        # Combine results
        combined_result = self._combine_results(rekognition_result, ai_vision_result)

        return combined_result

    def _check_rekognition(self, public_id: str, resource_type: str) -> Dict:
        """
        Check content using AWS Rekognition via Cloudinary.

        Uses Cloudinary's aws_rek_moderation add-on to detect:
        - Explicit content
        - Suggestive content
        - Violence
        - Visually disturbing content
        - Drugs, alcohol, tobacco
        - Hate symbols
        - Gambling

        Args:
            public_id: Cloudinary public ID of the asset
            resource_type: 'image' or 'video'

        Returns:
            Dict with Rekognition moderation results
        """
        try:
            # Get resource info with moderation data
            resource = cloudinary.api.resource(
                public_id,
                resource_type=resource_type,
                moderation='aws_rek'
            )

            moderation_data = resource.get('moderation', [])

            if not moderation_data:
                logger.warning(f"No Rekognition data for {public_id}, may need to enable add-on")
                return {
                    'is_safe': False,
                    'status': 'flagged',
                    'flagged_categories': ['rekognition_unavailable'],
                    'confidence_score': 0.0,
                    'raw_response': {'note': 'AWS Rekognition add-on may not be enabled'},
                }

            # Parse Rekognition results
            flagged_categories = []
            max_confidence = 0.0

            for mod_check in moderation_data:
                if mod_check.get('kind') == 'aws_rek':
                    status = mod_check.get('status', 'pending')
                    response = mod_check.get('response', {})

                    if status == 'approved':
                        return {
                            'is_safe': True,
                            'status': 'approved',
                            'flagged_categories': [],
                            'confidence_score': 0.0,
                            'raw_response': response,
                        }

                    # Check moderation labels
                    labels = response.get('moderation_labels', [])

                    for label in labels:
                        name = label.get('Name', '')
                        confidence = label.get('Confidence', 0) / 100.0  # Convert to 0-1
                        parent_name = label.get('ParentName', '')

                        max_confidence = max(max_confidence, confidence)

                        flagged_categories.append({
                            'category': name,
                            'parent': parent_name,
                            'confidence': confidence,
                            'severity': self._get_rekognition_severity(name, parent_name),
                        })

            # Determine if safe based on categories
            is_safe = not any(
                cat['severity'] in ['critical', 'high']
                for cat in flagged_categories
            )

            if not is_safe and any(cat['severity'] == 'critical' for cat in flagged_categories):
                status = 'rejected'
            elif not is_safe:
                status = 'flagged'
            else:
                status = 'approved'

            return {
                'is_safe': is_safe,
                'status': status,
                'flagged_categories': flagged_categories,
                'confidence_score': max_confidence,
                'raw_response': response,
            }

        except cloudinary.exceptions.NotFound:
            logger.error(f"Cloudinary resource not found: {public_id}")
            return {
                'is_safe': False,
                'status': 'flagged',
                'flagged_categories': ['resource_not_found'],
                'confidence_score': 0.0,
                'raw_response': {'error': 'Resource not found'},
            }
        except Exception as e:
            logger.error(f"Rekognition check error: {str(e)}", exc_info=True)
            return {
                'is_safe': False,
                'status': 'flagged',
                'flagged_categories': ['api_error'],
                'confidence_score': 0.0,
                'raw_response': {'error': str(e)},
            }

    def _check_custom_ai(self, public_id: str, resource_type: str) -> Dict:
        """
        Check content using Cloudinary AI Vision for custom categories.

        Custom checks for:
        - Minors (children, teenagers)
        - Gore (blood, injuries, corpses)
        - Satanic imagery (demons, occult symbols)
        - Weapons

        Args:
            public_id: Cloudinary public ID of the asset
            resource_type: 'image' or 'video'

        Returns:
            Dict with AI Vision moderation results
        """
        try:
            # Get resource with categorization and tags
            resource = cloudinary.api.resource(
                public_id,
                resource_type=resource_type,
                categorization='google_tagging',
                detection='cld_ai'
            )

            # Get auto-generated tags
            tags = resource.get('tags', [])
            info = resource.get('info', {})
            detection = info.get('detection', {}) if info else {}

            logger.info(f"AI Vision tags for {public_id}: {tags}")

            # Check for custom violation categories
            flagged_categories = []
            max_confidence = 0.0

            for check_name, check_config in self.CUSTOM_CHECKS.items():
                matching_tags = [
                    tag for tag in tags
                    if any(violation_tag in tag.lower() for violation_tag in check_config['tags'])
                ]

                if matching_tags:
                    # Assign confidence based on number of matching tags
                    confidence = min(0.5 + (len(matching_tags) * 0.1), 1.0)
                    max_confidence = max(max_confidence, confidence)

                    flagged_categories.append({
                        'category': check_name,
                        'matching_tags': matching_tags,
                        'confidence': confidence,
                        'severity': check_config['severity'],
                    })

            # Check face detection for minors specifically
            faces = detection.get('faces', [])
            if faces:
                logger.info(f"Detected {len(faces)} faces in {public_id}")
                # Additional logic could go here to estimate age ranges

            # Determine safety
            is_safe = len(flagged_categories) == 0

            if not is_safe and any(cat['severity'] == 'critical' for cat in flagged_categories):
                status = 'rejected'
            elif not is_safe:
                status = 'flagged'
            else:
                status = 'approved'

            return {
                'is_safe': is_safe,
                'status': status,
                'flagged_categories': flagged_categories,
                'confidence_score': max_confidence,
                'raw_response': {
                    'tags': tags,
                    'faces_detected': len(faces),
                    'detection_data': detection,
                },
            }

        except Exception as e:
            logger.error(f"AI Vision check error: {str(e)}", exc_info=True)
            return {
                'is_safe': False,
                'status': 'flagged',
                'flagged_categories': ['api_error'],
                'confidence_score': 0.0,
                'raw_response': {'error': str(e)},
            }

    def _get_rekognition_severity(self, category: str, parent: str = '') -> str:
        """
        Determine severity level for Rekognition category.

        Args:
            category: Rekognition label name
            parent: Parent category name

        Returns:
            Severity: 'critical', 'high', 'medium', or 'low'
        """
        check_name = parent if parent else category

        if check_name in self.REKOGNITION_CRITICAL:
            return 'critical'
        elif check_name in self.REKOGNITION_HIGH:
            return 'high'
        else:
            return 'medium'

    def _combine_results(self, rekognition_result: Dict, ai_vision_result: Dict) -> Dict:
        """
        Combine results from Rekognition and AI Vision checks.

        Args:
            rekognition_result: Results from AWS Rekognition
            ai_vision_result: Results from Cloudinary AI Vision

        Returns:
            Combined moderation result
        """
        # Both must be safe for overall safety
        is_safe = rekognition_result['is_safe'] and ai_vision_result['is_safe']

        # Combine flagged categories
        all_flags = (
            rekognition_result['flagged_categories'] +
            ai_vision_result['flagged_categories']
        )

        # Get highest confidence
        max_confidence = max(
            rekognition_result['confidence_score'],
            ai_vision_result['confidence_score']
        )

        # Determine overall status (most restrictive wins)
        statuses = [rekognition_result['status'], ai_vision_result['status']]
        if 'rejected' in statuses:
            status = 'rejected'
        elif 'flagged' in statuses:
            status = 'flagged'
        else:
            status = 'approved'

        return {
            'is_safe': is_safe,
            'status': status,
            'flagged_categories': [cat['category'] if isinstance(cat, dict) else cat for cat in all_flags],
            'confidence_score': max_confidence,
            'raw_response': {
                'rekognition': rekognition_result['raw_response'],
                'ai_vision': ai_vision_result['raw_response'],
                'combined_flags': all_flags,
            }
        }
