import re

# backend/utils/helpers.py

def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())

def keywords_from_text(text: str, limit: int = 80) -> list:
    # Basic stopword list to prevent "from", "to", "and" from appearing
    STOPWORDS = {"and", "the", "with", "from", "for", "this", "that", "of", "to", "in", "is", "was"}
    
    words = text.lower().split()
    # Filter: must be longer than 2 chars and not in the stopword list
    filtered_keywords = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    
    return filtered_keywords[:limit]    