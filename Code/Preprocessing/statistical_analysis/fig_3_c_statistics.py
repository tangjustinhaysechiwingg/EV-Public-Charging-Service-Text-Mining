import json
from collections import defaultdict
import geopandas as gpd
import pandas as pd
import os
from tqdm import tqdm
import shutil

# Regional SHP file configurations
REGION_CONFIG = {
    'europe': {
        'shp_path': "Data\\input\\GADM\\europe\\Europe.shp",
        'merge_field': 'HASC_1',
        'name_field': 'HASC_1'
    },
    'usa': {
        'shp_path': "Data\\input\\GADM\\usa\\gadm41_USA_1.shp",
        'merge_field': 'HASC_1',
        'name_field': 'HASC_1'
    },
    'china': {
        'shp_path': "Data\\input\\GADM\\china\\gadm41_CHN_1.shp",
        'merge_field': 'HASC_1',
        'name_field': 'HASC_1',
        'special_regions': ['HK', 'MO']
    }
}

def process_yearly_themes(comments_paths, region_paths):
    """Process yearly theme data from JSON files"""
    yearly_theme_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for region in ['europe', 'usa', 'china']:
        try:
            with open(comments_paths[region], 'r', encoding='utf-8') as f:
                comments = json.load(f)
            with open(region_paths[region], 'r', encoding='utf-8') as f:
                poi_mapping = json.load(f)
            
            poi_to_region = {poi: reg for reg, pois in poi_mapping.items() for poi in pois}
            
            for comment in tqdm(comments['comment_list'], desc=f"Processing {region} data"):
                poi = str(comment['uid'])
                if poi not in poi_to_region:
                    continue
                
                try:
                    year = comment['date'][:4]
                    if not year.isdigit() or int(year) < 2015 or int(year) > 2024:
                        continue
                except:
                    continue
                
                region_name = poi_to_region[poi]
                themes = [
                    "Charging Functionality and Reliability",
                    "Charging Performance",
                    "Location and Availability",
                    "Pricing and Payment",
                    "Environment and Service Experience"
                ]
                
                for theme in themes:
                    if comment['sentiment'].get(theme, '') != 'null':
                        yearly_theme_counts[year][f"{region}_{region_name}"][theme] += 1
                        
        except Exception as e:
            print(f"Error processing {region} data: {e}")
    
    return yearly_theme_counts

def create_combined_shp_with_topics(yearly_data, global_gdfs, output_dir):
    """Generate combined SHP files with yearly topics and export CSV"""
    os.makedirs(output_dir, exist_ok=True)
    
    for region, (gdf, config) in global_gdfs.items():
        print(f"\nProcessing {region} data...")
        
        merged_df = pd.DataFrame(index=gdf[config['merge_field']].unique())
        
        for year, year_data in yearly_data.items():
            year_suffix = year[2:]
            
            region_data = {k.replace(f"{region}_", ""): v 
                          for k, v in year_data.items() 
                          if k.startswith(f"{region}_")}
            
            region_df = pd.DataFrame.from_dict(region_data, orient='index')
            region_df = region_df.fillna(0).astype(int)
            
            themes = [
                "Charging Functionality and Reliability",
                "Charging Performance",
                "Location and Availability",
                "Pricing and Payment",
                "Environment and Service Experience"
            ]
            
            for theme in themes:
                if theme not in region_df:
                    region_df[theme] = 0
            
            region_df[f'topic_{year_suffix}'] = region_df[themes].idxmax(axis=1)
            
            merged_df = merged_df.merge(
                region_df[[f'topic_{year_suffix}']],
                left_index=True,
                right_index=True,
                how='left'
            )
        
        if region == 'china' and 'special_regions' in config:
            for special_region in config['special_regions']:
                if special_region in merged_df.index:
                    for col in merged_df.columns:
                        if col.startswith('topic_'):
                            merged_df.loc[special_region, col] = None
        
        merged_gdf = gdf.merge(
            merged_df,
            left_on=config['merge_field'],
            right_index=True,
            how='left'
        )
        
        # Save SHP file (temporarily)
        shp_output_path = os.path.join(output_dir, f"{region}_combined_topics.shp")
        merged_gdf.to_file(shp_output_path, encoding='utf-8')
        
        # Save CSV file (final output we want to keep)
        csv_output_path = os.path.join(output_dir, f"{region}_attribute_table.csv")
        merged_df.to_csv(csv_output_path, encoding='utf-8')
        
        # Delete the SHP file and its associated files
        shp_base = os.path.splitext(shp_output_path)[0]
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            file_path = shp_base + ext
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted temporary file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

def main():
    data_config = {
        'europe': {
            'comments': "Data\\interim\\LLM_result_processing\\europe_comments.json",
            'regions': "Data\\input\\UID mapping\\Europe\\Ownership of Charging Station Area.json"
        },
        'usa': {
            'comments': "Data\\interim\\LLM_result_processing\\usa_comments.json",
            'regions': "Data\\input\\UID mapping\\USA\\Ownership of Charging Station Area.json"
        },
        'china': {
            'comments': "Data\\interim\\LLM_result_processing\\china_comments.json",
            'regions': "Data\\input\\UID mapping\\China\\Ownership of Charging Station Area.json"
        }
    }
    
    global_gdfs = {}
    for region, config in REGION_CONFIG.items():
        try:
            gdf = gpd.read_file(config['shp_path'])
            global_gdfs[region] = (gdf, config)
        except Exception as e:
            print(f"Error loading {region} shapefile: {e}")
    
    comments_paths = {k: v['comments'] for k, v in data_config.items()}
    region_paths = {k: v['regions'] for k, v in data_config.items()}
    yearly_data = process_yearly_themes(comments_paths, region_paths)
    
    output_dir = "processing_output\\fig_3_c"
    create_combined_shp_with_topics(yearly_data, global_gdfs, output_dir)

if __name__ == "__main__":
    main()