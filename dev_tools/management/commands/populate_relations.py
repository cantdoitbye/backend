from django.core.management.base import BaseCommand
from connection.models import Relation, SubRelation

class Command(BaseCommand):
    help = 'Populates the Relation and SubRelation models with predefined data'

    def handle(self, *args, **kwargs):
        data = [
            {
                "relation": "Relatives",
                "sub_relations": [
                    {"sub_relation_name": "father", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Child"},
                    {"sub_relation_name": "son", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Parent"},
                    {"sub_relation_name": "husband", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Wife"},
                    {"sub_relation_name": "brother", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Sibling"},
                    {"sub_relation_name": "grandfather", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Grandchild"},
                    {"sub_relation_name": "grandson", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Grandparent"},
                    {"sub_relation_name": "uncle", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Nephew/Niece"},
                    {"sub_relation_name": "nephew/niece", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Uncle/Aunt"},
                    {"sub_relation_name": "cousin", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": "Cousin"},
                    {"sub_relation_name": "mother", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Child"},
                    {"sub_relation_name": "daughter", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Parent"},
                    {"sub_relation_name": "wife", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Husband"},
                    {"sub_relation_name": "sister", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Sibling"},
                    {"sub_relation_name": "grandmother", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Grandchild"},
                    {"sub_relation_name": "granddaughter", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Grandparent"},
                    {"sub_relation_name": "aunt", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Nephew/Niece"},
                    {"sub_relation_name": "niece", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Uncle/Aunt"},
                    {"sub_relation_name": "parent", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Child"},
                    {"sub_relation_name": "child", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Parent"},
                    {"sub_relation_name": "spouse", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": "Spouse"},
                    {"sub_relation_name": "sibling", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": "Sibling"},
                    {"sub_relation_name": "grandparents", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Grandchild"},
                    {"sub_relation_name": "grandchild", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Grandparents"},
                    {"sub_relation_name": "parent's sibling", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "sibling's child"},
                    {"sub_relation_name": "sibling's child", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "parent's sibling"},
                    {"sub_relation_name": "aunt's/uncle's child", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Cousin"}
                ]
            },
            {
                "relation": "Friend",
                "sub_relations": [
                    {"sub_relation_name": "friend", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": "Friend"},
                    {"sub_relation_name": "Caregiver", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Caretaker"},
                    {"sub_relation_name": "Pen pals", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": "Pen pals"},
                    {"sub_relation_name": "Affinity", "directionality": "Unidirectional", "approval_required": False, "reverse_connection": ""},
                    {"sub_relation_name": "Fictive kinship", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": ""},
                    {"sub_relation_name": "Ex-Girlfriend", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": ""},
                    {"sub_relation_name": "Ex-Boyfriend", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": ""}
                ]
            },
            {
                "relation": "Professional",
                "sub_relations": [
                    {"sub_relation_name": "Employee", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Employer"},
                    {"sub_relation_name": "Employer", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Employee"},
                    {"sub_relation_name": "Neighbour", "directionality": "Unidirectional", "approval_required": True, "reverse_connection": "Neighbour"},
                    {"sub_relation_name": "Colleague", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Colleague"},
                    {"sub_relation_name": "Mentor", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Mentee"},
                    {"sub_relation_name": "Mentee", "directionality": "Bidirectional", "approval_required": True, "reverse_connection": "Mentor"}
                ]
            }
        ]

        for relation_data in data:
            relation, created = Relation.objects.get_or_create(name=relation_data["relation"])
            for sub_relation_data in relation_data["sub_relations"]:
                SubRelation.objects.get_or_create(
                    relation=relation,
                    sub_relation_name=sub_relation_data["sub_relation_name"],
                    defaults={
                        "directionality": sub_relation_data["directionality"],
                        "approval_required": sub_relation_data["approval_required"],
                        "reverse_connection": sub_relation_data.get("reverse_connection", "")
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated the Relation and SubRelation models.'))
