"""
Django Management Command to Verify Imported Relations
Place this file at: connection/management/commands/verify_relations.py
Run with: python manage.py verify_relations
"""

from django.core.management.base import BaseCommand
from connection.models import Relation, SubRelation
from collections import Counter


class Command(BaseCommand):
    help = 'Verify imported relations and subrelations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Verifying Relations Data...\n'))
        
        # Check Relations
        self.stdout.write(self.style.SUCCESS('=== RELATIONS ==='))
        relations = Relation.objects.all()
        
        if relations.count() != 3:
            self.stdout.write(
                self.style.ERROR(f'⚠ Expected 3 relations, found {relations.count()}')
            )
        
        for rel in relations:
            subrel_count = SubRelation.objects.filter(relation=rel).count()
            self.stdout.write(
                f'  ID: {rel.id} | Name: {rel.name:15} | Subrelations: {subrel_count}'
            )
        
        # Check SubRelations
        self.stdout.write(f'\n{self.style.SUCCESS("=== SUBRELATIONS ===")}')
        total_subrelations = SubRelation.objects.count()
        self.stdout.write(f'Total subrelations: {total_subrelations}\n')
        
        # Group by relation
        for rel in relations:
            subrels = SubRelation.objects.filter(relation=rel)
            self.stdout.write(f'\n{rel.name} ({subrels.count()} subrelations):')
            
            for subrel in subrels[:5]:  # Show first 5
                self.stdout.write(
                    f'  • {subrel.sub_relation_name:25} | '
                    f'{subrel.directionality:15} | '
                    f'Circle: {subrel.default_circle:8} | '
                    f'Reverse: {subrel.reverse_connection[:20]}'
                )
            
            if subrels.count() > 5:
                self.stdout.write(f'  ... and {subrels.count() - 5} more')
        
        # Check for issues
        self.stdout.write(f'\n{self.style.WARNING("=== VALIDATION CHECKS ===")}')
        
        # 1. Check for empty default_circle
        empty_circles = SubRelation.objects.filter(default_circle='')
        if empty_circles.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ {empty_circles.count()} subrelations have empty default_circle:'
                )
            )
            for subrel in empty_circles:
                self.stdout.write(f'  • {subrel.relation.name} -> {subrel.sub_relation_name}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ All subrelations have default_circle set'))
        
        # 2. Check for empty reverse_connection
        empty_reverse = SubRelation.objects.filter(reverse_connection='')
        if empty_reverse.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠ {empty_reverse.count()} subrelations have empty reverse_connection:'
                )
            )
            for subrel in empty_reverse:
                self.stdout.write(f'  • {subrel.relation.name} -> {subrel.sub_relation_name}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ All subrelations have reverse_connection'))
        
        # 3. Check circle distribution
        self.stdout.write(f'\n{self.style.SUCCESS("=== CIRCLE DISTRIBUTION ===")}')
        circle_counts = SubRelation.objects.values_list('default_circle', flat=True)
        circle_stats = Counter(circle_counts)
        
        for circle, count in circle_stats.items():
            circle_name = circle if circle else '(empty)'
            self.stdout.write(f'  {circle_name:15} : {count:3} subrelations')
        
        # 4. Check directionality distribution
        self.stdout.write(f'\n{self.style.SUCCESS("=== DIRECTIONALITY DISTRIBUTION ===")}')
        direction_counts = SubRelation.objects.values_list('directionality', flat=True)
        direction_stats = Counter(direction_counts)
        
        for direction, count in direction_stats.items():
            self.stdout.write(f'  {direction:15} : {count:3} subrelations')
        
        # 5. Sample test queries
        self.stdout.write(f'\n{self.style.SUCCESS("=== SAMPLE TEST QUERIES ===")}')
        
        test_cases = [
            'father',
            'mother',
            'friend',
            'Boss',
            'Employee',
        ]
        
        for test_name in test_cases:
            try:
                subrel = SubRelation.objects.get(sub_relation_name__iexact=test_name)
                self.stdout.write(
                    f'  ✓ "{test_name:15}" -> '
                    f'Circle: {subrel.default_circle:8} | '
                    f'Reverse: {subrel.reverse_connection:15} | '
                    f'{subrel.directionality}'
                )
            except SubRelation.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ "{test_name}" NOT FOUND')
                )
            except SubRelation.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ "{test_name}" MULTIPLE ENTRIES FOUND (duplicate!)')
                )
        
        # Final summary
        self.stdout.write(f'\n{"="*60}')
        if empty_circles.exists() or empty_reverse.exists():
            self.stdout.write(
                self.style.WARNING(
                    '⚠ Some issues found. Review warnings above.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ All checks passed! Database is ready for use.'
                )
            )
        self.stdout.write('='*60)