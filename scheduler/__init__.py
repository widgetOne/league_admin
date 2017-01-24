def make_regular_season_spring_2017():
    team_counts = [6, 11, 11, 11, 6]
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    sch_template_path = 'inputs/reg_season/spring_2017_template_01_13.csv'
    sch_tries = 5000
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    seed = 1
    print('\nMaking schedule %s.' % seed)
    sch = make_schedule(team_counts, fac,
                        sch_tries=sch_tries, seed=seed, debug=True)
    save_schedules([sch], canned_path)
    audit_text = sch.get_audit_text()
    print("\n".join(audit_text))


if __name__ == '__main__':
    #make_regular_season_fall_2016()
    make_regular_season_spring_2017()
