from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth.hashers import make_password
import json
import os

class Command(BaseCommand):
    help = 'Clear the content types and reload fixture data'

    def add_arguments(self, parser):
        parser.add_argument('fixture', type=str, help='Path to the fixture file')

    def handle(self, *args, **options):
        fixture_path = options['fixture']

        self.stdout.write("Clearing content types...")
        with transaction.atomic(using='default'):
            ContentType.objects.all().delete()

        self.stdout.write(f"Processing fixture data from {fixture_path}...")
        try:
            with open(fixture_path, 'r') as fixture_file:
                data = json.load(fixture_file)

            self.stdout.write(self.style.NOTICE(f"Loaded fixture data: {data}"))

            user_model_name = 'app_name.user'  # Replace with actual model name

            processed_data = []
            for item in data:
                if item['model'] == user_model_name:
                    if 'password' in item['fields']:
                        self.stdout.write(self.style.NOTICE(f"Original password: {item['fields']['password']}"))
                        item['fields']['password'] = make_password(item['fields']['password'])
                        self.stdout.write(self.style.NOTICE(f"Hashed password: {item['fields']['password']}"))
                processed_data.append(item)

            temp_fixture_path = 'temp_fixture.json'
            with open(temp_fixture_path, 'w') as temp_file:
                json.dump(processed_data, temp_file)

            self.stdout.write(f"Loading fixture data from {temp_fixture_path}...")
            try:
                call_command('loaddata', temp_fixture_path)
                self.stdout.write(self.style.SUCCESS('Successfully loaded fixture data.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading fixture data: {e}'))
                self.stdout.write(self.style.ERROR('Rolling back transaction.'))

            # Optionally, clean up the temporary fixture file
            if os.path.exists(temp_fixture_path):
                os.remove(temp_fixture_path)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing fixture data: {e}'))
