import requests
from bs4 import BeautifulSoup
import time

queries = [
    "LLM context pruning",
    "LLM memory management forget",
    "LLM prompt noise removal",
    "LLM context compression",
    "dynamic context window pruning",
    "LLM conversation history optimization",
    "removing redundant tokens LLM",
    "LLM hallucination context cleaning"
]

for q in queries:
    print(f"Searching for: {q}")
    url = f"https://arxiv.org/search/?query={q.replace(' ', '+')}&searchtype=all"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print(f"Success for {q}")
        else:
            print(f"Failed for {q}: {r.status_code}")
    except Exception as e:
        print(f"Error for {q}: {e}")
    time.sleep(2)
