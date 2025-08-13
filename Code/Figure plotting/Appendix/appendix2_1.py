
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

# ======================
# Data Loading
# ======================
with open('Data\\interim\\appendix2\\weekly_occupied_comment_ratio.json', 'r', encoding='utf-8') as f:
   weekly_data = json.load(f)

# ======================
# Data Preparation
# ======================
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
ratios = [weekly_data.get(day, 0) for day in weekday_order]

# Calculate averages
workday_avg = np.mean(ratios[:5]) 
weekend_avg = np.mean(ratios[5:]) 

# ======================
# Visualization
# ======================
fig, ax = plt.subplots(figsize=(8, 4))

# Colors
main_color = '#4e79a7'
workday_color = '#e15759'
weekend_color = '#59a14f'

# Daily bars
bars = ax.bar(weekday_labels, ratios, color=main_color, width=0.7, 
              edgecolor='white', linewidth=0.5, alpha=0.9, label='Daily Ratio')

# Average bars with proper spacing
avg_positions = [len(weekday_labels)+1.5, len(weekday_labels)+3]
ax.bar(avg_positions[0], workday_avg, color=workday_color, width=0.7, 
       edgecolor='white', linewidth=0.5, alpha=0.9, label='Weekday Average')
ax.bar(avg_positions[1], weekend_avg, color=weekend_color, width=0.7,
       edgecolor='white', linewidth=0.5, alpha=0.9, label='Weekend Average')

# Chart elements
ax.set_title('(b) Proportion of Reveiws Containing the Keyword "occupied" by Day of the Week', pad=15,fontsize=13, fontweight='bold')
ax.set_xlabel('Day of the Week', labelpad=10)
ax.set_ylabel('Percentage', labelpad=10)
ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))

# X-axis ticks and labels
xticks = list(range(len(weekday_labels))) + avg_positions
xlabels = weekday_labels + ['Weekdays', 'Weekends']
ax.set_xticks(xticks)
ax.set_xticklabels(xlabels)

# Grid and layout
ax.yaxis.grid(True, linestyle='--', alpha=0.4)
ax.set_axisbelow(True)



# Average value labels
ax.text(avg_positions[0], workday_avg, f'{workday_avg:.1%}', 
        ha='center', va='bottom', fontsize=10)
ax.text(avg_positions[1], weekend_avg, f'{weekend_avg:.1%}',
        ha='center', va='bottom', fontsize=10)

# Legend and divider
ax.legend(loc='upper left', frameon=True, framealpha=0.9)
ax.axvline(len(weekday_labels)+0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax.text(len(weekday_labels)+0.2, max(ratios)*0.8, 'Period Averages', 
        rotation=90, va='center', ha='center', color='gray')

plt.tight_layout()
plt.savefig('figure\\appendix2\\weekly_occupied_ratio_comment.png', dpi=300, bbox_inches='tight')
plt.show()