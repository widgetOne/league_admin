from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class CompRefCompConstraint(SchedulerComponent):
    """A component that ensures referees are from the same division as the home team,
    but ONLY for the highest-index (most competitive) division.

    This is a relaxed version of RefSameDivisionConstraint that gives the solver
    more freedom for rec/lower divisions while keeping competitive games tightly
    reffed by peers.
    """

    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_ref_comp_division_constraint())
        self.add_validator(self._get_ref_comp_division_validator())
        self.add_debug_report(self._get_ref_comp_division_debug_report())
        self.add_debug_summary(self._get_ref_comp_division_debug_summary())

    @staticmethod
    def _get_comp_div_index(schedule):
        """Return the index of the most competitive (highest-index) division."""
        return len(schedule.facilities.team_counts) - 1

    # ── Constraint ────────────────────────────────────────────────────

    def _get_ref_comp_division_constraint(self):
        def enforce_ref_comp_division(schedule: Schedule):
            comp_div = self._get_comp_div_index(schedule)

            for m in schedule.matches:
                # Only enforce when the home team is in the competitive division.
                # home_div[m] is an IntVar; we use OnlyEnforceIf with a reified bool.
                is_comp_game = schedule.model.NewBoolVar(
                    f"comp_ref_comp_{m.weekend_idx}_{m.date}_{m.location}_{m.time_idx}"
                )
                schedule.model.Add(schedule.home_div[m] == comp_div).OnlyEnforceIf(is_comp_game)
                schedule.model.Add(schedule.home_div[m] != comp_div).OnlyEnforceIf(is_comp_game.Not())

                # When it IS a competitive game, ref must be from the same division
                schedule.model.Add(
                    schedule.ref_div[m] == comp_div
                ).OnlyEnforceIf(is_comp_game)

        return ModelActor(enforce_ref_comp_division)

    # ── Validator ─────────────────────────────────────────────────────

    def _get_ref_comp_division_validator(self):
        def validate_ref_comp_division(schedule):
            comp_div = self._get_comp_div_index(schedule)
            game_report = schedule.get_game_report()
            violations = []

            for _, game in game_report.iterrows():
                home_team = game['team1']
                ref_team = game['ref']
                home_division = schedule.team_div[home_team]
                ref_division = schedule.team_div[ref_team]

                if home_division == comp_div and ref_division != comp_div:
                    violations.append(
                        f"Game {game['date']} {game['time']}: Home team {home_team} "
                        f"(div {home_division}) reffed by team {ref_team} (div {ref_division})"
                    )

            if violations:
                raise ValueError(
                    f"Competitive-division ref constraint violated ({len(violations)}): "
                    + "; ".join(violations[:5])
                )

        return validate_ref_comp_division

    # ── Debug Summary ─────────────────────────────────────────────────

    def _get_ref_comp_division_debug_summary(self):
        def generate_summary(schedule):
            comp_div = self._get_comp_div_index(schedule)
            game_report = schedule.get_game_report()

            comp_same = 0
            comp_diff = 0
            other_same = 0
            other_diff = 0

            for _, game in game_report.iterrows():
                home_div = schedule.team_div[game['team1']]
                ref_div = schedule.team_div[game['ref']]
                if home_div == comp_div:
                    if ref_div == comp_div:
                        comp_same += 1
                    else:
                        comp_diff += 1
                else:
                    if home_div == ref_div:
                        other_same += 1
                    else:
                        other_diff += 1

            comp_total = comp_same + comp_diff
            other_total = other_same + other_diff
            parts = [f"Comp div {comp_div}: {comp_same}/{comp_total} same-div refs"]
            if other_total > 0:
                parts.append(f"Other divs: {other_same}/{other_total} same-div refs")
            return " | ".join(parts)

        return DebugReporter(generate_summary, "CompRefCompConstraint")

    # ── Debug Report ──────────────────────────────────────────────────

    def _get_ref_comp_division_debug_report(self):
        def generate_report(schedule):
            comp_div = self._get_comp_div_index(schedule)
            game_report = schedule.get_game_report()

            # Group teams by division
            divisions = {}
            for team in schedule.teams:
                div_idx = schedule.team_div[team]
                if div_idx not in divisions:
                    divisions[div_idx] = []
                divisions[div_idx].append(team)

            lines = []
            lines.append("REF COMP-DIVISION DEBUG REPORT")
            lines.append("=" * 50)
            lines.append(f"Competitive division index: {comp_div}")
            lines.append(f"Rule: only div {comp_div} games MUST have a same-division ref")
            lines.append("")

            total_violations = 0
            for div, div_teams in sorted(divisions.items()):
                is_enforced = div == comp_div
                label = "ENFORCED" if is_enforced else "not enforced"
                lines.append(f"Division {div} ({label}, {len(div_teams)} teams)")
                lines.append("-" * 40)

                home_games = game_report[game_report['team1'].isin(div_teams)]
                correct = 0
                wrong = []

                for _, game in home_games.iterrows():
                    ref_team = game['ref']
                    ref_division = schedule.team_div[ref_team]
                    if ref_division == div:
                        correct += 1
                    else:
                        wrong.append({
                            'game': f"{game['date']} {game['time']}",
                            'home': game['team1'],
                            'ref': ref_team,
                            'ref_div': ref_division,
                        })
                        if is_enforced:
                            total_violations += 1

                lines.append(f"  Games: {len(home_games)}  Same-div refs: {correct}  Cross-div refs: {len(wrong)}")
                if wrong and is_enforced:
                    lines.append("  VIOLATIONS:")
                    for v in wrong:
                        lines.append(
                            f"    {v['game']}: Home={v['home']} Ref={v['ref']} (div {v['ref_div']})"
                        )
                lines.append("")

            # Cross-tab summary
            lines.append("REFEREE ASSIGNMENT SUMMARY")
            lines.append("-" * 30)
            lines.append("Home Div | Ref Div | Count")
            lines.append("-" * 30)
            for home_div, home_teams in sorted(divisions.items()):
                home_games = game_report[game_report['team1'].isin(home_teams)]
                for ref_div, ref_teams in sorted(divisions.items()):
                    count = len(home_games[home_games['ref'].isin(ref_teams)])
                    enforced = home_div == comp_div
                    if enforced:
                        status = "✓" if home_div == ref_div else ("✗" if count > 0 else " ")
                    else:
                        status = "·" if home_div == ref_div else " "
                    lines.append(f"   {home_div:2d}    |   {ref_div:2d}    | {count:3d} {status}")

            lines.append("")
            status = "✓ PASS" if total_violations == 0 else "✗ FAIL"
            lines.append(f"Competitive-division violations: {total_violations}")
            lines.append(f"Overall Status: {status}")

            return "\n".join(lines)

        return DebugReporter(generate_report, "CompRefCompConstraint")
