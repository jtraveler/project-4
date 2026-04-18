"""
Management command: migrate Cloudinary media to Backblaze B2.

Downloads images and videos referenced by `Prompt.featured_image` /
`Prompt.featured_video` from Cloudinary and re-uploads them to B2,
then populates the `b2_image_url` / `b2_thumb_url` / `b2_large_url` /
`b2_medium_url` / `b2_webp_url` / `b2_video_url` fields on the model.

Idempotent: prompts that already have a populated `b2_image_url` are
skipped. Per-record error handling: one failure does NOT abort the
run — the error is logged and the loop continues.

USAGE
    python manage.py migrate_cloudinary_to_b2 --dry-run
    python manage.py migrate_cloudinary_to_b2 --limit 3
    python manage.py migrate_cloudinary_to_b2
    python manage.py migrate_cloudinary_to_b2 --model userprofile
    python manage.py migrate_cloudinary_to_b2 --model prompt

    # Avatar migration: supported via `--model userprofile` or `--model
    # all` (default). UserProfile.b2_avatar_url was added in migration
    # 0084 — run `python manage.py migrate` before using this command.

DEVELOPER NOTES
    - Cloud name is `dj0uufabo` (NOT `dj0uufabot` — a historical typo
      that caused 404s in earlier attempts).
    - Cloudinary URLs are built explicitly rather than via `.url`
      because the local Cloudinary config may be unavailable or stale.
    - Each record is saved in its own transaction so a failure mid-run
      doesn't roll back successfully migrated prompts.
"""

from __future__ import annotations

import logging
import time
from io import BytesIO

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from prompts.models import Prompt, UserProfile
from prompts.services.b2_upload_service import upload_image, upload_video

logger = logging.getLogger(__name__)

CLOUDINARY_CLOUD = "dj0uufabo"
CLOUDINARY_IMAGE_BASE = (
    f"https://res.cloudinary.com/{CLOUDINARY_CLOUD}/image/upload"
)
CLOUDINARY_VIDEO_BASE = (
    f"https://res.cloudinary.com/{CLOUDINARY_CLOUD}/video/upload"
)
DOWNLOAD_TIMEOUT = 30  # seconds
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50 MB hard cap (videos are chunky)
ALLOWED_DOWNLOAD_HOST = "res.cloudinary.com"


