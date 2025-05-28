import os
import requests
from . import utils
from .cache import query_cache

API_KEY = os.getenv("PERPLEXITY_API_KEY")
BASE_URL = "https://api.perplexity.ai"
ENDPOINT = "/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_search_sources(topic: str, count: int):
    cache_key = f"search::{topic}::{count}"
    if cache_key in query_cache:
        return query_cache[cache_key]

    prompt = (
        f"List {count} authoritative sources (title + URL) for further reading on “{topic}”."
    )
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are an AI assistant conducting precise web research."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "web_search_options": {"search_context_size": "high"}
    }
    r = requests.post(BASE_URL + ENDPOINT, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    results = utils.parse_search_results(text)
    query_cache[cache_key] = results
    return results

def get_structured_report(topic: str, temp: float, context: str):
    cache_key = f"report::{topic}::{temp}::{context}"
    if cache_key in query_cache:
        return query_cache[cache_key]

    system = (
        "You are DeepDive Scholar, an expert academic researcher. "
        "Produce a concise, structured report on the user's query. "
        "Use these sections:\n"
        "• **Definitions**\n"
        "• **Historical Milestones**\n"
        "• **Current Applications**\n"
        "• **Pros & Cons**\n\n"
        "Use bullet points where appropriate and numbered inline citations like [1], [2].\n"
        "End with a **References:** section listing URLs for each citation.\n\n"
        "If the user provided additional context, weave it in where relevant:\n"
        f"“{context}”\n"
    )
    payload = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": topic}
        ],
        "temperature": temp,
        "max_tokens": 2000,
        "web_search_options": {"search_context_size": "high"}
    }
    r = requests.post(BASE_URL + ENDPOINT, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]

    chain, answer = utils.extract_chain_of_thought(content)
    clean, refs = utils.extract_references(answer)
    result = {"report": clean, "references": refs, "chain": chain}
    query_cache[cache_key] = result
    return result
