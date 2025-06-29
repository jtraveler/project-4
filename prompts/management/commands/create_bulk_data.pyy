from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from prompts.models import Prompt
import random


class Command(BaseCommand):
    help = 'Create sample users and prompts for development'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting bulk creation...'))
        
        # Create sample users first
        users_created = self.create_sample_users()
        self.stdout.write(self.style.SUCCESS(f'Created {users_created} users'))
        
        # Create sample prompts
        prompts_created = self.create_sample_prompts()
        self.stdout.write(self.style.SUCCESS(f'Created {prompts_created} prompts'))
        
        self.stdout.write(self.style.SUCCESS('Bulk creation completed successfully!'))

    def create_sample_users(self):
        """Create 20 sample users with password '123test'"""
        users_data = [
            {'username': 'creator1', 'first_name': 'Alex', 'last_name': 'Chen', 'email': 'alex.chen@example.com'},
            {'username': 'artist2', 'first_name': 'Maya', 'last_name': 'Rodriguez', 'email': 'maya.rodriguez@example.com'},
            {'username': 'promptmaster3', 'first_name': 'Jordan', 'last_name': 'Smith', 'email': 'jordan.smith@example.com'},
            {'username': 'designer4', 'first_name': 'Zara', 'last_name': 'Johnson', 'email': 'zara.johnson@example.com'},
            {'username': 'creative5', 'first_name': 'Kai', 'last_name': 'Williams', 'email': 'kai.williams@example.com'},
            {'username': 'visualist6', 'first_name': 'Luna', 'last_name': 'Brown', 'email': 'luna.brown@example.com'},
            {'username': 'aiartist7', 'first_name': 'River', 'last_name': 'Davis', 'email': 'river.davis@example.com'},
            {'username': 'imagineer8', 'first_name': 'Sage', 'last_name': 'Miller', 'email': 'sage.miller@example.com'},
            {'username': 'pixelcraft9', 'first_name': 'Phoenix', 'last_name': 'Wilson', 'email': 'phoenix.wilson@example.com'},
            {'username': 'dreamweaver10', 'first_name': 'Indigo', 'last_name': 'Moore', 'email': 'indigo.moore@example.com'},
            {'username': 'artforge11', 'first_name': 'Nova', 'last_name': 'Taylor', 'email': 'nova.taylor@example.com'},
            {'username': 'vision12', 'first_name': 'Orion', 'last_name': 'Anderson', 'email': 'orion.anderson@example.com'},
            {'username': 'sketcher13', 'first_name': 'Iris', 'last_name': 'Thomas', 'email': 'iris.thomas@example.com'},
            {'username': 'render14', 'first_name': 'Atlas', 'last_name': 'Jackson', 'email': 'atlas.jackson@example.com'},
            {'username': 'concept15', 'first_name': 'Lyra', 'last_name': 'White', 'email': 'lyra.white@example.com'},
            {'username': 'studio16', 'first_name': 'Finn', 'last_name': 'Harris', 'email': 'finn.harris@example.com'},
            {'username': 'brush17', 'first_name': 'Echo', 'last_name': 'Martin', 'email': 'echo.martin@example.com'},
            {'username': 'canvas18', 'first_name': 'Storm', 'last_name': 'Garcia', 'email': 'storm.garcia@example.com'},
            {'username': 'palette19', 'first_name': 'Raven', 'last_name': 'Lee', 'email': 'raven.lee@example.com'},
            {'username': 'inspire20', 'first_name': 'Wren', 'last_name': 'Clark', 'email': 'wren.clark@example.com'},
        ]
        
        created_count = 0
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                }
            )
            if created:
                user.set_password('123test')
                user.save()
                created_count += 1
                self.stdout.write(f'Created user: {user.username}')
            else:
                self.stdout.write(f'User {user.username} already exists')
        
        return created_count

    def create_sample_prompts(self):
        """Create sample prompts with data from PromptDen and original content"""
        
        # Get all users for random assignment
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return 0

        # Comprehensive tag list
        all_tags = [
            'Landscape', 'Portrait', 'Whimsy', 'Fantasy', 'Sci-fi', 'Fashion', 
            'Children', 'Abstract', 'Nature', 'Architecture', 'Food', 'Animals', 
            'Vintage', 'Futuristic', 'Artistic', 'Photography', '3D Render', 'Minimalist'
        ]

        # Sample prompts data (mixing PromptDen scraped and original content)
        prompts_data = [
            {
                'title': 'Tropical Paradise in a Silver Spoon',
                'content': 'A highly realistic vertical photo of a silver spoon held above a ceramic bowl. Inside the spoon is a vivid tropical beach with soft golden sand, crystal-clear turquoise water, and tiny people swimming and sunbathing. The shoreline curves naturally into the bowl below, where the tropical sea continues with gentle waves, floating clouds, and seagulls flying above. The transition from spoon to bowl feels seamless and magical. Soft sunlight, dreamy atmosphere, 9:16 format, magical realism.',
                'excerpt': 'A world of wonder captured in a spoon, where the beauty of a tropical paradise blends effortlessly with the simplicity of a ceramic bowl, inviting you to imagine the magic that lies within.',
                'ai_generator': 'midjourney',
                'tags': ['Whimsy', 'Photography', 'Nature', 'Artistic'],
                'source_url': 'promptden.com/post/tropical-paradise-in-a-silver-spoon'
            },
            {
                'title': 'Whimsical Claymation Boy with Floating Dandelion Seeds',
                'content': 'A charming claymation-style boy character with oversized curious eyes and a gentle smile, sitting in a meadow surrounded by floating dandelion seeds. The seeds drift magically through the air, catching golden sunlight. The boy wears a simple striped shirt and has tousled hair. The scene has a dreamy, soft-focus background with warm lighting. Clay texture visible, stop-motion animation aesthetic, Pixar-like quality, heartwarming atmosphere.',
                'excerpt': 'Experience the magic of childhood wonder through this enchanting claymation scene where innocence meets the gentle beauty of floating dandelion wishes.',
                'ai_generator': 'midjourney',
                'tags': ['Children', 'Whimsy', '3D Render', 'Nature'],
                'source_url': 'promptden.com/post/whimsical-claymation-boy-with-floating-dandelion-seeds'
            },
            {
                'title': 'Discover the Cosmic Whale: A Journey Awaits',
                'content': 'A magnificent whale floating through a starry cosmic void, its body translucent and filled with swirling galaxies, nebulae, and twinkling stars. The whale\'s fins trail stardust and cosmic particles. Small planets orbit around its massive form. Deep space background with vibrant purples, blues, and golds. Ethereal lighting, mystical atmosphere, digital art style, highly detailed, fantasy realism.',
                'excerpt': 'Embark on an interstellar adventure with a cosmic whale that carries entire galaxies within its ethereal form, bridging the ocean depths with infinite space.',
                'ai_generator': 'stable-diffusion',
                'tags': ['Fantasy', 'Sci-fi', 'Animals', 'Abstract'],
                'source_url': 'promptden.com/post/discover-the-cosmic-whale-a-journey-awaits'
            },
            {
                'title': 'Retro Surfboards at Newport Beach: 60s Vibes',
                'content': 'A collection of vintage surfboards lined up against a wooden beach shack at Newport Beach. The boards feature classic 1960s designs with bright colors, floral patterns, and retro logos. Golden hour lighting casts warm shadows. Beach umbrellas, vintage cars, and people in 60s beach attire in the background. Film photography aesthetic, saturated colors, nostalgic mood, Kodachrome style.',
                'excerpt': 'Transport yourself to the golden age of surfing with these beautifully crafted vintage boards that capture the free-spirited essence of 1960s beach culture.',
                'ai_generator': 'dall-e-3',
                'tags': ['Vintage', 'Photography', 'Landscape', 'Artistic'],
                'source_url': 'promptden.com/post/retro-surfboards-at-newport-beach-60s-vibes'
            },
            {
                'title': 'Stylish Fox Character in Elegant 3D Render',
                'content': 'A sophisticated anthropomorphic fox character wearing a tailored navy blue suit with a silk tie. The fox has intelligent amber eyes, perfectly groomed fur, and a confident expression. Standing in an elegant library setting with leather-bound books and warm lighting. High-quality 3D rendering, Pixar-level detail, professional studio lighting, sophisticated color palette.',
                'excerpt': 'Meet the epitome of refined elegance in this stunning 3D fox character that combines wild charm with sophisticated style and intelligence.',
                'ai_generator': 'leonardo-ai',
                'tags': ['Animals', '3D Render', 'Fashion', 'Portrait'],
                'source_url': 'promptden.com/post/stylish-fox-character-in-elegant-3d-render'
            },
            {
                'title': 'Chic Kazakh Style: Joyful Moments at the Cafe',
                'content': 'A beautiful young woman in traditional Kazakh-inspired modern fashion, sitting at a cozy cafe. She wears an elegant embroidered dress with geometric patterns in rich burgundy and gold. Warm ambient lighting, steam rising from her tea cup, genuine laughter, cultural fusion style. Portrait photography, natural lighting, authentic cultural representation, joyful atmosphere.',
                'excerpt': 'Celebrate the beautiful fusion of traditional Kazakh elegance with modern cafe culture in this heartwarming portrait of authentic joy and cultural pride.',
                'ai_generator': 'midjourney',
                'tags': ['Portrait', 'Fashion', 'Photography', 'Artistic'],
                'source_url': 'promptden.com/post/chic-kazakh-style-joyful-moments-at-the-cafe'
            },
            {
                'title': 'Surreal Macro Beauty: Ethereal Petals Unveiled',
                'content': 'An extreme macro photograph of flower petals with an otherworldly twist. The petals appear to be made of translucent crystal with rainbow light refractions. Water droplets act like tiny lenses, each containing miniature worlds. Soft bokeh background with floating light particles. Surreal colors, dreamlike quality, high-resolution macro photography, ethereal lighting.',
                'excerpt': 'Discover a hidden universe within flower petals where reality bends and beauty transcends the ordinary in this mesmerizing macro exploration.',
                'ai_generator': 'stable-diffusion',
                'tags': ['Abstract', 'Nature', 'Photography', 'Artistic'],
                'source_url': 'promptden.com/post/surreal-macro-beauty-ethereal-petals-unveiled'
            },
            {
                'title': 'Iconic Lavender Album Cover: Clean Fashionable',
                'content': 'A minimalist album cover design featuring a model in flowing lavender fabric against a clean white background. The model poses elegantly with the fabric billowing around them. Soft purple and white color palette, fashion photography style, high-end aesthetic, negative space, typography-ready composition, modern and timeless.',
                'excerpt': 'Experience the perfect harmony of fashion and music in this clean, sophisticated album cover that embodies elegance through simplicity and lavender dreams.',
                'ai_generator': 'dall-e-3',
                'tags': ['Fashion', 'Minimalist', 'Photography', 'Portrait'],
                'source_url': 'promptden.com/post/iconic-lavender-album-cover-clean-fashionable'
            },
            {
                'title': 'Futuristic Cyberpunk Anime Street Fashion Mastery',
                'content': 'A cyberpunk anime character with neon-colored hair and high-tech street fashion walking through a futuristic Tokyo street. Holographic advertisements, neon lights reflecting on wet pavement, flying vehicles in the background. The character wears LED-embedded clothing and augmented reality glasses. Vibrant neon colors, anime art style, cyberpunk aesthetic, detailed urban environment.',
                'excerpt': 'Step into a neon-lit future where street fashion meets cutting-edge technology in this stunning cyberpunk anime vision of tomorrow\'s urban culture.',
                'ai_generator': 'midjourney',
                'tags': ['Sci-fi', 'Futuristic', 'Fashion', 'Artistic'],
                'source_url': 'promptden.com/post/futuristic-cyberpunk-anime-street-fashion-mastery'
            },
            {
                'title': 'Discover Tranquility: Winery in a Serene Forest',
                'content': 'A hidden boutique winery nestled deep within an ancient forest. Stone buildings with ivy-covered walls, wooden barrels aging under dappled sunlight filtering through the canopy. A gentle stream flows nearby with a small stone bridge. Peaceful atmosphere, golden hour lighting, rustic elegance, natural integration with the environment.',
                'excerpt': 'Find peace and sophistication in this enchanting forest winery where nature and craftsmanship create the perfect harmony for wine lovers and dreamers.',
                'ai_generator': 'leonardo-ai',
                'tags': ['Landscape', 'Architecture', 'Nature', 'Artistic'],
                'source_url': 'promptden.com/post/discover-tranquility-winery-in-a-serene-forest'
            },
            {
                'title': 'Brown Bear Paw Gripping a Beer Can',
                'content': 'A close-up shot of a massive brown bear paw carefully gripping a standard aluminum beer can. The contrast between the wild, powerful paw with thick fur and sharp claws against the modern beverage container. Forest background softly blurred. Hyper-realistic photography style, detailed fur texture, dramatic lighting, humorous concept with serious execution.',
                'excerpt': 'Witness the amusing yet powerful moment when wilderness meets civilization in this striking image of raw nature encountering modern refreshment.',
                'ai_generator': 'flux',
                'tags': ['Animals', 'Photography', 'Whimsy', 'Nature'],
                'source_url': 'promptden.com/post/brown-bear-paw-gripping-a-beer-can'
            },
            {
                'title': 'Enchanting Elf Eyes: Hyperrealistic Macro Photography',
                'content': 'An extreme close-up of mystical elf eyes with intricate golden and emerald iris patterns. Long, delicate eyelashes with dewdrops. The eyes reflect ancient forests and magical light. Hyperrealistic detail showing every texture, from the smooth skin to the complex iris structure. Fantasy makeup with subtle glitter and natural tones. Professional macro photography lighting.',
                'excerpt': 'Lose yourself in the mesmerizing depth of ancient magic captured in these stunning elf eyes that hold centuries of forest wisdom and ethereal beauty.',
                'ai_generator': 'midjourney',
                'tags': ['Fantasy', 'Portrait', 'Photography', 'Artistic'],
                'source_url': 'promptden.com/post/enchanting-elf-eyes-hyperrealistic-macro-photography'
            },
            {
                'title': 'Boho White Cave Retreat with Stunning Sea Views',
                'content': 'A luxurious bohemian cave dwelling carved into white limestone cliffs overlooking the Mediterranean sea. Flowing white fabrics, comfortable floor cushions, hanging plants, and natural wood furniture. Large openings frame the turquoise sea view. Soft natural lighting, peaceful atmosphere, luxury meets nature, architectural photography style.',
                'excerpt': 'Escape to this dreamy bohemian sanctuary where luxury cave living meets breathtaking ocean vistas in perfect harmony with natural stone and flowing fabrics.',
                'ai_generator': 'stable-diffusion',
                'tags': ['Architecture', 'Landscape', 'Artistic', 'Minimalist'],
                'source_url': 'promptden.com/post/boho-white-cave-retreat-with-stunning-sea-views'
            },
            {
                'title': 'Futuristic Ethereal Woman in Translucent White Dress',
                'content': 'A graceful woman wearing a flowing translucent white dress that seems to be made of light and mist. She stands in a futuristic environment with soft holographic elements floating around her. Her hair flows as if underwater, and her skin has a subtle luminescent quality. Sci-fi fashion, ethereal lighting, dreamy atmosphere, high-fashion photography meets science fiction.',
                'excerpt': 'Experience the future of fashion and beauty in this ethereal vision where technology and elegance merge to create something truly otherworldly.',
                'ai_generator': 'dall-e-3',
                'tags': ['Futuristic', 'Fashion', 'Portrait', 'Sci-fi'],
                'source_url': 'promptden.com/post/futuristic-ethereal-woman-in-translucent-white-dress'
            },
            {
                'title': 'Luxury Meets Wild: Stunning Portraits Unveiled',
                'content': 'A high-fashion portrait series featuring models in luxury garments posed in wild natural settings. A model in an elegant evening gown stands among tall grass in golden hour light. Another wears a designer coat while wolves roam peacefully in the background. Contrast between refined fashion and untamed nature, professional fashion photography, dramatic lighting.',
                'excerpt': 'Witness the striking juxtaposition of high fashion and untamed wilderness in these breathtaking portraits that redefine luxury in natural settings.',
                'ai_generator': 'leonardo-ai',
                'tags': ['Fashion', 'Portrait', 'Nature', 'Photography'],
                'source_url': 'promptden.com/post/luxury-meets-wild-stunning-portraits-unveiled'
            },
            {
                'title': 'Modern Male Model Portrait: Stylish Captivating',
                'content': 'A contemporary male model with perfectly styled hair and strong facial features. He wears a minimalist black turtleneck against a neutral background. Studio lighting creates dramatic shadows that accentuate his bone structure. Professional fashion photography, modern aesthetic, confident expression, high-end commercial style.',
                'excerpt': 'Discover the essence of modern masculinity in this captivating portrait that combines classic elegance with contemporary style and confidence.',
                'ai_generator': 'midjourney',
                'tags': ['Portrait', 'Fashion', 'Photography', 'Minimalist'],
                'source_url': 'promptden.com/post/modern-male-model-portrait-stylish-captivating'
            },
            {
                'title': 'Elegant Pink Crystal Chess Queen Figurine',
                'content': 'A meticulously crafted chess queen piece made entirely of pink crystal or rose quartz. The piece sits on a marble chessboard with soft lighting creating beautiful refractions through the translucent material. The queen features intricate carved details in her crown and dress. Luxury product photography, elegant composition, rich textures.',
                'excerpt': 'Admire the exquisite craftsmanship of this pink crystal chess queen that transforms a classic game piece into a work of art worthy of any collection.',
                'ai_generator': 'flux',
                'tags': ['Artistic', 'Minimalist', 'Photography', 'Abstract'],
                'source_url': 'promptden.com/post/elegant-pink-crystal-chess-queen-figurine'
            },
            {
                'title': 'Enchanting Fairy on Crescent Moon: High-Def Art',
                'content': 'A delicate fairy with translucent wings sitting gracefully on a golden crescent moon against a starry night sky. She wears a flowing gown made of moonbeams and stardust. Magical particles float around her, and distant galaxies provide a dreamy backdrop. Fantasy digital art, ethereal lighting, high detail, mystical atmosphere.',
                'excerpt': 'Enter a world of magic and wonder with this enchanting fairy who makes her home among the stars and calls the crescent moon her throne.',
                'ai_generator': 'stable-diffusion',
                'tags': ['Fantasy', 'Whimsy', 'Artistic', 'Abstract'],
                'source_url': 'promptden.com/post/enchanting-fairy-on-crescent-moon-high-def-art'
            },
            {
                'title': 'Charming Curvy Cartoon Woman in Fantasy Art',
                'content': 'A beautifully illustrated cartoon woman with a curvy figure in a fantasy art style. She has flowing hair and wears a medieval-inspired dress with intricate details. The background features a magical forest with glowing mushrooms and fireflies. Warm color palette, professional digital illustration, character design, fantasy genre.',
                'excerpt': 'Meet this charming character who brings warmth and personality to the fantasy realm with her endearing design and magical forest setting.',
                'ai_generator': 'dall-e-3',
                'tags': ['Fantasy', 'Portrait', 'Artistic', 'Whimsy'],
                'source_url': 'promptden.com/post/charming-curvy-cartoon-woman-in-fantasy-art'
            },
            {
                'title': 'Epic Sci-Fi Astronauts: A Cosmic Encounter',
                'content': 'Two astronauts in advanced spacesuits standing on an alien planet\'s surface, facing a massive alien structure or spacecraft in the distance. The alien world has multiple moons visible in a colorful sky. The astronauts\' suits feature LED displays and high-tech details. Epic scale, cinematic composition, science fiction movie poster style.',
                'excerpt': 'Join these brave explorers on an epic cosmic journey as they encounter the unknown on a distant alien world filled with mystery and wonder.',
                'ai_generator': 'leonardo-ai',
                'tags': ['Sci-fi', 'Futuristic', 'Landscape', 'Adventure'],
                'source_url': 'promptden.com/post/epic-sci-fi-astronauts-a-cosmic-encounter'
            },
            {
                'title': 'Intense Close-Up of a Race Car Driver\'s Eye',
                'content': 'An extreme close-up of a race car driver\'s eye visible through their helmet visor. The eye shows intense focus and determination. Reflections in the pupil reveal the racetrack and other cars. Sweat beads on the skin around the eye. High-speed photography style, dramatic lighting, sports photography, intense emotion captured.',
                'excerpt': 'Feel the adrenaline and intense focus of high-speed racing captured in this powerful close-up that reveals the driver\'s unwavering determination.',
                'ai_generator': 'midjourney',
                'tags': ['Portrait', 'Photography', 'Artistic', 'Abstract'],
                'source_url': 'promptden.com/post/intense-close-up-of-a-race-car-drivers-eye'
            },
            {
                'title': 'Radiant Skin: Elevate Your Natural Glow Today',
                'content': 'A beauty portrait showcasing flawless, radiant skin with natural makeup. Soft, even lighting highlights the skin\'s natural texture and glow. The model has a serene expression with minimal, natural-looking makeup that enhances rather than covers. Clean beauty aesthetic, skincare photography, healthy lifestyle imagery.',
                'excerpt': 'Discover the secret to naturally radiant skin in this stunning beauty portrait that celebrates the power of healthy, glowing complexion.',
                'ai_generator': 'flux',
                'tags': ['Portrait', 'Photography', 'Fashion', 'Minimalist'],
                'source_url': 'promptden.com/post/radiant-skin-elevate-your-natural-glow-today'
            },
            {
                'title': 'Retro Speed: Cyberpunk 2077 Art Poster',
                'content': 'A retro-futuristic poster design inspired by Cyberpunk 2077 aesthetics. Features a sleek sports car speeding through a neon-lit cityscape at night. Synthwave color palette with hot pink and cyan neon lights. Grid patterns and geometric shapes frame the composition. 1980s inspired typography, retro-futuristic art style.',
                'excerpt': 'Race into the neon-soaked future with this electrifying retro poster that perfectly captures the high-speed thrills of cyberpunk culture.',
                'ai_generator': 'stable-diffusion',
                'tags': ['Futuristic', 'Vintage', 'Artistic', 'Sci-fi'],
                'source_url': 'promptden.com/post/retro-speed-cyberpunk-2077-art-poster'
            },
            {
                'title': 'Epic Fusion of Science and Space Adventure',
                'content': 'A dramatic scene showing a scientist in a high-tech laboratory that seamlessly blends into a cosmic space environment. Scientific equipment floats alongside planets and stars. The scientist wears both a lab coat and space helmet. Beakers contain swirling galaxies instead of chemicals. Reality-bending composition, science fiction art, educational inspiration.',
                'excerpt': 'Witness the ultimate merger of scientific discovery and space exploration in this mind-bending visual that celebrates human curiosity and adventure.',
                'ai_generator': 'dall-e-3',
                'tags': ['Sci-fi', 'Futuristic', 'Abstract', 'Artistic'],
                'source_url': 'promptden.com/post/epic-fusion-of-science-and-space-adventure'
            },
            {
                'title': 'Futuristic Spire Design: Sailing into the Future',
                'content': 'An architectural marvel featuring a twisted spire building that appears to be sailing through clouds. The structure combines sleek metal and glass with sail-like elements. It rises from a futuristic cityscape below. The design suggests movement and grace despite being a stationary building. Architectural visualization, futuristic design, conceptual architecture.',
                'excerpt': 'Behold this revolutionary architectural concept that redefines skylines by combining the elegance of sailing with cutting-edge futuristic design.',
                'ai_generator': 'leonardo-ai',
                'tags': ['Architecture', 'Futuristic', 'Artistic', 'Abstract'],
                'source_url': 'promptden.com/post/futuristic-spire-design-sailing-into-the-future'
            },
            {
                'title': 'Whimsical Felt Dolls Adventure in Potato Chip Boat',
                'content': 'Adorable handmade felt dolls sailing in a boat made from a giant potato chip across a miniature ocean. The dolls wear tiny knitted sweaters and have embroidered faces. Waves are made of blue fabric, and seagulls are small white felt pieces. Craft photography, miniature world, handmade aesthetic, playful composition.',
                'excerpt': 'Embark on a delightfully absurd voyage with these charming felt dolls who prove that the best adventures happen in the most unexpected vessels.',
                'ai_generator': 'midjourney',
                'tags': ['Whimsy', 'Children', 'Artistic', 'Photography'],
                'source_url': 'promptden.com/post/whimsical-felt-dolls-adventure-in-potato-chip-boat'
            },
            {
                'title': 'Discover Demure Elegance: Impeccable Style Awaits',
                'content': 'A sophisticated fashion portrait featuring a model in understated elegant attire. She wears a classic beige trench coat with minimal jewelry and natural makeup. The pose and expression convey quiet confidence and refined taste. Neutral color palette, timeless fashion photography, sophisticated styling, editorial quality.',
                'excerpt': 'Embrace the power of understated elegance in this timeless fashion portrait that proves true style speaks in whispers, not shouts.',
                'ai_generator': 'flux',
                'tags': ['Fashion', 'Portrait', 'Photography', 'Minimalist'],
                'source_url': 'promptden.com/post/discover-demure-elegance-impeccable-style-awaits'
            },
        ]

        created_count = 0
        for prompt_data in prompts_data:
            # Check if prompt already exists
            if Prompt.objects.filter(title=prompt_data['title']).exists():
                self.stdout.write(f'Prompt "{prompt_data["title"]}" already exists')
                continue
            
            # Random author assignment
            author = random.choice(users)
            
            # Random status (mostly published)
            status = random.choices([0, 1], weights=[20, 80])[0]  # 80% published
            
            # Create the prompt
            prompt = Prompt.objects.create(
                title=prompt_data['title'],
                content=prompt_data['content'],
                excerpt=prompt_data['excerpt'],
                author=author,
                ai_generator=prompt_data['ai_generator'],
                status=status,
                featured_image='placeholder'  # Using placeholder as per your current setup
            )
            
            # Add tags
            for tag in prompt_data['tags']:
                prompt.tags.add(tag)
            
            created_count += 1
            self.stdout.write(f'Created prompt: "{prompt.title}" by {author.username}')
        
        return created_count