def _fetch(url: str) -> bytes | None:
    """Download from Cloudinary with a size cap, following redirects
    only within the `res.cloudinary.com` domain. Cloudinary's CDN
    commonly serves 302s from edge to origin, so redirects are allowed
    but confined to Cloudinary hosts as SSRF defense-in-depth.
    Returns bytes on 200 or None."""
    try:
        resp = requests.get(
            url,
            timeout=DOWNLOAD_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
    except requests.RequestException as exc:
        logger.warning("Download failed %s: %s", url, exc)
        return None
    try:
        # Confirm final redirect target is still a Cloudinary host.
        final_host = requests.utils.urlparse(resp.url).hostname or ""
        if not final_host.endswith(ALLOWED_DOWNLOAD_HOST):
            return None
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("Content-Type", "")
        if not (
            content_type.startswith("image/")
            or content_type.startswith("video/")
            or content_type.startswith("application/octet-stream")
        ):
            return None
        buf = bytearray()
        for chunk in resp.iter_content(64 * 1024):
            buf.extend(chunk)
            if len(buf) > MAX_DOWNLOAD_BYTES:
                logger.warning(
                    "Download exceeded %d bytes: %s",
                    MAX_DOWNLOAD_BYTES,
                    url,
                )
                return None
        return bytes(buf)
    finally:
        resp.close()


class Command(BaseCommand):
    help = (
        "Migrate Cloudinary images and videos to Backblaze B2. "
        "Idempotent — skips prompts that already have a B2 URL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be migrated. Makes NO changes.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help=(
                "Process at most N records. 0 = no limit. Applies "
                "separately to images and videos."
            ),
        )
        parser.add_argument(
            "--model",
            choices=("prompt", "userprofile", "all"),
            default="all",
            help=(
                "Which target(s) to migrate. `prompt` covers both "
                "images and videos on Prompt. `userprofile` covers "
                "avatar images on UserProfile. `all` covers both."
            ),
        )

    # ------------------------------------------------------------------
    #  Image migration
    # ------------------------------------------------------------------
    def _migrate_prompt_image(self, prompt: Prompt, dry_run: bool) -> str:
        if prompt.b2_image_url:
            return "skipped-already-b2"
        if not prompt.featured_image:
            return "no-cloudinary-image"

        # featured_image.public_id is the Cloudinary identifier.
        # Never str(featured_image) — CloudinaryResource.__str__ returns
        # the object repr, not the public_id, which silently produces
        # bogus download URLs.
        public_id = getattr(prompt.featured_image, "public_id", "") or ""

        if not public_id:
            return "no-public-id"

        # Try .jpg then .png — Cloudinary stores images with their
        # original extension; older entries vary between the two.
        content = None
        resolved_ext = "jpg"
        for ext in ("jpg", "png", "webp"):
            url = f"{CLOUDINARY_IMAGE_BASE}/{public_id}.{ext}"
            data = _fetch(url)
            if data:
                content = data
                resolved_ext = ext
                break

        if content is None:
            return f"download-failed: {public_id}"

        if dry_run:
            return (
                f"would-migrate: prompt id={prompt.pk} "
                f"bytes={len(content)} ext=.{resolved_ext}"
            )

        try:
            image_file = BytesIO(content)
            image_file.name = f"migrated_{prompt.pk}.{resolved_ext}"
            result = upload_image(
                image_file,
                original_filename=image_file.name,
            )
        except Exception as exc:
            return f"upload-exception: {exc}"

        if not result.get("success"):
            return f"upload-failed: {result.get('error')}"

        with transaction.atomic():
            prompt.refresh_from_db()
            urls = result.get("urls", {}) or {}
            prompt.b2_image_url = urls.get("original", "")
            prompt.b2_thumb_url = urls.get("thumb", "")
            prompt.b2_medium_url = urls.get("medium", "")
            prompt.b2_large_url = urls.get("large", "")
            prompt.b2_webp_url = urls.get("webp", "")
            prompt.save(
                update_fields=[
                    "b2_image_url",
                    "b2_thumb_url",
                    "b2_medium_url",
                    "b2_large_url",
                    "b2_webp_url",
                ]
            )
        return f"migrated: id={prompt.pk}"

    # ------------------------------------------------------------------
    #  Video migration
    # ------------------------------------------------------------------
    def _migrate_prompt_video(self, prompt: Prompt, dry_run: bool) -> str:
        if prompt.b2_video_url:
            return "skipped-already-b2"
        if not prompt.featured_video:
            return "no-cloudinary-video"

        # Same CloudinaryResource.public_id rule as images — never str().
        public_id = getattr(prompt.featured_video, "public_id", "") or ""

        if not public_id:
            return "no-public-id"

        # Video URL — Cloudinary delivers the source container
        # when no extension is given.
        content = None
        resolved_ext = "mp4"
        for ext in ("mp4", "mov", "webm"):
            url = f"{CLOUDINARY_VIDEO_BASE}/{public_id}.{ext}"
            data = _fetch(url)
            if data:
                content = data
                resolved_ext = ext
                break

        if content is None:
            return f"download-failed: {public_id}"

        if dry_run:
            return (
                f"would-migrate-video: prompt id={prompt.pk} "
                f"bytes={len(content)} ext=.{resolved_ext}"
            )

        try:
            video_file = BytesIO(content)
            video_file.name = f"migrated_{prompt.pk}.{resolved_ext}"
            result = upload_video(
                video_file,
                original_filename=video_file.name,
            )
        except Exception as exc:
            return f"video-upload-exception: {exc}"

        if not result.get("success"):
            return f"video-upload-failed: {result.get('error')}"

        with transaction.atomic():
            prompt.refresh_from_db()
            urls = result.get("urls", {}) or {}
            prompt.b2_video_url = urls.get("video", "") or urls.get(
                "original", ""
            )
            prompt.b2_video_thumb_url = urls.get("thumb", "")
            prompt.save(
                update_fields=[
                    "b2_video_url",
                    "b2_video_thumb_url",
                ]
            )
        return f"migrated-video: id={prompt.pk}"

    # ------------------------------------------------------------------
    #  Avatar migration (UserProfile)
    # ------------------------------------------------------------------
    def _migrate_avatar(
        self, profile: UserProfile, dry_run: bool
    ) -> str:
        if profile.b2_avatar_url:
            return "skipped-already-b2"
        if not profile.avatar:
            return "no-cloudinary-avatar"

        # Same CloudinaryResource.public_id rule as prompt images.
        public_id = getattr(profile.avatar, "public_id", "") or ""

        if not public_id:
            return "no-public-id"

        content = None
        resolved_ext = "jpg"
        for ext in ("jpg", "png", "webp"):
            url = f"{CLOUDINARY_IMAGE_BASE}/{public_id}.{ext}"
            data = _fetch(url)
            if data:
                content = data
                resolved_ext = ext
                break

        if content is None:
            return f"download-failed: {public_id}"

        if dry_run:
            return (
                f"would-migrate-avatar: profile id={profile.pk} "
                f"bytes={len(content)} ext=.{resolved_ext}"
            )

        try:
            image_file = BytesIO(content)
            image_file.name = f"avatar_{profile.pk}.{resolved_ext}"
            result = upload_image(
                image_file,
                original_filename=image_file.name,
            )
        except Exception as exc:
            return f"upload-exception: {exc}"

        if not result.get("success"):
            return f"upload-failed: {result.get('error')}"

        urls = result.get("urls", {}) or {}
        # Prefer the 'original' URL — templates can use CDN-side resizing
        # or the thumb URL directly if they need a smaller variant. The
        # 'original' variant is always present even in quick_mode.
        b2_url = urls.get("original", "") or urls.get("thumb", "")
        if not b2_url:
            return "upload-no-url"

        with transaction.atomic():
            profile.refresh_from_db()
            profile.b2_avatar_url = b2_url
            profile.save(update_fields=["b2_avatar_url"])
        return f"migrated-avatar: profile_id={profile.pk}"

    # ------------------------------------------------------------------
    #  Orchestration
    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = max(int(options["limit"] or 0), 0)
        model = options.get("model", "all")
        run_prompts = model in ("prompt", "all")
        run_profiles = model in ("userprofile", "all")

        # Upfront B2 config sanity check — fail fast instead of
        # wasting Cloudinary bandwidth + retry delay per record.
        from django.conf import settings as django_settings

        if not dry_run:
            b2_key = getattr(django_settings, "B2_ACCESS_KEY_ID", "")
            b2_secret = getattr(
                django_settings, "B2_SECRET_ACCESS_KEY", ""
            )
            if not (b2_key and b2_secret):
                raise CommandError(
                    "B2 credentials missing from settings — "
                    "set B2_ACCESS_KEY_ID and "
                    "B2_SECRET_ACCESS_KEY before running without --dry-run."
                )

        self.stdout.write(
            self.style.NOTICE(
                f"Cloudinary → B2 migration — dry_run={dry_run} "
                f"limit={limit or 'none'} model={model}"
            )
        )

        image_processed = 0
        image_succeeded = 0
        image_failed = 0
        image_skipped = 0
        video_processed = 0
        video_succeeded = 0
        video_failed = 0
        video_skipped = 0
        avatar_processed = 0
        avatar_succeeded = 0
        avatar_failed = 0
        avatar_skipped = 0

        if run_prompts:
            # Images first — Prompts with a Cloudinary image but no B2 image.
            image_qs = (
                Prompt.all_objects.exclude(featured_image="")
                .filter(b2_image_url__in=("", None))
                .order_by("id")
            )
            if limit:
                image_qs = image_qs[:limit]

            for i, prompt in enumerate(image_qs.iterator(chunk_size=50), 1):
                status = self._migrate_prompt_image(prompt, dry_run)
                image_processed += 1
                if status.startswith("migrated") or status.startswith(
                    "would-migrate"
                ):
                    image_succeeded += 1
                elif status.startswith("skipped") or status.startswith(
                    "no-"
                ):
                    image_skipped += 1
                else:
                    image_failed += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [{prompt.pk}] {status}"
                        )
                    )
                    continue
                if i % 10 == 0 or status.startswith("migrated"):
                    self.stdout.write(f"  [{prompt.pk}] {status}")
                # Gentle throttle so Cloudinary doesn't rate-limit.
                if not dry_run:
                    time.sleep(0.2)

            # Videos — Prompts with a Cloudinary video but no B2 video.
            video_qs = (
                Prompt.all_objects.exclude(featured_video="")
                .filter(b2_video_url__in=("", None))
                .order_by("id")
            )
            if limit:
                video_qs = video_qs[:limit]

            for prompt in video_qs.iterator(chunk_size=25):
                status = self._migrate_prompt_video(prompt, dry_run)
                video_processed += 1
                if status.startswith("migrated") or status.startswith(
                    "would-migrate"
                ):
                    video_succeeded += 1
                elif status.startswith("skipped") or status.startswith(
                    "no-"
                ):
                    video_skipped += 1
                else:
                    video_failed += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [video {prompt.pk}] {status}"
                        )
                    )
                    continue
                self.stdout.write(f"  [video {prompt.pk}] {status}")
                if not dry_run:
                    time.sleep(0.5)

        if run_profiles:
            # Avatars — UserProfile with a Cloudinary avatar but no B2 avatar.
            avatar_qs = (
                UserProfile.objects.exclude(avatar="")
                .exclude(avatar=None)
                .filter(b2_avatar_url__in=("", None))
                .order_by("id")
            )
            if limit:
                avatar_qs = avatar_qs[:limit]

            for i, profile in enumerate(avatar_qs.iterator(chunk_size=50), 1):
                status = self._migrate_avatar(profile, dry_run)
                avatar_processed += 1
                if status.startswith("migrated") or status.startswith(
                    "would-migrate"
                ):
                    avatar_succeeded += 1
                elif status.startswith("skipped") or status.startswith(
                    "no-"
                ):
                    avatar_skipped += 1
                else:
                    avatar_failed += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [avatar {profile.pk}] {status}"
                        )
                    )
                    continue
                if i % 10 == 0 or status.startswith("migrated"):
                    self.stdout.write(
                        f"  [avatar {profile.pk}] {status}"
                    )
                if not dry_run:
                    time.sleep(0.2)

        # ── Summary ──────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Summary"))
        self.stdout.write(
            f"  Images  : processed={image_processed} "
            f"succeeded={image_succeeded} "
            f"skipped={image_skipped} "
            f"failed={image_failed}"
        )
        self.stdout.write(
            f"  Videos  : processed={video_processed} "
            f"succeeded={video_succeeded} "
            f"skipped={video_skipped} "
            f"failed={video_failed}"
        )
        self.stdout.write(
            f"  Avatars : processed={avatar_processed} "
            f"succeeded={avatar_succeeded} "
            f"skipped={avatar_skipped} "
            f"failed={avatar_failed}"
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry-run — no changes made. Re-run without "
                    "--dry-run to apply."
                )
            )
