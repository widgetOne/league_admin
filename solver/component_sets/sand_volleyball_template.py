from ..components.total_play import TotalPlayConstraint
from ..components.vs_play_balance import VsPlayBalanceConstraint
from ..components.balance_reffing import BalanceReffingConstraint

def get_sand_volleyball_template():
    """Get the template of components for sand volleyball scheduling.
    
    Returns:
       Returns a list of the constaints required by default for any
       sand volleyball schedule.
    """
    return [TotalPlayConstraint(), VsPlayBalanceConstraint(), BalanceReffingConstraint()]
