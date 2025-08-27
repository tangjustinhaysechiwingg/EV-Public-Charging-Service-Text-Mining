# Mapping globally public charging service satisfaction trajectories of electric vehicle users 
This repository contains the Python code, the sample electric vehicle (EV) public charging review data, and relevant data used for the manuscript titled "**_Mapping globally public charging service satisfaction trajectories of electric vehicle users_**".

This research applies text mining, sentiment topic modelling methodologies to explore how real-world EV users worldwide experience and evaluate public charging infrastructure, and how satisfaction trajectories vary across different regions.

# Requirements and Installation
The whole analysis-related codes should run with a **Python** environment, regardless of operating systems theoretically. 
We successfully executed all the codes in Windows (Win10) machines

More detailed info is as below:

## Prerequisites 
It is highly recommended to install and use the following versions of python/packages to run the codes:
Bertopic:
- ``python``: 3.9.21
- ``jieba``: 0.42.1
- ``langdetect``: 1.0.9
- ``bertopic``: 0.17.0
- ``sentence_transformers``: 4.1.0
- ``scikit-learn``: 1.6.1
- ``plotly``: 6.1.1
- ``nltk``: 3.9.1
- ``sentence_transformers``: 4.1.0
- ``tqdm``: 4.67.1
- ``numpy``: 1.24.4
- ``torch``: 2.7.0
- ``umap-learn``: 0.5.7
- ``hdbscan``: 0.8.40

Others:
- ``python``: 3.12.3
- ``numpy``: 1.26.4
- ``pandas``: 2.2.2
- ``matplotlib``: 3.9.0
- ``transformers``: 4.52.3
- ``torch``: 2.6.0+cu126
- ``rasterio``: 1.3.9
- ``geopandas``: 0.14.4
- ``pyshp``: 2.3.1
- ``shapely``: 2.0.4
- ``tqdm``: 4.66.4
- ``geopandas``: 1.9.4
- ``scipy``: 1.15.3
- ``seaborn``: 0.13.2
- ``requests``: 2.32.3
- ``fake_useragent``: 2.2.0

## Installation
It is highly recommended to download [AnaConda](https://www.anaconda.com) to create/manage Python environments.
You can create a new Python environment and install required aforementioned packages via both the GUI or Command Line.
Typically, the installation should be prompt (around _10-20 min_ from a "_clean_" machine to "_ready-to-use_" machine, but highly dependent on the Internet speed)
- via **Anaconda GUI**
  1. Open the Anaconda
  2. Find and click "_Environments_" at the left sidebar
  3. Click "_Create_" to create a new Python environment
  4. Select the created Python environment in the list, and then search and install all packages one by one.


- via **Command Line** (using **_Terminal_** for macOS machine and **_Anaconda Prompt_** for Windows machine, respectively)
  1. Create your new Python environment
     ```
     conda create --name <input_your_environment_name> python=3.9.21     #Bertopic
     conda create --name <input_your_environment_name> python=3.12.3     #Others

     ```
  2. Activate the new environment 
     ```
     conda activate <input_your_environment_name>
     ```
  3. Install all packages one by one 
     ```
     conda install <package_name>=<specific_version>
     ```

# Usage
1. Git clone/download the repository to your local disk.
2. The full datasets will be provided upon request through our Global EV Data Initiative at https://globalevdata.github.io/datasets/ev-text/ev-charger-review.html.
3. Run
   1. **data collection**: run each script in the dir ``./Code/Data collection``
   2. **topic and sentiment analysis**: run each script in the dir ``./Code/Analysis/Topic_and_sentiment_analysis`` (Details can be seen in the document ``./Code/Analysis/Topic_and_sentiment_analysis/Workflow_for_topic_and_sentiment_analysis_of_EV_charging_station_reviews.docx``)
   3. **statistical analysis**: run each script in the dir ``./Code/Analysis/Statistical_analysis``
   4. **plot**: run each script in the dir ``./Code/Figure plotting``
4. Outputs (including text files and figures) will be stored in the dir ``./Data/Interim`` and ``./Data/Figure_plots``, respectively.


---

## 📧 Contact  
For questions, collaborations, or further inquiries, please reach out to Dr. Chengxiang Zhuge (Tony):  
✉️ [chengxiang.zhuge@polyu.edu.hk] | 🌐 [https://thetipteam.wixstudio.com/website]  

---

⭐ **If you find this work useful, please consider starring this repository!** ⭐
