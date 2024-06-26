import os

import caching
from optimizer import save_schedules, get_schedules


def load_current_schedule():
    path = 'scratch'
    schedule_name = 'round_robin-schedules-from-2024-06-24.pkl'
    full_path = os.path.join(path, schedule_name)
    return get_schedules(full_path)[0]


def upload_teamwise_schedules():
    sch = load_current_schedule()


if __name__ == '__main__':
    upload_teamwise_schedules()
