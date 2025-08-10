import datetime
from typing import Dict
def get_current_time() -> Dict:
    """Returns the current time in a formatted string."""
    return {
        'current_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }