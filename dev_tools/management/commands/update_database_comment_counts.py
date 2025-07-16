from django.core.management.base import BaseCommand
from post.redis import update_database_comment_counts
class Command(BaseCommand):
    help = 'Sync comment counts from Redis to the database'

    def handle(self, *args, **kwargs):
        try:
            update_database_comment_counts()  # Call the function to update counts
            self.stdout.write(self.style.SUCCESS('Successfully synced comment counts from Redis to the database.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error syncing comment counts: {e}'))
            
