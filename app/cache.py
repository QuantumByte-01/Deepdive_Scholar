from cachetools import TTLCache

# Cache up to 50 queries for 10 minutes
query_cache = TTLCache(maxsize=50, ttl=600)
