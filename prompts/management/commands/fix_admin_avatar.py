"""
Management command to investigate and fix admin user's corrupted avatar
Phase F Day 1 - Cloudinary 404 Fix

Usage:
    python manage.py fix_admin_avatar --investigate  # Just show what's wrong
    python manage.py fix_admin_avatar --fix          # Clear the corrupted avatar
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from prompts.models import UserProfile


class Command(BaseCommand):
    help = 'Investigate and fix admin user\'s corrupted Cloudinary avatar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--investigate',
            action='store_true',
            help='Just investigate and report, don\'t fix anything',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Clear the corrupted avatar for admin user',
        )

    def handle(self, *args, **options):
        investigate_only = options['investigate']
        apply_fix = options['fix']

        if not investigate_only and not apply_fix:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify --investigate or --fix'
                )
            )
            return

        # Investigation
        self.stdout.write(
            self.style.SUCCESS('=== ADMIN USER PROFILE INVESTIGATION ===')
        )

        try:
            admin_user = User.objects.get(username='admin')
            admin_profile = UserProfile.objects.get(user=admin_user)

            self.stdout.write(f"Username: {admin_user.username}")
            self.stdout.write(f"Has avatar: {bool(admin_profile.avatar)}")

            if admin_profile.avatar:
                self.stdout.write("\nAvatar Field Details:")
                self.stdout.write(f"  Raw value: {admin_profile.avatar}")
                self.stdout.write(f"  Type: {type(admin_profile.avatar)}")

                # Try to get string representation
                avatar_str = str(admin_profile.avatar)
                self.stdout.write(f"  String value: {avatar_str}")

                # Check if it contains the problematic ID
                if '8ee87aee-3c11' in avatar_str:
                    self.stdout.write(
                        self.style.ERROR(
                            "  *** FOUND PROBLEMATIC IMAGE ID ***"
                        )
                    )

                # Check if it's missing domain
                if avatar_str and not avatar_str.startswith('http'):
                    self.stdout.write(
                        self.style.ERROR(
                            "  *** AVATAR URL IS MISSING DOMAIN ***"
                        )
                    )

                # Try to get URL
                try:
                    url = admin_profile.avatar.url
                    self.stdout.write(f"  URL from .url property: {url}")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  Error getting .url: {e}")
                    )

                # Check CloudinaryResource properties
                if hasattr(admin_profile.avatar, 'public_id'):
                    self.stdout.write(
                        f"  Public ID: {admin_profile.avatar.public_id}"
                    )
                if hasattr(admin_profile.avatar, 'version'):
                    self.stdout.write(
                        f"  Version: {admin_profile.avatar.version}"
                    )
                if hasattr(admin_profile.avatar, 'resource_type'):
                    self.stdout.write(
                        f"  Resource Type: {admin_profile.avatar.resource_type}"
                    )

            # Compare with working user (jimbob)
            self.stdout.write(
                self.style.SUCCESS(
                    '\n=== COMPARISON WITH JIMBOB (WORKING) ==='
                )
            )
            try:
                jimbob_user = User.objects.get(username='jimbob')
                jimbob_profile = UserProfile.objects.get(user=jimbob_user)

                self.stdout.write(
                    f"Jimbob has avatar: {bool(jimbob_profile.avatar)}"
                )
                if jimbob_profile.avatar:
                    self.stdout.write(
                        f"  Jimbob avatar raw: {jimbob_profile.avatar}"
                    )
                    self.stdout.write(
                        f"  Jimbob avatar type: {type(jimbob_profile.avatar)}"
                    )
                    self.stdout.write(
                        f"  Jimbob avatar string: {str(jimbob_profile.avatar)}"
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING("Jimbob user not found")
                )

            # Apply fix if requested
            if apply_fix and admin_profile.avatar:
                self.stdout.write(
                    self.style.WARNING('\n=== APPLYING FIX ===')
                )
                self.stdout.write(
                    f"Clearing corrupted avatar for admin user..."
                )

                # Clear the corrupted avatar
                admin_profile.avatar = None
                admin_profile.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        '✓ Admin avatar cleared successfully!'
                    )
                )
                self.stdout.write(
                    'Admin can now re-upload a new avatar through the UI.'
                )
                self.stdout.write(
                    'Test at: /users/admin/ - 404 error should be gone.'
                )

            elif apply_fix and not admin_profile.avatar:
                self.stdout.write(
                    self.style.WARNING(
                        'Admin user has no avatar - nothing to fix!'
                    )
                )

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found in database!')
            )
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user has no profile!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
            import traceback
            traceback.print_exc()
