import json
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from collections import defaultdict
import os

def process_data(comments_path, mapping_path, shp_path, output_dir, region_field, region_name):
    """Process comment data and generate regional statistics in CSV format.
    
    Args:
        comments_path (str): Path to JSON comment data
        mapping_path (str): Path to UID-region mapping JSON
        shp_path (str): Path to boundary Shapefile
        output_dir (str): Output directory path
        region_field (str): Region ID field in Shapefile
        region_name (str): Region name for output file naming
    """
    
    # 1. Load comment data
    print(f"Loading {region_name} comment data...")
    try:
        with open(comments_path, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)
    except Exception as e:
        print(f"Failed to load comment data: {e}")
        return

    # 2. Load region mapping
    print(f"Loading {region_name} region mapping...")
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            region_mapping = json.load(f)
    except Exception as e:
        print(f"Failed to load mapping data: {e}")
        return

    # 3. Calculate user comment counts
    uid_comment_counts = defaultdict(int)
    for comment in comments_data['comment_list']:
        uid = str(comment['uid'])
        uid_comment_counts[uid] += 1

    # 4. Aggregate by region
    print(f"Calculating {region_name} region stats...")
    region_stats = {}
    for region_id, uids in tqdm(region_mapping.items(), desc=f"Processing {region_name}"):
        region_stats[region_id] = sum(uid_comment_counts.get(uid, 0) for uid in uids)
    
    # 5. Process boundaries
    print(f"Processing {region_name} boundaries...")
    try:
        gdf = gpd.read_file(shp_path)
        if region_field not in gdf.columns:
            raise ValueError(f"Missing field: {region_field}")
        gdf['Num_review'] = gdf[region_field].map(region_stats).fillna(0).astype(int)
    except Exception as e:
        print(f"Boundary processing failed: {e}")
        return
    
    # 6. Save CSV with standardized naming
    csv_filename = f"{region_name}_regions_with_comment_count.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        pd.DataFrame(gdf.drop(columns='geometry')).to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Successfully saved: {csv_path}\n")
    except Exception as e:
        print(f"Failed to save CSV: {e}")


if __name__ == "__main__":
    OUTPUT_DIR = 'Data\\interim\\fig_1_c'
    
    # Process China data
    process_data(
        comments_path='Data\\interim\\LLM_result_processing\\china_comments.json',
        mapping_path='Data\\input\\UID mapping\\China\\Ownership of Charging Station Area.json',
        shp_path='Data\\input\\GADM\\china\\gadm41_CHN_1.shp',
        output_dir=OUTPUT_DIR,
        region_field='HASC_1',
        region_name='china'
    )
    
    # Process Europe data
    process_data(
        comments_path='Data\\interim\\LLM_result_processing\\europe_comments.json',
        mapping_path='Data\\input\\UID mapping\\Europe\\Ownership of Charging Station Area.json',
        shp_path='Data\\input\\GADM\\europe\\Europe.shp',
        output_dir=OUTPUT_DIR,
        region_field='HASC_1',
        region_name='europe'
    )
    
    # Process USA data
    process_data(
        comments_path='Data\\interim\\LLM_result_processing\\usa_comments.json',
        mapping_path='Data\\input\\UID mapping\\USA\\Ownership of Charging Station Area.json',
        shp_path='Data\\input\\GADM\\usa\\gadm41_USA_1.shp',
        output_dir=OUTPUT_DIR,
        region_field='HASC_1',
        region_name='usa'
    )
