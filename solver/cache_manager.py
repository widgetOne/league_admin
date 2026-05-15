import os
import csv
from pathlib import Path
from datetime import datetime

from .exports.gsheets_export import format_schedule_as_csv

def save_schedule_to_cache(schedule, start_time: datetime, score: float):
    """Save a generated schedule to the local file-based cache.
    
    Args:
        schedule: The solved schedule object
        start_time: Datetime when the schedule generation started
        score: The objective score of the model
    """
    # 1. Determine cache hierarchy paths
    facilities = schedule.facilities
    fac_hash = facilities.get_hash()
    
    # Format team counts readable: "14_10_10"
    team_counts_str = "_".join(str(c) for c in facilities.team_counts)
    
    cache_dir = Path("local_cache") / fac_hash / team_counts_str
    
    # Ensure directory exists
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Write facility layout if it doesn't exist
    layout_path = cache_dir / "facility_layout.txt"
    if not layout_path.exists():
        with open(layout_path, 'w', encoding='utf-8') as f:
            f.write(str(facilities))
            
    # 3. Save the schedule itself in CSV format
    start_time_str = start_time.strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{score}_{start_time_str}.csv"
    csv_path = cache_dir / csv_filename
    
    # Format the schedule logic
    csv_data = format_schedule_as_csv(schedule)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        
    print(f"Schedule cached to: {csv_path}")
