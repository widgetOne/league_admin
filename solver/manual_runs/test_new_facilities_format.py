#!/usr/bin/env python3
"""
Test script to verify that both YAML formats produce equivalent facilities objects.

This script loads both volleyball_2025.yaml (legacy format) and 
volleyball_2025_revision_0.yaml (new format) and confirms they result 
in the same facilities object.
"""

import pathlib
from .. import Facilities


def compare_facilities(fac1: Facilities, fac2: Facilities) -> bool:
    """Compare two facilities objects for equality.
    
    Args:
        fac1: First facilities object
        fac2: Second facilities object
        
    Returns:
        bool: True if facilities are equivalent, False otherwise
    """
    print("🔍 Comparing facilities objects...")
    
    # Compare basic properties
    if fac1.team_counts != fac2.team_counts:
        print(f"❌ team_counts differ: {fac1.team_counts} vs {fac2.team_counts}")
        return False
    print(f"✅ team_counts match: {fac1.team_counts}")
    
    if fac1.games_per_season != fac2.games_per_season:
        print(f"❌ games_per_season differ: {fac1.games_per_season} vs {fac2.games_per_season}")
        return False
    print(f"✅ games_per_season match: {fac1.games_per_season}")
    
    if fac1.games_per_day != fac2.games_per_day:
        print(f"❌ games_per_day differ: {fac1.games_per_day} vs {fac2.games_per_day}")
        return False
    print(f"✅ games_per_day match: {fac1.games_per_day}")
    
    # Compare dates
    if fac1.dates != fac2.dates:
        print(f"❌ dates differ:")
        print(f"  Legacy: {fac1.dates}")
        print(f"  New:    {fac2.dates}")
        return False
    print(f"✅ dates match: {fac1.dates}")
    
    # Compare times (need to handle potential differences in time slots)
    fac1_times_str = [t.strftime('%H:%M') for t in fac1.times]
    fac2_times_str = [t.strftime('%H:%M') for t in fac2.times]
    
    if fac1_times_str != fac2_times_str:
        print(f"❌ times differ:")
        print(f"  Legacy: {fac1_times_str}")
        print(f"  New:    {fac2_times_str}")
        return False
    print(f"✅ times match: {fac1_times_str}")
    
    # Compare locations
    if fac1.locations != fac2.locations:
        print(f"❌ locations differ: {fac1.locations} vs {fac2.locations}")
        return False
    print(f"✅ locations match: {fac1.locations}")
    
    # Compare total teams
    if fac1.total_teams != fac2.total_teams:
        print(f"❌ total_teams differ: {fac1.total_teams} vs {fac2.total_teams}")
        return False
    print(f"✅ total_teams match: {fac1.total_teams}")
    
    # Compare matches (most complex comparison)
    if len(fac1.matches) != len(fac2.matches):
        print(f"❌ match count differs: {len(fac1.matches)} vs {len(fac2.matches)}")
        return False
    print(f"✅ match count matches: {len(fac1.matches)}")
    
    # Sort matches for comparison (by weekend_idx, date, time, location)
    def match_sort_key(match):
        return (match.weekend_idx, match.date, match.time, match.location)
    
    fac1_matches_sorted = sorted(fac1.matches, key=match_sort_key)
    fac2_matches_sorted = sorted(fac2.matches, key=match_sort_key)
    
    # Compare each match
    for i, (m1, m2) in enumerate(zip(fac1_matches_sorted, fac2_matches_sorted)):
        if (m1.weekend_idx != m2.weekend_idx or 
            m1.date != m2.date or 
            m1.location != m2.location or 
            m1.time != m2.time or 
            m1.time_idx != m2.time_idx):
            print(f"❌ Match {i} differs:")
            print(f"  Legacy: {m1}")
            print(f"  New:    {m2}")
            return False
    
    print(f"✅ All {len(fac1.matches)} matches are identical")
    
    return True


def test_facilities_formats():
    """Test that both YAML formats produce equivalent facilities objects."""
    print("🏐 Testing Facilities Format Compatibility")
    print("=" * 50)
    
    # Get paths to both YAML files
    current_dir = pathlib.Path(__file__).parent.parent
    legacy_yaml = current_dir / "facilities" / "configs" / "volleyball_2025.yaml"
    new_yaml = current_dir / "facilities" / "configs" / "volleyball_2025_revision_0.yaml"
    
    # Check that both files exist
    if not legacy_yaml.exists():
        print(f"❌ Legacy YAML file not found: {legacy_yaml}")
        return False
    
    if not new_yaml.exists():
        print(f"❌ New YAML file not found: {new_yaml}")
        return False
    
    print(f"📁 Legacy format: {legacy_yaml.name}")
    print(f"📁 New format: {new_yaml.name}")
    print()
    
    try:
        # Load both facilities
        print("📖 Loading legacy format...")
        legacy_facilities = Facilities.from_yaml(str(legacy_yaml))
        print(f"✅ Legacy facilities loaded: {len(legacy_facilities.matches)} matches")
        
        print("📖 Loading new format...")
        new_facilities = Facilities.from_yaml(str(new_yaml))
        print(f"✅ New facilities loaded: {len(new_facilities.matches)} matches")
        print()
        
        # Compare the facilities
        are_equal = compare_facilities(legacy_facilities, new_facilities)
        
        print()
        if are_equal:
            print("🎉 SUCCESS: Both YAML formats produce equivalent facilities objects!")
            print("✅ The facilities parser correctly handles both formats.")
        else:
            print("❌ FAILURE: The YAML formats produce different facilities objects.")
            print("🔧 The parser needs adjustment to handle the differences.")
            
        return are_equal
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the facilities format test."""
    success = test_facilities_formats()
    
    if success:
        print("\n🎯 Test completed successfully!")
    else:
        print("\n💥 Test failed - see output above for details.")
        exit(1)


if __name__ == "__main__":
    main() 