import os
import json
from collections import defaultdict
import shapefile
from tqdm import tqdm
import rasterio
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import pandas as pd
from rasterio.mask import mask
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import shutil

class ChargingStationSentimentAnalyzer:
    # All evaluation categories to analyze
    EVALUATION_CATEGORIES = [
        "Overall sentiment",
    ]

    # Sentiment types
    SENTIMENT_TYPES = ["Positive", "Negative", "Neutral"]

    def __init__(self, input_json_path, output_base_folder, population_tiff_path, region_shapefile):
        """
        Initialize the analyzer
        
        Parameters:
            input_json_path: Path to input JSON file
            output_base_folder: Base folder for output files
            population_tiff_path: Path to population density TIFF file
            region_shapefile: Path to regional administrative division Shapefile
        """
        self.input_json_path = input_json_path
        self.output_base_folder = output_base_folder
        self.population_tiff_path = population_tiff_path
        self.region_shapefile = region_shapefile
        self.uid_data = None
        self.location_info = None
        self.final_results = None

    def process_comments(self):
        """
        Process comment data, counting sentiment distribution for each POI across evaluation categories
        """
        self.uid_data = defaultdict(
            lambda: {
                category: defaultdict(int) 
                for category in self.EVALUATION_CATEGORIES
            }
        )
        
        self.location_info = defaultdict(dict)

        with open(self.input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for comment in tqdm(data['comment_list'], desc="Processing comments"):
                try:
                    uid = comment['uid']
                    lon = float(comment['longitude'])
                    lat = float(comment['latitude'])
                    date_str = comment.get('date', '')
                    year = int(date_str[:4])
                    if year < 2014 or year > 2025:
                        continue
                    self.location_info[uid] = {
                        "longitude": lon,
                        "latitude": lat
                    }
                    
                    for category in self.EVALUATION_CATEGORIES:
                        sentiment = comment['sentiment'].get(category, "null")
                        self.uid_data[uid][category][sentiment] += 1
                            
                except Exception as e:
                    print(f"Error processing comment: {e}")
                    continue

    def generate_final_results(self):
        """
        Generate final results including main sentiment for each POI across dimensions
        """
        self.final_results = []
        
        for uid, categories in self.uid_data.items():
            poi_result = {"uid": uid}
            poi_result.update(self.location_info[uid])
            
            for category in self.EVALUATION_CATEGORIES:
                sentiments = categories.get(category, {})
                
                for st in self.SENTIMENT_TYPES:
                    poi_result[f"{category}_{st}_count"] = sentiments.get(st, 0)
                
                if sentiments:
                    # Exclude "null" when selecting main sentiment
                    filtered_sentiments = {k: v for k, v in sentiments.items() if k != "null"}
                    if filtered_sentiments:
                        main_sentiment = max(filtered_sentiments.items(), key=lambda x: x[1])[0]
                    else:
                        main_sentiment = "null"
                else:
                    main_sentiment = "null"
                poi_result[f"{category}_main_sentiment"] = main_sentiment
            
            self.final_results.append(poi_result)

    def calculate_gini_coefficients(self):
        """
        Calculate Gini coefficients and save to Gini_Results folder
        Only calculate standard Gini coefficient, considering (0,0) point
        """
        # Create temporary folders for intermediate files
        temp_tiff_folder = os.path.join(self.output_base_folder, "Temp_TIFFs")
        temp_shp_folder = os.path.join(self.output_base_folder, "Temp_Shapefiles")
        os.makedirs(temp_tiff_folder, exist_ok=True)
        os.makedirs(temp_shp_folder, exist_ok=True)
        
        # Generate necessary files for Gini calculation
        self._generate_required_files_for_gini(temp_shp_folder, temp_tiff_folder)
        
        output_folder = os.path.join(self.output_base_folder, "Gini_Results")
        os.makedirs(output_folder, exist_ok=True)
        
        regions = gpd.read_file(self.region_shapefile)
        
        for category in self.EVALUATION_CATEGORIES:
            tiff_path = os.path.join(temp_tiff_folder, f"{category}_Positive.tiff")
            
            if not os.path.exists(tiff_path):
                print(f"Warning: TIFF file not found for {category} positive sentiment: {tiff_path}")
                continue
                
            print(f"\nCalculating Gini coefficients for {category} positive sentiment...")
            
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
                        pop_masked, _ = mask(pop_src, [geometry], crop=True, nodata=pop_src.nodata)
                        charger_masked, _ = mask(charger_src, [geometry], crop=True, nodata=charger_src.nodata)
                    except ValueError:
                        results.append({
                            "HASC_1": region_name,
                            "gini": np.nan
                        })
                        continue
                    
                    pop_masked = pop_masked[0]
                    charger_masked = charger_masked[0]
                    
                    # Keep all grids (including zero-population grids)
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
                    
                    # Calculate standard Gini coefficient
                    gini = self._calculate_simple_gini(valid_pop, valid_charger)
                    
                    results.append({
                        "HASC_1": region_name,
                        "gini": gini
                    })
                
                # Save results to CSV
                result_df = pd.DataFrame(results)
                output_csv_path = os.path.join(output_folder, f"{category}_gini_results.csv")
                result_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
                print(f"Saved Gini results for {category} to {output_csv_path}")
        
        # Clean up temporary files
        shutil.rmtree(temp_tiff_folder)
        shutil.rmtree(temp_shp_folder)

    def _generate_required_files_for_gini(self, temp_shp_folder, temp_tiff_folder):
        """
        Generate only the necessary files for Gini coefficient calculation
        """
        # Generate final results (needed for shapefile creation)
        self.generate_final_results()
        
        # Create only positive sentiment shapefiles
        for category in self.EVALUATION_CATEGORIES:
            self._create_positive_sentiment_shapefile(category, temp_shp_folder)
        
        # Generate TIFF files for positive sentiment only
        with rasterio.open(self.population_tiff_path) as src:
            transform = src.transform
            resolution = src.res
            width = src.width
            height = src.height
            crs = src.crs
            mask_nodata = src.nodata
            mask_data = src.read(1)

        for category in self.EVALUATION_CATEGORIES:
            shp_path = os.path.join(temp_shp_folder, f"{category}_Positive_points.shp")
            
            if os.path.exists(shp_path):
                tiff_path = os.path.join(temp_tiff_folder, f"{category}_Positive.tiff")
                os.makedirs(os.path.dirname(tiff_path), exist_ok=True)
                
                self._process_shapefile_to_tiff(
                    shp_path, tiff_path, 
                    width, height, transform, crs, 
                    mask_data, mask_nodata
                )

    def _create_positive_sentiment_shapefile(self, category, output_folder):
        """
        Create shapefile for positive sentiment only
        """
        sentiment = "Positive"
        filtered_data = [
            item for item in self.final_results 
            if item[f"{category}_main_sentiment"] == sentiment
        ]
        
        if not filtered_data:
            return
        
        shp_path = os.path.join(output_folder, f"{category}_{sentiment}_points.shp")
        os.makedirs(output_folder, exist_ok=True)
        
        w = shapefile.Writer(shp_path, shapefile.POINT)
        w.autoBalance = 1
        
        w.field('uid', 'C', 50)
        w.field('lon', 'F', 19, 5)
        w.field('lat', 'F', 19, 5)
        w.field('count', 'N')
        
        for item in tqdm(filtered_data, desc=f"Creating {category} {sentiment} Shapefile"):
            lon = item['longitude']
            lat = item['latitude']
            
            w.point(lon, lat)
            w.record(
                item['uid'],
                lon,
                lat,
                item[f"{category}_{sentiment}_count"]
            )
        
        w.close()
        self._create_prj_file(shp_path)

    def _create_prj_file(self, shp_path):
        """
        Create PRJ projection file
        """
        prj_content = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'
        prj_path = os.path.splitext(shp_path)[0] + '.prj'
        
        with open(prj_path, 'w') as f:
            f.write(prj_content)

    def _process_shapefile_to_tiff(self, shp_path, tiff_path, width, height, transform, crs, mask_data, mask_nodata):
        """
        Process single Shapefile and generate TIFF file
        """
        points = gpd.read_file(shp_path)
        if points.crs != crs:
            points = points.to_crs(crs)

        # Use int32 type to avoid overflow
        count_array = np.zeros((height, width), dtype=np.int32)

        for point in tqdm(points.geometry, desc=f"Processing {os.path.basename(shp_path)}"):
            if point is not None:
                x, y = point.x, point.y
                col, row = ~transform * (x, y)
                col, row = int(col), int(row)
                if 0 <= row < height and 0 <= col < width:
                    if count_array[row, col] < np.iinfo(np.int32).max - 1:
                        count_array[row, col] += 1

        # Handle nodata values
        if mask_nodata is not None:
            nodata_value = np.iinfo(np.int32).min if mask_nodata < np.iinfo(np.int32).min else mask_nodata
            nodata_value = np.iinfo(np.int32).max if nodata_value > np.iinfo(np.int32).max else nodata_value
            count_array[mask_data == mask_nodata] = nodata_value

        # Check for values exceeding int32 range
        if np.any(count_array > np.iinfo(np.int32).max):
            print("Warning: Some count values exceed int32 range, clipping")
            count_array = np.clip(count_array, np.iinfo(np.int32).min, np.iinfo(np.int32).max)

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
            nodata=nodata_value if mask_nodata is not None else None,
        ) as dst:
            dst.write(count_array, 1)

    def _calculate_simple_gini(self, population, charger):
        """
        Calculate simple Gini coefficient, considering (0,0) point
        """
        # Create DataFrame
        df = pd.DataFrame({
            'population': population,
            'charger': charger
        })
        
        # Calculate charger per capita
        df['charger_per_capita'] = np.where(
            df['population'] > 0,
            df['charger'] / df['population'],
            np.where(df['charger'] > 0, np.inf, 0)
        )
        
        # Sort by charger per capita
        df = df.sort_values('charger_per_capita')
        
        # Calculate cumulative percentages
        df['cum_pop'] = df['population'].cumsum() / df['population'].sum()
        df['cum_charger'] = df['charger'].cumsum() / df['charger'].sum()
        
        # Add (0,0) point
        df = pd.concat([
            pd.DataFrame({'cum_pop': [0], 'cum_charger': [0]}),
            df[['cum_pop', 'cum_charger']]
        ], ignore_index=True)
        
        # Calculate area under Lorenz curve
        B = np.trapz(df['cum_charger'], df['cum_pop'])
        
        # Calculate Gini coefficient
        gini = 1 - 2 * B
        return gini

    def run_analysis(self):
        """
        Run streamlined analysis pipeline focusing only on Gini coefficient CSV results
        """
        print("="*50)
        print("Starting Charging Station Sentiment Analysis Pipeline")
        print("="*50)
        
        # Only run necessary steps for Gini coefficient calculation
        print("\nProcessing comment data")
        self.process_comments()
        
        print("\nCalculating Gini coefficients")
        self.calculate_gini_coefficients()


