import logging
import re
from typing import Tuple, Optional

def parse_movie_title(text: str) -> Tuple[str, Optional[int]]:
    """
    Parse movie title and year from text.
    Example input: "The Matrix (1999)"
    Returns: ("The Matrix", 1999)
    """
    # Pattern to match title and optional year in parentheses
    pattern = r"(.+?)(?:\s*\((\d{4})\))?$"
    match = re.match(pattern, text.strip())
    
    if match:
        title = match.group(1).strip()
        year = int(match.group(2)) if match.group(2) else None
        return title, year
    
    return text.strip(), None

def is_admin(user_id: int, admin_ids: list) -> bool:
    """Check if user is an admin."""
    return user_id in admin_ids

def is_authorized_group(group_id: int, auth_groups: list) -> bool:
    """Check if group is authorized."""
    return group_id in auth_groups

def format_movie_info(movie) -> str:
    """Format movie information for display."""
    year_str = f" ({movie.year})" if movie.year else ""
    description = f"\n\n{movie.description}" if movie.description else ""
    
    return f"🎬 *{movie.title}*{year_str}{description}"
  
