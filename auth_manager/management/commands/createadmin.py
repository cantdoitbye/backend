from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import CommandError

class Command(BaseCommand):
    help = 'Create a superuser with a default username of "admin"'

    def handle(self, *args, **options):
        username = 'admin'
        email = None
        while not email:
            email = input('Email: ')
            if not email:
                self.stdout.write(self.style.ERROR('Error: Email is mandatory.'))

        password = None
        while not password:
            password = input('Password: ')
            password_confirm = input('Password (again): ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Error: Your passwords didn\'t match. Please try again.'))
                password = None
                continue

            if not password:
                self.stdout.write(self.style.ERROR('Error: Blank passwords aren\'t allowed.'))
                password = None
                continue

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Error: User with username "{username}" already exists.'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser created successfully.'))

            user = User.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'User credentials: Username: {user.username}, Password: {password}, Email: {user.email}'))
