import re, os, json
from urllib.parse import urlparse

def extract_chain_of_thought(text: str):
    if "<think>" in text and "</think>" in text:
        before, after = text.split("</think>", 1)
        chain = before.replace("<think>", "").strip()
        return chain, after.strip()
    return None, text

def extract_references(text: str):
    idx = text.lower().rfind("references:")
    if idx == -1:
        return text.strip(), []
    main = text[:idx].strip()
    refs_lines = text[idx:].splitlines()[1:]
    refs = []
    for line in refs_lines:
        match_url = re.search(r'https?://\S+', line)
        if not match_url:
            continue
        url = match_url.group().rstrip(").,")
        num_match = re.search(r'\[(\d+)\]', line) or re.match(r'(\d+)\.', line)
        num = int(num_match.group(1)) if num_match else len(refs) + 1
        refs.append((num, url))
    refs.sort(key=lambda x: x[0])
    return main, refs

def parse_search_results(text: str):
    lines = text.splitlines()
    out = []
    for line in lines:
        u = re.search(r'https?://\S+', line)
        if not u:
            continue
        url = u.group().rstrip(").,")
        title = line[:u.start()].strip(" -.:")
        if not title:
            domain = urlparse(url).netloc.replace("www.", "")
            title = domain
        out.append((title, url))
    return out

# --- Feedback storage in JSON ---
FEEDBACK_PATH = os.path.join(os.getcwd(), "data", "feedback.json")

def save_feedback(topic, rating, comment):
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    data = []
    if os.path.exists(FEEDBACK_PATH):
        data = json.load(open(FEEDBACK_PATH, encoding="utf-8"))
    data.append({"topic": topic, "rating": rating, "comment": comment})
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_average_rating(topic):
    if not os.path.exists(FEEDBACK_PATH):
        return None
    data = json.load(open(FEEDBACK_PATH, encoding="utf-8"))
    ratings = [d["rating"] for d in data if d["topic"].lower() == topic.lower()]
    if not ratings:
        return None
    return round(sum(ratings) / len(ratings), 1)
