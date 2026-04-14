from datetime import datetime, timedelta


def get_time_now() -> datetime:
    return datetime.utcnow() + timedelta(hours=3)
