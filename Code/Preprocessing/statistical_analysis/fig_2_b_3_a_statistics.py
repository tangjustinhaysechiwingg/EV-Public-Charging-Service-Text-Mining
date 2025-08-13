import json
import geopandas as gpd
import pandas as pd
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm
import os
import shutil

# Global Configuration
GLOBAL_CONFIG = {
    'regions': {
        'China': {
            'input': {
                'region_mapping': 'Data\\input\\UID mapping\\China\\Ownership of Charging Station Area.json',
                'comments_data': 'Data\\interim\\LLM_result_processing\\china_comments.json',
                'shapefile': 'Data\\input\\GADM\\china\\gadm41_CHN_1.shp'
            },
            'output': {
                'yearly_results_dir': os.path.join('Data','interim','fig_2_b_3_a_statistics', 'china', 'yearly_sentiment_results'),
                'summary_tables_dir': os.path.join('Data','interim','fig_2_b_3_a_statistics', 'china', 'table')
            }
        },
        'USA': {
            'input': {
                'region_mapping': 'Data\\input\\UID mapping\\USA\\Ownership of Charging Station Area.json',
                'comments_data': 'Data\\interim\\LLM_result_processing\\usa_comments.json',
                'shapefile': 'Data\\input\\GADM\\usa\\gadm41_USA_1.shp'
            },
            'output': {
                'yearly_results_dir': os.path.join('Data','interim','fig_2_b_3_a_statistics', 'usa', 'yearly_sentiment_results'),
                'summary_tables_dir': os.path.join('Data','interim','fig_2_b_3_a_statistics', 'usa', 'table')
            }
        },
        'Europe': {
            'input': {
                'region_mapping': 'Data\\input\\UID mapping\\Europe\\Ownership of Charging Station Area.json',
                'comments_data': 'Data\\interim\\LLM_result_processing\\europe_comments.json',
                'shapefile': 'Data\\input\\GADM\\europe\\Europe.shp'
            },
            'output': {
                'yearly_results_dir': os.path.join('Data','interim','fig_2_b_3_a_statistics', 'europe', 'yearly_sentiment_results'),
                'summary_tables_dir': os.path.join('Data','interim','fig_2_b_3_a_statistics', 'europe', 'table')
            }
        },
    },
    'analysis_dimensions': [
        "Charging Functionality and Reliability",
        "Charging Performance",
        "Location and Availability",
        "Pricing and Payment",
        "Environment and Service Experience",
        "Overall sentiment",
    ],
    'years': range(2015, 2025)  # 2015-2024
}

def parse_date(date_str):
    """Parse date string in various formats"""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

def initialize_output_directories(region_config):
    """Create all necessary output directories"""
    for dir_type in ['yearly_results_dir', 'summary_tables_dir']:
        os.makedirs(region_config['output'][dir_type], exist_ok=True)

def load_input_data(region_config):
    """Load all input data for a region"""
    print(f"Loading data for {region_config['name']}...")
    try:
        with open(region_config['input']['region_mapping'], 'r', encoding='utf-8') as f:
            region_data = json.load(f)

        with open(region_config['input']['comments_data'], 'r', encoding='utf-8') as f:
            comments_data = json.load(f)['comment_list']

        print("Loading administrative boundaries...")
        gdf = gpd.read_file(region_config['input']['shapefile'])
        
        return region_data, comments_data, gdf
    except Exception as e:
        print(f"Error loading input data for {region_config['name']}: {e}")
        raise

def create_uid_to_region_mapping(region_data):
    """Create UID to region mapping"""
    uid_to_region = {}
    for region, uids in region_data.items():
        for uid in uids:
            uid_to_region[str(uid)] = region  # Ensure UID is string
    return uid_to_region

def analyze_sentiment_by_year(comments_data, uid_to_region, years, region_name):
    """Analyze sentiment by year for all dimensions"""
    print(f"\nStarting yearly analysis for {region_name}...")
    
    yearly_stats = {}
    for year in years:
        yearly_stats[year] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for comment in tqdm(comments_data, desc="Processing comments"):
        uid = str(comment.get('uid', comment.get('poi_uid', '')))  # Handle different UID fields
        
        if uid in uid_to_region:
            try:
                comment_date = parse_date(comment['date'])
                year = comment_date.year
                if year in yearly_stats:
                    region = uid_to_region[uid]
                    
                    # Handle Chinese sentiment data structure
                    sentiment_data = comment.get('sentiment', {})
                    
                    # Process each dimension
                    for dimension in GLOBAL_CONFIG['analysis_dimensions']:
                        if dimension in sentiment_data:
                            sentiment = sentiment_data[dimension]
                            
                            # Skip "未提及" entries
                            if sentiment == "null":
                                continue
                                
                            # Convert Chinese sentiments to English keys
                            if 'Positive' in sentiment:
                                sentiment_key = 'positive'
                            elif 'Neutral' in sentiment:
                                sentiment_key = 'neutral'
                            elif 'Negative' in sentiment:
                                sentiment_key = 'negative'
                            else:
                                continue  # Skip unknown sentiment values
                            
                            yearly_stats[year][region][dimension][sentiment_key] += 1
            except Exception as e:
                print(f"Error processing comment: {e}, content: {comment}")
    
    return yearly_stats

