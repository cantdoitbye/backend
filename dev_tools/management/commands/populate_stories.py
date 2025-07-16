from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from story.models import Story
from auth_manager.models import Users
from datetime import datetime
import uuid
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from tqdm import tqdm
import random

class Command(BaseCommand):
    help = 'Creates 10 stories for each user with realistic titles, content, and privacy settings using GPT-2'

    def handle(self, *args, **options):
        User = get_user_model()
        model_name = "gpt2"
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        model = GPT2LMHeadModel.from_pretrained(model_name)

        model.config.pad_token_id = model.config.eos_token_id

        def generate_text(prompt, max_new_tokens=50):
            inputs = tokenizer.encode(prompt, return_tensors="pt")
            outputs = model.generate(inputs, max_new_tokens=max_new_tokens, num_return_sequences=1, no_repeat_ngram_size=2)
            text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return text

        title_prompts = [
            "Create a unique and engaging title for a story about adventure:",
            "Generate a compelling story title about love:",
            "What would be a great title for a mystery story?",
            "Think of an intriguing title for a sci-fi story:",
            "Give a fascinating title for a historical fiction story:"
        ]

        content_prompts = [
            "Write an interesting story content about an adventure:",
            "Generate a story content that revolves around a romantic encounter:",
            "Describe a thrilling mystery story content:",
            "Create a captivating story content set in a futuristic world:",
            "Narrate an engaging historical fiction story content:"
        ]

        self.stdout.write('Creating 10 stories for each user...')

        try:
            users = User.objects.all()
            if not users.exists():
                raise Exception("No users found in the database.")
            
            with transaction.atomic():
                for user in tqdm(users, desc="Processing users"):
                    neo4j_user = Users.nodes.get(user_id=user.id)
                    for i in range(2):
                        title_prompt = random.choice(title_prompts)
                        content_prompt = random.choice(content_prompts)
                        title = generate_text(title_prompt, max_new_tokens=10).strip()
                        content = generate_text(content_prompt, max_new_tokens=100).strip()

                        story = Story(
                            uid=str(uuid.uuid4()),  # Generate a unique ID for each story
                            title=title,  # Generate a realistic title
                            content=content,  # Generate realistic content
                            privacy=random.choice(['Universal', 'Outer', 'Inner']),  # Randomly choose privacy setting
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        story.save()
                        story.created_by.connect(neo4j_user)
                        neo4j_user.story.connect(story)
                        self.stdout.write(self.style.SUCCESS(f'Successfully created story "{story.title}" for user {user.username}'))

            self.stdout.write(self.style.SUCCESS('Successfully created stories for each user.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating stories: {e}'))
