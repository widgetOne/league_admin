#!/usr/bin/env python3
"""
Multi-run volleyball scheduler for the season.

This script runs the volleyball scheduler multiple times to escape local minima,
tracks the best objective score in Google Sheets, and only uploads improved schedules.
"""

import pathlib
import os
from .. import Facilities, Schedule
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runner import make_schedule
from ..exports.gsheets_export import get_team_counts_from_sheets


from datetime import datetime
from ..cache_manager import save_schedule_to_cache

def generate_multiple_schedules():
    """Run the volleyball scheduler multiple times and cache the results.
    
    This script runs the scheduler to escape local minima and saves all valid
    schedules to the local file cache. It does not upload to Google Sheets.
    """
    print("Running Multi-Run Volleyball Scheduler...")
    
    # Load facilities
    current_dir = pathlib.Path(__file__).parent.parent # Get the 'solver' directory
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball.yaml"
    
    # Fetch team counts from Google Sheets team_input tab
    print("Fetching team counts from Google Sheets...")
    team_counts = get_team_counts_from_sheets()
    print(f"Team counts from sheet: {team_counts}")
    
    facilities = Facilities.from_yaml(str(facilities_yaml_path), team_counts=team_counts)
    print("Facilities loaded.")
    
    # Get schedule components
    schedule_components = get_sand_volleyball_template()
    
    best_schedule = None
    best_creator = None
    best_score = float('inf')
    improved_runs = 0
    early_stop = False
    
    # Run the scheduler 1 time for testing
    for run_num in range(1, 2):
        print(f"\n{'='*60}")
        print(f"RUN {run_num}/20")
        print(f"{'='*60}")
        
        try:
            # Generate schedule
            run_start_time = datetime.now()
            schedule, creator = make_schedule(facilities, schedule_components)
            current_score = schedule.solver.ObjectiveValue()
            
            print(f"Run {run_num} completed with objective score: {current_score:,.2f}")
            
            # Save EVERY valid schedule locally to the cache
            try:
                save_schedule_to_cache(schedule, run_start_time, current_score, creator)
            except Exception as e:
                print(f"⚠️ Failed to cache schedule locally: {e}")
            
            # Check if this is better than our current best
            if current_score < best_score:
                print(f"🎉 NEW BEST SCORE for this session! Improved from {best_score if best_score != float('inf') else 'inf'} to {current_score:,.2f}")
                best_schedule = schedule
                best_creator = creator
                best_score = current_score
                improved_runs += 1
                
                # Check for early stop condition
                if current_score <= 80000:
                    print(f"🎯 EXCELLENT SCORE ACHIEVED! Score {current_score:,.2f} <= 80,000 - stopping early!")
                    early_stop = True
                    break
            else:
                print(f"No improvement in this session. Current session best remains: {best_score:,.2f}")
                
        except Exception as e:
            print(f"❌ Run {run_num} failed: {e}")
            continue
    
    # Summary
    print(f"\n{'='*60}")
    print(f"MULTI-RUN SUMMARY")
    print(f"{'='*60}")
    if early_stop:
        print(f"Completed runs: {run_num} (stopped early - excellent score achieved!)")
    else:
        print(f"Completed runs: 20")
    print(f"Session best score: {best_score if best_score != float('inf') else 'None'}")
    
    print(f"\nMulti-run optimization and caching complete! Run get_volleyball_schedule.py to upload the best cached result.")


if __name__ == "__main__":
    generate_multiple_schedules() 
