import os
import re
import json
import pandas as pd
from tqdm.auto import tqdm
import jieba
from langdetect import detect, LangDetectException
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import plotly.io as pio
import nltk
from nltk.tokenize import word_tokenize
from functools import lru_cache  
import torch
#--- Initialize configuration---
os.makedirs('result_optimized', exist_ok=True)
nltk.data.path.append("D:\\berttopic\\nltk_data")
 
#--- Data loading---
def load_comments(json_files):
    all_contents = []
    for file in tqdm(json_files, desc="Loading files"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_contents.extend([c["content"] for c in data["comment_list"] if c["content"].strip()])
    return pd.DataFrame(all_contents, columns=["content"])

json_files = [
    "processing_data\\review_data\china_comments.json",
    "processing_data\\review_data\usa_comments.json",
    "processing_data\\review_data\europe_comments.json"
]
data = load_comments(json_files)
print(f"Loaded {len(data):,} comments")

#Optimize preprocessing---
def load_stopwords(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

stopwords = load_stopwords("processing_data\\stop_words.txt")

@lru_cache(maxsize=10000)
def cached_detect(text):
    try:
        return detect(text)  
    except LangDetectException:
        return 'en'

def multilingual_tokenize(text, lang):
    if lang.startswith('zh'):
        return jieba.lcut(text)
    else:
        try:
            return word_tokenize(text, language=lang[:2])
        except:
            return word_tokenize(text)

def clean_text(text):
    text = re.sub(r'http\S+|@\w+|#\w+|[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def process_batch(texts):
    processed = []
    for text in texts:
        text = clean_text(text)
        if not text:  
            continue
            
        lang = cached_detect(text)
        words = multilingual_tokenize(text, lang)
        words = [
            w.lower() for w in words 
            if w.lower() not in stopwords 
            and len(w) >= 2 
            and not w.isnumeric()
        ]
        processed.append(" ".join(words))
    return processed


batch_size = 50_000
data["processed"] = pd.Series(dtype=str) 

for i in tqdm(range(0, len(data), batch_size), desc="Batch processing"):
    batch = data["content"].iloc[i:i+batch_size]
    processed_batch = process_batch(batch)
    
    end_idx = min(i + len(processed_batch), len(data))
    data.loc[i:end_idx-1, "processed"] = processed_batch
    

# --- BERTopic ---
hdbscan_model = HDBSCAN(
    min_cluster_size=40,
    min_samples=20,
    cluster_selection_epsilon=0.3,
    cluster_selection_method='eom',
    metric='euclidean',
    core_dist_n_jobs=4,
    memory='./hdbscan_cache',
    prediction_data=True
)

umap_model = UMAP(
    n_neighbors=50,
    n_components=30,
    min_dist=0.0,
    metric='cosine',
    low_memory=True,
    random_state=42
)

topic_model = BERTopic(
    embedding_model=SentenceTransformer(
        'paraphrase-multilingual-MiniLM-L12-v2',
        device='cuda' if torch.cuda.is_available() else 'cpu'
    ),
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=CountVectorizer(
        stop_words=None,
        token_pattern=r'\b[^\s]+\b',
        max_features=10000
    ),
    min_topic_size=20,
    nr_topics='auto',
    calculate_probabilities=False,
    verbose=True,

)

print("\nTraining model...")
texts = data["processed"].dropna().tolist()
topics, _ = topic_model.fit_transform(texts)


output_path = 'processing_output\\result_optimized'
os.makedirs(output_path, exist_ok=True)


doc_info = topic_model.get_document_info(texts)
topic_freq = topic_model.get_topic_freq()
data.to_csv(os.path.join(output_path, "processed_comments.csv"), index=False, encoding='utf-8-sig')
doc_info.to_csv(os.path.join(output_path, 'document_topic_info.csv'), index=False, encoding='utf-8-sig')
topic_freq.to_csv(os.path.join(output_path, 'topic_frequency.csv'), index=False, encoding='utf-8-sig')


all_topics = topic_model.get_topics()
with open(os.path.join(output_path, 'topic_representations.txt'), 'w', encoding='utf-8') as f:
    for topic_id, words in all_topics.items():
        if topic_id != -1:
            freq = topic_freq[topic_freq['Topic']==topic_id]['Count'].values[0]
            f.write(f"Topic ID: {topic_id}\n")
            f.write(f"Frequency: {freq}\n")
            f.write(f"Keywords: {[word for word, _ in words]}\n")  


fig_topics = topic_model.visualize_topics()
fig_bar = topic_model.visualize_barchart()
fig_hierarchy = topic_model.visualize_hierarchy()
fig_heatmap = topic_model.visualize_heatmap()

pio.write_html(fig_topics, os.path.join(output_path, "topics_overview.html"))
pio.write_html(fig_bar, os.path.join(output_path, "topics_barchart.html"))
pio.write_html(fig_hierarchy, os.path.join(output_path, "topics_hierarchy.html"))
pio.write_html(fig_heatmap, os.path.join(output_path, "topics_heatmap.html"))


topic_model.save(os.path.join(output_path, "bertopic_model"), save_embedding_model=False)  

print("\n=== Model ===")
print(f"Total number of themes: {len(topic_freq)-1}")  
print(f"parameter configuration:")
print(f"- Embedded model: {topic_model.embedding_model}")
print(f"- Clustering method: {topic_model.hdbscan_model}")

print("The generated files include:")
for fname in os.listdir(output_path):
    print(f"- {fname}")