import json
import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import matplotlib

plt.rcParams['font.family'] = 'Times New Roman'

# Themes
themes = [
    "Charging Functionality and Reliability",
    "Location and Availability",
    "Pricing and Payment",
]
themes1 = {
    "Charging Functionality and Reliability": "(a)",
    "Location and Availability": "(b)",
    "Pricing and Payment": "(c)"
}

# Custom color mapping
def get_color_func_for_theme(theme):
    if theme == "Charging Functionality and Reliability":
        colors = ["#AED6F1", "#3498DB", "#0A3D62"]
    elif theme == "Location and Availability":
        colors = ["#FADBD8", "#E74C3C", "#7B241C"]
    elif theme == "Pricing and Payment":
        colors = ["#D7CCC8", "#8D6E63", "#5D4037"]
    
    cmap = LinearSegmentedColormap.from_list(f"custom_{theme}", colors)
    return lambda word, font_size, position, orientation, random_state, **kwargs: \
        matplotlib.colors.rgb2hex(cmap(np.random.rand()))

# Load the processed data from JSON
with open('Data\\interim\\appendix3\\wordcloud_keywords.json', 'r', encoding='utf-8') as f:
    all_region_data = json.load(f)

# Create one figure per theme
for theme in themes:
    # Create a new figure for this theme
    plt.figure(figsize=(12, 4))
    plt.suptitle(f"{themes1[theme]} {theme}", fontsize=16, fontweight='bold', y=0.93)
    
    # Create subplots for each region
    for j, region_name in enumerate(['China', 'USA', 'Europe']):
        ax = plt.subplot(1, 3, j+1)
        
        if region_name in all_region_data and theme in all_region_data[region_name]:
            keywords = all_region_data[region_name][theme]
            filtered_keywords = {k: v for k, v in keywords.items() if v >= 10}
            
            if filtered_keywords:
                wordcloud = WordCloud(
                    width=400,
                    height=300,
                    background_color='white',
                    font_path='simhei.ttf',
                    color_func=get_color_func_for_theme(theme),
                    max_words=200,
                    relative_scaling=0.5,
                    prefer_horizontal=0.9,
                    min_font_size=10,
                    max_font_size=150,
                ).generate_from_frequencies(filtered_keywords)
                
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.set_title(region_name, fontsize=16, fontweight='bold')
                ax.axis('off')
            else:
                ax.text(0.5, 0.5, 'No data', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes)
                ax.set_title(region_name, fontsize=16, fontweight='bold')
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, 'No data', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes)
            ax.set_title(region_name, fontsize=16, fontweight='bold')
            ax.axis('off')
    
    plt.tight_layout()
    os.makedirs('figure\\appendix3', exist_ok=True)
    plt.savefig(f'figure\\appendix3\\{theme.replace(" ", "_")}_wordclouds.png', 
                bbox_inches='tight', dpi=300)
    plt.close()
    print(f'Generated figure for theme: {theme}')

print('All theme-specific figures generated!')