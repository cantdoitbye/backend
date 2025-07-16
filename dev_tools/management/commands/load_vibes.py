import json
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from vibe_manager.models import IndividualVibe, CommunityVibe, BrandVibe, ServiceVibe

class Command(BaseCommand):
    help = 'Load vibes data from a JSON file and populate the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file containing the vibe data')

    # Function to normalize and compare vibe names (case insensitive)
    def normalize_vibe_name(self, vibe_name):
        return vibe_name.strip().lower()

    # Function to check for duplicate entries by name (case insensitive) for a given model
    def is_duplicate_vibe(self, vibe_name, model_class):
        normalized_name = self.normalize_vibe_name(vibe_name)
        return model_class.objects.filter(name_of_vibe__iexact=normalized_name).exists()

    # Function to process individual vibes
    def process_individual_vibes(self, individual_data):
        print("Starting to process Individual Vibes...")
        for vibe_data in individual_data:
            normalized_name = self.normalize_vibe_name(vibe_data['Name of Vibe'])
            if not self.is_duplicate_vibe(normalized_name, IndividualVibe):
                try:
                    print(f"Processing Individual Vibe: {vibe_data['Name of Vibe']}")
                    vibe = IndividualVibe(
                        name_of_vibe=normalized_name,
                        description=vibe_data.get('description', ''),
                        weightage_iaq=vibe_data['Weightage on IAQ'],
                        weightage_iiq=vibe_data['Weightage on IIQ'],
                        weightage_ihq=vibe_data['Weightage on IHQ'],
                        weightage_isq=vibe_data['Weightage on ISQ'],
                    )
                    vibe.save()
                    print(f"Successfully saved Individual Vibe: {vibe_data['Name of Vibe']}")
                except IntegrityError:
                    print(f"Failed to save Individual Vibe: {vibe_data['Name of Vibe']} (Duplicate)")
            else:
                print(f"Duplicate individual vibe found and skipped: {vibe_data['Name of Vibe']}")
        print("Finished processing Individual Vibes.\n")

    # Function to process community vibes
    def process_community_vibes(self, community_data):
        print("Starting to process Community Vibes...")
        for vibe_data in community_data:
            normalized_name = self.normalize_vibe_name(vibe_data['Name of Vibe'])
            if not self.is_duplicate_vibe(normalized_name, CommunityVibe):
                try:
                    print(f"Processing Community Vibe: {vibe_data['Name of Vibe']}")
                    vibe = CommunityVibe(
                        name_of_vibe=normalized_name,
                        description=vibe_data.get('description', ''),
                        weightage_ceq=vibe_data['Weightage on CEQ'],
                        weightage_csq=vibe_data['Weightage on CSQ'],
                        weightage_cgq=vibe_data['Weightage on CGQ'],
                        weightage_ciq=vibe_data['Weightage on CIQ'],
                    )
                    vibe.save()
                    print(f"Successfully saved Community Vibe: {vibe_data['Name of Vibe']}")
                except IntegrityError:
                    print(f"Failed to save Community Vibe: {vibe_data['Name of Vibe']} (Duplicate)")
            else:
                print(f"Duplicate community vibe found and skipped: {vibe_data['Name of Vibe']}")
        print("Finished processing Community Vibes.\n")

    # Function to process brand vibes
    def process_brand_vibes(self, brand_data):
        print("Starting to process Brand Vibes...")
        for vibe_data in brand_data:
            normalized_name = self.normalize_vibe_name(vibe_data['Name of Vibe'])
            if not self.is_duplicate_vibe(normalized_name, BrandVibe):
                try:
                    print(f"Processing Brand Vibe: {vibe_data['Name of Vibe']}")
                    vibe = BrandVibe(
                        name_of_vibe=normalized_name,
                        description=vibe_data.get('description', ''),
                        weightage_bqq=vibe_data['Weightage on BQQ'],
                        weightage_brq=vibe_data['Weightage on BRQ'],
                        weightage_biq=vibe_data['Weightage on BIQ'],
                        weightage_bsq=vibe_data['Weightage on BSQ'],
                    )
                    vibe.save()
                    print(f"Successfully saved Brand Vibe: {vibe_data['Name of Vibe']}")
                except IntegrityError:
                    print(f"Failed to save Brand Vibe: {vibe_data['Name of Vibe']} (Duplicate)")
            else:
                print(f"Duplicate brand vibe found and skipped: {vibe_data['Name of Vibe']}")
        print("Finished processing Brand Vibes.\n")

    # Function to process service vibes
    def process_service_vibes(self, service_data):
        print("Starting to process Service Vibes...")
        for vibe_data in service_data:
            normalized_name = self.normalize_vibe_name(vibe_data['Name of Vibe'])
            if not self.is_duplicate_vibe(normalized_name, ServiceVibe):
                try:
                    print(f"Processing Service Vibe: {vibe_data['Name of Vibe']}")
                    vibe = ServiceVibe(
                        name_of_vibe=normalized_name,
                        description=vibe_data.get('description', ''),
                        weightage_seq=vibe_data['Weightage on SEQ'],
                        weightage_srq=vibe_data['Weightage on SRQ'],
                        weightage_ssq=vibe_data['Weightage on SSQ'],
                        weightage_suq=vibe_data['Weightage on SUQ'],
                    )
                    vibe.save()
                    print(f"Successfully saved Service Vibe: {vibe_data['Name of Vibe']}")
                except IntegrityError:
                    print(f"Failed to save Service Vibe: {vibe_data['Name of Vibe']} (Duplicate)")
            else:
                print(f"Duplicate service vibe found and skipped: {vibe_data['Name of Vibe']}")
        print("Finished processing Service Vibes.\n")

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        # Load JSON data from file
        print(f"Loading data from {json_file}...")
        with open(json_file, 'r') as file:
            data = json.load(file)
        print("Data loaded successfully.\n")

        # Process each category in the JSON
        if 'Individual' in data:
            self.process_individual_vibes(data['Individual'])

        if 'Community' in data:
            self.process_community_vibes(data['Community'])

        if 'Brand' in data:
            self.process_brand_vibes(data['Brand'])

        if 'Service' in data:
            self.process_service_vibes(data['Service'])

        print("All vibes have been processed and saved to the database.\n")
