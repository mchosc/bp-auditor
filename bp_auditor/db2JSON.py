#!/usr/bin/env python3

import json
from datetime import datetime
from db import read_all_reports_fromDB  # Adjust the import path as needed

def main():
    db_location = 'reports.db'  # Path to your SQLite database
    # Set to the first day of the current month for the timestamp
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Fetch data from the database
    data = read_all_reports_fromDB(db_location, first_of_month)

    # Convert to JSON
    json_data = json.dumps(data, indent=4)
    print(json_data)

    # Optionally, write to a JSON file
    with open('output_reports.json', 'w') as f:
        f.write(json_data)

if __name__ == "__main__":
    main()
