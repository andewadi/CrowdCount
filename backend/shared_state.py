# shared_state.py
from collections import defaultdict
from datetime import datetime

live_data = {
    "total": 0,
    "zones": defaultdict(int),
    "timestamp": None
}

history_log = []  # for CSV/PDF export
