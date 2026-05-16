import os
import csv
from pathlib import Path
from datetime import datetime

from .exports.gsheets_export import format_schedule_as_csv

def save_schedule_to_cache(schedule, start_time: datetime, score: float, creator=None):
    """Save a generated schedule to the local file-based cache.
    
    Args:
        schedule: The solved schedule object
        start_time: Datetime when the schedule generation started
        score: The objective score of the model
        creator: Optional ScheduleCreator object for generating debug reports
    """
    # 1. Determine cache hierarchy paths
    facilities = schedule.facilities
    schedule_name = facilities.get_schedule_name()
    
    # Format team counts readable: "14_10_10"
    team_counts_str = "_".join(str(c) for c in facilities.team_counts)
    
    cache_dir = Path("local_cache") / schedule_name / team_counts_str
    
    # Ensure directory exists
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Write facility layout if it doesn't exist
    layout_path = cache_dir / "facility_layout.txt"
    if not layout_path.exists():
        with open(layout_path, 'w', encoding='utf-8') as f:
            f.write(str(facilities))
            
    # 3. Save the schedule itself in CSV format
    start_time_str = start_time.strftime("%Y%m%d_%H%M%S")
    base_filename = f"{score}_{start_time_str}"
    csv_filename = f"{base_filename}.csv"
    csv_path = cache_dir / csv_filename
    
    # Format the schedule logic
    csv_data = format_schedule_as_csv(schedule)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
        
    print(f"Schedule cached to: {csv_path}")
    
    # 4. Save the debug report if creator is provided
    if creator:
        debug_filename = f"{base_filename}_debug.txt"
        debug_path = cache_dir / debug_filename
        debug_report = creator.generate_debug_reports(schedule)
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(debug_report)
        print(f"Debug report cached to: {debug_path}")

def get_best_cached_schedule(facilities):
    """Find the best (lowest penalty score) cached schedule for the given facilities.
    
    Args:
        facilities: The Facilities object
        
    Returns:
        tuple: (csv_path, debug_path) of the best cached schedule, or (None, None) if no cache found.
    """
    schedule_name = facilities.get_schedule_name()
    team_counts_str = "_".join(str(c) for c in facilities.team_counts)
    
    cache_dir = Path("local_cache") / schedule_name / team_counts_str
    
    if not cache_dir.exists():
        return None, None
        
    best_score = float('inf')
    best_csv_path = None
    
    for csv_path in cache_dir.glob("*.csv"):
        filename = csv_path.name
        try:
            # Filename format: {score}_{datetime}.csv
            score_str = filename.split('_')[0]
            score = float(score_str)
            if score < best_score:
                best_score = score
                best_csv_path = csv_path
        except (ValueError, IndexError):
            continue
            
    if best_csv_path:
        # Check if corresponding debug report exists
        debug_filename = best_csv_path.name.replace(".csv", "_debug.txt")
        debug_path = cache_dir / debug_filename
        if not debug_path.exists():
            debug_path = None
            
        return best_csv_path, debug_path
        
    return None, None

