"""
Constants and configuration data for the prompts app.

This module contains read-only configuration data that is reused across
multiple parts of the application (views, forms, admin, etc.).
"""

# SEO Phase 3: AI Generator Metadata
# Used by: ai_generator_category view, upload forms, admin displays

AI_GENERATORS = {
    'midjourney': {
        'name': 'Midjourney',
        'slug': 'midjourney',
        'description': '''
            <p>Midjourney is a leading AI image generation tool known for producing stunning, artistic images from text prompts.
            Created by the independent research lab Midjourney, Inc., this powerful AI specializes in creating highly detailed,
            dreamlike imagery that often has a painterly or illustrative quality.</p>

            <p>Midjourney operates through Discord and uses a freemium model. It's particularly popular among digital artists,
            designers, and creative professionals for concept art, mood boards, and creative exploration. The AI excels at
            understanding artistic styles, lighting, composition, and can generate images in various art movements from
            photorealism to abstract expressionism.</p>
        ''',
        'website': 'https://www.midjourney.com',
        'icon': 'images/generators/midjourney-icon.png',  # Placeholder
        'choice_value': 'midjourney',
    },
    'dalle3': {
        'name': 'DALL-E 3',
        'slug': 'dalle3',
        'description': '''
            <p>DALL-E 3 is OpenAI's latest and most advanced image generation model, representing a significant leap forward
            in AI art creation. Built on the foundation of its predecessors, DALL-E 3 offers dramatically improved prompt
            understanding, image quality, and the ability to generate text within images—a feature previous versions struggled with.</p>

            <p>Integrated directly into ChatGPT Plus and available through Microsoft Bing Image Creator, DALL-E 3 excels at
            interpreting complex, detailed prompts and producing images that closely match user intentions. It's particularly
            strong at photorealistic renders, product visualization, and creative compositions that combine multiple concepts seamlessly.</p>
        ''',
        'website': 'https://openai.com/dall-e-3',
        'icon': 'images/generators/dalle3-icon.png',  # Placeholder
        'choice_value': 'dalle3',
    },
    'dalle2': {
        'name': 'DALL-E 2',
        'slug': 'dalle2',
        'description': '''
            <p>DALL-E 2, released by OpenAI in 2022, revolutionized AI image generation with its ability to create realistic
            images and art from natural language descriptions. As the predecessor to DALL-E 3, this model introduced many
            groundbreaking capabilities that set new standards for the industry.</p>

            <p>DALL-E 2 pioneered features like inpainting (editing specific parts of images), outpainting (extending images
            beyond their original borders), and variations (creating different versions of a generated or uploaded image).
            While superseded by DALL-E 3, it remains a capable tool for creative exploration and is valued for its unique
            artistic interpretation style.</p>
        ''',
        'website': 'https://openai.com/dall-e-2',
        'icon': 'images/generators/dalle2-icon.png',  # Placeholder
        'choice_value': 'dalle2',
    },
    'stable-diffusion': {
        'name': 'Stable Diffusion',
        'slug': 'stable-diffusion',
        'description': '''
            <p>Stable Diffusion is an open-source AI image generation model developed by Stability AI in collaboration with
            researchers from CompVis, LAION, and Runway. Being open-source sets it apart from competitors, allowing developers
            to run it locally on their own hardware and customize it extensively.</p>

            <p>The model has spawned a vibrant ecosystem of tools, interfaces, and fine-tuned versions optimized for specific
            styles (anime, architecture, portraits, etc.). Stable Diffusion is particularly popular among technical users and
            developers who value control, customization, and the ability to train custom models. It excels at detailed,
            high-resolution imagery and supports advanced techniques like ControlNet for precise composition control.</p>
        ''',
        'website': 'https://stability.ai/stable-diffusion',
        'icon': 'images/generators/stable-diffusion-icon.png',  # Placeholder
        'choice_value': 'stable_diffusion',
    },
    'leonardo-ai': {
        'name': 'Leonardo AI',
        'slug': 'leonardo-ai',
        'description': '''
            <p>Leonardo AI is a powerful image generation platform that combines ease of use with professional-grade features.
            Built for creators, designers, and artists, Leonardo AI offers a streamlined interface while providing advanced
            controls for fine-tuning image generation.</p>

            <p>The platform stands out for its curated selection of AI models optimized for different use cases (game assets,
            product design, character creation, etc.) and its Canvas feature that allows for precise editing and refinement.
            Leonardo AI also offers consistent character generation, making it particularly valuable for game developers and
            storytellers who need to maintain visual consistency across multiple images.</p>
        ''',
        'website': 'https://leonardo.ai',
        'icon': 'images/generators/leonardo-icon.png',  # Placeholder
        'choice_value': 'leonardo',
    },
    'flux': {
        'name': 'Flux',
        'slug': 'flux',
        'description': '''
            <p>Flux is Black Forest Labs' cutting-edge image generation model, created by the team behind Stable Diffusion.
            Flux represents the next generation of AI image synthesis, offering state-of-the-art quality with exceptional
            prompt adherence and photorealistic rendering capabilities.</p>

            <p>Available in multiple variants (Flux Pro, Dev, and Schnell), this model excels at understanding complex prompts
            and generating highly detailed, coherent images. Flux is particularly noted for its superior handling of human
            anatomy, realistic lighting, and the ability to generate legible text within images—addressing common weaknesses
            in earlier AI models.</p>
        ''',
        'website': 'https://blackforestlabs.ai',
        'icon': 'images/generators/flux-icon.png',  # Placeholder
        'choice_value': 'flux',
    },
    'sora': {
        'name': 'Sora',
        'slug': 'sora',
        'description': '''
            <p>Sora is OpenAI's groundbreaking text-to-video AI model, capable of generating realistic and imaginative video
            scenes from text descriptions. Announced in February 2024, Sora represents a major advancement in AI video
            generation, capable of creating videos up to 60 seconds long with highly detailed scenes, complex camera motion,
            and multiple characters with vibrant emotions.</p>

            <p>The model demonstrates deep understanding of language and how objects interact in the physical world, generating
            videos that maintain visual quality and subject consistency throughout. While still in limited release, Sora has
            shown remarkable capabilities in generating cinematic shots, animated scenes, and realistic simulations that could
            revolutionize content creation across industries.</p>
        ''',
        'website': 'https://openai.com/sora',
        'icon': 'images/generators/sora-icon.png',  # Placeholder
        'choice_value': 'sora',
    },
    'sora2': {
        'name': 'Sora 2',
        'slug': 'sora2',
        'description': '''
            <p>Sora 2 is the next iteration of OpenAI's revolutionary video generation model, building upon the groundbreaking
            capabilities of the original Sora. This enhanced version offers improved video quality, longer generation times,
            better physics simulation, and more refined control over video output.</p>

            <p>With Sora 2, creators can generate even more realistic and complex video sequences, featuring advanced camera
            movements, sophisticated lighting transitions, and improved temporal consistency. The model demonstrates enhanced
            understanding of narrative flow and can better interpret creative direction from text prompts, making it an
            invaluable tool for filmmakers, animators, and content creators pushing the boundaries of AI-generated video.</p>
        ''',
        'website': 'https://openai.com/sora',  # Will be updated when official Sora 2 page launches
        'icon': 'images/generators/sora2-icon.png',  # Placeholder
        'choice_value': 'sora2',
    },
    'veo3': {
        'name': 'Veo 3',
        'slug': 'veo3',
        'description': '''
            <p>Veo 3 is Google DeepMind's latest advancement in AI video generation technology, competing directly with
            models like OpenAI's Sora. Veo 3 represents Google's push into high-quality, prompt-driven video synthesis,
            offering creators unprecedented control over AI-generated video content.</p>

            <p>The model excels at understanding complex scene descriptions, maintaining consistent character appearances
            across frames, and generating smooth, realistic motion. Veo 3 is particularly strong in handling diverse video
            styles—from photorealistic footage to stylized animation—and offers advanced features for editing and refining
            generated videos through natural language instructions.</p>
        ''',
        'website': 'https://deepmind.google/technologies/veo',
        'icon': 'images/generators/veo3-icon.png',  # Placeholder
        'choice_value': 'veo3',
    },
    'adobe-firefly': {
        'name': 'Adobe Firefly',
        'slug': 'adobe-firefly',
        'description': '''
            <p>Adobe Firefly is Adobe's family of generative AI models integrated directly into Adobe Creative Cloud applications
            like Photoshop, Illustrator, and Express. Designed specifically for creative professionals, Firefly emphasizes
            commercial safety and is trained on Adobe Stock images, openly licensed content, and public domain content where
            copyright has expired.</p>

            <p>Firefly stands out for its seamless integration with professional creative workflows, offering features like
            Generative Fill (add or replace objects in images), Text Effects (create stunning typography), and Generative
            Recolor (recolor vector artwork). For designers and creative professionals already using Adobe's ecosystem,
            Firefly provides AI-powered enhancement without leaving familiar tools.</p>
        ''',
        'website': 'https://www.adobe.com/products/firefly.html',
        'icon': 'images/generators/firefly-icon.png',  # Placeholder
        'choice_value': 'firefly',
    },
    'bing-image-creator': {
        'name': 'Bing Image Creator',
        'slug': 'bing-image-creator',
        'description': '''
            <p>Bing Image Creator is Microsoft's free AI image generation tool, powered by OpenAI's DALL-E technology.
            Integrated into Microsoft's Bing search engine and Edge browser, it offers accessible AI image generation to
            anyone with a Microsoft account, making advanced AI art creation available to the mainstream public.</p>

            <p>The tool provides a user-friendly interface for creating images from text prompts, with daily credits for
            faster generation and the option for slower, queue-based generation when credits run out. Bing Image Creator is
            particularly valuable for users seeking quick concept visualization, social media content, or creative exploration
            without the learning curve or cost of more specialized AI art tools.</p>
        ''',
        'website': 'https://www.bing.com/images/create',
        'icon': 'images/generators/bing-icon.png',  # Placeholder
        'choice_value': 'bing',
    },
}

# Filter validation lists for ai_generator_category view
VALID_PROMPT_TYPES = ['image', 'video']
VALID_DATE_FILTERS = ['today', 'week', 'month', 'year']
VALID_SORT_OPTIONS = ['recent', 'popular', 'trending']


# =============================================================================
# BOT DETECTION PATTERNS (Phase G Part B - View Tracking)
# =============================================================================

BOT_USER_AGENT_PATTERNS = [
    # Search engine bots
    'googlebot', 'bingbot', 'slurp', 'duckduckbot',
    'baiduspider', 'yandexbot', 'sogou', 'exabot',

    # Social media bots
    'facebot', 'facebookexternalhit', 'twitterbot', 'linkedinbot',

    # SEO/Analytics bots
    'semrushbot', 'ahrefsbot', 'mj12bot', 'dotbot', 'petalbot',

    # Archive bots
    'ia_archiver', 'bytespider', 'applebot',

    # Generic patterns
    'bot', 'crawler', 'spider', 'scraper',

    # HTTP clients (often used for scraping)
    'curl', 'wget', 'python-requests', 'axios', 'node-fetch',
]

# Default rate limit for view tracking (views per minute per IP)
DEFAULT_VIEW_RATE_LIMIT = 10
