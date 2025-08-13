import json
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from tqdm import tqdm

# Configuration for each region
timezones = {
    'China': pytz.timezone('Asia/Shanghai'),
    'USA': pytz.timezone('America/New_York'),
    'Europe': pytz.timezone('Europe/Berlin')
}

# Store data from various regions for output purposes
regions = {
    'China': {
        'filename': 'Data\\interim\\LLM_result_processing\\china_comments.json',
        'date_format': "%Y-%m-%d %H:%M",
        'date_format1': "%Y-%m-%d %H:%M:%S",
        'date_format2': "%Y-%m-%d",
        'timezone': timezones['China']
    },
    'USA': {
        'filename': 'Data\\interim\\LLM_result_processing\\usa_comments.json',
        'date_format': "%Y-%m-%dT%H:%M:%SZ",  
        'timezone': timezones['USA']
    },
    'Europe': {
        'filename': 'Data\\interim\\LLM_result_processing\\europe_comments.json',
        'date_format': "%Y-%m-%dT%H:%M:%SZ",  
        'timezone': timezones['Europe']
    }
}

def load_data(config):
    try:
        with open(config['filename'], 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {config['filename']}: {e}")
        return {"comment_list": []}

def convert_to_local(dt_naive, config):
    if config['date_format'].endswith('Z'):  # 
        utc_dt = pytz.utc.localize(dt_naive)
        local_dt = utc_dt.astimezone(config['timezone'])
        return local_dt
    else:  # If it is not UTC time (such as China data), assuming it is already local time
        return config['timezone'].localize(dt_naive)

# Initialize data structure
metrics = {
    'weekday': {
        'names': ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        'data': {region: [0]*7 for region in regions}
    },
    'month': {
        'names': [f"Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        'data': {region: [0]*12 for region in regions}
    },
    'hour': {
        'names': [f"{h:02d}:00" for h in range(24)],
        'data': {region: [0]*24 for region in regions}
    }
}

# Processing data
for region, config in regions.items():
    data = load_data(config)
    for comment in tqdm(data.get("comment_list", [])):
        try:
            dt_naive = datetime.strptime(comment["date"], config['date_format'])
            dt_local = convert_to_local(dt_naive, config)
            
            if not (2015 <= dt_local.year <= 2024):
                continue
            
            metrics['weekday']['data'][region][dt_local.weekday()] += 1
            metrics['month']['data'][region][dt_local.month-1] += 1
            metrics['hour']['data'][region][dt_local.hour] += 1
        except Exception as e:
            try:
                dt_naive = datetime.strptime(comment["date"], config['date_format1'])
                dt_local = convert_to_local(dt_naive, config)
            
                if not (2015 <= dt_local.year <= 2024):
                    continue
            
                metrics['weekday']['data'][region][dt_local.weekday()] += 1
                metrics['month']['data'][region][dt_local.month-1] += 1
            except Exception as e:
                try:
                    dt_naive = datetime.strptime(comment["date"], config['date_format2'])
                    dt_local = convert_to_local(dt_naive, config)
            
                    if not (2015 <= dt_local.year <= 2024):
                        continue
            
                    metrics['weekday']['data'][region][dt_local.weekday()] += 1
                    metrics['month']['data'][region][dt_local.month-1] += 1
                except Exception as e:
                    continue


for dim_name, dim_data in metrics.items():
    for region in regions:
        total = sum(dim_data['data'][region])
        if total > 0:
            percentages = [round(x/total*100, 2) for x in dim_data['data'][region]]
            dim_data[region] = percentages
            peak_idx = np.argmax(percentages)

json_filename = "Data\\interim\\fig_1_b\\fig_1_b.json"

# JSON
with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2)



