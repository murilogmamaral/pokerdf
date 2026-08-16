import re
from typing import NamedTuple, Optional

class ParsedBuyIn(NamedTuple):
    prize: float
    bounty: Optional[float]
    rake: float
    currency: Optional[str]

BUYIN_REGEX = re.compile(
    r'^(?P<currency>[^\d\s\.\,]+)?\s*'
    r'(?P<prize>\d+(?:[\.\,]\d+)?)\s*'
    r'(?:\+\s*(?:[^\d\s\.\,]+)?(?P<bounty>\d+(?:[\.\,]\d+)?)\s*)?'
    r'\+\s*(?:[^\d\s\.\,]+)?(?P<rake>\d+(?:[\.\,]\d+)?)$',
    re.IGNORECASE
)

def parse_buyin(buyin_str: str) -> ParsedBuyIn:
    if not buyin_str or buyin_str.strip().lower() in ("freeroll", "play money", "0"):
        return ParsedBuyIn(prize=0.0, bounty=None, rake=0.0, currency=None)
    
    clean_str = buyin_str.strip()
    match = BUYIN_REGEX.match(clean_str)
    if not match:
        return ParsedBuyIn(prize=0.0, bounty=None, rake=0.0, currency=None)
    
    currency = match.group("currency")
    prize = float(match.group("prize").replace(',', '.'))
    bounty_raw = match.group("bounty")
    bounty = float(bounty_raw.replace(',', '.')) if bounty_raw else None
    rake = float(match.group("rake").replace(',', '.'))
    
    return ParsedBuyIn(prize=prize, bounty=bounty, rake=rake, currency=currency)
