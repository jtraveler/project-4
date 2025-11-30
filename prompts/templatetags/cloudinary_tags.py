from django import template
import re

register = template.Library()

@register.filter
def cloudinary_transform(image_url, transformations):
    """
    Insert Cloudinary transformations in the correct position and force HTTPS
    Usage: {{ image.url|cloudinary_transform:"q_auto,w_300,h_500,c_limit" }}
           {{ image|cloudinary_transform:"q_auto,w_300,h_500,c_limit" }}  # Also works with CloudinaryResource directly

    Handles four types of inputs:
    1. CloudinaryResource objects: Extract public_id and build URL
    2. Full Cloudinary URLs: https://res.cloudinary.com/.../upload/...
    3. Malformed URLs without domain: Just the public_id
    4. Partial URLs: Missing /upload/ section
    """
    if not image_url:
        return image_url

    # Handle CloudinaryResource objects (from CloudinaryField)
    # Convert to string to get the public_id
    if hasattr(image_url, 'public_id'):
        # It's a CloudinaryResource - extract public_id
        image_url = str(image_url)  # str(CloudinaryResource) returns public_id

    # Import settings to get cloud name
    from django.conf import settings
    cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')

    # Case 1: URL doesn't contain cloudinary.com at all - it's just a public_id
    if 'cloudinary.com' not in image_url:
        # Build full URL from scratch using public_id
        if cloud_name:
            # Assume it's an image unless it has video file extension
            resource_type = 'video' if any(ext in image_url.lower() for ext in ['.mp4', '.mov', '.avi']) else 'image'
            return f"https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{transformations}/{image_url}"
        else:
            # Can't fix without cloud name
            return image_url

    # Force HTTPS for security
    image_url = image_url.replace('http://', 'https://')

    # Case 2: Full URL with /upload/ - standard transformation
    pattern = r'(https://res\.cloudinary\.com/[^/]+/image/upload/)(.+)'
    match = re.match(pattern, image_url)

    if match:
        base_url = match.group(1)  # Everything up to and including /upload/
        rest_of_url = match.group(2)  # Everything after /upload/

        # Insert transformations after /upload/ and before the rest
        return f"{base_url}{transformations}/{rest_of_url}"

    # Case 3: Partial URL - has cloudinary.com but missing /upload/
    # Pattern: https://res.cloudinary.com/[cloud_name]/image/[public_id]
    partial_pattern = r'(https://res\.cloudinary\.com/[^/]+/image/)(.+)'
    partial_match = re.match(partial_pattern, image_url)

    if partial_match:
        base_url = partial_match.group(1)  # Everything up to /image/
        public_id = partial_match.group(2)  # The public_id

        # Rebuild with /upload/ and transformations
        return f"{base_url}upload/{transformations}/{public_id}"

    # Couldn't transform - return original
    return image_url