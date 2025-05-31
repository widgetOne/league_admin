import yaml
from dataclasses import dataclass
from typing import List, Dict, NamedTuple, Set
import pandas as pd
from datetime import datetime

@dataclass
class TimeSlot:
    """Represents a time slot with its court layout."""
    time: str
    courts: List[int]

    def __str__(self):
        return f"Time: {self.time}, Courts: {self.courts}"

@dataclass
class GameSlot:
    """Represents a single game slot in the facility."""
    weekend_idx: int
    date: str
    location: int
    time: str
    time_idx: int

    def __str__(self):
        return f"Week {self.weekend_idx} ({self.date}) - Court {self.location + 1} at {self.time}"

class Facilities:
    """Represents the physical and temporal constraints of the facility."""
    
    def __init__(self, 
                 team_counts: List[int],
                 game_slots: List[GameSlot],
                 games_per_season: int = 6,
                 games_per_day: int = 1):
        """Initialize the facility with its constraints.
        
        Args:
            team_counts: List of number of teams in each division
            game_slots: List of available game slots
            games_per_season: Number of games each team plays in the season
            games_per_day: Number of games each team plays per day
        """
        self.team_counts = team_counts
        self.game_slots = game_slots
        self.games_per_season = games_per_season
        self.games_per_day = games_per_day

    @property
    def dates(self) -> List[str]:
        """Get the list of unique dates in the schedule."""
        return sorted(set(slot.date for slot in self.game_slots))

    @property
    def times(self) -> List[str]:
        """Get the list of unique times in the schedule."""
        return sorted(set(slot.time for slot in self.game_slots))

    @property
    def locations(self) -> List[int]:
        """Get the list of unique locations in the schedule."""
        return sorted(set(slot.location for slot in self.game_slots))

    def __str__(self) -> str:
        """Return a comprehensive string representation of the facility configuration.
        
        Returns:
            A formatted string containing all facility information
        """
        lines = []
        
        # Team Information
        lines.append("Team Configuration:")
        for div_idx, count in enumerate(self.team_counts):
            lines.append(f"  Division {div_idx + 1}: {count} teams")
        lines.append(f"Games per season: {self.games_per_season}")
        lines.append(f"Games per day: {self.games_per_day}")
        lines.append("")
        
        # Game Slots Summary
        lines.append("Game Slots:")
        # Group slots by week
        slots_by_week = {}
        for slot in self.game_slots:
            if slot.weekend_idx not in slots_by_week:
                slots_by_week[slot.weekend_idx] = {}
            if slot.date not in slots_by_week[slot.weekend_idx]:
                slots_by_week[slot.weekend_idx][slot.date] = {}
            if slot.location not in slots_by_week[slot.weekend_idx][slot.date]:
                slots_by_week[slot.weekend_idx][slot.date][slot.location] = []
            slots_by_week[slot.weekend_idx][slot.date][slot.location].append(slot.time)
        
        # Print in hierarchical format
        for week in sorted(slots_by_week.keys()):
            lines.append(f"Week {week}:")
            for date in sorted(slots_by_week[week].keys()):
                if len(slots_by_week[week]) == 1:
                    # If only one date in week, show it on same line
                    lines.append(f"  {date}:")
                else:
                    lines.append(f"  {date}")
                for court in sorted(slots_by_week[week][date].keys()):
                    times = sorted(slots_by_week[week][date][court])
                    lines.append(f"    Court {court + 1}: {times}")
        
        return "\n".join(lines)
    
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
            
        # Generate game slots from the configuration
        game_slots = []
        for idx, date in enumerate(config['dates']):
            week_idx = idx + 1
            for time_idx, time_slot in enumerate(config['time_slots']):
                for court_idx, court_active in enumerate(time_slot['courts']):
                    if court_active == 1:
                        game_slots.append(GameSlot(
                            weekend_idx=week_idx,
                            date=date,
                            location=court_idx,
                            time=time_slot['time'],
                            time_idx=time_idx
                        ))
            
        return cls(
            team_counts=config['team_counts'],
            game_slots=game_slots,
            games_per_season=config.get('games_per_season', 6),
            games_per_day=config.get('games_per_day', 1)
        ) 