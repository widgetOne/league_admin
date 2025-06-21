#!/usr/bin/env python3
"""
Multi-run volleyball scheduler for 2025.

This script runs the volleyball scheduler multiple times to escape local minima,
tracks the best objective score in Google Sheets, and only uploads improved schedules.
"""

import pathlib
import os
from .. import Facilities, Schedule
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runner import make_schedule
from ..exports.gsheets_export import export_schedule_to_sheets, get_best_objective_score, save_best_objective_score
from .make_teamwise_schedules_2025 import make_teamwise_schedules


def generate_multiple_schedules(update_schedule=True):
    """Run the volleyball scheduler multiple times and track the best result.
    
    Args:
        update_schedule (bool): Whether to update Google Sheets during runs. 
                               If False, only tracks best score without uploading.
    """
    print("Running Multi-Run Volleyball Scheduler for 2025...")
    
    # Load facilities
    current_dir = pathlib.Path(__file__).parent.parent # Get the 'solver' directory
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball_2025.yaml"
    facilities = Facilities.from_yaml(str(facilities_yaml_path))
    print("Facilities loaded.")
    
    # Get the current best objective score from Google Sheets
    current_best_score = get_best_objective_score()
    print(f"Current best objective score: {current_best_score:,.2f}")
    
    # Get schedule components
    schedule_components = get_sand_volleyball_template()
    
    best_schedule = None
    best_creator = None
    best_score = current_best_score
    improved_runs = 0
    early_stop = False
    
    # Run the scheduler 20 times (or until we find a score <= 80,000)
    for run_num in range(1, 21):
        print(f"\n{'='*60}")
        print(f"RUN {run_num}/20")
        print(f"{'='*60}")
        
        try:
            # Generate schedule
            schedule, creator = make_schedule(facilities, schedule_components)
            current_score = schedule.solver.ObjectiveValue()
            
            print(f"Run {run_num} completed with objective score: {current_score:,.2f}")
            
            # Check if this is better than our current best
            if current_score < best_score:
                print(f"🎉 NEW BEST SCORE! Improved from {best_score:,.2f} to {current_score:,.2f}")
                best_schedule = schedule
                best_creator = creator
                best_score = current_score
                improved_runs += 1
                
                # Upload the improved schedule if update_schedule is True
                if update_schedule:
                    print(f"🚀 Uploading improved schedule to Google Sheets...")
                    try:
                        export_schedule_to_sheets(schedule, creator)
                        save_best_objective_score(current_score)
                        print(f"✅ Upload complete! New best score saved: {current_score:,.2f}")
                        
                        # Generate teamwise schedules immediately
                        print(f"📋 Generating individual team schedules...")
                        make_teamwise_schedules()
                        print(f"✅ Individual team schedules generated!")
                        
                    except Exception as e:
                        print(f"⚠️  Failed to upload/generate schedules: {e}")
                else:
                    print(f"📝 Skipping upload (update_schedule=False)")
                
                # Check for early stop condition
                if current_score <= 80000:
                    print(f"🎯 EXCELLENT SCORE ACHIEVED! Score {current_score:,.2f} <= 80,000 - stopping early!")
                    early_stop = True
                    break
            else:
                print(f"No improvement. Current best remains: {best_score:,.2f}")
                
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
    print(f"Runs with improvements: {improved_runs}")
    print(f"Starting best score: {current_best_score:,.2f}")
    print(f"Final best score: {best_score:,.2f}")
    
    if best_score < current_best_score:
        improvement = current_best_score - best_score
        improvement_pct = (improvement / current_best_score) * 100
        print(f"Total improvement: {improvement:,.2f} ({improvement_pct:.2f}%)")
        if update_schedule:
            print(f"✅ All improvements were uploaded immediately during the runs.")
        else:
            print(f"📝 Improvements were found but not uploaded (update_schedule=False).")
    else:
        print(f"No improvement found across all runs.")
        
        # Generate teamwise schedules even if no improvement (using current best schedule)
        if update_schedule:
            print(f"\n📋 Generating individual team schedules from current best...")
            try:
                make_teamwise_schedules()
                print(f"✅ Individual team schedules generated successfully!")
            except Exception as e:
                print(f"⚠️  Failed to generate team schedules: {e}")
        else:
            print(f"📝 Skipping teamwise schedule generation (update_schedule=False).")
    
    print(f"\nMulti-run optimization complete!")


if __name__ == "__main__":
    generate_multiple_schedules() 