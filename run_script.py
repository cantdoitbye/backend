import pandas as pd
import json

def process_section(df, name_col_index, weightage_col_indices):
    # Extract the headers from the first row
    headers = df.iloc[0, weightage_col_indices].tolist()

    # Extract the relevant columns (Name of Vibe and weightages)
    columns_to_extract = [name_col_index] + weightage_col_indices
    section_df = df.iloc[1:, columns_to_extract].dropna(how='all').reset_index(drop=True)
    
    # Fill NaN values with 0
    section_df = section_df.fillna(0)

    # Create a list of dictionaries for each row
    corrected_entries = []
    for _, row in section_df.iterrows():
        entry = {"Name of Vibe": row[0]}  # First column is "Name of Vibe"
        for i, col in enumerate(weightage_col_indices):
            entry[headers[i]] = row[i + 1]  # Map weightage columns to their respective headers
        corrected_entries.append(entry)
    
    return corrected_entries

def process_all_sections(df):
    # Define the column indices for each section
    sections_config = {
        'Individual': {
            'name_col_index': 0,  # Name of Vibe in column A
            'weightage_col_indices': [1, 2, 3, 4]  
        },
        'Community': {
            'name_col_index': 6,  # Name of Vibe in column F
            'weightage_col_indices': [7, 8, 9, 10]  
        },
        'Brand': {
            'name_col_index': 12,  # Name of Vibe in column K
            'weightage_col_indices': [13, 14, 15, 16]  
        },
        'Product': {
            'name_col_index': 18,  # Name of Vibe in column P
            'weightage_col_indices': [19, 20, 21, 22]  
        },
        'Service': {
            'name_col_index': 24,  # Name of Vibe in column U
            'weightage_col_indices': [25, 26, 27, 28]  
        }
    }

    structured_data = {}
    
    # Process each section
    for section, config in sections_config.items():
        structured_data[section] = process_section(df, config['name_col_index'], config['weightage_col_indices'])
    
    return structured_data

def save_to_json(data, output_file):
    # Save the structured data to a JSON file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"JSON data saved to {output_file}")

# Load the Excel file
file_path = 'Sheet.xlsx'  # Replace with your actual file path
df = pd.read_excel(file_path)

# Process all sections
structured_data = process_all_sections(df)

# Save the result to a JSON file
output_file_path = 'structured_vibe_weights_all_sections.json'
save_to_json(structured_data, output_file_path)
