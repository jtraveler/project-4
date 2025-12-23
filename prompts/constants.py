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
        'seo_subheader': 'AI Art Examples & Creative Ideas',
        'seo_description': 'Explore our collection of {count} Midjourney prompts shared by our community featuring stunning AI-generated artwork. From photorealistic portraits to fantastical landscapes, discover prompts that unlock Midjourney\'s full creative potential. Each prompt includes the exact text used, making it easy to recreate or adapt for your own projects.',
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
        'choice_value': 'Midjourney',  # Must match database values (case-insensitive)
        'supports_images': True,
        'supports_video': True,  # V1 Video launched June 2025
    },
    'dalle3': {
        'name': 'DALL-E 3',
        'slug': 'dalle3',
        'seo_subheader': 'AI Image Examples & Prompt Ideas',
        'seo_description': 'Browse {count} DALL-E 3 prompts showcasing OpenAI\'s most advanced image generation capabilities. Find inspiration for product renders, concept art, and creative compositions with proven prompts that deliver stunning results. Perfect for ChatGPT Plus users looking to master DALL-E 3\'s powerful features.',
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
        'choice_value': 'DALL-E 3',  # Must match database values (case-insensitive)
        'supports_images': True,
        'supports_video': False,
    },
    'dalle2': {
        'name': 'DALL-E 2',
        'slug': 'dalle2',
        'seo_subheader': 'AI Image Generation Examples',
        'seo_description': 'Discover {count} DALL-E 2 prompts that showcase this groundbreaking AI model\'s unique artistic style. Learn from community-shared prompts featuring inpainting, outpainting, and creative variations. Great for users who appreciate DALL-E 2\'s distinctive interpretation of creative concepts.',
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
        'choice_value': 'DALL-E 2',  # Must match database display values
        'supports_images': True,
        'supports_video': False,
    },
    'stable-diffusion': {
        'name': 'Stable Diffusion',
        'slug': 'stable-diffusion',
        'seo_subheader': 'Open Source AI Art Examples',
        'seo_description': 'Explore {count} Stable Diffusion prompts from the open-source AI art community. Find prompts optimized for SDXL, custom models, and ControlNet techniques. Perfect for developers and creators who want full control over their AI image generation workflow.',
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
        'choice_value': 'Stable Diffusion',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'leonardo-ai': {
        'name': 'Leonardo AI',
        'slug': 'leonardo-ai',
        'seo_subheader': 'AI Art & Game Asset Examples',
        'seo_description': 'Browse {count} Leonardo AI prompts perfect for game development, character design, and concept art. Discover prompts optimized for Leonardo\'s specialized models and Canvas editing features. Ideal for creators who need consistent, high-quality visual assets.',
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
        'choice_value': 'Leonardo AI',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'flux': {
        'name': 'Flux',
        'slug': 'flux',
        'seo_subheader': 'High-Quality AI Image Examples',
        'seo_description': 'Explore {count} Flux prompts showcasing next-generation AI image quality from Black Forest Labs. Find prompts that leverage Flux\'s superior anatomy rendering, realistic lighting, and text generation capabilities. Compare Flux Pro, Dev, and Schnell variants with real examples.',
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
        'choice_value': 'Flux',  # Must match database display values
        'supports_images': True,
        'supports_video': False,
    },
    'sora': {
        'name': 'Sora',
        'slug': 'sora',
        'seo_subheader': 'AI Video & Image Generation Examples',
        'seo_description': 'Discover {count} Sora prompts demonstrating OpenAI\'s revolutionary text-to-video AI capabilities. Browse cinematic video prompts featuring complex camera motion, realistic physics, and detailed character animations. Learn how to craft prompts that maximize Sora\'s video generation potential.',
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
        'choice_value': 'Sora',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'sora2': {
        'name': 'Sora 2',
        'slug': 'sora2',
        'seo_subheader': 'Next-Gen AI Video Examples',
        'seo_description': 'Explore {count} Sora 2 prompts showcasing the latest advancements in AI video generation. Find prompts optimized for improved physics simulation, longer video sequences, and enhanced temporal consistency. Perfect for filmmakers and content creators seeking cutting-edge video AI capabilities.',
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
        'choice_value': 'Sora 2',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'veo3': {
        'name': 'Veo 3',
        'slug': 'veo3',
        'seo_subheader': 'Google AI Video Generation Examples',
        'seo_description': 'Discover {count} Veo 3 prompts powered by Google DeepMind\'s advanced video AI technology. Browse prompts demonstrating smooth motion, consistent characters, and diverse video styles. Learn prompt techniques for Google\'s answer to AI video generation.',
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
        'choice_value': 'Veo 3',  # Must match database display values
        'supports_images': False,
        'supports_video': True,
    },
    'adobe-firefly': {
        'name': 'Adobe Firefly',
        'slug': 'adobe-firefly',
        'seo_subheader': 'Creative AI Image Examples',
        'seo_description': 'Browse {count} Adobe Firefly prompts designed for creative professionals using Adobe Creative Cloud. Find commercially-safe prompts for Generative Fill, Text Effects, and vector artwork. Perfect for designers who need AI-powered enhancement within their existing Adobe workflow.',
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
        'choice_value': 'Adobe Firefly',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'bing-image-creator': {
        'name': 'Bing Image Creator',
        'slug': 'bing-image-creator',
        'seo_subheader': 'Free AI Image Examples',
        'seo_description': 'Discover {count} free Bing Image Creator prompts powered by DALL-E technology. Find easy-to-use prompts perfect for beginners and casual creators. No subscription required—just a Microsoft account to start creating AI images today.',
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
        'choice_value': 'Bing Image Creator',  # Must match database display values
        'supports_images': True,
        'supports_video': False,
    },
    'grok': {
        'name': 'Grok',
        'slug': 'grok',
        'seo_subheader': 'xAI Image & Video Examples',
        'seo_description': 'Explore {count} Grok prompts from xAI\'s creative AI assistant integrated with X (Twitter). Discover prompts that push creative boundaries while maintaining safety guidelines. Perfect for social media content creation and unique creative explorations.',
        'description': '''
            <p>Grok is xAI's AI assistant that includes powerful image generation capabilities. Developed by Elon Musk's
            artificial intelligence company, Grok combines conversational AI with the ability to create images from
            text descriptions, offering a unique blend of chat and creative generation in one platform.</p>

            <p>Grok's image generation is known for its willingness to tackle creative prompts that other AI systems
            might decline, while still maintaining safety guidelines. Integrated into the X (formerly Twitter) platform,
            Grok offers Premium+ subscribers access to both its conversational AI and image creation features, making it
            a versatile tool for social media content creation and creative exploration.</p>
        ''',
        'website': 'https://x.ai',
        'icon': 'images/generators/grok-icon.png',  # Placeholder
        'choice_value': 'Grok',  # Must match database display values
        'supports_images': True,
        'supports_video': True,  # Grok supports video generation
    },
    'wan21': {
        'name': 'WAN 2.1',
        'slug': 'wan21',
        'seo_subheader': 'Open Source AI Video Examples',
        'seo_description': 'Browse {count} WAN 2.1 prompts from Alibaba\'s powerful open-source video generation model. Find prompts for creating coherent video sequences with consistent characters and smooth motion. Supports multiple aspect ratios from social media clips to professional productions.',
        'description': '''
            <p>WAN 2.1 is an advanced AI video generation model from Alibaba's Tongyi Wanxiang team. This powerful
            text-to-video model can generate high-quality video content from text prompts, supporting various styles
            from realistic footage to animated content.</p>

            <p>WAN 2.1 excels at understanding complex scene descriptions and generating coherent video sequences with
            consistent characters and smooth motion. The model supports multiple aspect ratios and resolutions, making
            it suitable for various content creation needs from social media clips to professional video production.</p>
        ''',
        'website': 'https://tongyi.aliyun.com/wanxiang',
        'icon': 'images/generators/wan21-icon.png',  # Placeholder
        'choice_value': 'WAN 2.1',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'wan22': {
        'name': 'WAN 2.2',
        'slug': 'wan22',
        'seo_subheader': 'Advanced AI Video & Image Examples',
        'seo_description': 'Explore {count} WAN 2.2 prompts showcasing Alibaba\'s latest video generation improvements. Find prompts optimized for enhanced temporal consistency, realistic physics, and dynamic camera work. Perfect for creators seeking advanced AI video capabilities with character consistency.',
        'description': '''
            <p>WAN 2.2 is the latest iteration of Alibaba's Tongyi Wanxiang video generation model, offering enhanced
            video quality, longer generation capabilities, and improved understanding of complex prompts compared to
            its predecessor WAN 2.1.</p>

            <p>This updated model features better temporal consistency, more realistic physics simulation, and enhanced
            control over video style and composition. WAN 2.2 is particularly strong in generating videos with dynamic
            camera movements, complex scene transitions, and maintaining character consistency throughout longer sequences.</p>
        ''',
        'website': 'https://tongyi.aliyun.com/wanxiang',
        'icon': 'images/generators/wan22-icon.png',  # Placeholder
        'choice_value': 'WAN 2.2',  # Must match database display values
        'supports_images': True,
        'supports_video': True,
    },
    'nano-banana': {
        'name': 'Nano Banana',
        'slug': 'nano-banana',
        'seo_subheader': 'Google Gemini AI Image Examples',
        'seo_description': 'Discover {count} Nano Banana prompts for stylized AI image generation powered by Google\'s Gemini. Find prompts that showcase this platform\'s unique artistic approach and distinctive visual style. Perfect for creators seeking visually distinctive AI-generated imagery.',
        'description': '''
            <p>Nano Banana is an emerging AI video generation model that focuses on creating high-quality, stylized
            video content from text prompts. Known for its unique artistic approach, Nano Banana excels at generating
            creative and visually distinctive video sequences.</p>

            <p>The model is particularly popular among content creators looking for video generation with a distinctive
            aesthetic. Nano Banana supports various video styles and offers intuitive controls for adjusting the
            visual style, motion dynamics, and overall composition of generated videos.</p>
        ''',
        'website': 'https://nanobanana.ai',
        'icon': 'images/generators/nano-banana-icon.png',  # Placeholder
        'choice_value': 'Nano Banana',  # Must match database display values
        'supports_images': True,  # Nano Banana is image-only
        'supports_video': False,
    },
    'nano-banana-pro': {
        'name': 'Nano Banana Pro',
        'slug': 'nano-banana-pro',
        'seo_subheader': 'Professional AI Image Examples',
        'seo_description': 'Explore {count} Nano Banana Pro prompts for premium AI image generation with higher resolution outputs. Discover prompts optimized for professional-quality imagery with enhanced style controls. Perfect for studios and professional creators demanding the highest quality AI-generated images.',
        'description': '''
            <p>Nano Banana Pro is the premium version of the Nano Banana AI video generation platform, offering enhanced
            capabilities, higher resolution outputs, and advanced features for professional content creation.</p>

            <p>The Pro version includes extended video duration support, improved motion quality, and additional style
            controls that allow for more precise creative direction. Nano Banana Pro is designed for professional
            creators and studios who need higher-quality outputs and more control over their AI-generated video content.</p>
        ''',
        'website': 'https://nanobanana.ai',
        'icon': 'images/generators/nano-banana-pro-icon.png',  # Placeholder
        'choice_value': 'Nano Banana Pro',  # Must match database display values
        'supports_images': True,  # Nano Banana Pro is image-only
        'supports_video': False,
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
