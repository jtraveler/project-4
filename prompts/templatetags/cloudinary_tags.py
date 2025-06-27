from django import template
import re

register = template.Library()

@register.filter
def cloudinary_transform(image_url, transformations):
    """
    Insert Cloudinary transformations in the correct position
    Usage: {{ image.url|cloudinary_transform:"f_auto,q_auto,w_400,h_600,c_limit,dpr_auto" }}
    """
    if not image_url or 'cloudinary.com' not in image_url:
        return image_url
    
    # Pattern to match Cloudinary URLs and insert transformations after /upload/
    pattern = r'(https?://res\.cloudinary\.com/[^/]+/image/upload/)(.+)'
    match = re.match(pattern, image_url)
    
    if match:
        base_url = match.group(1)  # Everything up to and including /upload/
        rest_of_url = match.group(2)  # Everything after /upload/
        
        # Insert transformations after /upload/ and before the rest
        return f"{base_url}{transformations}/{rest_of_url}"
    
    return image_url