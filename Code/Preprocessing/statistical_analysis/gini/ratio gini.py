import os
import pandas as pd

# Configure paths for 6 CSV files (3 regions × 2 datasets each)
CSV_PATHS = {
    "China": {
        "charger_positve": "Data\\interim\\figure_4\\positive\\china\\Gini_CSV_Results\\Overall sentiment_gini_results.csv",
        "charger_all": "Data\\interim\\figure_4\\all_point\\China\\Gini_Results\\china_chargers_gini.csv"
    },
    "USA": {
        "charger_positve": "Data\\interim\\figure_4\\positive\\usa\\Gini_CSV_Results\\Overall sentiment_gini_results.csv",
        "charger_all": "Data\\interim\\figure_4\\all_point\\usa\\Gini_Results\\usa_chargers_gini.csv"
    },
    "Europe": {
        "charger_positve": "Data\\interim\\figure_4\\positive\\europe\\Gini_CSV_Results\\Overall sentiment_gini_results.csv",
        "charger_all": "Data\\interim\\figure_4\\all_point\\europe\\Gini_Results\\europe_chargers_gini.csv"
    }
}

# Output directory path
OUTPUT_FOLDER = "Data\\interim\\figure_4\\ratio"

def process_all_regions():
    """Main function to process all regions"""
    for region_name, paths in CSV_PATHS.items():
        print(f"\n{'='*30} Processing region: {region_name} {'='*30}")
        
        # Check if all files exist for this region
        if not all(os.path.exists(p) for p in paths.values()):
            print(f"Warning: Missing files for {region_name}, skipping...")
            continue
        
        # Create output directory for this region
        region_output = os.path.join(OUTPUT_FOLDER, region_name)
        os.makedirs(region_output, exist_ok=True)
        
        # Calculate ratio and save results
        calculate_ratio_and_save(
            csv_path1=paths["charger_positve"],
            csv_path2=paths["charger_all"],
            output_folder=region_output,
            region_name=region_name
        )

def calculate_ratio_and_save(csv_path1, csv_path2, output_folder, region_name):
    """
    Process two CSV files for a single region and calculate the gini ratio
    
    Args:
        csv_path1: Path to first CSV file (positive charger data)
        csv_path2: Path to second CSV file (all charger data)
        output_folder: Directory to save results
        region_name: Name of current region being processed
    """
    try:
        # Read both CSV files into DataFrames
        df1 = pd.read_csv(csv_path1)
        df2 = pd.read_csv(csv_path2)
        
        # Verify required columns exist
        for field in ['HASC_1', 'gini']:
            if field not in df1.columns or field not in df2.columns:
                raise ValueError(f"Missing required field: {field}")
        
        # Merge the two datasets on HASC_1 field
        merged = df1.merge(
            df2[['HASC_1', 'gini']], 
            on='HASC_1', 
            suffixes=('_charger_positve', '_charger_all')
        )
        
        # Calculate ratio with small epsilon to avoid division by zero
        merged['gini_ratio'] = (merged['gini_charger_positve'] + 1e-6) / (merged['gini_charger_all'] + 1e-6)
        
        # Keep only the required columns in final output
        result = merged[['HASC_1', 'gini_ratio']]
        
        # Save results to CSV
        output_csv = os.path.join(output_folder, f"gini_ratio_{region_name}.csv")
        result.to_csv(output_csv, index=False)
        print(f"✓ Successfully saved ratio results: {output_csv}")
        
    except Exception as e:
        print(f"× Processing failed: {str(e)}")

if __name__ == "__main__":
    # Execute the processing pipeline
    process_all_regions()
    print("\nAll regions processed! Results saved in:", OUTPUT_FOLDER)