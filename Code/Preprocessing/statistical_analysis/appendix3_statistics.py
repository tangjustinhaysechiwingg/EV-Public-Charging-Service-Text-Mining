import json
import os
from collections import defaultdict
from tqdm import tqdm
import re

# Region files
region_files = {
    'China': 'processing_output\\LLM_result\\china_comments.json',
    'USA': 'processing_output\\LLM_result\\usa_comments.json',
    'Europe': 'processing_output\\LLM_result\\europe_comments.json'
}
region_files = {
    'China': 'Data\\interim\\LLM_result_processing\\china_comments.json',
    'USA': 'Data\\interim\\LLM_result_processing\\usa_comments.json',
    'Europe': 'Data\\interim\\LLM_result_processing\\europe_comments.json'
}
# Themes
themes = [
    "Charging Functionality and Reliability",
    "Location and Availability",
    "Pricing and Payment",
]

def is_chinese(keyword):
    return bool(re.search('[\u4e00-\u9fff]', keyword))

def process_region(region_name, filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    theme_keywords = {theme: defaultdict(int) for theme in themes}
    
    for comment in tqdm(data['comment_list']):
        sentiment = comment['sentiment']
        keywords = comment['keywords']
        
        for theme in themes:
            if sentiment.get(theme) == "Negative":
                for keyword in keywords:
                    if not is_chinese(keyword):
                        theme_keywords[theme][keyword] += 1
    
    # Convert defaultdict to regular dict for JSON serialization
    return {theme: dict(keywords) for theme, keywords in theme_keywords.items()}

# Process all regions and save to JSON
all_region_data = {}
for region_name, filepath in region_files.items():
    if os.path.exists(filepath):
        all_region_data[region_name] = process_region(region_name, filepath)
    else:
        print(f'File not found: {filepath}')

# Save the processed data to JSON
os.makedirs('Data\\interim\\appendix3', exist_ok=True)
with open('Data\\interim\\appendix3\\wordcloud_keywords.json', 'w', encoding='utf-8') as f:
    json.dump(all_region_data, f, ensure_ascii=False, indent=2)

print('Word cloud data saved to JSON file!')