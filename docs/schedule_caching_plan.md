# File-Based Schedule Caching System Plan

This document outlines the design for a local file-based caching system to store intermediate and final schedules generated during single or multi-run optimization processes.

## 1. Hashing and Directory Structure

To ensure that cached schedules correspond to the exact constraints they were generated under, we will group schedules by their facility configuration and team counts.

**Facilities Hash Method:**
* We will add a `get_hash(self)` method to the `Facilities` class.
* This method will generate a deterministic hash (e.g., SHA-256, taking the first 8 characters) based on the core structural data: the list of `Match` objects (dates, times, locations) and `games_per_season`. 
* *Note: We exclude `team_counts` from this specific hash so the hash purely represents the "physical court availability."*

**Directory Naming Convention:**
* Caches will be stored in a local directory, such as `local_cache/`.
* Level 1 (Facilities Configuration): A readable schedule name that includes the number of days, teams per day (average courts per day * 2), and the short hash, e.g., `local_cache/7d_32.0_tpd_a1b2c3d4/`
* Level 2 (Team Counts): A readable format of the team counts, e.g., `local_cache/7d_32.0_tpd_a1b2c3d4/14_10_10/`

## 2. File Contents and Naming

Within the definition directory (`local_cache/[hash]/[counts]/`), two types of files will be generated:

**1. Facility Layout File:**
* A readable copy of the schedule layout (the output of `str(facilities)`) so the court configuration is easily reviewable.
* Name: `facility_layout.txt`

**2. Schedule Files:**
* Files will be named using the model's objective score and the datetime when the schedule generation started.
* Pattern: `{score}_{datetime_start}.csv`
* Example: `local_cache/a1b2c3d4/14_10_10/12450.5_20260514_173000.csv`

## 3. Implementation Steps

1. **Update `Facilities` Class (`solver/facilities/facility.py`):**
   * Implement `get_hash()` utilizing the `hashlib` library to hash a string representation of all `self.matches`.

2. **Create Cache Manager (`solver/cache_manager.py`):**
   * Create a new module responsible for handling these file operations.
   * Include a function `save_schedule_to_cache(schedule, start_time, score)`.
   * The function will retrieve the hash and team counts from `schedule.facilities`, construct the directory path, ensure the directory exists, and write the file.

3. **Integrate with Runner Scripts:**
   * In `make_schedule_and_debug_files()` or inside the multi-run loop (`volleyball_2026_multi_run.py`), capture the start time of the run.
   * Once a valid solution is found, pass the schedule, the score, and the start time to the cache manager.
   * This ensures that every valid solution found during a multi-run is preserved locally, allowing us to review all candidates, not just the single best one tracked in Google Sheets.
