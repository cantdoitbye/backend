from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates a super admin and staff users with predefined names and passwords'

    def add_arguments(self, parser):
        parser.add_argument(
            '--superadmin-password',
            type=str,
            help='Password for the super admin',
        )
        parser.add_argument(
            '--staff-password',
            type=str,
            help='Password for the staff users',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        superadmin_password = options['superadmin_password']
        staff_password = options['staff_password']

        if not superadmin_password:
            superadmin_password = self.get_input('Enter password for super admin: ')

        if not staff_password:
            staff_password = self.get_input('Enter password for staff users: ')

        superadmin_name = 'superadmin'
        staff_names = ['staff1', 'staff2', 'staff3', 'staff4', 'staff5']

        self.stdout.write('Creating super admin and staff users...')

        try:
            with transaction.atomic():
                if not User.objects.filter(username=superadmin_name).exists():
                    User.objects.create_superuser(username=superadmin_name, password=superadmin_password)
                    self.stdout.write(self.style.SUCCESS(f'Successfully created super admin {superadmin_name}'))

                for name in staff_names:
                    if not User.objects.filter(username=name).exists():
                        User.objects.create_user(username=name, password=staff_password, is_staff=True)
                        self.stdout.write(self.style.SUCCESS(f'Successfully created staff user {name}'))
            self.stdout.write(self.style.SUCCESS('Successfully created super admin and staff users.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating users: {e}'))

    def get_input(self, prompt):
        return input(prompt)
