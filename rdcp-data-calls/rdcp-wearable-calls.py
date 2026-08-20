# RDCP Toolbox - Participant info calls
# This script retrieves wearable data using the participant ID.

import rdcp_utils
import rdcp_script_utils
import json
import re
import os

study_ids = []

participant_ids = [
#     '6a21501ad1ef7e947151dbfb', # eigen test account 1
#     '6a1959a1627e0b0c53de1958', # eigen test account 2
]

if (len(participant_ids) == 0 and len(study_ids) == 0):
    study_id = rdcp_script_utils.id_input('study')
    study_ids.append(study_id)

export_email_instead_of_firstname_input = input("Do you want to export email instead of firstname? (y/N) ").strip().lower()
export_email_instead_of_firstname = True if export_email_instead_of_firstname_input == 'y' or export_email_instead_of_firstname_input == 'yes' else False

participant_map = {}

if len(participant_ids) != 0:

    for participant_id in participant_ids:
            participant = rdcp_utils.get_participant( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), participant_id )
            participant_map[participant['id']] = participant
else:

    participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url() )

    for participant in participants:
        participant_map[participant['id']] = participant

    participant_ids = [participant['id'] for participant in participants if any(study_id in study_ids for study_id in participant['studies'])]

params = ['stepcount','heartrate','resting_heartrate','heartrate_variability_rmssd','heartrate_variability_sdnn','sleep']
# params = ['stepcount']
# params = ['stepcount','heartrate_variability_rmssd','heartrate_variability_sdnn']

header_list = [
    "Participant ID",
    "Firstname" if not export_email_instead_of_firstname else "Email",
    "Has started experiment",
    "Has completed experiment",
    "Phone model",
    "Phone manufacturer",
    "Measurements (fetched/total)",
    "Has HRV measurements",
    "Measurement sources",
    "Measured params",
    "First sync date",
    "Last sync date"
]

output_file = open(f"./output/{'-'.join(study_ids) if len(study_ids) > 0 else 'specific-participants'}_wearable_summary.tsv", 'w')
output_file.write(f"{'\t'.join(header_list)}\n")

if not os.path.exists('./output/BYOD'):
    os.makedirs('./output/BYOD')

if 'heartrate_variability_rmssd' not in params and 'heartrate_variability_sdnn' not in params:
    print("NOTE: HRV data will not be fetched because 'heartrate_variability_rmssd' and 'heartrate_variability_sdnn' are not in the params list")