def process_yearly_stats(yearly_stats, gdf, years, region_config):
    """Process yearly statistics and generate outputs"""
    all_summary_data = {dim: [] for dim in GLOBAL_CONFIG['analysis_dimensions']}
    
    for year in years:
        print(f"\nProcessing {year} data for {region_config['name']}...")
        year_stats = yearly_stats[year]
        
        # First pass: Process all dimensions to collect summary data
        for dimension in GLOBAL_CONFIG['analysis_dimensions']:
            # Temporary variables to collect stats for this dimension
            year_pos = 0
            year_neu = 0
            year_neg = 0
            
            # Collect stats from all regions for this dimension
            for region, stats in year_stats.items():
                if dimension in stats:
                    dim_stats = stats[dimension]
                    year_pos += dim_stats.get('positive', 0)
                    year_neu += dim_stats.get('neutral', 0)
                    year_neg += dim_stats.get('negative', 0)
            
            # Add to summary data
            year_total = year_pos + year_neu + year_neg
            all_summary_data[dimension].append({
                'Year': year,
                'Positive': year_pos,
                'Neutral': year_neu,
                'Negative': year_neg,
                'Total': year_total,
                'Positive%': round(year_pos/year_total*100, 1) if year_total > 0 else 0,
                'Negative%': round(year_neg/year_total*100, 1) if year_total > 0 else 0
            })
        
        # Second pass: Only process "Overall sentiment" for CSV output
        for dimension in GLOBAL_CONFIG['analysis_dimensions']:
            if dimension != "Overall sentiment":
                continue
                
            year_gdf = gdf.copy()
            year_gdf['year'] = year
            year_gdf['positive'] = 0
            year_gdf['neutral'] = 0
            year_gdf['negative'] = 0
            year_gdf['final_sentiment'] = 'no_data'
            year_gdf['total_comments'] = 0
            
            for region, stats in year_stats.items():
                if dimension in stats:
                    dim_stats = stats[dimension]
                    mask = year_gdf['HASC_1'] == region
                    if mask.any():
                        pos = dim_stats.get('positive', 0)
                        neu = dim_stats.get('neutral', 0)
                        neg = dim_stats.get('negative', 0)
                        total = pos + neu + neg
                        
                        year_gdf.loc[mask, 'positive'] = pos
                        year_gdf.loc[mask, 'neutral'] = neu
                        year_gdf.loc[mask, 'negative'] = neg
                        year_gdf.loc[mask, 'total_comments'] = total
                        
                        if total > 0:
                            if neg == max(pos, neu, neg):
                                final_sentiment = 'negative'
                            elif pos == max(pos, neu, neg):
                                final_sentiment = 'positive'
                            else:
                                final_sentiment = 'neutral'
                            
                            year_gdf.loc[mask, 'final_sentiment'] = final_sentiment
            
            # Generate temporary SHP file (for processing)
            safe_dim_name = dimension.replace(' ', '_').replace('/', '_')
            temp_shp_dir = os.path.join(region_config['output']['yearly_results_dir'], f'temp_{year}_{safe_dim_name}')
            os.makedirs(temp_shp_dir, exist_ok=True)
            temp_shp = os.path.join(temp_shp_dir, f'sentiment_{year}_{safe_dim_name}.shp')
            
            try:
                year_gdf.to_file(temp_shp, encoding='utf-8')
            except Exception as e:
                print(f"Error saving temporary Shapefile: {e}")
            
            # Save CSV (final output we want to keep)
            year_csv = os.path.join(
                region_config['output']['yearly_results_dir'], 
                f'sentiment_stats_{year}_{safe_dim_name}.csv'
            )
            try:
                year_gdf[['HASC_1', 'positive', 'neutral', 'negative', 'total_comments', 'final_sentiment']].to_csv(
                    year_csv, index=False, encoding='utf-8-sig' if region_config['name'] == 'China' else 'utf-8')
            except Exception as e:
                print(f"Error saving CSV: {e}")
            
            # Clean up temporary SHP files
            try:
                shutil.rmtree(temp_shp_dir)
                print(f"Removed temporary SHP files for {year} {dimension}")
            except Exception as e:
                print(f"Error removing temporary SHP files: {e}")
    
    # Save summary tables for all dimensions
    save_summary_tables(all_summary_data, region_config)

def save_summary_tables(all_summary_data, region_config):
    """Save summary tables for all dimensions"""
    print("\nGenerating annual summary tables...")
    for dimension, data in all_summary_data.items():
        safe_dim_name = dimension.replace(' ', '_').replace('/', '_')
        summary_df = pd.DataFrame(data)
        
        summary_csv = os.path.join(
            region_config['output']['summary_tables_dir'], 
            f'sentiment_summary_2015-2024_{safe_dim_name}.csv'
        )
        try:
            summary_df.to_csv(summary_csv, index=False, 
                            encoding='utf-8-sig' if region_config['name'] == 'China' else 'utf-8')
            print(f"Summary table saved: {summary_csv}")
        except Exception as e:
            print(f"Error saving summary table: {e}")

def main():
    # Process each region
    for region_name, region_config in GLOBAL_CONFIG['regions'].items():
        try:
            # Add name to config for reference
            region_config['name'] = region_name
            
            # Initialize
            initialize_output_directories(region_config)
            
            # Load data
            region_data, comments_data, gdf = load_input_data(region_config)
            uid_to_region = create_uid_to_region_mapping(region_data)
            
            # Analyze sentiment
            yearly_stats = analyze_sentiment_by_year(
                comments_data, uid_to_region, GLOBAL_CONFIG['years'], region_name)
            
            # Process and save results
            process_yearly_stats(
                yearly_stats, gdf, GLOBAL_CONFIG['years'], region_config)
            
        except Exception as e:
            print(f"Error processing {region_name}: {e}")
            continue
    
    print("\nAll processing completed!")

if __name__ == "__main__":
    main()