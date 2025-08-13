import json
import os
from glob import glob
from tqdm import tqdm
import re
import csv

def transform_sentiment(sentiment_str):
    if not sentiment_str:
        return None
    
    parts = sentiment_str.split(',')
    if len(parts) < 2:
        return None
    
    overall_sentiment_num = parts[0].strip()
    if overall_sentiment_num != 'Negative'or overall_sentiment_num == 'Neutral':
        match = re.search(r"\d+", overall_sentiment_num)  
        if match:
            overall_sentiment_num = match.group()


    category_num = parts[1].strip()
    keywords = [k.strip() for k in parts[2:] if k.strip()] if len(parts) > 2 else []
    
    # Map overall sentiment number to text
    if overall_sentiment_num == '6' or overall_sentiment_num == 'Negative':
        overall_sentiment = "Negative"
    elif overall_sentiment_num == '7' or overall_sentiment_num == 'Positive':
        overall_sentiment = "Positive"
    elif overall_sentiment_num == '8' or overall_sentiment_num == 'Neutral':
        overall_sentiment = "Neutral"

    
    # Map category number to field name
    category_map = {
        '1': "Charging Functionality and Reliability",
        '2': "Charging Performance",
        '3': "Location and Availability",
        '4': "Pricing and Payment",
        '5': "Environment and Service Experience",
        '9': "Other"
    }
    
    category = category_map.get(category_num, "Other")
    
    sentiment_analysis = {
        "Charging Functionality and Reliability": "null",
        "Charging Performance": "null",
        "Location and Availability": "null",
        "Pricing and Payment": "null",
        "Environment and Service Experience": "null",
        "Overall sentiment": overall_sentiment
    }
    
    if category_num != '9':
        sentiment_analysis[category] = overall_sentiment
    
    return {
        "sentiment_analysis": sentiment_analysis,
        "keywords": keywords if keywords else "null"
    }

def transform_comment(comment):
    transformed = {
        "content": comment["content"],
        "date": comment["date"],
        "uid": comment["uid"],
        "longitude": str(comment["longitude"]),
        "latitude": str(comment["latitude"])
    }
    
    sentiment_info = transform_sentiment(comment.get("sentiment", ""))
    if sentiment_info:
        transformed["sentiment"] = sentiment_info["sentiment_analysis"]
        transformed["keywords"] = sentiment_info["keywords"]
    else:
        transformed["sentiment"] = {
            "Charging Functionality and Reliability": "null",
            "Charging Performance": "null",
            "Location and Availability": "null",
            "Pricing and Payment": "null",
            "Environment and Service Experience": "null",
            "Overall sentiment": "null"
        }
        transformed["keywords"] = "null"
    
    return transformed

def process_files(input_folder, output_file):
    merged_data = {"comment_list": []}
    
    json_files = glob(os.path.join(input_folder, "*.json"))
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for comment in tqdm(data.get("comment_list", [])):
                date =(comment.get("date", [])[:4])
                if int(date)<2015 or (int(date)) > 2024:
                    continue
                transformed_comment = transform_comment(comment)
                merged_data["comment_list"].append(transformed_comment)
    

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

input_folder = "Data\\interim\\LLM_result\\europe"
output_file = "Data\\interim\\LLM_result_processing\\europe_comments.json"
process_files(input_folder, output_file)

input_folder = "Data\\interim\\LLM_result\\usa"
output_file = "Data\\interim\\LLM_result_processing\\usa_comments.json"
process_files(input_folder, output_file)

input_folder = "Data\\interim\\LLM_result\\china"
output_file = "Data\\interim\\LLM_result_processing\\china_comments.json"
process_files(input_folder, output_file)