"""
Django Management Command to Import Relations from PDF Data
Place this file at: connection/management/commands/import_relations.py
"""

from django.core.management.base import BaseCommand
from connection.models import Relation, SubRelation


class Command(BaseCommand):
    help = 'Import subrelations from PDF data into connection_subrelation table'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting relation import...'))
        
        # Get existing relations by their database IDs
        # From your screenshots: 1=Relatives, 2=Friend, 3=Professional
        try:
            relatives = Relation.objects.get(id=1)
            friend = Relation.objects.get(id=2)
            professional = Relation.objects.get(id=3)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Found relations: {relatives.name}, {friend.name}, {professional.name}'
                )
            )
        except Relation.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(
                    'Error: Required relations (id 1,2,3) not found in database. '
                    'Please ensure they exist first.'
                )
            )
            return

        # Map relation names to objects
        relations_map = {
            'Relatives': relatives,
            'Friend': friend,
            'Professional': professional,
        }

        # Complete subrelations data from PDF
        # Format: (relation_name, sub_relation_name, directionality, approval_required, reverse_connection, default_circle)
        subrelations_data = [
            # ============ RELATIVES (relation_id = 1) ============
            ('Relatives', 'father', 'Bidirectional', True, 'Child', 'Inner'),
            ('Relatives', 'son', 'Bidirectional', True, 'Parent', 'Inner'),
            ('Relatives', 'husband', 'Bidirectional', True, 'Wife', 'Outer'),
            ('Relatives', 'brother', 'Bidirectional', True, 'Sibling', 'Inner'),
            ('Relatives', 'grandfather', 'Bidirectional', True, 'Grandchild', 'Universe'),
            ('Relatives', 'grandson', 'Bidirectional', True, 'Grandparent', 'Universe'),
            ('Relatives', 'uncle', 'Bidirectional', True, 'Nephew/Niece', 'Universe'),
            ('Relatives', 'nephew/niece', 'Bidirectional', True, 'Uncle/Aunt', 'Universe'),
            ('Relatives', 'cousin', 'Unidirectional', True, 'Cousin', 'Outer'),
            ('Relatives', 'mother', 'Bidirectional', True, 'Child', 'Inner'),
            ('Relatives', 'daughter', 'Bidirectional', True, 'Parent', 'Inner'),
            ('Relatives', 'wife', 'Bidirectional', True, 'Husband', 'Outer'),
            ('Relatives', 'sister', 'Bidirectional', True, 'Sibling', 'Inner'),
            ('Relatives', 'grandmother', 'Bidirectional', True, 'Grandchild', 'Universe'),
            ('Relatives', 'granddaughter', 'Bidirectional', True, 'Grandparent', 'Universe'),
            ('Relatives', 'aunt', 'Bidirectional', True, 'Nephew/Niece', 'Universe'),
            ('Relatives', 'niece', 'Bidirectional', True, 'Uncle/Aunt', 'Outer'),
            ('Relatives', 'parent', 'Bidirectional', True, 'Child', 'Inner'),
            ('Relatives', 'child', 'Bidirectional', True, 'Parent', 'Inner'),
            ('Relatives', 'spouse', 'Unidirectional', True, 'Spouse', 'Universe'),
            ('Relatives', 'sibling', 'Unidirectional', True, 'Sibling', 'Inner'),
            ('Relatives', 'grandparents', 'Bidirectional', True, 'Grandchild', 'Universe'),
            ('Relatives', 'grandchild', 'Bidirectional', True, 'Grandparents', 'Universe'),
            ('Relatives', "parent's sibling", 'Bidirectional', True, "sibling's child", 'Inner'),
            ('Relatives', "sibling's child", 'Bidirectional', True, "parent's sibling", 'Inner'),
            ('Relatives', "aunt's/uncle's child", 'Bidirectional', True, 'cousin', 'Inner'),
            ('Relatives', 'Father-in-law', 'Bidirectional', True, 'Daughter-in-law/Son-in-law', 'Outer'),
            ('Relatives', 'Mother-in-law', 'Bidirectional', True, 'Daughter-in-law/Son-in-law', 'Outer'),
            ('Relatives', 'Brother-in-law', 'Bidirectional', True, 'Sister-in-law/Brother-in-law', 'Outer'),
            ('Relatives', 'Sister-in-law', 'Bidirectional', True, 'Sister-in-law/Brother-in-law', 'Outer'),
            ('Relatives', 'Step-son', 'Bidirectional', True, 'Step-parent', 'Outer'),
            ('Relatives', 'Step-daughter', 'Bidirectional', True, 'Step-parent', 'Outer'),
            ('Relatives', 'Consanguinity', 'Unidirectional', True, 'Consanguinity', 'Universe'),
            ('Relatives', 'Godparents', 'Bidirectional', True, 'Godchild', 'Outer'),
            ('Relatives', 'Maternal relatives', 'Bidirectional', True, 'Relative', 'Inner'),
            ('Relatives', 'Paternal relatives', 'Bidirectional', True, 'Relative', 'Inner'),

            # ============ FRIEND (relation_id = 2) ============
            ('Friend', 'friend', 'Unidirectional', True, 'friend', 'Inner'),
            ('Friend', 'Best Friend', 'Unidirectional', True, 'friend', 'Inner'),
            ('Friend', 'Caregiver', 'Bidirectional', True, 'Caretaker', 'Universe'),
            ('Friend', 'Pen pals', 'Unidirectional', True, 'Pen pals', 'Universe'),
            ('Friend', 'Affinity', 'Unidirectional', False, '', 'Outer'),
            ('Friend', 'Fictive kinship', 'Unidirectional', True, '', 'Outer'),
            ('Friend', 'Ex-Girlfriend', 'Unidirectional', True, '', 'Outer'),
            ('Friend', 'Ex-Boyfriend', 'Unidirectional', True, '', 'Outer'),
            ('Friend', 'Roomate', 'Unidirectional', True, 'Roommate', 'Outer'),
            ('Friend', 'Flatmate', 'Unidirectional', True, 'Flatmate', 'Outer'),
            ('Friend', 'Frenemy', 'Unidirectional', False, 'N/A', 'Outer'),
            ('Friend', 'Fling', 'Unidirectional', False, 'N/A', 'Outer'),
            ('Friend', 'College mate', 'Unidirectional', True, 'College mate', 'Inner'),
            ('Friend', 'School mate', 'Unidirectional', True, 'School mate', 'Outer'),
            ('Friend', 'Room mate', 'Unidirectional', True, 'Room mate', 'Inner'),

            # ============ PROFESSIONAL (relation_id = 3) ============
            ('Professional', 'Employee', 'Bidirectional', True, 'Employer', 'Outer'),
            ('Professional', 'Employer', 'Bidirectional', True, 'Employee', 'Outer'),
            ('Professional', 'Neighbour', 'Unidirectional', True, 'Neighbour', 'Outer'),
            ('Professional', 'Mentor', 'Bidirectional', True, 'Mentee', 'Universe'),
            ('Professional', 'Mentee', 'Bidirectional', True, 'Mentor', 'Universe'),
            ('Professional', 'co worker', 'Unidirectional', True, 'co worker', 'Universe'),
            ('Professional', 'team mate', 'Unidirectional', True, 'team mate', 'Outer'),
            ('Professional', 'Boss', 'Bidirectional', True, 'subordinate', 'Outer'),
            ('Professional', 'manager', 'Bidirectional', True, 'Team member', 'Outer'),
            ('Professional', 'Office mate', 'Unidirectional', True, 'Office mate', 'Outer'),
            ('Professional', 'Batch Mate', 'Unidirectional', True, 'Batch Mate', 'Outer'),
            ('Professional', 'Fan', 'Unidirectional', False, 'N/A', 'Outer'),
            ('Professional', 'Only Fan', 'Unidirectional', False, '', 'Outer'),
            ('Professional', 'SuperFan', 'Unidirectional', False, 'N/A', 'Outer'),
            ('Professional', 'Follower', 'Unidirectional', False, 'N/A', 'Outer'),
            ('Professional', 'Admirer', 'Unidirectional', False, 'N/A', 'Outer'),
            ('Professional', 'Coworker', 'Unidirectional', True, 'coworker', 'Universe'),
            ('Professional', 'Business partner', 'Bidirectional', True, 'business partner', 'Outer'),
            ('Professional', 'Service provider', 'Bidirectional', True, 'Client', 'Outer'),
            ('Professional', 'Investor', 'Bidirectional', True, 'Entrepreneur', 'Outer'),
            ('Professional', 'Union representative', 'Bidirectional', True, 'Union Member', 'Outer'),
            ('Professional', 'Neighbors', 'Unidirectional', True, 'Neighbour', 'Outer'),
            ('Professional', 'Teacher', 'Bidirectional', True, 'Student', 'Inner'),
            ('Professional', 'penpal', 'Unidirectional', True, 'penpal', 'Outer'),
            ('Professional', 'Travel Buddies', 'Unidirectional', True, 'Travel Buddies', 'Outer'),
            ('Professional', 'Fitness Buddies', 'Unidirectional', True, 'Fitness Buddies', 'Outer'),
        ]

        # Import subrelations
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for rel_name, sub_name, direction, approval, reverse, circle in subrelations_data:
            try:
                relation_obj = relations_map.get(rel_name)
                if not relation_obj:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Relation "{rel_name}" not found in map')
                    )
                    error_count += 1
                    continue

                # Use update_or_create to handle existing records
                subrelation, created = SubRelation.objects.update_or_create(
                    relation=relation_obj,
                    sub_relation_name=sub_name,
                    defaults={
                        'directionality': direction,
                        'approval_required': approval,
                        'reverse_connection': reverse,
                        'default_circle': circle
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created: {rel_name} -> {sub_name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'  ↻ Updated: {rel_name} -> {sub_name}')
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error with {rel_name} -> {sub_name}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Import completed!'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count} subrelations'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {updated_count} subrelations'))
        
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'  Errors: {error_count}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal subrelations in database: {SubRelation.objects.count()}')
        )
        self.stdout.write('='*60)