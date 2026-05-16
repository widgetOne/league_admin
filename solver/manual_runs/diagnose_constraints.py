"""Constraint isolation diagnostic.

Runs each component individually (and optionally in pairs) against the
model to identify which constraints are satisfiable alone, which cause
INFEASIBLE, and which cause UNKNOWN (timeout).

Usage:
    python -m solver.manual_runs.diagnose_constraints
"""
import itertools
import time as time_mod
from ortools.sat.python import cp_model

from ..facilities import Facilities
from ..schedule import Schedule
from ..schedule_creator import ScheduleCreator
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from ..exports.gsheets_export import get_team_counts_from_sheets

# ---------- configuration ----------
YAML_PATH = "solver/facilities/configs/volleyball.yaml"
TIMEOUT_SECONDS = 30  # short timeout per probe
TEST_PAIRS = True      # also test all 2-component combos
# -----------------------------------

STATUS_LABELS = {
    cp_model.OPTIMAL: "✅ OPTIMAL",
    cp_model.FEASIBLE: "✅ FEASIBLE",
    cp_model.INFEASIBLE: "❌ INFEASIBLE",
    cp_model.UNKNOWN: "⏱️  UNKNOWN (timeout)",
    cp_model.MODEL_INVALID: "🚫 INVALID",
}


def probe_components(facilities, components, timeout=TIMEOUT_SECONDS):
    """Run the solver with a specific set of components and a short timeout.
    
    Returns (status_code, elapsed_seconds).
    """
    model = cp_model.CpModel()
    schedule = Schedule(facilities, model)

    for component in components:
        for constraint in component._constraints:
            constraint(schedule)
        for optimizer in component._optimizers:
            optimizer(schedule)

    if hasattr(schedule, 'things_to_minimize') and schedule.things_to_minimize:
        schedule.model.Minimize(sum(schedule.things_to_minimize))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 8

    t0 = time_mod.time()
    status = solver.Solve(model)
    elapsed = time_mod.time() - t0
    return status, elapsed


def main():
    # Load facilities
    team_counts = get_team_counts_from_sheets()
    print(f"Team counts: {team_counts}")
    facilities = Facilities.from_yaml(YAML_PATH, team_counts=team_counts)

    # Get all components from the template (including commented-out ones)
    all_components = get_sand_volleyball_template()

    print(f"\n{'='*60}")
    print(f"CONSTRAINT ISOLATION DIAGNOSTIC")
    print(f"{'='*60}")
    print(f"Timeout per probe: {TIMEOUT_SECONDS}s")
    print(f"Components to test: {len(all_components)}")
    print()

    # ---------- Phase 1: Individual components ----------
    print(f"{'─'*60}")
    print("PHASE 1: Individual components")
    print(f"{'─'*60}")
    
    individual_results = {}
    for comp in all_components:
        name = comp.__class__.__name__
        status, elapsed = probe_components(facilities, [comp])
        label = STATUS_LABELS.get(status, f"?? ({status})")
        individual_results[name] = status
        print(f"  {name:40s} {label}  ({elapsed:.1f}s)")

    # ---------- Phase 2: Pairs ----------
    if TEST_PAIRS:
        print(f"\n{'─'*60}")
        print("PHASE 2: Component pairs")
        print(f"{'─'*60}")

        # Only pair components that passed individually
        passing = [c for c in all_components
                   if individual_results[c.__class__.__name__] in (cp_model.OPTIMAL, cp_model.FEASIBLE)]

        if len(passing) < 2:
            print("  Not enough individually-passing components to test pairs.")
        else:
            for a, b in itertools.combinations(passing, 2):
                name = f"{a.__class__.__name__} + {b.__class__.__name__}"
                status, elapsed = probe_components(facilities, [a, b])
                label = STATUS_LABELS.get(status, f"?? ({status})")
                print(f"  {name:60s} {label}  ({elapsed:.1f}s)")

    # ---------- Phase 3: Cumulative (add one at a time) ----------
    print(f"\n{'─'*60}")
    print("PHASE 3: Cumulative build-up")
    print(f"{'─'*60}")

    active = []
    for comp in all_components:
        name = comp.__class__.__name__
        active.append(comp)
        active_names = " + ".join(c.__class__.__name__ for c in active)
        status, elapsed = probe_components(facilities, active)
        label = STATUS_LABELS.get(status, f"?? ({status})")
        print(f"  +{name:40s} → {label}  ({elapsed:.1f}s)")
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"  ⛔ Stopped — model became {label} after adding {name}")
            break

    print(f"\n{'='*60}")
    print("Diagnostic complete.")


if __name__ == "__main__":
    main()
