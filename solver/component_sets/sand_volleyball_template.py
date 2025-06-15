from ..components.total_play import TotalPlayConstraint
from ..components.vs_play_balance import VsPlayBalanceConstraint
from ..components.balance_reffing import BalanceReffingConstraint
from ..components.play_near_ref import PlayNearRefConstraint
from ..components.ref_same_division import RefSameDivisionConstraint
from ..components.one_thing_at_a_time import OneThingAtATimeConstraint
from ..components.rec_in_low_courts import RecInLowCourtsProcessor
from ..components.time_variety_optimization import TimeVarietyOptimization
from ..components.bye_week_optimization import ByeWeekOptimization
from ..components.triple_busy_optimization import TripleBusyOptimization

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
        ByeWeekOptimization(weight=1000.0),
        TripleBusyOptimization(weight=10000.0),
    ]
