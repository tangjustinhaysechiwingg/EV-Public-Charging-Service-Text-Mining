import json
from datetime import datetime
from collections import defaultdict

def process_occupied_hourly(data):
    """Processing the 24-hour distribution of occupied keywords"""
    hourly_stats = defaultdict(lambda: {
        'total_comments': 0,
        'occupied_comments': 0,
        'occupied_keywords': 0,
        'total_keywords': 0
    })

    for comment in data['comment_list']:
        try:
            date_str = comment['date']
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            hour = dt.hour
            
            hourly_stats[hour]['total_comments'] += 1
            hourly_stats[hour]['total_keywords'] += len(comment['keywords'])
            
            if 'occupied' in comment['keywords']:
                hourly_stats[hour]['occupied_comments'] += 1
                hourly_stats[hour]['occupied_keywords'] += comment['keywords'].count('occupied')
        except:
            continue


    hourly_keyword_ratio = {
        str(hour): hourly_stats[hour]['occupied_keywords'] / hourly_stats[hour]['total_keywords'] 
        for hour in hourly_stats if hourly_stats[hour]['total_keywords'] > 0
    }
    hourly_comment_ratio = {
        str(hour): hourly_stats[hour]['occupied_comments'] / hourly_stats[hour]['total_comments'] 
        for hour in hourly_stats if hourly_stats[hour]['total_comments'] > 0
    }

    with open('Data\\interim\\appendix2\\hourly_occupied_comment_ratio.json', 'w', encoding='utf-8') as f:
        json.dump(hourly_comment_ratio, f, ensure_ascii=False, indent=2)

def process_occupied_weekly(data):
    """Processing the weekly distribution of occupied keywords"""
    weekly_stats = defaultdict(lambda: {
        'total_comments': 0,
        'occupied_comments': 0,
        'occupied_keywords': 0,
        'total_keywords': 0
    })
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

    for comment in data['comment_list']:
        dt = None
        date_str = comment['date']
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except:
                continue
        
        if dt:
            weekday = dt.strftime('%A')
            weekly_stats[weekday]['total_comments'] += 1
            weekly_stats[weekday]['total_keywords'] += len(comment['keywords'])
            
            if 'occupied' in comment['keywords']:
                weekly_stats[weekday]['occupied_comments'] += 1
                weekly_stats[weekday]['occupied_keywords'] += comment['keywords'].count('occupied')

    weekly_keyword_ratio = {
        day: weekly_stats[day]['occupied_keywords'] / weekly_stats[day]['total_keywords'] 
        for day in weekly_stats if weekly_stats[day]['total_keywords'] > 0
    }
    weekly_comment_ratio = {
        day: weekly_stats[day]['occupied_comments'] / weekly_stats[day]['total_comments'] 
        for day in weekly_stats if weekly_stats[day]['total_comments'] > 0
    }


    with open('Data\\interim\\appendix2\\weekly_occupied_comment_ratio.json', 'w', encoding='utf-8') as f:
        json.dump(weekly_comment_ratio, f, ensure_ascii=False, indent=2)

def process_broken_monthly(data):
    """Process the monthly distribution of broken keywords (1-12 months)"""
    monthly_stats = defaultdict(lambda: {
        'total_comments': 0,
        'broken_comments': 0,
        'broken_keywords': 0,
        'total_keywords': 0
    })
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

    for comment in data['comment_list']:
        dt = None
        date_str = comment['date']
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except:
                continue
        
        if dt:
            month = dt.month
            monthly_stats[month]['total_comments'] += 1
            monthly_stats[month]['total_keywords'] += len(comment['keywords'])
            
            if 'broken' in comment['keywords']:
                monthly_stats[month]['broken_comments'] += 1
                monthly_stats[month]['broken_keywords'] += comment['keywords'].count('broken')

    monthly_keyword_ratio = {
        str(month): monthly_stats[month]['broken_keywords'] / monthly_stats[month]['total_keywords'] 
        for month in monthly_stats if monthly_stats[month]['total_keywords'] > 0
    }
    monthly_comment_ratio = {
        str(month): monthly_stats[month]['broken_comments'] / monthly_stats[month]['total_comments'] 
        for month in monthly_stats if monthly_stats[month]['total_comments'] > 0
    }

    with open('Data\\interim\\appendix2\\monthly_broken_comment_ratio.json', 'w', encoding='utf-8') as f:
        json.dump(monthly_comment_ratio, f, ensure_ascii=False, indent=2)

def main():

    with open('Data\\interim\\LLM_result_processing\\china_comments.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
 
    process_occupied_hourly(data)
    process_occupied_weekly(data)
    process_broken_monthly(data)  

if __name__ == "__main__":
    main()