import json
import datetime

def convert_date_format(date_str):
    # Handle NaN values
    if date_str == 'NaN':
        return 'NaN'

    try:
        # Parse the input date string
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        # Convert the date object to the desired format
        formatted_date = date_obj.strftime('%m/%d/%y, %I:%M:%S %p')
        return formatted_date
    except ValueError:
        return 'Invalid date format'

# Read input JSON file
input_file_path = 'issueData.json'  # Change this to your input file path
output_file_path = 'ModifiedIssueData.json'  # Change this to your output file path

# Load data from input JSON file
with open(input_file_path, 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Convert date formats in the JSON data
for key, entry in json_data.items():
    if "created_at" in entry:
        entry["created_at"] = convert_date_format(entry["created_at"])
    if "closed_at" in entry:
        entry["closed_at"] = convert_date_format(entry["closed_at"])
    if "date" in entry:
        entry["date"] = convert_date_format(entry["date"])

# Write modified JSON data to output file
with open(output_file_path, 'w', encoding='utf-8') as file:
    json.dump(json_data, file, indent=4)

print("Conversion completed. Output written to", output_file_path)
