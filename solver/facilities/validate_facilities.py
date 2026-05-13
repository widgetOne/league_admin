import math

def validate_facilities(facilities):
    """
    Validate that the facility has enough game slots to support the requested schedule.
    
    Args:
        facilities: The Facilities object to validate.
        
    Raises:
        ValueError: If there are not enough available match slots for the season.
    """
    games_per_season = facilities.games_per_season
    available_matches = len(facilities.matches)
    
    # Calculate required matches division by division
    # For a division with odd teams and odd games_per_season, we round up the number of 
    # matches needed (ceiling) to ensure enough capacity for all team appearances.
    required_matches = sum(math.ceil(count * games_per_season / 2) for count in facilities.team_counts)
    
    if available_matches < required_matches:
        raise ValueError(
            f"Facility Validation Failed: Not enough game slots available. "
            f"Available: {available_matches}, "
            f"Required: {required_matches} "
            f"(based on division team counts {facilities.team_counts} playing {games_per_season} games each)."
        )
    
    print(f"Facility validation passed: {available_matches} slots available for {required_matches} required games.")
