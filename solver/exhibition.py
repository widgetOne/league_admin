"""Utility functions for computing exhibition game counts.

Exhibition games occur when the math of team counts and games per season
doesn't produce perfect pairings. Specifically, a division needs an
exhibition game when both games_per_season and team_count are odd — 
the total team-games in that division would be odd, which can't divide
evenly into 2-team matches.
"""
from typing import List


def exhibition_games_by_division(team_counts: List[int], games_per_season: int) -> List[int]:
    """Calculate the expected number of exhibition games per division.
    
    A division needs exactly 1 exhibition game when both games_per_season
    and the division's team count are odd. Otherwise it needs 0.
    
    Args:
        team_counts: List of team counts per division
        games_per_season: Number of official games each team plays
        
    Returns:
        List of expected exhibition game counts, one per division
    """
    return [
        1 if (games_per_season % 2 == 1 and count % 2 == 1) else 0
        for count in team_counts
    ]


def has_exhibition_games(team_counts: List[int], games_per_season: int) -> bool:
    """Check whether any division requires exhibition games.
    
    Args:
        team_counts: List of team counts per division
        games_per_season: Number of official games each team plays
        
    Returns:
        True if at least one division needs exhibition games
    """
    return any(count > 0 for count in exhibition_games_by_division(team_counts, games_per_season))
