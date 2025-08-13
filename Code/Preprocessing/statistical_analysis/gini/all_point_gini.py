import os
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import shutil

class GiniCalculator:
    def __init__(self, charger_shp_path, population_tiff_path, region_shapefile, output_folder):
        """
        Initialize Gini coefficient calculator
        
        Parameters:
            charger_shp_path: Path to charging station Shapefile
            population_tiff_path: Path to population density TIFF file
            region_shapefile: Path to regional administrative division Shapefile
            output_folder: Path to output folder
        """
        self.charger_shp_path = charger_shp_path
        self.population_tiff_path = population_tiff_path
        self.region_shapefile = region_shapefile
        self.output_folder = output_folder
        
        # Create output folders (temporary)
        os.makedirs(os.path.join(output_folder, "temp_tiffs"), exist_ok=True)
        os.makedirs(os.path.join(output_folder, "Gini_Results"), exist_ok=True)

    def points_to_tiff(self):
        """
        Convert charging station Shapefile to TIFF grid (temporary)
        """
        with rasterio.open(self.population_tiff_path) as src:
            transform = src.transform
            resolution = src.res
            width = src.width
            height = src.height
            crs = src.crs
            mask_nodata = src.nodata
            mask_data = src.read(1)

        output_tiff_folder = os.path.join(self.output_folder, "temp_tiffs")
        
        # Get filename from input path
        shp_file = os.path.basename(self.charger_shp_path)
        tiff_name = shp_file.replace(".shp", ".tiff")
        tiff_path = os.path.join(output_tiff_folder, tiff_name)
        
        # Read point data
        points = gpd.read_file(self.charger_shp_path)
        if points.crs != crs:
            points = points.to_crs(crs)

        # Create count array - using float32 type to handle large nodata values
        count_array = np.zeros((height, width), dtype=np.float32)

        # Rasterize point data
        for point in tqdm(points.geometry, desc=f"Processing {shp_file}"):
            if point is not None:
                x, y = point.x, point.y
                col, row = ~transform * (x, y)
                col, row = int(col), int(row)
                if 0 <= row < height and 0 <= col < width:
                    count_array[row, col] += 1

        # Handle nodata values - using original nodata value directly
        if mask_nodata is not None:
            count_array[mask_data == mask_nodata] = mask_nodata

        # Save TIFF file (temporary)
        with rasterio.open(
            tiff_path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=count_array.dtype,
            crs=crs,
            transform=transform,
            nodata=mask_nodata if mask_nodata is not None else None,
        ) as dst:
            dst.write(count_array, 1)
        
        return tiff_path

    def calculate_gini_coefficients(self):
        """
        Calculate Gini coefficients for regions and save only CSV tables
        """
        tiff_folder = os.path.join(self.output_folder, "temp_tiffs")
        output_folder = os.path.join(self.output_folder, "Gini_Results")
        
        regions = gpd.read_file(self.region_shapefile)
        
        # Get charger TIFF file
        shp_file = os.path.basename(self.charger_shp_path)
        tiff_file = shp_file.replace(".shp", ".tiff")
        tiff_path = os.path.join(tiff_folder, tiff_file)
        
        category = os.path.splitext(shp_file)[0]
        
        print(f"\nCalculating Gini coefficients for: {category}")
        
        with rasterio.open(tiff_path) as charger_src, \
             rasterio.open(self.population_tiff_path) as pop_src:
            
            if regions.crs != charger_src.crs:
                regions = regions.to_crs(charger_src.crs)
            
            results = []
            
            for idx, region in tqdm(regions.iterrows(), total=len(regions), 
                                   desc=f"Processing {category}"):
                geometry = region.geometry
                region_name = region.get("HASC_1", f"Region_{idx}")
                
                try:
                    # Crop region data
                    pop_masked, _ = mask(pop_src, [geometry], crop=True, nodata=pop_src.nodata)
                    charger_masked, _ = mask(charger_src, [geometry], crop=True, nodata=charger_src.nodata)
                except ValueError:
                    results.append({
                        "region": region_name,
                        "gini": np.nan
                    })
                    continue
                
                pop_masked = pop_masked[0]
                charger_masked = charger_masked[0]
                
                # Filter valid data
                mask_valid = (pop_masked != pop_src.nodata) & (charger_masked != charger_src.nodata)
                valid_pop = pop_masked[mask_valid]
                valid_charger = charger_masked[mask_valid]
                
                if len(valid_pop) == 0:
                    results.append({
                        "HASC_1": region_name,
                        "gini": np.nan
                    })
                    continue
                
                total_charger = int(np.sum(valid_charger))
                total_population = np.sum(valid_pop)
                
                if total_charger == 0:
                    results.append({
                        "HASC_1": region_name,
                        "gini": np.nan
                    })
                    continue
                
                # Calculate Gini coefficient
                gini = self._calculate_simple_gini(valid_pop, valid_charger)
                
                results.append({
                    "HASC_1": region_name,
                    "gini": gini,
                    "total_charger": total_charger,
                    "total_population": total_population
                })
            
            # Save results to CSV only (don't save Shapefile)
            result_df = pd.DataFrame(results)
            
            # Save CSV
            output_csv_path = os.path.join(output_folder, f"{category}_gini.csv")
            result_df.to_csv(output_csv_path, index=False)
            print(f"Saved Gini coefficient results to CSV: {output_csv_path}")

    def _calculate_simple_gini(self, population, charger):
        """
        Calculate a simple Gini coefficient, handling zero values
        
        Args:
            population: Array of population values
            charger: Array of charger counts
            
        Returns:
            float: Gini coefficient
        """
        # Create DataFrame
        df = pd.DataFrame({
            'population': population,
            'charger': charger
        })
        
        # Calculate chargers per capita
        df['charger_per_capita'] = np.where(
            df['population'] > 0,
            df['charger'] / df['population'],
            np.where(df['charger'] > 0, np.inf, 0)
        )
        
        # Sort by chargers per capita
        df = df.sort_values('charger_per_capita')
        
        # Calculate cumulative percentages
        df['cum_pop'] = df['population'].cumsum() / df['population'].sum()
        df['cum_charger'] = df['charger'].cumsum() / df['charger'].sum()
        
        # Add starting point (0,0)
        df = pd.concat([
            pd.DataFrame({'cum_pop': [0], 'cum_charger': [0]}),
            df[['cum_pop', 'cum_charger']]
        ], ignore_index=True)
        
        # Calculate area under Lorenz curve
        B = np.trapz(df['cum_charger'], df['cum_pop'])
        
        # Calculate Gini coefficient
        gini = 1 - 2 * B
        return gini

    def cleanup_temp_files(self):
        """Remove all temporary files (TIFFs and intermediate folders)"""
        temp_folders = [
            os.path.join(self.output_folder, "temp_tiffs"),
            os.path.join(self.output_folder, "Gini_Results")  # We'll keep the CSV here
        ]
        
        for folder in temp_folders:
            if os.path.exists(folder):
                try:
                    if folder.endswith("temp_tiffs"):
                        shutil.rmtree(folder)
                        print(f"Deleted temporary folder: {folder}")
                except Exception as e:
                    print(f"Error deleting folder {folder}: {e}")

    def run_analysis(self):
        """
        Run complete analysis pipeline and clean up temporary files
        """
        print("="*50)
        print("Starting Charger Distribution Equity Analysis")
        print("="*50)
        
        try:
            steps = [
                ("Converting point data to TIFF", self.points_to_tiff),
                ("Calculating Gini coefficients", self.calculate_gini_coefficients),
            ]
            
            for step_name, step_func in steps:
                print(f"\n{'='*20} {step_name} {'='*20}")
                step_func()
            
            # Clean up temporary files
            print("\nCleaning up temporary files...")
            self.cleanup_temp_files()
            
        except Exception as e:
            print(f"\nError during analysis: {e}")
            raise
        finally:
            print("\n" + "="*50)
            print("Analysis completed!")
            print("="*50)

