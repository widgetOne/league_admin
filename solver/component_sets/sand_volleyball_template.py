from ..components.total_play import TotalPlayConstraint
from ..components.vs_play_balance import VsPlayBalanceConstraint
from ..components.balance_reffing import BalanceReffingConstraint
from ..components.play_near_ref import PlayNearRefConstraint
from ..components.ref_same_division import RefSameDivisionConstraint
from ..components.comp_ref_comp import CompRefCompConstraint
from ..components.same_div_ref_optimization import SameDivisionRefOptimization
from ..components.one_thing_at_a_time import OneThingAtATimeConstraint
from ..components.rec_in_low_courts import RecInLowCourtsProcessor
from ..components.time_variety_optimization import TimeVarietyOptimization
from ..components.bye_week_optimization import ByeWeekOptimization
from ..components.no_three_hours_days import NoThreeHoursDays

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
        CompRefCompConstraint(),  # Only enforces same-div refs for the competitive division
        SameDivisionRefOptimization(weight=10.0),  # Soft penalty per cross-division ref
        TimeVarietyOptimization(weight=1.0),
        RecInLowCourtsProcessor(),
        ByeWeekOptimization(weight=10000.0),
        NoThreeHoursDays(),
    ]

