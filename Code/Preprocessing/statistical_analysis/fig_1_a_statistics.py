import json
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

# Configuration for each region
regions = {
    'China': {
        'filename': 'Data\\interim\\LLM_result_processing\\china_comments.json',
        'date_format': "%Y-%m-%d %H:%M",
        'date_format1': "%Y-%m-%d %H:%M:%S",
        'date_format2': "%Y-%m-%d",
        'color': '#1f77b4'
    },
    'USA': {
        'filename': 'Data\\interim\\LLM_result_processing\\usa_comments.json',
        'date_format': "%Y-%m-%dT%H:%M:%SZ",
        'color': '#2ca02c'
    },
    'Europe': {
        'filename': 'Data\\interim\\LLM_result_processing\\europe_comments.json',
        'date_format': "%Y-%m-%dT%H:%M:%SZ",
        'color': '#d62728'
    }
}

# Store data from various regions for output purposes
region_data = {}

def process_region_data(region_config):
    """Process data for a single region and return counts and total"""
    with open(region_config['filename'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    year_month_counts = defaultdict(lambda: defaultdict(int))
    total_comments = 0
    
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, region_config['date_format'])
        except ValueError:
            try:
                return datetime.strptime(date_str, region_config['date_format1'])
            except ValueError:
                return datetime.strptime(date_str, region_config['date_format2'])
    
    for comment in tqdm(data["comment_list"]):
        dt = parse_date(comment["date"])
        if dt is None:
            continue
        year, month = dt.year, dt.month
        if 2015 <= year <= 2024:
            year_month_counts[year][month] += 1
            total_comments += 1    
            
    
    years = sorted(year_month_counts.keys())
    comment_counts = [sum(year_month_counts[year].values()) for year in years]
    
    # Calculate growth rates
    growth_rates = []
    for i in range(1, len(comment_counts)):
        if comment_counts[i-1] > 0:  # Avoid division by zero
            growth = ((comment_counts[i] - comment_counts[i-1]) / comment_counts[i-1]) * 100
            growth_rates.append(growth)
        else:
            growth_rates.append(0)
    
    return years, comment_counts, growth_rates, total_comments
# Process and plot each region
for i, (region, config) in enumerate(regions.items()):
    years, counts, rates, total = process_region_data(config)
    
    region_data[region] = {
        'years': years,
        'counts': counts,
        'rates': rates,
        'total': total
    }
    
json_filename = "Data\\interim\\fig_1_a\\fig_1_a.json"

# JSON
with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump(region_data, f, ensure_ascii=False, indent=2)