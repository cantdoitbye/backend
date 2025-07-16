import pandas as pd
import json

def process_interests(df):
    structured_data = {}
    
    for _, row in df.iterrows():
        category = row['Category']
        # Split the comma-separated sub-interests into a list
        sub_interests = [sub.strip() for sub in row['Sub-Interests'].split(',')]
        structured_data[category] = sub_interests
    
    return structured_data

def save_to_json(data, output_file):
    # Save the structured data to a JSON file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"JSON data saved to {output_file}")

# Load the Excel file
file_path = 'Interest_list.xlsx'  # Replace with your actual file path
df = pd.read_excel(file_path)

# Process all sections
structured_data = process_interests(df)

# Save the result to a JSON file
output_file_path = 'structured_interests.json'
save_to_json(structured_data, output_file_path)
