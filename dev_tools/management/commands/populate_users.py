from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates 10 users with predefined Indian names and the same password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            help='Password for all users',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        names = [
            'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun',
            'Aditi', 'Ananya', 'Saanvi', 'Diya', 'Riya'
        ]

        password = options['password']
        if not password:
            password = self.get_input('Enter password for all users: ')

        self.stdout.write('Creating 10 users...')

        try:
            with transaction.atomic():
                for name in names:
                    if not User.objects.filter(username=name).exists():
                        User.objects.create_user(username=name, password=password)
                        self.stdout.write(self.style.SUCCESS(f'Successfully created user {name}'))
            self.stdout.write(self.style.SUCCESS('Successfully created 10 users.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating users: {e}'))

    def get_input(self, prompt):
        return input(prompt)
