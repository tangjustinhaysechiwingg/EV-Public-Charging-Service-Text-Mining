import requests
import json
from tqdm import tqdm
import time
import random
import csv
from fake_useragent import UserAgent
import numpy as np
import math
from multiprocessing import Pool
import os
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create necessary directories
os.makedirs("Data_collection/china/area", exist_ok=True)
os.makedirs("Data_collection/china/comments", exist_ok=True)
os.makedirs("Data_collection/china/charger", exist_ok=True)
os.makedirs("Data_collection/china/result", exist_ok=True)

# WGS-84 to GCJ-02
def wgs84_to_gcj02(lat, lng):
    a = 6378245.0  
    ee = 0.00669342162296594323  

    def transform_lat(x, y):
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
        return ret

    def transform_lng(x, y):
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
        return ret

    dlat = transform_lat(lng - 105.0, lat - 35.0)
    dlng = transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return mglat, mglng

# GCJ-02 to BD-09
def gcj02_to_bd09(lat, lng):
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * math.pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * math.pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lat, bd_lng

# WGS-84 to BD-09
def wgs84_to_bd09(lat, lng):
    gcj_lat, gcj_lng = wgs84_to_gcj02(lat, lng)
    bd_lat, bd_lng = gcj02_to_bd09(gcj_lat, gcj_lng)
    return bd_lat, bd_lng

def bd09_to_mercator(lat, lng):
    R = 6378137
    lng_rad = math.radians(lng)
    lat_rad = math.radians(lat)
    x = R * lng_rad
    y = R * math.log(math.tan(math.pi / 4 + lat_rad / 2))
    return x, y

def Quartile(x1, y1, x2, y2, cell_length, charge_number, charger_list, comment_list):
    ua = UserAgent()
    cell_length_temp = cell_length / 2
    
    for sub_x in range(2):
        for sub_y in range(2): 
            sub_x1 = x1 + cell_length_temp * sub_x
            sub_y1 = y1 + cell_length_temp * sub_y
            sub_x2 = sub_x1 + cell_length_temp
            sub_y2 = sub_y1 + cell_length_temp
            
            url = f'https://map.baidu.com/?newmap=1&reqflag=pcmap&biz=1&from=webmap&da_par=direct&pcevaname=pc4.1&qt=spot&from=webmap&wd=%E5%85%85%E7%94%B5%E7%AB%99&wd2=&pn=0&nn=0&db=0&sug=0&addr=0&&da_src=pcmappg.poi.page&on_gel=1&src=7&gr=3&l=15&rn=50&tn=B_NORMAL_MAP&u_loc=13474216,3749589&ie=utf-8&b=({sub_x1},{sub_y1};{sub_x2},{sub_y2})&t=1738733826178&newfrom=zhuzhan_webmap'
            
            try:
                headers = {'User-Agent': ua.random}
                response = requests.get(url=url, headers=headers, timeout=30)
                response.raise_for_status()
                
                json_data = response.json()
                
                if 'content' in json_data:
                    if len(json_data['content']) == 50:
                        Quartile(sub_x1, sub_y1, sub_x2, sub_y2, cell_length_temp, charge_number, charger_list, comment_list)
                    else:
                        charge_number.append(len(json_data['content']))
                        # Save Area Data
                        with open(f"Data_collection/china/area/bbox_{sub_x1}_{sub_y1}_{sub_x2}_{sub_y2}.json", 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)
                        
                        # Handle each charging station
                        for content in json_data['content']:
                            process_charger_station(content, charger_list, comment_list)
                            
            except Exception as e:
                logging.error(f"Quartile error for area ({sub_x1},{sub_y1};{sub_x2},{sub_y2}): {e}")
                time.sleep(random.uniform(1, 3))

