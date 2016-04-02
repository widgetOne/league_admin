



def check_schedule_vs_members(sch, members):
    if len(members) != len(sch.divisions):
        raise(ValueError('the members and schedule structures are inconsistent'))
    for div_idx, teams in enumerate(members):
        if len(teams) != len(sch.divisions[div_idx].teams):
            raise(ValueError('the members and schedule structures are inconsistent'))

def schedule_report():
    from schedule import load_reg_schedule
    sch = load_reg_schedule()

if __name__ == '__main__':
    from schedule import load_reg_schedule
    from members import import_teams
    sch = load_reg_schedule()
    members = import_teams()
    check_schedule_vs_members(sch, members)