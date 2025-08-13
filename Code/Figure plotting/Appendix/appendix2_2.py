import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams
from matplotlib.ticker import PercentFormatter

# ======================
# Academic Style Settings
# ======================
plt.style.use('seaborn-v0_8-paper')
rcParams.update({
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

def plot_monthly_ratios():
    # 1. Load JSON data
    monthly_data = generate_monthly_data()
    
    # 2. Prepare data - January to December
    month_order = [str(i) for i in range(1, 13)]
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ratios = [monthly_data.get(month, 0) for month in month_order]

    # Calculate averages
    summer_avg = np.mean(ratios[6:8])  # July-August
    other_avg = np.mean(ratios[:6] + ratios[8:])  # Other months

    # 3. Create visualization
    fig, ax = plt.subplots(figsize=(8, 4))

    # Color scheme
    main_color = '#4e79a7'
    summer_color = '#e15759'
    other_color = '#59a14f'

    # Monthly bars
    bars = ax.bar(month_labels, ratios, color=main_color, width=0.7,
                 edgecolor='white', linewidth=0.5, alpha=0.9, label='Monthly Ratio')

    # Average bars with proper spacing
    avg_positions = [len(month_labels)+1.5, len(month_labels)+3.5]
    ax.bar(avg_positions[0], summer_avg, color=summer_color, width=0.7,
          edgecolor='white', linewidth=0.5, alpha=0.9, label='Jul-Aug Average')
    ax.bar(avg_positions[1], other_avg, color=other_color, width=0.7,
          edgecolor='white', linewidth=0.5, alpha=0.9, label='Other Months Average')

    # Chart elements
    ax.set_title('(a) Proportion of Reveiws Containing the Keyword "broken" by Month', pad=20, fontsize=13,fontweight='bold')
    ax.set_xlabel('Month', labelpad=10)
    ax.set_ylabel('Percentage', labelpad=10)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))

    # X-axis settings
    xticks = list(range(len(month_labels))) + avg_positions
    xlabels = month_labels + ['Jul-Aug', 'Other months']
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_xlim(-0.5, len(month_labels)+4.5)  # Proper spacing

    # Grid and layout
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)

    # Average value labels
    ax.text(avg_positions[0], summer_avg, f'{summer_avg:.1%}',
           ha='center', va='bottom', fontsize=10)
    ax.text(avg_positions[1], other_avg, f'{other_avg:.1%}',
           ha='center', va='bottom', fontsize=10)

    # Legend and divider
    ax.legend(loc='upper left', frameon=True, framealpha=0.9)
    ax.axvline(len(month_labels)+0.75, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.text(len(month_labels)+0.4, max(ratios)*0.8, 'Period Averages',
           rotation=90, va='center', ha='center', color='gray')

    plt.tight_layout()
    plt.savefig('figure\\appendix2\\monthly_broken_ratio_comment.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_monthly_data():
    """Load monthly data from JSON file"""
    with open('Data\\interim\\appendix2\\monthly_broken_comment_ratio.json', 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    plot_monthly_ratios()