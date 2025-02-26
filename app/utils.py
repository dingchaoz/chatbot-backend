from math import ceil

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