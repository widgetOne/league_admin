import datetime
import os.path

from run_regular_season import make_2024_sand_schedule
from optimizer import save_schedules, get_schedules
from optimizer import get_default_potential_sch_loc


def get_schedule_with_caching():
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    if not os.path.isfile(canned_path):
        sch = make_2024_sand_schedule()
        save_schedules([sch], canned_path)
    else:
        sch = get_schedules(canned_path)[0]
    return sch


def test_caching_process():
    _ = get_schedule_with_caching()
    cached_sch = get_schedule_with_caching()
    fresh_sch = make_2024_sand_schedule()
    they_match = cached_sch.get_audit_text().strip() == fresh_sch.get_audit_text().strip()
    print(f'they_match {they_match}')


if __name__ == '__main__':
    test_caching_process()