def process_charger_station(content, charger_list, comment_list):
    ua = UserAgent()
    uid = content.get('uid', '')
    if not uid:
        return
    
    try:
        # Get detailed information
        detail_url = f'https://map.baidu.com/?uid={uid}&ugc_type=3&ugc_ver=1&qt=detailConInfo&device_ratio=1&compat=1&pcevaname=pc4.1&newfrom=zhuzhan_webmap'
        headers = {'User-Agent': ua.random}
        
        detail_response = requests.get(detail_url, headers=headers, timeout=30)
        detail_response.raise_for_status()
        detail_data = detail_response.json()
        
        # Save detailed data
        with open(f"Data_collection/china/charger/{uid}_detail.json", 'w', encoding='utf-8') as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=4)
        
        # Get comment information
        comment_list_temp = []
        try:
            comment_url = f'https://ugc.map.baidu.com/cube/comment/index?uid={uid}&pageIndex=1&pageCount=10&pic_videos=1&tab=1&pcevaname=pc4.1&newfrom=zhuzhan_webmap'
            comment_response = requests.get(comment_url, headers=headers, timeout=30)
            comment_response.raise_for_status()
            comment_data = comment_response.json()
            
            # Save comment data
            with open(f"Data_collection/china/comments/{uid}_comment.json", 'w', encoding='utf-8') as f:
                json.dump(comment_data, f, ensure_ascii=False, indent=4)
            
            # Extract comment content
            if ('data' in comment_data and 'comment_num' in comment_data['data'] 
                and comment_data['data']['comment_num'] > 0):
                for comment in comment_data['data'].get('comment_list', []):
                    if 'content' in comment:
                        comment_list_temp.append(comment['content'])
                        comment_list.append(comment['content'])
                        
        except Exception as e:
            logging.warning(f"Failed to get comments for {uid}: {e}")

        charger_detail = {
            'x': detail_data.get('content', {}).get('x', ''),
            'y': detail_data.get('content', {}).get('y', ''),
            'uid': uid,
            'name': content.get('name', ''),
            'address': content.get('addr', ''),
            'comment': comment_list_temp
        }
        charger_list.append(charger_detail)
        
        time.sleep(random.uniform(0.5, 1.5))
        
    except Exception as e:
        logging.error(f"Failed to process charger station {uid}: {e}")

def job(x, y, id_latitude):
    ua = UserAgent()
    charger_list = []
    comment_list = []
    charge_number = []
    
    cell_length = 10000
    grid_cols = 691  
    grid_rows = 514   
    
    total_cells = grid_cols * grid_rows
    
    for i in tqdm(range(total_cells), desc=f"Processing latitude {id_latitude}"):
        try:

            col = i % grid_cols
            row = i // grid_cols
            
            x1 = x + col * cell_length
            y1 = y + id_latitude * cell_length * grid_rows + row * cell_length
            x2 = x1 + cell_length
            y2 = y1 + cell_length
            
            url = f'https://map.baidu.com/?newmap=1&reqflag=pcmap&biz=1&from=webmap&da_par=direct&pcevaname=pc4.1&qt=spot&from=webmap&wd=%E5%85%85%E7%94%B5%E7%AB%99&wd2=&pn=0&nn=0&db=0&sug=0&addr=0&&da_src=pcmappg.poi.page&on_gel=1&src=7&gr=3&l=15&rn=50&tn=B_NORMAL_MAP&u_loc=13474216,3749589&ie=utf-8&b=({x1},{y1};{x2},{y2})&t=1738733826178&newfrom=zhuzhan_webmap'
            
            headers = {'User-Agent': ua.random}
            response = requests.get(url=url, headers=headers, timeout=30)
            response.raise_for_status()
            
            json_data = response.json()
            
            if 'content' in json_data:
                if len(json_data['content']) == 50:
                    Quartile(x1, y1, x2, y2, cell_length, charge_number, charger_list, comment_list)
                else:
                    charge_number.append(len(json_data['content']))
                    with open(f"Data_collection/china/area/bbox_{x1}_{y1}_{x2}_{y2}.json", 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)
                    
                    for content in json_data['content']:
                        process_charger_station(content, charger_list, comment_list)
            
            time.sleep(random.uniform(0.5, 2))
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for grid {i}: {e}")
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            logging.error(f"Unexpected error for grid {i}: {e}")
            time.sleep(random.uniform(2, 4))
    
    try:
        with open(f"Data_collection/china/result/charger_{id_latitude}.json", "w", encoding="utf-8") as f:
            json.dump(charger_list, f, ensure_ascii=False, indent=4)
        
        with open(f"Data_collection/china/result/comments_{id_latitude}.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['comment'])
            for comment in comment_list:
                writer.writerow([comment])
                
        logging.info(f"Latitude {id_latitude} completed: {len(charger_list)} chargers, {len(comment_list)} comments")
        
    except Exception as e:
        logging.error(f"Failed to save results for latitude {id_latitude}: {e}")

if __name__ == '__main__':
    china = [8120000,2038000,15030000,7178000]
    num_processes = min(40, os.cpu_count())
    
    logging.info(f"Starting {num_processes} processes")
    
    with Pool(processes=num_processes) as pool:
        results = []
        for i in range(num_processes):
            result = pool.apply_async(job, (china[0], china[1], i))
            results.append(result)