from django.core.management.base import BaseCommand
from community.utils.generate_community import generate_communities_based_on_interest  # Assuming you have a utility function for this

class Command(BaseCommand):
    help = 'Generate communities based on user interests'

    def handle(self, *args, **kwargs):
        try:
            generate_communities_based_on_interest()  # Call the function to generate communities
            self.stdout.write(self.style.SUCCESS('Successfully generated communities based on user interests.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating communities: {e}'))
