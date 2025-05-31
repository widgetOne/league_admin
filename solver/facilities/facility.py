import yaml
from dataclasses import dataclass
from typing import List, Dict, NamedTuple, Set
import pandas as pd
from datetime import datetime, time

@dataclass
class TimeSlot:
    """Represents a time slot with its court layout."""
    time: time
    courts: List[int]

    def __str__(self):
        return f"Time: {self.time.strftime('%H:%M')}, Courts: {self.courts}"

@dataclass
class GameSlot:
    """Represents a single game slot in the facility."""
    weekend_idx: int
    date: str
    location: int
    time: time
    time_idx: int

    def __str__(self):
        return f"Week {self.weekend_idx} ({self.date}) - Court {self.location + 1} at {self.time.strftime('%H:%M')}"

class Facilities:
    """Represents the physical and temporal constraints of the facility."""
    
    def __init__(self, 
                 team_counts: List[int],
                 games_per_season: int,
                 games_per_day: int,
                 times: List[time],
                 dates: List[str],
                 locations: List[str],
                 game_slots: List[GameSlot]):
        """Initialize a new Facilities instance.
        
        Args:
            team_counts: List of team counts per division
            games_per_season: Number of games each team plays in a season
            games_per_day: Maximum number of games a team can play in one day
            times: List of available time slots
            dates: List of available dates
            locations: List of available locations
            game_slots: List of all possible game slots
        """
        self.team_counts = team_counts
        self.games_per_season = games_per_season
        self.games_per_day = games_per_day
        self.times = times
        self.dates = dates
        self.locations = locations
        self.game_slots = game_slots
        
        # Create time index mapping for maintaining original order
        self.time_idx = {t: idx for idx, t in enumerate(times)}

    @property
    def dates(self) -> List[str]:
        """Get the list of unique dates in the schedule."""
        return sorted(set(slot.date for slot in self.game_slots))

    @property
    def times(self) -> List[time]:
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
                    # Sort times based on their index in time_idx
                    times = sorted(slots_by_week[week][date][court], 
                                 key=lambda t: self.time_idx[t])
                    # Format times as 24-hour strings
                    time_strs = [t.strftime('%H:%M') for t in times]
                    lines.append(f"    Court {court + 1}: {time_strs}")
        
        return "\n".join(lines)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert the game slots to a pandas DataFrame."""
        return pd.DataFrame([{
            **vars(slot),
            'time': slot.time.strftime('%H:%M')
        } for slot in self.game_slots])
    
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
            
        # Parse times as datetime.time objects
        times = [datetime.strptime(t, '%H:%M').time() for t in config['times']]
        # Parse time_slots as well
        time_slots = []
        for ts in config['time_slots']:
            t_obj = datetime.strptime(ts['time'], '%H:%M').time()
            time_slots.append({'time': t_obj, 'courts': ts['courts']})
        
        # Generate game slots from the configuration
        game_slots = []
        for idx, date in enumerate(config['dates']):
            week_idx = idx + 1
            for time_idx, time_slot in enumerate(time_slots):
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
            games_per_season=config.get('games_per_season', 6),
            games_per_day=config.get('games_per_day', 1),
            times=times,
            dates=config['dates'],
            locations=config['locations'],
            game_slots=game_slots
        ) 