if __name__ == "__main__":
    # Input/output configuration for Europe
    input_json_path = "Data\\interim\\LLM_result_processing\\europe_comments.json"
    output_base_folder = "Data\\interim\\figure_4\\positive_point\\europe"
    population_tiff_path = "Data\\input\\worldpop\\europe1.tif"
    region_shapefile = "Data\\input\\GADM\\europe\\Europe.shp"
    
    # Create analyzer and run analysis for Europe
    analyzer = ChargingStationSentimentAnalyzer(input_json_path, output_base_folder, population_tiff_path, region_shapefile)
    analyzer.run_analysis()
    
    # Input/output configuration for China
    input_json_path = "Data\\interim\\LLM_result_processing\\china_comments.json"
    output_base_folder = "Data\\interim\\figure_4\\positive_point\\china"
    population_tiff_path = "Data\\input\\worldpop\\chn_ppp_2020_1km_Aggregated_UNadj.tif"
    region_shapefile = "Data\\input\\GADM\\china\\gadm41_CHN_1.shp"
    
    # Create analyzer and run analysis for China
    analyzer = ChargingStationSentimentAnalyzer(input_json_path, output_base_folder, population_tiff_path, region_shapefile)
    analyzer.run_analysis()
    
    # Input/output configuration for USA
    input_json_path = "Data\\interim\\LLM_result_processing\\usa_comments.json"
    output_base_folder = "Data\\interim\\figure_4\\positive_point\\usa"
    population_tiff_path = "Data\\input\\worldpop\\usa_ppp_2020_1km_Aggregated_UNadj.tif"
    region_shapefile = "Data\\input\\GADM\\usa\\gadm41_USA_1.shp"
    
    # Create analyzer and run analysis for USA
    analyzer = ChargingStationSentimentAnalyzer(input_json_path, output_base_folder, population_tiff_path, region_shapefile)
    analyzer.run_analysis()