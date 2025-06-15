from ..components.total_play import TotalPlayConstraint
from ..components.vs_play_balance import VsPlayBalanceConstraint
from ..components.balance_reffing import BalanceReffingConstraint
from ..components.one_thing_at_a_time import OneThingAtATimeConstraint
from ..components.play_near_ref import PlayNearRefConstraint
from ..components.ref_same_division import RefSameDivisionConstraint
from ..components.time_variety_optimization import TimeVarietyOptimization
from ..components.rec_in_low_courts import RecInLowCourtsProcessor
from ..components.minimize_bye_weeks import MinimizeByeWeeks

def get_sand_volleyball_template():
    """Get the sand volleyball template components.
    
    Returns:
        list: List of SchedulerComponent instances
    """
    return [
        TotalPlayConstraint(),
        VsPlayBalanceConstraint(),
        BalanceReffingConstraint(),
        OneThingAtATimeConstraint(),
        PlayNearRefConstraint(),
        RefSameDivisionConstraint(),
        TimeVarietyOptimization(weight=1.0),
        RecInLowCourtsProcessor(),
        MinimizeByeWeeks(weight=10.0),
    ] 