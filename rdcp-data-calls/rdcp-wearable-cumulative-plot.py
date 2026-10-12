# RDCP Toolbox - Participant wearable cumulative plots
# Generates daily step-count and sleep-duration bar graphs for each participant.

import json
import math
import os
import re
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

root_dir = os.path.dirname(os.path.abspath(__file__))
byod_dir = os.path.join(root_dir, "output", "BYOD")
plots_dir = os.path.join(root_dir, "output", "BYOD-plots")


params = ["stepcount", "sleep"]

participant_ids = []
# participant_ids = [
#     "6aae39c07b4394e44bcab4e5"
# ]

if participant_ids:
    print(f"Filtering BYOD JSON files for participant IDs: {', '.join(participant_ids)}")


def load_records(path):
    with open(path, "r") as source:
        payload = json.load(source)
    if isinstance(payload, dict):
        return payload.get("records", [])
    if isinstance(payload, list):
        return payload
    return []


def local_datetime(timestamp, timezone_name):
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(ZoneInfo(timezone_name))


def add_sleep_interval(daily_sleep, start, end):
    while start.date() < end.date():
        midnight = datetime.combine(start.date() + timedelta(days=1), time.min, tzinfo=start.tzinfo)
        daily_sleep[start.date()] += elapsed_seconds(start, midnight)
        start = midnight
    if elapsed_seconds(start, end) > 0:
        daily_sleep[start.date()] += elapsed_seconds(start, end)


def elapsed_seconds(start, end):
    return (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds()


def is_asleep(stage):
    normalized_stage = str(stage or "").replace("_", "").replace(" ", "").lower()
    return normalized_stage.startswith("asleep") or normalized_stage in {"sleep", "sleeping"}


os.makedirs(plots_dir, exist_ok=True)

daily_values = defaultdict(lambda: {param: defaultdict(float) for param in params})
seen_records = defaultdict(lambda: {param: set() for param in params})
participant_study_dict = {}
matching_files_found = False

if not os.path.isdir(byod_dir):
    raise FileNotFoundError(f"Missing BYOD directory: {byod_dir}")

filename_pattern = re.compile(r"^(?P<study>[^_]+)_(?P<participant>[^_]+)_(?P<param>.+)\.json$")

for filename in os.listdir(byod_dir):
    match = filename_pattern.match(filename)
    if not match:
        continue

    participant_id = match.group("participant")
    param = match.group("param")
    if param not in params:
        continue
    if participant_ids and participant_id not in participant_ids:
        continue

    matching_files_found = True
    participant_study_dict[participant_id] = match.group("study")
    path = os.path.join(byod_dir, filename)

    for record in load_records(path):
        metadata = record.get("metadata") or {}
        timezone_name = metadata.get("timezone") or "UTC"

        if param == "stepcount":
            timestamp = record.get("start_date") or record.get("time")
            count = record.get("count")
            if timestamp is None or isinstance(count, bool):
                continue
            try:
                count = float(count)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(count):
                continue

            start = local_datetime(timestamp, timezone_name)
            identity = (timestamp, record.get("end_date"), count)
            if identity in seen_records[participant_id][param]:
                continue
            seen_records[participant_id][param].add(identity)
            daily_values[participant_id][param][start.date()] += count
            continue

        samples = record.get("samples") or []
        if samples:
            for sample in samples:
                if not is_asleep(sample.get("stage")):
                    continue
                start_raw = sample.get("start_time")
                end_raw = sample.get("end_time")
                if not start_raw or not end_raw:
                    continue
                start = local_datetime(start_raw, timezone_name)
                end = local_datetime(end_raw, timezone_name)
                if elapsed_seconds(start, end) <= 0:
                    continue

                identity = (start_raw, end_raw, sample.get("stage"))
                if identity in seen_records[participant_id][param]:
                    continue
                seen_records[participant_id][param].add(identity)
                add_sleep_interval(daily_values[participant_id][param], start, end)
        else:
            start_raw = record.get("start_date") or record.get("time")
            end_raw = record.get("end_date") or start_raw
            if not start_raw or not end_raw:
                continue
            start = local_datetime(start_raw, timezone_name)
            end = local_datetime(end_raw, timezone_name)
            if elapsed_seconds(start, end) <= 0:
                continue

            identity = (start_raw, end_raw, "session")
            if identity in seen_records[participant_id][param]:
                continue
            seen_records[participant_id][param].add(identity)
            add_sleep_interval(daily_values[participant_id][param], start, end)

if not matching_files_found:
    participant_filter_label = ", ".join(participant_ids) if participant_ids else "all participants"
    raise FileNotFoundError(f"No BYOD JSON files found in: {byod_dir} for {participant_filter_label}")

participants_with_values = {
    participant_id: values
    for participant_id, values in daily_values.items()
    if any(values[param] for param in params)
}
if not participants_with_values:
    participant_filter_label = ", ".join(participant_ids) if participant_ids else "all participants"
    raise ValueError(
        f"Found BYOD JSON files in {byod_dir} for {participant_filter_label}, "
        "but none contained plottable step-count or sleep records"
    )

for index, (participant_id, values) in enumerate(participants_with_values.items(), start=1):
    populated_dates = [day for param in params for day in values[param]]
    first_day = min(populated_dates)
    last_day = max(populated_dates)
    days = [first_day + timedelta(days=offset) for offset in range((last_day - first_day).days + 1)]
    study_id = participant_study_dict[participant_id]

    fig, (steps_ax, sleep_ax) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    steps_ax.bar(
        days,
        [values["stepcount"].get(day, 0) for day in days],
        color="#1f77b4",
        width=0.8,
    )
    steps_ax.set_ylabel("Steps")
    steps_ax.set_title("Daily steps")
    steps_ax.grid(True, axis="y", alpha=0.25)

    sleep_ax.bar(
        days,
        [values["sleep"].get(day, 0) / 3600 for day in days],
        color="#2ca02c",
        width=0.8,
    )
    sleep_ax.set_ylabel("Sleep (hours)")
    sleep_ax.set_title("Daily sleep")
    sleep_ax.set_xlabel("Date")
    sleep_ax.grid(True, axis="y", alpha=0.25)

    tick_interval = max(1, math.ceil(len(days) / 14))
    sleep_ax.xaxis.set_major_locator(mdates.DayLocator(interval=tick_interval))
    sleep_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.suptitle(f"Daily steps and sleep for participant '{participant_id}' of study '{study_id}'")
    plt.setp(sleep_ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()

    output_file = os.path.join(plots_dir, f"{study_id}_{participant_id}_cumulative.png")
    fig.savefig(output_file, dpi=160)
    plt.close(fig)
    print(f"Generated cumulative plot for participant '{participant_id}' ({index}/{len(participants_with_values)}): {output_file}")

print(f"Done generating cumulative plots for {len(participants_with_values)} participant(s).")
