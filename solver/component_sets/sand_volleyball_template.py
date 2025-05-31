from ..schedule_component.components.total_play import TotalPlay

def get_sand_volleyball_template():
    """Get the template of components for sand volleyball scheduling.
    
    Returns:
        A list of constraint components for sand volleyball scheduling.
    """
    return TotalPlay()