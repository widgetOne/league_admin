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
class Match:
    """Represents a single game slot in the facility."""
    weekend_idx: int
    date: str
    location: int
    time: time
    time_idx: int

    def __str__(self):
        return f"Week {self.weekend_idx} ({self.date}) - Court {self.location + 1} at {self.time.strftime('%H:%M')}"

    def __hash__(self):
        return hash((self.weekend_idx, self.date, self.location, self.time, self.time_idx))
    
    def __eq__(self, other):
        return (self.__hash__()) == (other.__hash__())

class Facilities:
    """Represents the physical and temporal constraints of the facility."""
    
    def __init__(self, 
                 team_counts: List[int],
                 games_per_season: int,
                 games_per_day: int,
                 times: List[time],
                 dates: List[str],
                 locations: List[str],
                 matches: List[Match]):
        """Initialize a new Facilities instance.
        
        Args:
            team_counts: List of team counts per division
            games_per_season: Number of games each team plays in a season
            games_per_day: Maximum number of games a team can play in one day
            times: List of available time slots
            dates: List of available dates
            locations: List of available locations
            matches: List of all possible game slots
        """
        self.team_counts = team_counts
        self.games_per_season = games_per_season
        self.games_per_day = games_per_day
        self._times = times
        self._dates = dates
        self._locations = locations
        self.matches = matches
        
        # Create time index mapping for maintaining original order
        self.time_idx = {t: idx for idx, t in enumerate(times)}

    @property
    def times(self) -> List[time]:
        """Get the list of unique times in the schedule."""
        return self._times

    @times.setter
    def times(self, value: List[time]):
        """Set the list of times."""
        self._times = value

    @property
    def dates(self) -> List[str]:
        """Get the list of unique dates in the schedule."""
        return self._dates

    @dates.setter
    def dates(self, value: List[str]):
        """Set the list of dates."""
        self._dates = value

    @property
    def locations(self) -> List[int]:
        """Get the list of unique locations in the schedule."""
        return self._locations

    @locations.setter
    def locations(self, value: List[int]):
        """Set the list of locations."""
        self._locations = value

    @property
    def total_teams(self) -> int:
        """Get the total number of teams across all divisions."""
        return sum(self.team_counts)

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
        lines.append("Matches:")
        # Group slots by week
        slots_by_week = {}
        for slot in self.matches:
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
        } for slot in self.matches])
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Facilities':
        """Create a Facilities instance from a YAML configuration file.
        
        Supports two formats:
        1. Legacy format: global time_slots + separate dates list
        2. New format: dates list with embedded time_slots per date
        
        Args:
            yaml_path: Path to the YAML configuration file
            
        Returns:
            A new Facilities instance configured according to the YAML file
        """
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Detect format and normalize to new format
        if 'time_slots' in config and isinstance(config['dates'], list) and isinstance(config['dates'][0], str):
            # Legacy format: global time_slots + string dates
            normalized_dates = []
            for date_str in config['dates']:
                normalized_dates.append({
                    'date': date_str,
                    'time_slots': config['time_slots']
                })
        else:
            # New format: dates with embedded time_slots
            normalized_dates = config['dates']
        
        # Extract all unique times across all dates (maintaining order)
        # Only include times where at least one court is active
        all_times = []
        time_set = set()
        for date_entry in normalized_dates:
            for time_slot in date_entry['time_slots']:
                # Only include this time if at least one court is active
                if any(court == 1 for court in time_slot['courts']):
                    time_str = time_slot['time']
                    if time_str not in time_set:
                        all_times.append(datetime.strptime(time_str, '%H:%M').time())
                        time_set.add(time_str)
        
        # Create time index mapping
        time_to_idx = {t: idx for idx, t in enumerate(all_times)}
        
        # Generate game slots from the configuration
        matches = []
        date_strings = []
        
        for idx, date_entry in enumerate(normalized_dates):
            week_idx = idx + 1
            date_str = date_entry['date']
            date_strings.append(date_str)
            
            for time_slot in date_entry['time_slots']:
                # Only process time slots where at least one court is active
                if any(court == 1 for court in time_slot['courts']):
                    t_obj = datetime.strptime(time_slot['time'], '%H:%M').time()
                    time_idx = time_to_idx[t_obj]
                    
                    for court_idx, court_active in enumerate(time_slot['courts']):
                        if court_active == 1:
                            matches.append(Match(
                                weekend_idx=week_idx,
                                date=date_str,
                                location=court_idx,
                                time=t_obj,
                                time_idx=time_idx
                            ))
        
        # Determine number of courts from first time slot
        first_time_slots = normalized_dates[0]['time_slots']
        num_courts = len(first_time_slots[0]['courts']) if first_time_slots else 4
            
        return cls(
            team_counts=config['team_counts'],
            games_per_season=config.get('games_per_season', 6),
            games_per_day=config.get('games_per_day', 1),
            times=all_times,
            dates=date_strings,
            locations=list(range(num_courts)),
            matches=matches
        ) 