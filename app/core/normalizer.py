"""File name normalization using text-unidecode."""

import re
from text_unidecode import unidecode


def normalize_filename(name: str) -> str:
    """Transliterate and normalize a filename.

    - Transliterate non-ASCII to ASCII
    - Replace spaces and dashes with underscores
    - Remove special characters (keep alphanumeric, underscore, dot)
    - Collapse consecutive underscores
    - Strip leading/trailing underscores
    """
    name = unidecode(name)
    name = re.sub(r"[\s\-]+", "_", name)
    name = re.sub(r"[^\w.]", "", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name
