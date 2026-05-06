import pathlib
import pandas as pd
from ..facilities.facility import Facilities
from ..schedule import Schedule

def compare_new_and_old_vball_2025_schedules():
    """
    Analyzes and compares the game slot availability between the canned schedule
    and the new revision 1 facility configuration.
    """
    print("--- Schedule Syncing Validation ---")

    # --- Load Old (Canned) Schedule ---
    current_dir = pathlib.Path(__file__).parent.parent
    canned_schedule_path = current_dir / "scratch" / "last_volleyball_schedule 2025-06-18.txt"
    if not canned_schedule_path.exists():
        print(f"❌ Canned schedule not found at: {canned_schedule_path}")
        return
    
    print(f"📁 Loading old schedule from: {canned_schedule_path.name}")
    old_schedule = Schedule.parse_canned_schedule(str(canned_schedule_path))
    old_games_df = old_schedule.get_game_report()

    # Aggregate game counts per day for the old schedule
    old_schedule_counts = old_games_df.groupby(['weekend_idx', 'date', 'time']).size().reset_index(name='game_slots')
    print(f"✅ Old schedule loaded. Found {len(old_games_df)} total games.")

    # --- Load New (Revision 1) Facilities ---
    facilities_path = current_dir / "facilities" / "configs" / "volleyball_2025_revision_1.yaml"
    if not facilities_path.exists():
        print(f"❌ Facility config not found at: {facilities_path}")
        return

    print(f"📁 Loading new facilities from: {facilities_path.name}")
    new_facilities = Facilities.from_yaml(str(facilities_path))
    
    # Aggregate game counts per day for the new facilities
    new_facilities_df = new_facilities.to_dataframe()
    new_facilities_counts = new_facilities_df.groupby(['weekend_idx', 'date', 'time']).size().reset_index(name='game_slots')
    print(f"✅ New facilities loaded. Found {len(new_facilities_df)} total match slots.")
    print("-" * 35)
    
    # --- Normalize Time Formats ---
    old_schedule_counts['time'] = pd.to_datetime(old_schedule_counts['time']).dt.strftime('%H:%M:%S')
    new_facilities_counts['time'] = pd.to_datetime(new_facilities_counts['time']).dt.strftime('%H:%M:%S')

    # --- Compare Schedules ---
    print("\n📅 Daily Game Slot Comparison:")
    
    # Merge the two dataframes for a side-by-side comparison
    comparison_df = pd.merge(
        old_schedule_counts,
        new_facilities_counts,
        on=['weekend_idx', 'date', 'time'],
        suffixes=('_old', '_new'),
        how='outer'
    ).fillna(0)
    
    # Sort for readability
    comparison_df.sort_values(by=['weekend_idx', 'date', 'time'], inplace=True)
    comparison_df['game_slots_old'] = comparison_df['game_slots_old'].astype(int)
    comparison_df['game_slots_new'] = comparison_df['game_slots_new'].astype(int)

    # Print the comparison table
    print(comparison_df.to_string(index=False))

    # --- Identify Mismatches ---
    mismatches = comparison_df[comparison_df['game_slots_old'] > comparison_df['game_slots_new']]
    
    if not mismatches.empty:
        print("\n\n🚨 Mismatches Found! The following days/times in the old schedule do not have enough slots in the new facility config:")
        for _, row in mismatches.iterrows():
            print(f"  - Wk {row['weekend_idx']}, {row['date']} at {row['time']}: "
                  f"Needs {row['game_slots_old']} slots, but only {row['game_slots_new']} are available.")
    else:
        print("\n\n✅ Success! All game slots from the old schedule are available in the new facility configuration.")

if __name__ == "__main__":
    compare_new_and_old_vball_2025_schedules() 