import datetime
import os.path

from run_regular_season import make_2024_sand_schedule
from optimizer import save_schedules, get_schedules
from optimizer import get_default_potential_sch_loc


def load_current_schedule():
    path = 'scratch'
    schedule_name = 'round_robin-schedules-from-2024-06-24.pkl'
    full_path = os.path.join(path, schedule_name)
    return get_schedules(full_path)[0]


def load_v2_current_schedule():
    path = 'scratch'
    schedule_name = 'round_robin-schedules-from-2024-06-26.pkl'
    full_path = os.path.join(path, schedule_name)
    return get_schedules(full_path)[0]


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
