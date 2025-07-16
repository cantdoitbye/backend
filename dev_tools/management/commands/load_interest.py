from django.core.management.base import BaseCommand
from auth_manager.models import InterestList
import json
import os

class Command(BaseCommand):
    help = 'Populate the InterestList model with data from structured_interests.json'

    def handle(self, *args, **kwargs):
        try:
            # Define the full path to structured_interests.json
            file_path = os.path.join('structured_interests.json')
            
            # Load data from structured_interests.json
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Iterate over each category and populate the model
            for category, sub_interests in data.items():
                # Prepare sub-interests list with id and name
                sub_interests_list = [{"id": idx + 1, "name": sub_interest} for idx, sub_interest in enumerate(sub_interests)]

                # Create or update the InterestList entry
                InterestList.objects.update_or_create(
                    name=category,
                    defaults={"sub_interests": sub_interests_list}
                )

            self.stdout.write(self.style.SUCCESS('Successfully populated InterestList with structured interests data.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating InterestList: {e}'))
