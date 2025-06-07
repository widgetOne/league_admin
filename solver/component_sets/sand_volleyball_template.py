from ..components.total_play import TotalPlayConstraint
from ..components.vs_play_balance import VsPlayBalanceConstraint
from ..components.balance_reffing import BalanceReffingConstraint
from ..components.play_near_ref import PlayNearRefConstraint
from ..components.ref_same_division import RefSameDivisionConstraint
from ..components.one_thing_at_a_time import OneThingAtATimeConstraint
from ..components.rec_in_low_courts import RecInLowCourtsProcessor

def get_sand_volleyball_template():
    """Get the template of components for sand volleyball scheduling.
    
    Returns:
       Returns a list of the constaints required by default for any
       sand volleyball schedule.
    """
    return [
        TotalPlayConstraint(), 
        VsPlayBalanceConstraint(), 
        BalanceReffingConstraint(),
        OneThingAtATimeConstraint(),
        PlayNearRefConstraint(),
        RefSameDivisionConstraint(),
        RecInLowCourtsProcessor()
    ]
