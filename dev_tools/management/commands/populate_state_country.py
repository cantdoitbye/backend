import json
from django.core.management.base import BaseCommand
from django.db import transaction
from auth_manager.models import CountryInfo, StateInfo, CityInfo
from tqdm import tqdm


class Command(BaseCommand):
    help = "Populate country, state, and city tables from a JSON file"

    def handle(self, *args, **kwargs):
        json_file_path = "Indian_Cities_In_States_JSON"  # Update the path if needed

        # Load JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            # Expected structure: { "State Name": ["City1", "City2", ...] }
            data = json.load(file)

        # Ensure "India" is in the CountryInfo table
        country, _ = CountryInfo.objects.get_or_create(country_name="India")

        self.stdout.write(self.style.SUCCESS(
            "✅ 'India' added to CountryInfo table."))

        # Use bulk operations for better performance
        with transaction.atomic():
            # First, create all states in bulk
            states_to_create = []
            existing_states = set(StateInfo.objects.filter(country=country).values_list('state_name', flat=True))
            
            for state_name in data.keys():
                if state_name not in existing_states:
                    states_to_create.append(StateInfo(state_name=state_name, country=country))
            
            if states_to_create:
                StateInfo.objects.bulk_create(states_to_create, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(f"✅ Created {len(states_to_create)} states"))

            # Get all state objects for mapping
            state_objects = {state.state_name: state for state in StateInfo.objects.filter(country=country)}

            # Now create cities in bulk for each state
            total_cities = sum(len(cities) for cities in data.values())
            self.stdout.write(f"Processing {total_cities} cities...")
            
            cities_to_create = []
            batch_size = 1000
            
            for state_name, city_list in tqdm(data.items(), desc="Processing states"):
                state_obj = state_objects[state_name]
                
                # Get existing cities for this state
                existing_cities = set(CityInfo.objects.filter(state=state_obj).values_list('city_name', flat=True))
                
                # Add new cities to batch
                for city_name in city_list:
                    if city_name not in existing_cities:
                        cities_to_create.append(CityInfo(city_name=city_name, state=state_obj))
                
                # Create cities in batches to avoid memory issues
                if len(cities_to_create) >= batch_size:
                    CityInfo.objects.bulk_create(cities_to_create, ignore_conflicts=True)
                    self.stdout.write(f"✅ Created batch of {len(cities_to_create)} cities")
                    cities_to_create = []
            
            # Create remaining cities
            if cities_to_create:
                CityInfo.objects.bulk_create(cities_to_create, ignore_conflicts=True)
                self.stdout.write(f"✅ Created final batch of {len(cities_to_create)} cities")

        self.stdout.write(self.style.SUCCESS(
            "✅ StateInfo and CityInfo tables populated successfully!"))
