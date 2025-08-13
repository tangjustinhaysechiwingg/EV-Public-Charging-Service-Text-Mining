import json
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm

def parse_date(date_str):
    """Flexible date parser that handles multiple formats"""
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",  # USA/Europe format
        "%Y-%m-%d %H:%M:%S",    # China format 1
        "%Y-%m-%d %H:%M",        # China format 2
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unparseable date format: {date_str}")

def load_and_process_data(filepath, region_name):
    """Load and process data from JSON file"""
    print(f"\nProcessing {region_name} data...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    yearly_stats = defaultdict(lambda: {'Positive': 0, 'Negative': 0, 'Neutral': 0})
    total_comments = 0
    
    for comment in tqdm(data['comment_list'], desc=f"Processing {region_name}"):
        try:
            date = parse_date(comment['date'])
            year = date.year
            
            if 2015 <= year <= 2024:
                final_eval = comment['sentiment']['Overall sentiment']
                if final_eval != 'null':  
                    yearly_stats[year][final_eval] += 1
                    total_comments += 1
        except Exception as e:
            continue
    
    # Convert defaultdict to regular dict for JSON serialization
    yearly_stats = {k: dict(v) for k, v in yearly_stats.items()}
    
    return {
        'region': region_name,
        'yearly_stats': yearly_stats,
        'total_comments': total_comments
    }

def save_processed_data(region_data_list, output_path):
    """Save all processed data to a JSON file"""
    results = {}
    
    for region_data in region_data_list:
        region_name = region_data['region']
        yearly_stats = region_data['yearly_stats']
        total_comments = region_data['total_comments']
        
        # Prepare data for saving
        years = sorted(y for y in yearly_stats.keys() if 2015 <= y <= 2024)
        results[region_name] = {
            'years': years,
            'counts': {
                'positive': [yearly_stats[y]['Positive'] for y in years],
                'neutral': [yearly_stats[y]['Neutral'] for y in years],
                'negative': [yearly_stats[y]['Negative'] for y in years],
                'total': [sum(yearly_stats[y].values()) for y in years]
            },
            'percentages': {
                'positive': [p/t*100 if t > 0 else 0 for p, t in 
                           zip([yearly_stats[y]['Positive'] for y in years],
                               [sum(yearly_stats[y].values()) for y in years])],
                'neutral': [n/t*100 if t > 0 else 0 for n, t in 
                          zip([yearly_stats[y]['Neutral'] for y in years],
                              [sum(yearly_stats[y].values()) for y in years])],
                'negative': [ng/t*100 if t > 0 else 0 for ng, t in 
                           zip([yearly_stats[y]['Negative'] for y in years],
                               [sum(yearly_stats[y].values()) for y in years])]
            },
            'metadata': {
                'total_comments': total_comments,
                'comment_years': {str(y): sum(yearly_stats[y].values()) for y in yearly_stats}
            }
        }
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nSuccessfully saved processed data to {output_path}")
    print("File structure includes:")
    print("- Years analyzed")
    print("- Raw counts (positive, neutral, negative, total)")
    print("- Percentage values")
    print("- Metadata (total comments, comments per year)")

# Process data for all regions
regions = [
    ('Data\\interim\\LLM_result_processing\\usa_comments.json', "USA"),
    ('Data\\interim\\LLM_result_processing\\europe_comments.json', "Europe"),
    ('Data\\interim\\LLM_result_processing\\china_comments.json', "China")
]

region_data_list = []
for filepath, region_name in regions:
    region_data = load_and_process_data(filepath, region_name)
    region_data_list.append(region_data)

# Save all processed data
output_path = 'Data\\interim\\fig_2_a\\fig_2_a.json'
save_processed_data(region_data_list, output_path)