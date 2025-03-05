from math import ceil
from typing import List
import re

def get_pagination_info(total: int, limit: int, offset: int):
    """
    Calculate pagination information.
    
    :param total: Total number of items
    :param limit: Number of items per page
    :param offset: Current offset
    :return: Dictionary with page and page_count
    """
    page = (offset // limit) + 1
    page_count = ceil(total / limit)
    return {"page": page, "pageCount": page_count}

def to_dict(obj, exclude_fields: List[str] = []):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name not in exclude_fields}

def clean_text(text):
    """
    Clean the extracted text by removing headers, page numbers, and references.
    """
    # Remove headers like "BIOM 255 (Leffert) - Discussion Feb. 1, 2007"
    text = re.sub(r'BIOM 255 \(Leffert\) - Discussion Feb\. 1, 2007', '', text)
    
    # Remove page numbers (e.g., "Page 1 of 10" if present)
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove lines that are entirely in uppercase (likely headers)
    text = re.sub(r'^[A-Z\s]+$', '', text, flags=re.MULTILINE)
    
    # Remove references section (heuristic: starts with "REFERENCES AND NOTES")
    text = re.split(r'\nREFERENCES AND NOTES\n', text)[0]
    
    # Remove extra whitespace and empty lines
    text = re.sub(r'\n+', '\n', text).strip()
    
    return text