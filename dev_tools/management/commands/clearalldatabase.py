from django.core.management.base import BaseCommand
from neomodel import db
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = 'Cleans the Neo4j database, deletes all constraints, indexes, properties, and deletes User data from the relational database'

    def handle(self, *args, **options):
        self.stdout.write('\n')
        self.stdout.write('Starting to clean the databases...')
        
        try:
            # Clean Neo4j database
            db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
            self.clean_neo4j_database()
            self.stdout.write(self.style.SUCCESS('Successfully cleaned the Neo4j database.'))

            # Clean User model data from relational database
            self.clean_relational_db_user()
            self.stdout.write(self.style.SUCCESS('Successfully deleted User data from the relational database.'))
            self.stdout.write('\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cleaning the databases: {e}'))
            self.stdout.write('\n')

    def clean_neo4j_database(self):
        # Delete all nodes
        db.cypher_query('MATCH (n) DETACH DELETE n')
        self.stdout.write(self.style.SUCCESS('Successfully deleted all nodes in the Neo4j database.'))

        # Delete all constraints
        constraints = db.cypher_query('SHOW CONSTRAINTS')[0]
        for constraint in constraints:
            constraint_name = constraint[1]  # Get the constraint name
            db.cypher_query(f'DROP CONSTRAINT `{constraint_name}`')
            self.stdout.write(self.style.SUCCESS(f'Dropped constraint: {constraint_name}'))

        # Delete all indexes
        indexes = db.cypher_query('SHOW INDEXES')[0]
        for index in indexes:
            index_name = index[1]  # Get the index name
            db.cypher_query(f'DROP INDEX `{index_name}`')
            self.stdout.write(self.style.SUCCESS(f'Dropped index: {index_name}'))

        # Remove all properties from nodes
        self.remove_all_properties_from_nodes()

        # Remove all properties from relationships
        self.remove_all_properties_from_relationships()

    def remove_all_properties_from_nodes(self):
        nodes = db.cypher_query('MATCH (n) RETURN properties(n), id(n)')[0]
        for node in nodes:
            properties, node_id = node
            remove_properties_query = f"MATCH (n) WHERE id(n) = {node_id} REMOVE " + ", ".join([f"n.{key}" for key in properties.keys()])
            db.cypher_query(remove_properties_query)
        self.stdout.write(self.style.SUCCESS('Successfully removed all properties from nodes.'))

    def remove_all_properties_from_relationships(self):
        relationships = db.cypher_query('MATCH ()-[r]->() RETURN properties(r), id(r)')[0]
        for relationship in relationships:
            properties, rel_id = relationship
            remove_properties_query = f"MATCH ()-[r]->() WHERE id(r) = {rel_id} REMOVE " + ", ".join([f"r.{key}" for key in properties.keys()])
            db.cypher_query(remove_properties_query)
        self.stdout.write(self.style.SUCCESS('Successfully removed all properties from relationships.'))

    def clean_relational_db_user(self):
        User = get_user_model()
        
        # Start a database transaction
        with transaction.atomic():
            User.objects.all().delete()
