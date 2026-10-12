# RDCP Toolbox - Participant info calls
# This script generates timeseries data availability plots for each participant based on 'wearable-calls' output files.
# When participant_ids is not empty, it will only do so for the listed participant IDs. Otherwise, it will generate plots for all participants found in the 'wearable-calls' output files.

import json
import os
import re
import sys
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timezone

import rdcp_utils

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root_dir))

byod_dir = os.path.join(root_dir, "output", "BYOD")
plots_dir = os.path.join(root_dir, "output", "BYOD-plots")

params = [
    "stepcount",
    "heartrate",
    "resting_heartrate",
    "heartrate_variability_rmssd",
    "heartrate_variability_sdnn",
    "sleep"
]

participant_ids = []
# participant_ids = [
#     '6ac60547b4c60f046786aef5'
# ]

if len(participant_ids) > 0:
    print(f"Filtering BYOD JSON files for participant IDs: {', '.join(participant_ids)}")

def load_records(path):
    with open(path, "r") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        return payload.get("records", [])
    if isinstance(payload, list):
        return payload
    return []

os.makedirs(plots_dir, exist_ok=True)

series = defaultdict(lambda: defaultdict(list))
seen_intervals = defaultdict(lambda: defaultdict(set))
matching_files_found = False

if not os.path.isdir(byod_dir):
    raise FileNotFoundError(f"Missing BYOD directory: {byod_dir}")

participant_study_dict = {}

for filename in os.listdir(byod_dir):

    match = re.match(r"^(?P<study>[^_]+)_(?P<participant>[^_]+)_(?P<param>.+)\.json$", filename)

    if not match:
        continue

    participant_id = match.group("participant")

    if len(participant_ids) != 0 and participant_id not in participant_ids:
        continue

    matching_files_found = True

    study_id = match.group("study")
    participant_study_dict[participant_id] = study_id

    param = match.group("param")
    path = os.path.join(byod_dir, filename)

    for record in load_records(path):

        timezone_name = record['metadata']['timezone'] or "UTC"

        start_raw = record['start_date'] if 'start_date' in record else record['time']
        end_raw = record['end_date'] if 'end_date' in record else record['time']

        start_str = rdcp_utils.adjust_timestamp(start_raw, timezone_name, True) if start_raw else None
        end_str = rdcp_utils.adjust_timestamp(end_raw, timezone_name, True) if end_raw else None

        if start_str is None:
            continue
        if end_str is None:
            end_str = start_str

        interval = (start_str, end_str)

        if interval in seen_intervals[participant_id][param]:
            # print('Skipping duplicate interval for participant', participant_id, 'param', param, 'interval', interval)
            continue

        seen_intervals[participant_id][param].add(interval)
        series[participant_id][param].append(interval)

if not matching_files_found:
   participant_filter_label = ", ".join(participant_ids) if len(participant_ids) > 0 else "all participants"
   raise FileNotFoundError(f"No BYOD JSON files found in: {byod_dir} for {participant_filter_label}")

if not series:
   participant_filter_label = ", ".join(participant_ids) if len(participant_ids) > 0 else "all participants"
   raise ValueError(f"Found BYOD JSON files in {byod_dir} for {participant_filter_label}, but none contained plottable records")

total_start_datetime = datetime.now(timezone.utc)
today = total_start_datetime.date()
today_end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

for index, (participant_id, param_dict) in enumerate(series.items(), start=1):

    participant_start_datetime = datetime.now(timezone.utc)

    fig, ax = plt.subplots(figsize=(14, 5))
    y_positions = {param: i for i, param in enumerate(params)}

    first_start = today_end

    for param in params:

        intervals = param_dict.get(param, [])

        for start_str, end_str in intervals:

            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)

            if start.date() > today:
                continue

            if start < first_start:
                first_start = start

            clipped_end = min(end, today_end)
            duration = mdates.date2num(clipped_end) - mdates.date2num(start)

            if duration <= 0:

                ax.plot(
                    mdates.date2num(start),
                    y_positions[param],
                    marker="|",
                    markersize=28,
                    markeredgewidth=1.6,
                    color="#1f77b4",
                )
                continue

            ax.broken_barh(
                [(mdates.date2num(start), duration)],
                (y_positions[param] - 0.35, 0.7),
                facecolors="#1f77b4",
                edgecolors="#1f77b4",
            )

    file = os.path.join(plots_dir, f"{participant_study_dict[participant_id]}_{participant_id}.png")

    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(params)
    ax.set_xlim(mdates.date2num(first_start), mdates.date2num(today_end))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.grid(True, axis="x", alpha=0.25)
    ax.set_title(f"Wearable data availability for participant '{participant_id}' of study '{study_id}'")
    ax.set_xlabel("Date")
    ax.set_ylabel("Parameter")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(file, dpi=160)
    plt.close(fig)

    print(f"Generated plot for participant '{participant_id}' ({index}/{len(series)}), generation took {(datetime.now(timezone.utc) - participant_start_datetime).total_seconds() / 60:.2f} minutes.")


print(f"Done generating plots for all participants, generation took {(datetime.now(timezone.utc) - total_start_datetime).total_seconds() / 60:.2f} minutes.")
