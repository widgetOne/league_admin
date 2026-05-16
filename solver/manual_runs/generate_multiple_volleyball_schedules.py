#!/usr/bin/env python3
"""
CLI for multi-run volleyball schedule generation.

Usage examples:
    # Generate 1 schedule with 2-minute solver runs
    python -m solver.manual_runs.generate_multiple_volleyball_schedules -n 1 -t 2

    # Generate 6 schedules with 5-minute solver runs
    python -m solver.manual_runs.generate_multiple_volleyball_schedules -n 6 -t 5

    # Generate schedules for 30 minutes total, 4 minutes each
    python -m solver.manual_runs.generate_multiple_volleyball_schedules --total-time 30 -t 4
"""

import argparse
import sys
from ..generate_schedule import generate_schedules


def main():
    parser = argparse.ArgumentParser(
        description="Generate volleyball schedules and cache the results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s -n 1 -t 2        # 1 schedule, 2-min solver\n"
            "  %(prog)s -n 6 -t 5        # 6 schedules, 5-min solver\n"
            "  %(prog)s --total-time 30   # run for 30 min total\n"
        ),
    )

    parser.add_argument(
        "-t", "--solve-time",
        type=float,
        default=4.0,
        metavar="MIN",
        help="Minutes per solver run (default: 4)",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-n", "--num-schedules",
        type=int,
        default=None,
        metavar="N",
        help="Number of schedules to generate",
    )
    group.add_argument(
        "--total-time",
        type=float,
        default=None,
        metavar="MIN",
        help="Total wall-clock minutes to spend generating schedules",
    )

    parser.add_argument(
        "--update-sheet",
        action="store_true",
        default=False,
        help="Upload best schedule to Google Sheets after generation",
    )

    args = parser.parse_args()

    generate_schedules(
        solve_time_minutes=args.solve_time,
        num_schedules=args.num_schedules,
        total_time_minutes=args.total_time,
        update_sheet=args.update_sheet,
    )


if __name__ == "__main__":
    main()
