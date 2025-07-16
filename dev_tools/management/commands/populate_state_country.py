import json
from django.core.management.base import BaseCommand
# Update 'myapp' with your actual Django app name
from auth_manager.models import CountryInfo, StateInfo, CityInfo


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

        # Populate StateInfo and CityInfo tables
        for state_name, city_list in data.items():
            # Create state linked to India
            state_obj, _ = StateInfo.objects.get_or_create(
                state_name=state_name, country=country)

            # Create cities linked to the state
            for city_name in city_list:
                CityInfo.objects.get_or_create(
                    city_name=city_name, state=state_obj)

        self.stdout.write(self.style.SUCCESS(
            "✅ StateInfo and CityInfo tables populated successfully!"))
