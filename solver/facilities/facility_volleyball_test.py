import os
from pathlib import Path
from facility import Facilities
import difflib

def test_volleyball_facility_output():
    # Get the directory of this file
    current_dir = Path(__file__).parent
    
    # Construct paths
    config_path = current_dir / "configs" / "volleyball_2025.yaml"
    output_path = current_dir / "configs_test_output" / "volleyball_2025_output.txt"
    
    # Create facility from config
    facility = Facilities.from_yaml(str(config_path))
    
    # Get the string representation
    facility_str = str(facility)
    
    # If output file doesn't exist, create it
    if not output_path.exists():
        with open(output_path, 'w') as f:
            f.write(facility_str)
        print(f"Created new output file at {output_path}")
        return
    
    # Read expected output
    with open(output_path, 'r') as f:
        expected_output = f.read()
    
    # Compare outputs
    if facility_str != expected_output:
        print("---- Difference between actual and expected output ----")
        diff = difflib.unified_diff(
            expected_output.splitlines(),
            facility_str.splitlines(),
            fromfile='expected_output',
            tofile='facility_str',
            lineterm=''
        )
        for line in diff:
            print(line)
    assert facility_str == expected_output, "Facility string output does not match expected output"
    print("Test passed: Facility string output matches expected output")

if __name__ == "__main__":
    test_volleyball_facility_output() 