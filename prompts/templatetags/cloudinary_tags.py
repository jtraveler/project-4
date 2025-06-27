from django import template
import re

register = template.Library()

@register.filter
def cloudinary_transform(image_url, transformations):
    """
    Insert Cloudinary transformations in the correct position and force HTTPS
    Usage: {{ image.url|cloudinary_transform:"q_auto,w_400,h_600,c_limit" }}
    """
    if not image_url or 'cloudinary.com' not in image_url:
        return image_url
    
    # Force HTTPS for security
    image_url = image_url.replace('http://', 'https://')
    
    # Pattern to match Cloudinary URLs and insert transformations after /upload/
    pattern = r'(https://res\.cloudinary\.com/[^/]+/image/upload/)(.+)'
    match = re.match(pattern, image_url)
    
    if match:
        base_url = match.group(1)  # Everything up to and including /upload/
        rest_of_url = match.group(2)  # Everything after /upload/
        
        # Insert transformations after /upload/ and before the rest
        return f"{base_url}{transformations}/{rest_of_url}"
    
    return image_url