for participant_id in participant_ids:

    has_started_mme = False
    has_completed_mme = False
    has_hrv_data = False
    
    sources = []
    measured_params = []
    total_fetched_measurements = 0
    total_measurements = 0

    first_measurment_date = None
    last_measurement_date = None

    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant_id}/experiments" )

    if response:

        items = response['items']

        phone_model = ''
        phone_manufacturer = ''

        for item in items:

            if 'type' in item.keys() and item['type'] == 'multiMetric':
                has_started_mme = True
                phone_model = item['deviceMetadata']['deviceModel']
                phone_manufacturer = item['deviceMetadata']['manufacturer']
                has_completed_mme = item['result']['completed']

    for param in params:

        response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/health/{param}", { "user_id": participant_id, "limit": 9999999999 } )

        if response:

            record_count = len(response['records'])
            first_record = response['records'][0] if record_count > 0 else None
            first_record_time = first_record['start_date'] if first_record and 'start_date' in first_record else first_record['time'] if first_record and 'time' in first_record else 'NA'
            last_record = response['records'][-1] if record_count > 0 else None
            last_record_time = last_record['end_date'] if last_record and 'end_date' in last_record else last_record['time'] if last_record and 'time' in last_record else 'NA'

            if last_record_time != 'NA':

                measured_params.append(param)

                last_record_time = rdcp_utils.adjust_timestamp(last_record_time, last_record['metadata']['timezone'], False)
                first_record_time = rdcp_utils.adjust_timestamp(first_record_time, first_record['metadata']['timezone'], False)

                if not first_measurment_date or first_record_time < first_measurment_date:
                    first_measurment_date = first_record_time

                if not last_measurement_date or last_record_time > last_measurement_date:
                    last_measurement_date = last_record_time

                if param.startswith('heartrate_variability'):
                    has_hrv_data = True

                for record in response['records']:

                    source = { 'type': record['metadata']['device']['type'], 'model': record['metadata']['device']['model'], 'app': record['metadata']['app']['name'] }

                    if source not in sources:
                        sources.append(source)

                total_fetched_measurements += response['metadata']['count']
                total_measurements += response['metadata']['total_count']

            elif param == 'stepcount':
                break

            # print(f"Successfully fetched {response['metadata']['count']}/{response['metadata']['total_count']} '{param}' data entries for participant '{participant_id}', latest measurement: {last_record_time}, HRV: {has_hrv_data}")

            with open(f"./output/BYOD/{participant_id}_{param}.json", 'w') as f:
                f.write(json.dumps(response, indent=4))

    source_labels = []

    if total_measurements > 0:

        for source in sources:

            source_label = 'Not_determined'

            if source['model'] and re.search(r'Watch\d+,\d+', source['model']):
                source_label = 'Apple Watch (Apple Watch)'
            elif source['app'] and source['app'].startswith('com.apple.health'):
                source_label = 'Apple Health'
            elif source['app'] and source['app'].startswith('com.android.healthconnect'):
                source_label = 'Google Health Connect'
            elif source['app'] and source['app'].startswith('com.garmin'):
                source_label = 'Garmin Health Connect'
            elif source['app'] and source['app'].startswith('com.sec.android.app.shealth'):
                source_label = 'Samsung Health'
            elif source['app'] and source['app'].startswith('com.google.android.apps.fitness'):
                source_label = 'Google Fitness'
            elif source['app'] and source['app'].startswith('com.fitbit.FitbitMobile'):
                source_label = 'Fitbit'
            elif source['app'] and source['app'].startswith('fi.polar.polarflow'):
                source_label = 'Polar'
            elif source['app'] and source['app'].startswith('com.ouraring.oura'):
                source_label = 'Oura'
            elif source['app'] and source['app'].startswith('com.coros.coros'):
                source_label = 'Coros'
            elif source['app'] and source['app'].startswith('com.sports-tracker.suunto'):
                source_label = 'Suunto'
            elif source['type'] and source['type'] == 'Phone':
                source_label = 'Phone'
                print(f"Source label set to Phone, more info to extract? Source: {json.dumps(source)}")
            else:
                print(f"Source label could not be determined, more info to extract? Source: {json.dumps(source)}")

            source_labels.append(source_label)

    participant_label = participant_map[participant_id]['firstname'] if not export_email_instead_of_firstname else participant_map[participant_id]['email']
    has_started_mme_label = 'Yes' if has_started_mme else 'No'
    has_completed_mme_label = 'Yes' if has_completed_mme else 'No'
    measurements_label = f"{total_fetched_measurements}/{total_measurements}" if total_measurements > 0 else ''
    hrv_label = 'Yes' if has_hrv_data else 'No' if has_started_mme and total_measurements > 0 else ''
    source_labels = ', '.join(sorted(source_labels))
    param_labels = ', '.join(measured_params)

    line_list = [
        participant_id,
        participant_label,
        has_started_mme_label,
        has_completed_mme_label,
        phone_model,
        phone_manufacturer,
        measurements_label,
        hrv_label,
        source_labels,
        param_labels,
        first_measurment_date.isoformat(timespec="seconds") if first_measurment_date else '',
        last_measurement_date.isoformat(timespec="seconds") if last_measurement_date else ''
    ]

    output_file.write(f"{'\t'.join(line_list)}\n")

output_file.close()
