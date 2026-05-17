from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class SameDivisionRefOptimization(SchedulerComponent):
    """An optimization that penalizes inter-division reffing.

    Adds a penalty to the objective for every match where the referee is from a
    different division than the home team.  This is a soft preference — the
    solver will still assign cross-division refs when it must, but will prefer
    same-division refs when possible.
    """

    def __init__(self, weight=10.0):
        """Initialize the component.

        Args:
            weight: Penalty added to the objective per cross-division ref
                    assignment.  Higher values make same-division reffing
                    more important relative to other objectives.
        """
        super().__init__()
        self.weight = weight
        self.add_optimizer(self._get_same_div_ref_optimizer())
        self.add_debug_report(self._get_same_div_ref_debug_report())
        self.add_debug_summary(self._get_same_div_ref_debug_summary())

    # ── Optimizer ─────────────────────────────────────────────────────

    def _get_same_div_ref_optimizer(self):
        def optimize_same_div_refs(schedule: Schedule):
            if not hasattr(schedule, 'things_to_minimize'):
                schedule.things_to_minimize = []

            for m in schedule.matches:
                # Boolean: true when ref_div is greater than home_div (1x weight)
                ref_greater = schedule.model.NewBoolVar(
                    f"ref_greater_{m.weekend_idx}_{m.date}_{m.location}_{m.time_idx}"
                )
                schedule.model.Add(
                    schedule.ref_div[m] > schedule.home_div[m]
                ).OnlyEnforceIf(ref_greater)
                schedule.model.Add(
                    schedule.ref_div[m] <= schedule.home_div[m]
                ).OnlyEnforceIf(ref_greater.Not())

                # Boolean: true when home_div is greater than ref_div (4x weight)
                home_greater = schedule.model.NewBoolVar(
                    f"home_greater_{m.weekend_idx}_{m.date}_{m.location}_{m.time_idx}"
                )
                schedule.model.Add(
                    schedule.home_div[m] > schedule.ref_div[m]
                ).OnlyEnforceIf(home_greater)
                schedule.model.Add(
                    schedule.home_div[m] <= schedule.ref_div[m]
                ).OnlyEnforceIf(home_greater.Not())

                schedule.things_to_minimize.append(ref_greater * int(self.weight))
                schedule.things_to_minimize.append(home_greater * int(4 * self.weight))

        return ModelActor(optimize_same_div_refs)

    # ── Debug Summary ─────────────────────────────────────────────────

    def _get_same_div_ref_debug_summary(self):
        def generate_summary(schedule):
            game_report = schedule.get_game_report()
            same = 0
            ref_greater = 0
            home_greater = 0
            for _, game in game_report.iterrows():
                home_div = schedule.team_div[game['team1']]
                ref_div = schedule.team_div[game['ref']]
                if home_div == ref_div:
                    same += 1
                elif ref_div > home_div:
                    ref_greater += 1
                else:
                    home_greater += 1
            total = same + ref_greater + home_greater
            pct = (same / total * 100) if total > 0 else 0
            total_penalty = ref_greater * self.weight + home_greater * (4 * self.weight)
            return (
                f"Same-div refs: {same}/{total} ({pct:.0f}%) | "
                f"Cross-div refs: {ref_greater + home_greater} (ref>home: {ref_greater}, home>ref: {home_greater}, penalty: {total_penalty:.0f})"
            )

        return DebugReporter(generate_summary, "SameDivisionRefOptimization")

    # ── Debug Report ──────────────────────────────────────────────────

    def _get_same_div_ref_debug_report(self):
        def generate_report(schedule):
            game_report = schedule.get_game_report()

            # Group teams by division
            divisions = {}
            for team in schedule.teams:
                div_idx = schedule.team_div[team]
                if div_idx not in divisions:
                    divisions[div_idx] = []
                divisions[div_idx].append(team)

            lines = []
            lines.append("SAME-DIVISION REF OPTIMIZATION REPORT")
            lines.append("=" * 50)
            lines.append(f"Penalty weight (ref_div > home_div): {self.weight}")
            lines.append(f"Penalty weight (home_div > ref_div): {4 * self.weight}")
            lines.append("")

            # Cross-tab: Home Div → Ref Div
            lines.append("Home Div | Ref Div | Count")
            lines.append("-" * 30)
            ref_greater_count = 0
            home_greater_count = 0
            for home_div, home_teams in sorted(divisions.items()):
                home_games = game_report[game_report['team1'].isin(home_teams)]
                for ref_div, ref_teams in sorted(divisions.items()):
                    count = len(home_games[home_games['ref'].isin(ref_teams)])
                    if home_div == ref_div:
                        marker = "✓"
                    else:
                        marker = "✗" if count > 0 else "·"
                        if ref_div > home_div:
                            ref_greater_count += count
                        else:
                            home_greater_count += count
                    lines.append(f"   {home_div:2d}    |   {ref_div:2d}    | {count:3d} {marker}")

            lines.append("")
            lines.append(f"Cross-div refs where ref_div > home_div: {ref_greater_count} (penalty: {ref_greater_count * self.weight:.0f})")
            lines.append(f"Cross-div refs where home_div > ref_div: {home_greater_count} (penalty: {home_greater_count * 4 * self.weight:.0f})")
            lines.append(f"Total penalty contribution: {(ref_greater_count * self.weight + home_greater_count * 4 * self.weight):.0f}")

            return "\n".join(lines)

        return DebugReporter(generate_report, "SameDivisionRefOptimization")
