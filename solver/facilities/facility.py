import yaml
from dataclasses import dataclass
from typing import List, Dict, NamedTuple
import pandas as pd
from datetime import datetime

@dataclass
class TimeSlot:
    """Represents a time slot with its court layout."""
    time: str
    courts: List[int]

@dataclass
class GameSlot:
    """Represents a single game slot in the facility."""
    weekend_idx: int
    date: str
    location: int
    time: str
    time_idx: int

class Facilities:
    """Represents the physical and temporal constraints of the facility."""
    
    def __init__(self, 
                 team_counts: List[int],
                 time_slots: List[TimeSlot],
                 dates: List[str],
                 games_per_season: int = 6,
                 games_per_day: int = 1):
        """Initialize the facility with its constraints.
        
        Args:
            team_counts: List of number of teams in each division
            time_slots: List of TimeSlot objects containing time and court layout
            dates: List of dates for the season
            games_per_season: Number of games each team plays in the season
            games_per_day: Number of games each team plays per day
        """
        self.team_counts = team_counts
        self.time_slots = time_slots
        self.dates = dates
        self.games_per_season = games_per_season
        self.games_per_day = games_per_day
        
        # Generate all possible game slots
        self.game_slots = self._generate_game_slots()
        
    def _generate_game_slots(self) -> List[GameSlot]:
        """Generate all possible game slots based on the facility configuration."""
        game_slots = []
        for idx, date in enumerate(self.dates):
            week_idx = idx + 1
            for time_idx, time_slot in enumerate(self.time_slots):
                for court_idx, court_active in enumerate(time_slot.courts):
                    if court_active == 1:
                        game_slots.append(GameSlot(
                            weekend_idx=week_idx,
                            date=date,
                            location=court_idx,
                            time=time_slot.time,
                            time_idx=time_idx
                        ))
        return game_slots
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert the game slots to a pandas DataFrame."""
        return pd.DataFrame([vars(slot) for slot in self.game_slots])
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Facilities':
        """Create a Facilities instance from a YAML configuration file.
        
        Args:
            yaml_path: Path to the YAML configuration file
            
        Returns:
            A new Facilities instance configured according to the YAML file
        """
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Convert time slots from dict to TimeSlot objects
        time_slots = [
            TimeSlot(time=slot['time'], courts=slot['courts'])
            for slot in config['time_slots']
        ]
            
        return cls(
            team_counts=config['team_counts'],
            time_slots=time_slots,
            dates=config['dates'],
            games_per_season=config.get('games_per_season', 6),
            games_per_day=config.get('games_per_day', 1)
        ) 