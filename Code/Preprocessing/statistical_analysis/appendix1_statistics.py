import json
from collections import defaultdict
from tqdm import tqdm

# Keywords to be analyzed
TARGET_KEYWORDS = ['slow charging', 'slow', 'broken', 'not working']

def process_files(region_files):
    result = {}
    
    for region_name, file_path in region_files.items():
        region_data = defaultdict(lambda: {
            'total_comments': 0,  # Total number of comments
            'comments_with_keywords': {kw: 0 for kw in TARGET_KEYWORDS},  # Number of comments containing various keywords
            'comments_with_any_keyword': 0  # Number of comments containing any target keywords
        })
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for comment in tqdm(data['comment_list']):
                    # Extract year
                    date_str = comment['date']
                    year = int(date_str[:4])
                    
                    # Only process data from 2018 to 2024
                    if 2018 <= year <= 2024:
                        region_data[year]['total_comments'] += 1
                        keywords = comment['keywords']
                        keyword_set = set(kw.lower() for kw in keywords)
                        
                        # Check if any target keywords are included
                        has_any_keyword = False
                        for target_kw in TARGET_KEYWORDS:
                            if any(target_kw in kw for kw in keyword_set):
                                region_data[year]['comments_with_keywords'][target_kw] += 1
                                has_any_keyword = True
                        
                        if has_any_keyword:
                            region_data[year]['comments_with_any_keyword'] += 1
            
            # Calculate the proportion of comments for each keyword
            region_result = {}
            for year, year_data in region_data.items():
                total_comments = year_data['total_comments']
                if total_comments == 0:
                    continue  
                    
                year_result = {
                    'total_comments': total_comments,
                }
                
                for kw, count in year_data['comments_with_keywords'].items():
                    year_result[kw] = count / total_comments
                    
                region_result[str(year)] = year_result
            
            result[region_name] = region_result
            
        except FileNotFoundError:
            print(f"Warning: The file {file_path} does not exist, skipping the region {region_name}")
        except json.JSONDecodeError:
            print(f"Warning: The file {file_path} is not in a valid JSON format, skipping the region {region_name}")
        except KeyError as e:
            print(f"Warning: The file {file_path} is missing the necessary field {str (e)}, skipping the region {region_name}")
    
    return result


if __name__ == "__main__":

    region_files = {
        "China": "Data\\interim\\LLM_result_processing\\china_comments.json",
        "USA": "Data\\interim\\LLM_result_processing\\usa_comments.json",
        "Europe": "Data\\interim\\LLM_result_processing\\europe_comments.json"
    }
    
    output_data = process_files(region_files)

    with open('Data\\interim\\appendix1\\appendix1.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    