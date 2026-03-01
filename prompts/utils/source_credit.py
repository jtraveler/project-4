"""
Source credit parsing utilities for PromptFinder.

Parses user input to detect URLs vs plain text credits.
Extracts display-friendly domain names from known sites.
"""
from urllib.parse import urlparse

KNOWN_SITES = {
    'prompthero.com': 'PromptHero',
    'www.prompthero.com': 'PromptHero',
    'civitai.com': 'Civitai',
    'www.civitai.com': 'Civitai',
    'lexica.art': 'Lexica',
    'www.lexica.art': 'Lexica',
    'openart.ai': 'OpenArt',
    'www.openart.ai': 'OpenArt',
    'midjourney.com': 'Midjourney',
    'www.midjourney.com': 'Midjourney',
    'playground.ai': 'Playground',
    'www.playground.ai': 'Playground',
    'promptbase.com': 'PromptBase',
    'www.promptbase.com': 'PromptBase',
}


def parse_source_credit(raw_input):
    """
    Parse raw source credit input into (display_name, url_or_empty).

    If input looks like a URL: extract domain, look up KNOWN_SITES
    for a friendly name, otherwise use the domain as display_name.
    If input is plain text: return (text, '').

    Args:
        raw_input: User-provided string (URL or plain text).

    Returns:
        tuple: (display_name: str, url: str)
            display_name: Human-readable source name
            url: Full URL if input was a URL, empty string otherwise
    """
    if not raw_input or not raw_input.strip():
        return ('', '')

    text = raw_input.strip()

    # Check if it looks like a URL
    if text.startswith(('http://', 'https://')):
        parsed = urlparse(text)
        hostname = parsed.hostname or ''
        display_name = KNOWN_SITES.get(hostname, hostname)
        return (display_name, text)

    # Check if it's a bare domain-like input (e.g., "prompthero.com/prompt/abc")
    if '.' in text and ' ' not in text and '/' in text:
        url = 'https://' + text
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        display_name = KNOWN_SITES.get(hostname, hostname)
        return (display_name, url)

    # Plain text
    return (text, '')
