################
# Generates some stats based on the prompts.json file
################

import json
from datetime import datetime
from collections import defaultdict

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def get_month_counts(data):
    month_counts = defaultdict(int)
    for entry in data:
        date = datetime.strptime(entry['date'], '%Y-%m-%dT%H:%M:%S.%f')
        month_key = f"{date.year}-{date.month:02d}"
        month_counts[month_key] += 1
    return month_counts

def get_average_entries_per_week_and_day(data):
    start_date = datetime.strptime(data[0]['date'], '%Y-%m-%dT%H:%M:%S.%f')
    end_date = datetime.strptime(data[-1]['date'], '%Y-%m-%dT%H:%M:%S.%f')
    total_days = (end_date - start_date).days + 1
    total_weeks = total_days // 7
    total_entries = len(data)
    avg_entries_per_week = total_entries / total_weeks
    avg_entries_per_day = total_entries / total_days
    return avg_entries_per_week, avg_entries_per_day

def main():
    file_path = 'db/prompts.json'
    data = read_json_file(file_path)
    
    month_counts = get_month_counts(data)
    print("Entries per month:")
    for month, count in month_counts.items():
        print(f"{month}: {count}")
    
    avg_entries_per_week, avg_entries_per_day = get_average_entries_per_week_and_day(data)
    print(f"\nAverage entries per week: {avg_entries_per_week:.2f}")
    print(f"Average entries per day: {avg_entries_per_day:.2f}")

if __name__ == '__main__':
    main()