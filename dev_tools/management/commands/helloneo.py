from django.core.management.base import BaseCommand
from neomodel import db
from neomodel.exceptions import NeomodelException

class Command(BaseCommand):
    help = 'Checks the Neo4j database connection'

    def handle(self, *args, **options):
        self.stdout.write('Checking Neo4j database connection...')

        try:
            # Attempt to run a simple query
            db.cypher_query('MATCH (n) RETURN n LIMIT 1')
            self.stdout.write(self.style.SUCCESS('Neo4j database connection successful!'))
        except NeomodelException as e:
            self.stdout.write(self.style.ERROR(f'Neo4j database connection failed: {e}'))
