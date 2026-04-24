"""
prompts.admin package.

Session 168-F split the previous 2,459-line prompts/admin.py
into this package. Django discovers admin classes via
@admin.register() decorators, which fire at import time.
Importing each submodule triggers its registrations.

Import order matters:

1. forms + inlines (no side effects) — imported first so later
   submodules can import from them.

2. taxonomy_admin — contains ``admin.site.unregister(Tag)`` which
   must run before any taxonomy admin classes register.

3. All other admin submodules (each fires @admin.register as
   they load; users_admin contains ``admin.site.unregister(User)``
   internally before CustomUserAdmin registers).

4. custom_views — trash_dashboard is a standalone view, not an
   admin class.

5. ``admin.site.index_template`` — set last, after all
   registrations fire.

6. Backward-compat re-exports — Grep E found two external
   importers: ``prompts.tests.test_admin_actions`` imports
   ``PromptAdmin``, and ``prompts_manager.urls`` imports
   ``trash_dashboard``. Re-exporting them here preserves the
   ``from prompts.admin import X`` import paths without
   requiring consumer-file changes.
"""

# 1. Dependencies (no side effects)
from . import forms        # noqa: F401
from . import inlines      # noqa: F401

# 2. Taxonomy (unregisters default Tag admin before its own classes register)
from . import taxonomy_admin  # noqa: F401

# 3. Domain admin modules (each fires @admin.register on import)
from . import prompt_admin     # noqa: F401
from . import moderation_admin  # noqa: F401
from . import users_admin      # noqa: F401  (also unregisters User)
from . import interactions_admin  # noqa: F401
from . import bulk_gen_admin   # noqa: F401
from . import site_admin       # noqa: F401
from . import credits_admin    # noqa: F401

# 4. Custom views
from . import custom_views  # noqa: F401

# 5. Site-wide admin customization (last, after all registrations)
from django.contrib import admin as _admin
_admin.site.index_template = 'admin/custom_index.html'

# 6. Backward-compat re-exports for existing consumer imports.
#    - PromptAdmin: imported by prompts/tests/test_admin_actions.py:16
#    - trash_dashboard: imported by prompts_manager/urls.py:8
#    Also expose forms-layer names defensively in case management
#    commands or shells reference them.
from .forms import PromptAdminForm, RESERVED_SLUGS  # noqa: F401
from .prompt_admin import PromptAdmin  # noqa: F401
from .custom_views import trash_dashboard  # noqa: F401
