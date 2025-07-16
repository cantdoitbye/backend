import json
from django.core.management.base import BaseCommand
from vibe_manager.models import Vibe
from auth_manager.models import Users

class Command(BaseCommand):
    help = 'Populate the Vibe model with full data from a JSON file'

    def add_arguments(self, parser):
        # Add an optional argument to specify a JSON file path
        parser.add_argument(
            '--json-file',
            type=str,
            help='Specify the path to the JSON file to import vibes',
            default='vibes_full_data.json'
        )

    def handle(self, *args, **kwargs):
        json_file_path = kwargs['json_file']
        user_uid = 'a45621067f9e464b896c5db3a9d90cb8'  # The provided user UID

        try:
            # Retrieve the user from the Users model
            user = Users.nodes.get(uid=user_uid)

            with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)

                for row in data:
                    vibe = Vibe(
                        name=row['name'],
                        category=row['category'],
                        description=row['description'],
                        subCategory=row['subCategory'],
                        desc=row.get('desc', ''),
                        iq=float(row['iq']),
                        aq=float(row['aq']),
                        sq=float(row['sq']),
                        hq=float(row['hq']),
                        popularity=int(row.get('popularity', 0))  # Default to 0 if 'popularity' is not provided
                    )

                    # Connect the Vibe to the user
                    vibe.save()
                    vibe.created_by.connect(user)

            self.stdout.write(self.style.SUCCESS('Successfully populated Vibes from JSON file.'))

        except Users.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with UID {user_uid} does not exist.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {json_file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON format in file: {json_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {str(e)}'))
