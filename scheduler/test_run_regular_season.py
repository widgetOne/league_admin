import datetime

import pytest
from run_regular_season import make_2024_sand_schedule


@pytest.fixture
def expected_output():
    with open('test/expected_output/run_regular_season_expected_output.txt', 'r') as file:
        return file.read().strip()


def test_my_function(expected_output):
    sch = make_2024_sand_schedule()
    actual_audit_report = sch.get_audit_text().strip()
    if actual_audit_report != expected_output:
        audit_text = sch.get_audit_text().strip()
        date_str = str(datetime.date.today())
        with open(f'test/scratch/run_regular_season_audit_report_{date_str}.txt', 'w') as file:
            file.write(audit_text)
    assert len(actual_audit_report) == len(expected_output), 'lengths didnt match'
    assert actual_audit_report == expected_output, 'audit reporting didnt match'


if __name__ == "__main__":
    pytest.main([__file__])
