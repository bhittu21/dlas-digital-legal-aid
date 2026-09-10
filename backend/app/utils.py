import datetime

def now_utc() -> datetime.datetime:
    """
    Return timezone-aware current UTC datetime.
    Compatible with Python 3.12, 3.13, 3.14+.
    """
    return datetime.datetime.now(datetime.timezone.utc)
