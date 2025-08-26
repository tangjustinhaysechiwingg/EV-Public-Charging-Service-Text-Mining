import os
import requests
import json
from tqdm import tqdm
import time
import random
import csv
from fake_useragent import UserAgent
from multiprocessing import Pool
from datetime import datetime
from multiprocessing.pool import ThreadPool

class ChargerDataScraper:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.area_dir = os.path.join(output_dir, "area")
        self.charger_dir = os.path.join(output_dir, "charger")
        self.results_dir = os.path.join(output_dir, "results")
        self.completed_file = os.path.join(output_dir, "completed_grids.csv")
        self.error_log_file = os.path.join(output_dir, "error_logs.csv")
        
        # Dynamic residential IP
        self.proxy_auth = ""   
        self.proxy_server = ""

        self.proxy = {
            'http': f'socks5h://{self.proxy_auth}@{self.proxy_server}',
            'https': f'socks5h://{self.proxy_auth}@{self.proxy_server}',
        }
        
        # Headers configuration
        self.website_ua = [
            "\"Not(A:Brand\";v=\"99\", \"Microsoft Edge\";v=\"133\", \"Gecko\";v=\"133\"",
            "\"Not(A:Brand\";v=\"99\", \"Firefox\";v=\"133\", \"Gecko\";v=\"133\"",
            "\"Not(A:Brand\";v=\"99\", \"Safarie\";v=\"133\", \"AppleWebKit\";v=\"133\"",
            "\"Not(A:Brand\";v=\"99\", \"Opera\";v=\"133\", \"Chromium\";v=\"133\"",
            "\"Not(A:Brand\";v=\"99\", \"Brave\";v=\"133\", \"Chromium\";v=\"133\"",
        ]
        
        self.cognito_auth = [
            '',
            ]
        
        # Create necessary directories
        self._create_dirs()
        
        # Initialize UserAgent
        self.ua = UserAgent()
        
        # Initialize error log
        self._init_error_log()
    
    def _create_dirs(self):
        """Create all necessary directories"""
        os.makedirs(self.area_dir, exist_ok=True)
        os.makedirs(self.charger_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
    
    def _init_error_log(self):
        """Initialize error log file"""
        if not os.path.exists(self.error_log_file):
            with open(self.error_log_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'grid_id', 'url', 'error_type', 'error_message'])
    
    def _log_error(self, grid_id, url, error_type, error_message):
        """Log error to error log file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.error_log_file, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, grid_id, url, error_type, str(error_message)])

    def get_headers(self):
        """Generate random headers for requests"""
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en",
            "Sec-CH-UA": random.choice(self.website_ua),
            #"Sec-CH-UA-Mobile": "?0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Authorization": "Basic d2ViX3YyOkVOanNuUE54NHhXeHVkODU=",
            "Origin": "https://www.plugshare.com",
            #"Referer": "https://www.plugshare.com",
            "Cognito-Authorization": random.choice(self.cognito_auth),
            "User-Agent": self.ua.random
        }
    
    def area_charger(self, x1, y1, area_url, cell_length, charge_number, grid_id):
        """Process charger area data"""
        try:
            sleep_time = random.uniform(2, 4)
            #time.sleep(sleep_time)
            
            response = requests.get(
                url=area_url,
                headers=self.get_headers(),
                proxies=self.proxy,
                timeout=6
            )
            
            page_text = response.text
            json1 = json.loads(page_text)
            
            if len(json1) == 250:
                self.quartile(x1, y1, cell_length, charge_number, grid_id)
            else:
                charge_number.append(len(json1))
                self._save_area_data(x1, y1, cell_length, json1)
                
                for charger in json1:
                    try:
                        self.process_charger_detail(charger["id"])
                    except Exception as e:
                        error_msg = f"Error processing charger detail: {e}"
                        print(error_msg)
                        self._log_error(
                            grid_id, 
                            f"charger_id:{charger['id']}", 
                            "Detail Processing Error", 
                            error_msg
                        )
                        
        except Exception as e:
            error_msg = f"Area charger error: {e}"
            print(error_msg)
            self._log_error(grid_id, area_url, "Area Charger Error", error_msg)
            # Retry the area
            self.area_charger(x1, y1, area_url, cell_length, charge_number, grid_id)

    def process_charger_detail(self, charger_id):
        """Process individual charger detail"""
        try:
            detail_url = f"https://api.plugshare.com/v3/locations/{charger_id}"
            
            sleep_time = random.uniform(2, 4)
            #time.sleep(sleep_time)
            
            detail_response = requests.get(
                url=detail_url,
                headers=self.get_headers(),
                proxies=self.proxy,
                timeout=6
            )
            
            detail_json = json.loads(detail_response.text)
            self._save_charger_detail(charger_id, detail_json)
            print(charger_id)
        except Exception as e:
            error_msg = f"Detail request error: {e}"
            print(error_msg)
            # Retry the detail
            self.process_charger_detail(charger_id)

    def quartile(self, x1_centre, y1_centre, cell_length, charge_number, grid_id):
        """Divide area into quarters if too many results"""
        cell_length_temp = cell_length / 2
        x1 = x1_centre - cell_length_temp / 2
        y1 = y1_centre - cell_length_temp / 2
        
        for sub_x in range(2):
            for sub_y in range(2): 
                try: 
                    sub_x1 = x1 + cell_length_temp * sub_x
                    sub_y1 = y1 + cell_length_temp * sub_y
                    
                    url = ("https://api.plugshare.com/v3/locations/region?access=1&count=500&minimal=0&"
                          "outlets=%5B%7B%22connector%22:20,%22power%22:0%7D,%7B%22connector%22:13,%22power%22:0%7D,"
                          "%7B%22connector%22:3,%22power%22:0%7D,%7B%22connector%22:2,%22power%22:0%7D,"
                          "%7B%22connector%22:4,%22power%22:0%7D,%7B%22connector%22:7,%22power%22:0%7D,"
                          "%7B%22connector%22:5,%22power%22:0%7D%5D"
                          f"&spanLat={cell_length_temp}&spanLng={cell_length_temp}"
                          f"&latitude={sub_y1}&longitude={sub_x1}")

                    sleep_time = random.uniform(2, 4)
                    #time.sleep(sleep_time)
                    
                    response = requests.get(
                        url=url,
                        headers=self.get_headers(),
                        proxies=self.proxy,
                        timeout=6
                    )
                    
                    json1 = json.loads(response.text)
                    
                    if len(json1) == 250:
                        self.quartile(sub_x1, sub_y1, cell_length_temp, charge_number, grid_id)
                    else:
                        charge_number.append(len(json1))
                        self._save_area_data(sub_x1, sub_y1, cell_length_temp, json1)
                        
                        for charger in json1:
                            try:
                                self.process_charger_detail(charger["id"])
                            except Exception as e:
                                error_msg = f"Error processing charger detail: {e}"
                                print(error_msg)
                                self._log_error(
                                    grid_id, 
                                    f"charger_id:{charger['id']}", 
                                    "Detail Processing Error", 
                                    error_msg
                                )
                                
                except Exception as e:
    
                    self.area_charger(sub_x1, sub_y1, url, cell_length_temp, charge_number, grid_id)

    def _save_area_data(self, x1, y1, cell_length, data):
        """Save area data to file"""
        filename = os.path.join(self.area_dir, f"bbox_centre{x1}_centre{y1}_lenth{cell_length}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _save_charger_detail(self, charger_id, data):
        """Save charger detail to file"""
        filename = os.path.join(self.charger_dir, f"{charger_id}_detail.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _save_result_data(self, grid_id, data):
        """Save result data to file"""
        filename = os.path.join(self.results_dir, f"charger_{grid_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _load_completed_grids(self):
        """Load completed grids from file"""
        if not os.path.exists(self.completed_file):
            return set()
        
        completed = set()
        with open(self.completed_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row:  # Check if row is not empty
                    completed.add(int(row[0]))
        return completed

    def _mark_grid_completed(self, grid_id):
        """Mark grid as completed"""
        file_exists = os.path.isfile(self.completed_file)
        with open(self.completed_file, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['grid_id'])
            writer.writerow([grid_id])

    def load_grids_from_csv(self, csv_file):
        """Load grid coordinates from CSV file"""
        grids = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                grids.append((
                    float(row['xmin']),
                    float(row['ymin']),
                    float(row['xmax']),
                    float(row['ymax']),
                    int(row['grid_id'])
                ))
        return grids

    def process_grid(self, grid_info):
        """Process a single grid"""
        x1, y1, x2, y2, grid_id = grid_info
        
        # Skip if already completed
        completed_grids = self._load_completed_grids()
        if grid_id in completed_grids:
            return 0
            
        cell_length = 1.01
        charge_number = []
        
        try:
            # Calculate center point of the grid
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            url = ("https://api.plugshare.com/v3/locations/region?access=1&count=500&minimal=0&"
                  "outlets=%5B%7B%22connector%22:20,%22power%22:0%7D,%7B%22connector%22:13,%22power%22:0%7D,"
                  "%7B%22connector%22:3,%22power%22:0%7D,%7B%22connector%22:2,%22power%22:0%7D,"
                  "%7B%22connector%22:4,%22power%22:0%7D,%7B%22connector%22:7,%22power%22:0%7D,"
                  "%7B%22connector%22:5,%22power%22:0%7D%5D"
                  f"&spanLat={cell_length}&spanLng={cell_length}"
                  f"&latitude={center_y}&longitude={center_x}")

            self.area_charger(center_x, center_y, url, cell_length, charge_number, grid_id)
            
            # Mark grid as completed using the original grid ID
            self._mark_grid_completed(grid_id)
            
            return sum(charge_number)
            
        except Exception as e:
            error_msg = f"Grid processing error: {e}"
            print(error_msg)
            self._log_error(
                grid_id, 
                url, 
                "Grid Processing Error", 
                error_msg
            )
            return 0

    def run(self, grid_csv=None, processes=15):
        """Run the scraper"""
        if grid_csv:
            # Process grids from CSV file
            all_grids = self.load_grids_from_csv(grid_csv)
            completed_grids = self._load_completed_grids()
            pending_grids = [grid for grid in all_grids if grid[4] not in completed_grids]
            
            print(f"Total grids: {len(all_grids)}")
            print(f"Completed grids: {len(completed_grids)}")
            print(f"Pending grids: {len(pending_grids)}")
            
            if not pending_grids:
                print("All grids already processed")
                return
                
            # Process grids with multiprocessing
            with ThreadPool(processes=processes) as pool:  
                results = []
                with tqdm(total=len(pending_grids), desc='Processing grids') as pbar:
                    for result in pool.imap_unordered(self.process_grid, pending_grids):
                        results.append(result)
                        pbar.update()            
                        total_chargers = sum(results)
            print(f"Total chargers found in this run: {total_chargers}")

if __name__ == '__main__':
    scraper = ChargerDataScraper(output_dir="Plugshare_data")
    
    # Process grids from a CSV file
    scraper.run(grid_csv="plugshare_fishnet.csv", processes=50)