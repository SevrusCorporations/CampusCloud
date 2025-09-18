from rapidfuzz import process

def match_query(queries:list, query):
    matched = process.extract(query, queries, limit=5)
    return matched