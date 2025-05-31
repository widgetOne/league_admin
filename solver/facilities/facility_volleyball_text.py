from pathlib import Path
from facility import Facilities

def main():
    current_dir = Path(__file__).parent
    config_path = current_dir / "configs" / "volleyball_2025.yaml"
    output_path = current_dir / "configs_test_output" / "volleyball_2025_output.txt"

    facility = Facilities.from_yaml(str(config_path))
    facility_str = str(facility)
    print(facility_str)

    with open(output_path, 'r') as f:
        expected_output = f.read()
    if facility_str == expected_output:
        print("\nOutput matches expected output.")
    else:
        print("\nOutput does NOT match expected output!")

if __name__ == "__main__":
    main() 