import cProfile
import pstats
import datetime
import run_regular_season

def get_profile_of_process(command):
    """function to run other functions with profiler without having to set
    the formatting, for which I have always wanted the same parameters"""
    # http://stackoverflow.com/questions/582336/how-can-you-profile-a-script
    stat_path = '/tmp/rt_run_stats_{}.txt'.format(datetime.datetime.now()).replace(' ', '_')
    cProfile.run(command, stat_path)
    print('stat_path = {}'.format(stat_path))
    p = pstats.Stats(stat_path)
    p.strip_dirs().sort_stats(-1).print_stats()
    p.sort_stats('cumulative').print_stats(40)


if __name__ == '__main__':
    #get_profile_of_process("class_googleparser.google_parser_manual_test('https://www.google.com/maps?cid=1141207638858050160')")
    get_profile_of_process( "run_regular_season.make_2018_fall_regular_season_schedule()")
