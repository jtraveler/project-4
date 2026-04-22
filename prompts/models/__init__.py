"""
prompts.models package — models for the prompts app.

Session 168-D split the previous 3,517-line prompts/models.py
into this package. External code should import from
`prompts.models` as before — the shim below re-exports every
public class and constant to preserve backward compatibility.

Internal package code (submodule-to-submodule references) should
import from the specific submodule (`from .moderation import
ContentFlag`) when a circular-import would otherwise occur.
"""

# Re-export all public classes
from .users import UserProfile, AvatarChangeLog, EmailPreferences, Follow
from .taxonomy import TagCategory, SubjectCategory, SubjectDescriptor
from .prompt import (
    PromptManager, Prompt, SlugRedirect, DeletedPrompt, PromptView,
)
from .interactions import (
    Comment, Collection, CollectionItem, Notification,
)
from .moderation import (
    PromptReport, ModerationLog, ProfanityWord, ContentFlag,
    NSFWViolation,
)
from .bulk_gen import (
    BulkGenerationJob, GeneratedImage, GeneratorModel,
)
from .credits import UserCredit, CreditTransaction
from .site import SiteSettings, CollaborateRequest

# Re-export module-level constants that external code imports
# (test_bulk_page_creation.py:775 imports AI_GENERATOR_CHOICES)
from .constants import (
    STATUS,
    MODERATION_STATUS,
    MODERATION_SERVICE,
    AI_GENERATOR_CHOICES,
    DELETION_REASONS,
    NOTIFICATION_TYPE_CATEGORY_MAP,
)

__all__ = [
    # Models
    'UserProfile', 'AvatarChangeLog', 'EmailPreferences', 'Follow',
    'TagCategory', 'SubjectCategory', 'SubjectDescriptor',
    'PromptManager', 'Prompt', 'SlugRedirect', 'DeletedPrompt',
    'PromptView',
    'Comment', 'Collection', 'CollectionItem', 'Notification',
    'PromptReport', 'ModerationLog', 'ProfanityWord', 'ContentFlag',
    'NSFWViolation',
    'BulkGenerationJob', 'GeneratedImage', 'GeneratorModel',
    'UserCredit', 'CreditTransaction',
    'SiteSettings', 'CollaborateRequest',
    # Constants
    'STATUS', 'MODERATION_STATUS', 'MODERATION_SERVICE',
    'AI_GENERATOR_CHOICES', 'DELETION_REASONS',
    'NOTIFICATION_TYPE_CATEGORY_MAP',
]
