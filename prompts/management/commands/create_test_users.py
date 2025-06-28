from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Create dummy test users for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of test users to create (default: 10)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password for all test users (default: testpass123)'
        )

    def handle(self, *args, **options):
        count = options['count']
        password = options['password']
        
        # Predefined user data for more realistic accounts
        user_templates = [
            {'username': 'alice_creator', 'first_name': 'Alice', 'last_name': 'Johnson', 'email': 'alice@example.com'},
            {'username': 'bob_designer', 'first_name': 'Bob', 'last_name': 'Smith', 'email': 'bob@example.com'},
            {'username': 'carol_artist', 'first_name': 'Carol', 'last_name': 'Davis', 'email': 'carol@example.com'},
            {'username': 'david_prompt', 'first_name': 'David', 'last_name': 'Wilson', 'email': 'david@example.com'},
            {'username': 'emma_creative', 'first_name': 'Emma', 'last_name': 'Brown', 'email': 'emma@example.com'},
            {'username': 'frank_ai', 'first_name': 'Frank', 'last_name': 'Miller', 'email': 'frank@example.com'},
            {'username': 'grace_writer', 'first_name': 'Grace', 'last_name': 'Taylor', 'email': 'grace@example.com'},
            {'username': 'henry_coder', 'first_name': 'Henry', 'last_name': 'Anderson', 'email': 'henry@example.com'},
            {'username': 'ivy_digital', 'first_name': 'Ivy', 'last_name': 'Thomas', 'email': 'ivy@example.com'},
            {'username': 'jack_innovator', 'first_name': 'Jack', 'last_name': 'Jackson', 'email': 'jack@example.com'},
            {'username': 'kate_visionary', 'first_name': 'Kate', 'last_name': 'Martinez', 'email': 'kate@example.com'},
            {'username': 'liam_generator', 'first_name': 'Liam', 'last_name': 'Garcia', 'email': 'liam@example.com'},
            {'username': 'maya_storyteller', 'first_name': 'Maya', 'last_name': 'Rodriguez', 'email': 'maya@example.com'},
            {'username': 'noah_architect', 'first_name': 'Noah', 'last_name': 'Lee', 'email': 'noah@example.com'},
            {'username': 'olivia_curator', 'first_name': 'Olivia', 'last_name': 'White', 'email': 'olivia@example.com'},
            {'username': 'peter_synthwave', 'first_name': 'Peter', 'last_name': 'Clark', 'email': 'peter@example.com'},
            {'username': 'quinn_futurist', 'first_name': 'Quinn', 'last_name': 'Lewis', 'email': 'quinn@example.com'},
            {'username': 'ruby_renaissance', 'first_name': 'Ruby', 'last_name': 'Walker', 'email': 'ruby@example.com'},
            {'username': 'sam_experimental', 'first_name': 'Sam', 'last_name': 'Hall', 'email': 'sam@example.com'},
            {'username': 'tara_dreamweaver', 'first_name': 'Tara', 'last_name': 'Young', 'email': 'tara@example.com'},
        ]
        
        created_users = []
        
        with transaction.atomic():
            for i in range(count):
                # Use predefined templates, or generate generic ones if we need more
                if i < len(user_templates):
                    user_data = user_templates[i]
                else:
                    user_data = {
                        'username': f'testuser{i+1}',
                        'first_name': f'User{i+1}',
                        'last_name': 'Test',
                        'email': f'testuser{i+1}@example.com'
                    }
                
                # Check if user already exists
                if User.objects.filter(username=user_data['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f'User {user_data["username"]} already exists, skipping...')
                    )
                    continue
                
                # Create the user
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=password,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                created_users.append(user)
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user.username} ({user.email})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {len(created_users)} test users!')
        )
        self.stdout.write(
            self.style.WARNING(f'All users have password: "{password}"')
        )
        self.stdout.write(
            self.style.HTTP_INFO('You can now log in with any of these accounts for testing.')
        )