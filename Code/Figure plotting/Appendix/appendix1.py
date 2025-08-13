import json
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import PercentFormatter

# ======================
# Academic Style Settings
# ======================
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.dpi': 300,
    'axes.facecolor': 'white',
    'grid.color': '#e0e0e0'
})

# Load analysis results
with open('Data\\interim\\appendix1\\appendix1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define keyword colors (colorblind-friendly palette)
keyword_colors = {
    'slow charging': '#1f77b4',  # Blue
    'slow': '#ff7f0e',          # Orange
    'broken': '#2ca02c',        # Green
    'not working': '#d62728'    # Red
}
string_ = {
    "China":"(a)",
    "USA":"(b)",
    "Europe":"(c)",
}
# Create charts for each region
for region, region_data in data.items():
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Collect and sort all years
    years = sorted([int(y) for y in region_data.keys()])
    if not years:
        continue  # Skip regions with no data
    
    # Plot lines for each keyword
    for keyword in ['slow charging', 'slow', 'broken', 'not working']:
        values = []
        valid_years = []
        
        for year in range(min(years), max(years)+1):
            year_str = str(year)
            if year_str in region_data and keyword in region_data[year_str]:
                values.append(region_data[year_str][keyword])
                valid_years.append(year)
        
        if values:  # Only plot if data exists
            ax.plot(valid_years, values, 
                   marker='o', 
                   markersize=8,
                   label=keyword.capitalize(),
                   color=keyword_colors[keyword],
                   linewidth=2.5,
                   alpha=0.8)
    
    # Chart decorations
    ax.set_title(f'{string_[region]} {region}', pad=20, fontweight='bold')
    ax.set_xlabel('Year', labelpad=10)
    ax.set_ylabel('Proportion of Reviews', labelpad=10)
    
    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))
    
    # Set x-axis to integer years
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Grid and frame
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    
    # Legend outside plot
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), 
              frameon=True, framealpha=0.9)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    plt.savefig(f'figure\\appendix1\\{region}_keyword_trend.png', dpi=300, bbox_inches='tight')
    plt.close()  # Close figure to prevent display if running in script

print("Visualization complete. Charts saved as PNG files.")