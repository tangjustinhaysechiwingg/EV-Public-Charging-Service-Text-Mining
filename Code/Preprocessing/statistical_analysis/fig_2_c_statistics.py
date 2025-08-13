import json
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm
import pytz

# Function to load data from JSON file
def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load all datasets
europe_data = load_data('Data\\interim\\LLM_result_processing\\europe_comments.json')
usa_data = load_data('Data\\interim\\LLM_result_processing\\usa_comments.json')
china_data = load_data('Data\\interim\\LLM_result_processing\\china_comments.json')

# Timezone definitions
UTC = pytz.utc
EUROPE_TZ = pytz.timezone('Europe/Berlin')
USA_TZ = pytz.timezone('America/New_York')
CHINA_TZ = pytz.timezone('Asia/Shanghai')

# Strict datetime parser for hourly statistics (single format)
def parse_datetime_for_hour(date_str, region):
    try:
        if region == 'Europe':
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            dt = UTC.localize(dt)
            return dt.astimezone(EUROPE_TZ)
        elif region == 'USA':
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            dt = UTC.localize(dt)
            return dt.astimezone(USA_TZ)
        elif region == 'China':
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            return dt
    except Exception as e:
        return None

# Flexible datetime parser for weekly/monthly statistics (multiple formats)
def parse_datetime_for_week_month(date_str, region):
    try:
        # Parse as naive datetime first
        if "T" in date_str and date_str.endswith("Z"):
            # Format: "YYYY-MM-DDTHH:MM:SSZ" (UTC time)
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            dt = UTC.localize(dt)  # Mark as UTC
        else:
            # Try parsing as China local time format (no timezone info)
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        return None
            # Mark as local time directly (no UTC conversion)
        
        # Convert timezone based on region
        if region == 'Europe':
            return dt.astimezone(EUROPE_TZ) if dt.tzinfo else EUROPE_TZ.localize(dt)
        elif region == 'USA':
            return dt.astimezone(USA_TZ) if dt.tzinfo else USA_TZ.localize(dt)
        elif region == 'China':
            return dt.astimezone(CHINA_TZ) if dt.tzinfo else CHINA_TZ.localize(dt)
        else:
            return None
    except Exception as e:
        return None

# Helper function to calculate percentages
def calculate_percentage(count_dict):
    total = sum(count_dict.values())
    if total == 0:
        return {k: 0 for k in count_dict.keys()}
    return {k: round(v / total * 100, 2) for k, v in count_dict.items()}

# Process region data (strict separation between hourly and weekly/monthly stats)
def process_region(data, region_name):
    stats = {
        'hourly_counts': defaultdict(lambda: {'Positive': 0, 'Neutral': 0, 'Negative': 0}),
        'weekly_counts': defaultdict(lambda: {'Positive': 0, 'Neutral': 0, 'Negative': 0}),
        'monthly_counts': defaultdict(lambda: {'Positive': 0, 'Neutral': 0, 'Negative': 0}),
        'hourly_percentage': defaultdict(dict),
        'weekly_percentage': defaultdict(dict),
        'monthly_percentage': defaultdict(dict)
    }
    
    for comment in tqdm(data['comment_list'], desc=f"Processing {region_name}"):
        try:
            # Strict parsing for hourly stats
            hour_date = parse_datetime_for_hour(comment['date'], region_name)
            
            # Flexible parsing for weekly/monthly stats
            week_month_date = parse_datetime_for_week_month(comment['date'], region_name)
            
            final_eval = comment['sentiment']['Overall sentiment']
            
            if final_eval in ['Positive', 'Neutral', 'Negative']:
                # Only count if hour data can be parsed
                if hour_date and 2015 <= hour_date.year <= 2024:
                    hour = hour_date.hour
                    stats['hourly_counts'][hour][final_eval] += 1
                
                # Weekly/monthly stats use flexible parsing
                if week_month_date and 2015 <= week_month_date.year <= 2024:
                    weekday = week_month_date.weekday()  
                    stats['weekly_counts'][weekday][final_eval] += 1
                    
                    month = week_month_date.month
                    stats['monthly_counts'][month][final_eval] += 1
                    
        except Exception as e:
            continue
    
    # Calculate percentages
    for hour in stats['hourly_counts']:
        stats['hourly_percentage'][hour] = calculate_percentage(stats['hourly_counts'][hour])
    
    for weekday in stats['weekly_counts']:
        stats['weekly_percentage'][weekday] = calculate_percentage(stats['weekly_counts'][weekday])
    
    for month in stats['monthly_counts']:
        stats['monthly_percentage'][month] = calculate_percentage(stats['monthly_counts'][month])
    
    return stats

print("\nProcessing regional data...")
europe_stats = process_region(europe_data, 'Europe')
usa_stats = process_region(usa_data, 'USA')
china_stats = process_region(china_data, 'China')

# Convert stats to serializable dictionary structure
def convert_stats_to_dict(stats):
    return {
        'hourly_counts': {str(h): dict(s) for h, s in stats['hourly_counts'].items()},
        'weekly_counts': {str(w): dict(s) for w, s in stats['weekly_counts'].items()},
        'monthly_counts': {str(m): dict(s) for m, s in stats['monthly_counts'].items()},
        'hourly_percentage': {str(h): dict(p) for h, p in stats['hourly_percentage'].items()},
        'weekly_percentage': {str(w): dict(p) for w, p in stats['weekly_percentage'].items()},
        'monthly_percentage': {str(m): dict(p) for m, p in stats['monthly_percentage'].items()}
    }

# Convert and save regional data
europe_dict = convert_stats_to_dict(europe_stats)
usa_dict = convert_stats_to_dict(usa_stats)
china_dict = convert_stats_to_dict(china_stats)

# Save combined data with all regions
combined_stats = {
    'Europe': europe_dict,
    'USA': usa_dict,
    'China': china_dict,
    'metadata': {
        'time_range': '2015-2024',
        'timezones': {
            'Europe': 'Europe/Berlin',
            'USA': 'America/New_York',
            'China': 'Asia/Shanghai'
        },
        'weekly_mapping': {
            '0': 'Mon',
            '1': 'Tue',
            '2': 'Wed',
            '3': 'Thu',
            '4': 'Fri',
            '5': 'Sat',
            '6': 'Sun'
        },
        'monthly_mapping': {
            '1': 'Jan',
            '2': 'Feb', 
            '3': 'Mar',
            '4': 'Apr',
            '5': 'May',
            '6': 'Jun',
            '7': 'Jul',
            '8': 'Aug',
            '9': 'Sep',
            '10': 'Oct',
            '11': 'Nov',
            '12': 'Dec'
        },
        'hourly_mapping': {str(h): f'{h}:00' for h in range(24)},
        'parse_method': {
            'hourly': 'Strict single format parsing',
            'weekly_monthly': 'Flexible multi-format parsing'
        }
    }
}

with open('Data\\interim\\fig_2_c\\fig_2_c.json', 'w', encoding='utf-8') as f:
    json.dump(combined_stats, f, ensure_ascii=False, indent=2)