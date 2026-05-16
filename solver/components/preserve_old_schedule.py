from typing import List, Any
import pandas as pd
from ..schedule import Schedule
from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter

class PreserveOldSchedule(SchedulerComponent):
    """
    Component to lock in games from a previous schedule for specified weekends.
    """

    def __init__(self, old_schedule: Schedule, weekend_idxs: List[int]):
        """
        Initializes the component.

        Args:
            old_schedule: A solved Schedule object to source constraints from.
            weekend_idxs: A list of integer weekend indices to lock.
        """
        super().__init__()
        self.old_schedule_df = old_schedule.get_game_report()
        self.weekends_to_preserve = weekend_idxs
        
        # Add the constraint, validator, and debug report to the component
        self.add_constraint(ModelActor(self.preserve_weekend_games))
        self.add_validator(ModelActor(self.validate_preserved_games))
        self.add_debug_report(DebugReporter(self.generate_preservation_report, self.__class__.__name__))
        self.add_debug_summary(DebugReporter(self._generate_preservation_summary, self.__class__.__name__))

    def _generate_preservation_summary(self, solved_schedule: Schedule) -> str:
        games_to_preserve = self._get_games_to_preserve()
        count = len(games_to_preserve)
        weekends = ", ".join(str(w) for w in sorted(self.weekends_to_preserve))
        return f"{count} matches preserved from baseline schedule (weekends: {weekends})"

    def preserve_weekend_games(self, new_schedule: Schedule):
        """Applies constraints to match games from the old schedule."""
        print(f"Applying constraints to preserve games from weekends: {self.weekends_to_preserve}")
        games_to_preserve = self._get_games_to_preserve()
        if games_to_preserve.empty:
            print("Warning: No games found in the old schedule for the specified weekends.")
            return

        # Create a more robust lookup map for the new schedule's matches
        new_matches_map = {}
        for m in new_schedule.matches:
            # Normalize the time object for consistent matching
            key = (m.weekend_idx, m.date, m.time.strftime("%H:%M:%S"))
            if key not in new_matches_map:
                new_matches_map[key] = []
            new_matches_map[key].append(m)

        discrepancies, games_constrained = self._apply_constraints(games_to_preserve, new_schedule, new_matches_map)
        
        print(f"Successfully constrained {games_constrained} games.")
        if discrepancies:
            self._raise_discrepancy_error(discrepancies)

    def validate_preserved_games(self, solved_schedule: Schedule):
        """Validator to confirm that the preserved games exist in the final schedule."""
        print(f"Validating preserved games for weekends: {self.weekends_to_preserve}")
        games_to_preserve = self._get_games_to_preserve()
        solved_games_df = solved_schedule.get_game_report()

        # Merge to find matches
        merged = pd.merge(
            games_to_preserve,
            solved_games_df,
            on=['weekend_idx', 'date', 'time', 'location', 'team1', 'team2', 'ref'],
            how='left',
            indicator=True
        )

        missing_games = merged[merged['_merge'] == 'left_only']
        if not missing_games.empty:
            raise ValueError(f"Validation failed! {len(missing_games)} preserved games are missing from the final schedule.")
        print("Validation successful: All preserved games are present in the final schedule.")

    def generate_preservation_report(self, solved_schedule: Schedule) -> str:
        """Generates a debug report summarizing the preservation actions."""
        report_lines = [
            f"PreserveOldSchedule Report",
            f"Target Weekends: {self.weekends_to_preserve}",
        ]
        games_to_preserve = self._get_games_to_preserve()
        report_lines.append(f"Games to Preserve: {len(games_to_preserve)} games")
        
        # Add more details if needed, for example, listing the games
        
        return "\n".join(report_lines)

    def _get_games_to_preserve(self) -> pd.DataFrame:
        """Helper to filter games from the old schedule."""
        return self.old_schedule_df[self.old_schedule_df['weekend_idx'].isin(self.weekends_to_preserve)].copy()

    def _apply_constraints(self, games_df, schedule, matches_map):
        """Helper to apply constraints and track discrepancies."""
        discrepancies = []
        constrained_count = 0
        
        # Keep track of which new matches have been used
        used_matches = set()

        for _, game_row in games_df.iterrows():
            # Ensure the time from the dataframe matches the normalized key format
            match_key = (
                game_row['weekend_idx'],
                game_row['date'],
                pd.to_datetime(game_row['time']).strftime("%H:%M:%S")
            )
            
            potential_matches = matches_map.get(match_key, [])
            
            # Find an available match that hasn't been used yet
            target_match = None
            for match in potential_matches:
                if match not in used_matches:
                    target_match = match
                    break

            if target_match:
                # Constrain the found match and mark it as used
                schedule.model.Add(schedule.home_team[target_match] == int(game_row['team1']))
                schedule.model.Add(schedule.away_team[target_match] == int(game_row['team2']))
                schedule.model.Add(schedule.ref[target_match] == int(game_row['ref']))
                used_matches.add(target_match)
                constrained_count += 1
            else:
                # No available match slot found for this game
                discrepancies.append(f"  - Wk {game_row['weekend_idx']}, {game_row['date']}, {game_row['time']} (No available court)")
                
        return discrepancies, constrained_count
        
    def _raise_discrepancy_error(self, discrepancies):
        """Helper to format and raise the configuration mismatch error."""
        error_message = (
            "Schedule generation failed due to configuration mismatch.\n"
            "The following games from the old schedule could not be found "
            "in the new facility configuration:\n"
        )
        error_message += "\n".join(discrepancies)
        raise ValueError(error_message) 