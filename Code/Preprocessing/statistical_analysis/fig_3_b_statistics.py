import os
import json
from collections import defaultdict
import pandas as pd
from tqdm import tqdm

# 1. Define the theme and corresponding English abbreviations
THEME_MAPPING = {
    "Charging Functionality and Reliability": "CR",
    "Charging Performance": "CP",
    "Location and Availability": "LA",
    "Pricing and Payment": "PP",
    "Environment and Service Experience": "ES"
}

# 2. Define emotion classification (excluding 'null')

SENTIMENTS = ["Positive", "Neutral", "Negative"]
SENTIMENT_EN = ["Positive", "Neutral", "Negative"]  
# 3. Define year range and regional files
YEARS = range(2015, 2025)
REGION_FILES = {
    'China': 'Data\\interim\\LLM_result_processing\\china_comments.json',
    'USA': 'Data\\interim\\LLM_result_processing\\usa_comments.json',
    'Europe': 'Data\\interim\\LLM_result_processing\\europe_comments.json'
}


def process_region_data(region_name, file_path):

    # 1. Initialize counter
    theme_sentiment_counts = defaultdict(lambda: defaultdict(int))
    
    # 2. Read and analyze data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for comment in tqdm(data['comment_list']):
            try:
                year = int(comment['date'].split('-')[0])
                if year not in YEARS:
                    continue
                
            
                for theme_ch, theme_en in THEME_MAPPING.items():
                    sentiment = comment['sentiment'][theme_ch]
                    if sentiment in SENTIMENTS:  
                        theme_sentiment_counts[theme_en][sentiment] += 1
            except:
                continue

    # 3. Calculate the proportion (grouped by theme)
    region_data = {'Theme': [], 'Positive': [], 'Neutral': [], 'Negative': []}
    
    for theme_en in THEME_MAPPING.values():
        total = sum(theme_sentiment_counts[theme_en].values())
        region_data['Theme'].append(theme_en)
        
        # Calculate the proportion of each emotion (set to 0 if there is no data)
        for sentiment_en, sentiment_ch in zip(SENTIMENT_EN, SENTIMENTS):
            count = theme_sentiment_counts[theme_en][sentiment_ch]
            percentage = round((count / total * 100) if total > 0 else 0.0, 1)
            region_data[sentiment_en].append(percentage)
    
    return region_data


def main():
    all_region_data = {}
    
    # 1. Handle each region
    for region_name, file_path in REGION_FILES.items():
        region_data = process_region_data(region_name, file_path)
        all_region_data[f"{region_name.lower()}_data"] = region_data
        
        
        print(f"\n{region_name} result:")
        print(pd.DataFrame(region_data).to_string(index=False))
    
    # 2. Save the Results

    with open('Data\\interim\\fig_3_b\\fig_3_b.json', 'w', encoding='utf-8') as f:
        json.dump(all_region_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()