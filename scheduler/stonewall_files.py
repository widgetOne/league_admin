import os


STONEWALL_INPUT_PATH = 'inputs/stonewall'


def get_stonewall_schedules(root=STONEWALL_INPUT_PATH):
    return os.listdir(root)


def find_stonewall_schedules_needed():
    get_stonewall_schedules


if __name__ == '__main__':
    main()