if __name__ == "__main__":
    # Configuration for China
    charger_shp_path = "Data\\input\\all_charger_shp\\china_chargers.shp"
    population_tiff_path = "Data\\input\\worldpop\\chn_ppp_2020_1km_Aggregated_UNadj.tif"
    region_shapefile = "Data\\input\\GADM\\china\\gadm41_CHN_1.shp"
    output_folder = "Data\\interim\\figure_4\\all_point\\China"

    # Run analysis
    analyzer = GiniCalculator(charger_shp_path, population_tiff_path, region_shapefile, output_folder)
    analyzer.run_analysis()
    
    # Configuration for Europe
    charger_shp_path = "Data\\input\\all_charger_shp\\europe_chargers.shp"
    population_tiff_path = "Data\\input\\worldpop\\europe1.tif"
    region_shapefile = "Data\\input\\GADM\\europe\\Europe.shp"
    output_folder = "Data\\interim\\figure_4\\all_point\\europe"
    
    # Run analysis
    analyzer = GiniCalculator(charger_shp_path, population_tiff_path, region_shapefile, output_folder)
    analyzer.run_analysis()
    
    # Configuration for USA
    charger_shp_path = "Data\\input\\all_charger_shp\\usa_chargers.shp"
    population_tiff_path = "Data\\input\\worldpop\\usa_ppp_2020_1km_Aggregated_UNadj.tif"
    region_shapefile = "Data\\input\\GADM\\usa\\gadm41_USA_1.shp"
    output_folder = "Data\\interim\\figure_4\\all_point\\usa"
    
    # Run analysis
    analyzer = GiniCalculator(charger_shp_path, population_tiff_path, region_shapefile, output_folder)
    analyzer.run_analysis()