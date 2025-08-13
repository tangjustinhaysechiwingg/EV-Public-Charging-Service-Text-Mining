import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

# ======================
# Academic style settings
# ======================
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'figure.autolayout': True,
    'axes.facecolor': 'white',
    'grid.color': '#e0e0e0'
})

# ======================
# Data loading and processing
# ======================
def load_and_process_data(filepath):
    """Load and process JSON data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        hourly_data = json.load(f)
    
    hours = sorted([int(h) for h in hourly_data.keys()])
    ratios = [hourly_data[str(h)] for h in hours]
    
    # Calculate time period averages
    early_hours = [h for h in hours if 0 <= h <= 6]
    late_hours = [h for h in hours if h > 6]
    early_avg = np.mean([hourly_data[str(h)] for h in early_hours]) if early_hours else 0
    late_avg = np.mean([hourly_data[str(h)] for h in late_hours]) if late_hours else 0
    
    return hours, ratios, early_avg, late_avg

# ======================
# Visualization function
# ======================
def create_visualization(hours, ratios, early_avg, late_avg, title):
    """Create academic-style bar chart"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Color scheme
    hour_color = '#4e79a7'  # Main color for hourly bars
    early_color = '#e15759' # Color for early average
    late_color = '#59a14f'  # Color for late average
    
    # Plot hourly bars (now with proper legend handle)
    hourly_bars = ax.bar(hours, ratios, color=hour_color, width=0.7, 
                       edgecolor='white', linewidth=0.5, alpha=0.9, zorder=2,
                       label='Hourly Ratio')
    
    # Plot period averages with more space
    avg_positions = [max(hours) + 3, max(hours) + 5]  # Increased spacing
    early_bar = ax.bar(avg_positions[0], early_avg, color=early_color, width=0.7,
                      edgecolor='white', linewidth=0.5, alpha=0.9, zorder=2,
                      label='0-6h Average')
    late_bar = ax.bar(avg_positions[1], late_avg, color=late_color, width=0.7,
                     edgecolor='white', linewidth=0.5, alpha=0.9, zorder=2,
                     label='7-23h Average')
    
    # Chart styling
    ax.set_title(title, pad=15, fontweight='bold',fontsize=13)
    ax.set_xlabel('Hour of the Day', labelpad=8)
    ax.set_ylabel('Percentage', labelpad=8)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))
    
    # X-axis settings - show every 3 hours
    xticks = [h for h in hours if h % 3 == 0] + avg_positions
    xlabels = [f'{h:02d}:00' for h in hours if h % 3 == 0] + ['0-6h', '7-23h']
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    
    # Grid lines
    ax.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=1)
    ax.set_axisbelow(True)
    
    # Legend - now showing all three elements
    ax.legend(loc='upper center', frameon=True, framealpha=0.9)
    
    # Divider line
    ax.axvline(max(hours) + 1.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.text(max(hours) + 0.8, max(ratios)*0.85, 'Period Averages', 
            rotation=90, va='center', ha='center', color='gray', fontsize=9)
    # Average value labels
    ax.text(avg_positions[0], early_avg, f'{early_avg:.1%}', 
        ha='center', va='bottom', fontsize=10)
    ax.text(avg_positions[1], late_avg, f'{late_avg:.1%}',
        ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    return fig, ax

# ======================
# Main program
# ======================
if __name__ == "__main__":
    # File path selection
    filepath = 'Data\\interim\\appendix2\\hourly_occupied_comment_ratio.json'

    
    
    # Load and process data
    hours, ratios, early_avg, late_avg = load_and_process_data(filepath)
    
    # Create visualization
    title = f'(c) Proportion of Reveiws Containing the Keyword "occupied" by Hour of the Day'
    fig, ax = create_visualization(hours, ratios, early_avg, late_avg, title)
    
    # Save figure
    plt.savefig('figure\\appendix2\\hourly_occupied_ratio_comment.png', 
                dpi=300, bbox_inches='tight')
    plt.show()