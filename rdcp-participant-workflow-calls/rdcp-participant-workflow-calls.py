# RDCP Toolbox - Participant Workflow calls
# Script to get, update (overwrite) or delete participant workflows.

import rdcp_utils
import rdcp_script_utils
import os
import json
import datetime
import pytz

now = datetime.datetime.now(datetime.timezone.utc)

if not os.path.exists('input'):
    os.makedirs('input')

option_input = input("Do you want to:\n(1) Get all active participant workflows for study\n(2) Overwrite participant workflows from file to study\n(3) Delete all workflows for participant\n(4) Exit\n\nYour input: ").strip().lower()

study_id = None
participant_id = None

if option_input == "3":
    participant_id = rdcp_script_utils.id_input('participant',True)
elif option_input in ["1","2"]:
    study_id = rdcp_script_utils.id_input('study')
else:
    if option_input != "4":
        print("ERROR: Wrong input")
    exit()

if option_input == "1":

    schedule_map = {}

    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),"GET", f"/user/patients", { "projectId": study_id } )

    print( json.dumps(response, indent=2) )

    if not response:
        print("ERROR: GET patients call failed")
        exit()

    for participant in response['items']:

        if 'schedules' in participant and participant['schedules']:

            active_schedules = []

            for schedule in participant['schedules']:

                if 'active' not in schedule or not schedule['active']:
                    continue

                if 'startOn' not in schedule or 'startDatetime' not in schedule['startOn'] or not schedule['startOn']['startDatetime']:
                    print(f"WARNING: schedule ({schedule['_id']}) without start date found, skipping...")
                    # print(json.dumps(schedule, indent=4))
                    continue

                if 'eventDuration' not in schedule:
                    print(f"WARNING: schedule ({schedule['_id']}) without event duration found, skipping...")
                    # print(json.dumps(schedule, indent=4))
                    continue

                try:
                    startDatetime = datetime.datetime.strptime(schedule['startOn']['startDatetime'], "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    startDatetime = datetime.datetime.strptime(schedule['startOn']['startDatetime'], "%Y-%m-%dT%H:%M:%SZ")

                startDatetime = startDatetime.replace(tzinfo=datetime.timezone.utc)
                endDatetime = startDatetime + datetime.timedelta(minutes=schedule['eventDuration'])

                if endDatetime > now:

                    # Adjust startDatetime and endDatetime to participant timezone if available
                    if 'timezone' in schedule and schedule['timezone']:

                        try:
                            participant_tz = pytz.timezone(schedule['timezone'])
                            startDatetime = startDatetime.astimezone(participant_tz)
                            endDatetime = endDatetime.astimezone(participant_tz)

                        except Exception as e:
                            print(f"WARNING: invalid timezone '{schedule['timezone']}' for schedule ({schedule['_id']}), using UTC timezone...")

                    active_schedules.append({ "startTime": startDatetime.strftime("%Y-%m-%dT%H:%M:%S %Z"), "endTime": endDatetime.strftime("%Y-%m-%dT%H:%M:%S %Z"), "experimentType": schedule['action']['configuration']['experimentType'], "featureId": schedule['action']['configuration']['featureId'] })

            if len(active_schedules) > 0:

                # Sort active schedules by start time
                active_schedules.sort(key=lambda x: x['startTime'])
                schedule_map[participant['_id']] = { "firstname": participant.get('firstname', 'NA'), "lastname": participant.get('lastname', 'NA'), "schedules": active_schedules }

elif option_input in ["2","3"]:

    schedule_map = {}

    if option_input == "2":

        input_folder_path = "input"

        experiment_configuration_map = {}
        participant_id_map = {}
        participant_startdate_map = {}

        response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),"GET", f"/study/{study_id}" )

        if not response:
            print("ERROR: GET study call failed")
            exit()

        for item in response['features']:

            if item['type'] == 'questionnaire':

                experiment_configuration_map[item['biomarkerDescription']] = {
                    'experimentType': item['type'],
                    'featureId': item['featureId']
                }

            elif item['type'] == 'multiMetric':

                experiment_configuration_map[item['configuration']['name']] = {
                    'experimentType': item['type'],
                    'name': item['configuration']['name'],
                    'description': item['configuration']['description'],
                    'duration': item['configuration']['duration'],
                    'historicDataDuration': item['configuration']['historicDataDuration'],
                    'healthMetrics': item['configuration']['healthMetrics'],
                    'dataSources': item['configuration']['dataSources']
                }

        participant_map = {}
        participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url() )

        for participant in participants:

            participant_map[participant['id']] = participant

            if study_id in participant['studies']:

                participant_id_map[f"{participant['email']}".lower()] = participant['id']

                if 'firstname' in participant and 'lastname' in participant:
                    participant_id_map[f"{participant['firstname']} {participant['lastname']}".lower()] = participant['id']
                else:
                    print(f"WARNING: nameless participant found: {participant['email']}")

        workflow_source_json = '''{"userId":null,"projectId":null,"active":true,"eventDuration":null,"reminders":[],"startOn":{"event":"StartDate","startDatetime":null},"timezone":"Europe/Amsterdam","tenantName":"tno","seriesStartDatetime":null,"seriesEndDatetime":null,"action":{"configuration":{"experimentType":null,"featureId":null},"scheduleAction":"CreateExperimentTask","expireAction":"ExpireExperimentTask","remindAction":"CheckIfExperimentTaskIsToBeReminded"},"notification":{}}'''

        for filename in os.listdir(input_folder_path):

            if filename.endswith('.tsv') or filename.endswith('.txt'):

                name = filename.split('.')[0]
                file_path = os.path.join(input_folder_path, filename)

                with open(file_path, "r") as workflow_file:

                    for i, line in enumerate(workflow_file):

                        if i != 0:

                            line = line.strip()
                            split = line.split('\t')

                            if len(split) > 1:

                                name_or_email = split[0].strip().lower()
                                start_date_string = split[1].strip()
                                task_type = split[2].strip()
                                task_title = split[3].strip()
                                task_days_from_start = int(split[4].strip()) if split[4].strip().isdigit() else None
                                task_availability_start_time_string = split[5].strip()
                                task_availability_duration = int(split[6].strip()) if split[6].strip().isdigit() else None
                                task_notification_push = split[7].strip().lower()
                                task_notification_email = split[8].strip().lower()
                                task_reminder_1_offset = int(split[9].strip()) if split[9].strip().isdigit() else None
                                task_reminder_1_push = split[10].strip().lower()
                                task_reminder_1_email = split[11].strip().lower()
                                task_reminder_2_offset = int(split[12].strip()) if split[12].strip().isdigit() else None
                                task_reminder_2_push = split[13].strip().lower()
                                task_reminder_2_email = split[14].strip().lower()
                                task_reminder_3_offset = int(split[15].strip()) if split[15].strip().isdigit() else None
                                task_reminder_3_push = split[16].strip().lower()
                                task_reminder_3_email = split[17].strip().lower()
                                participant_timezone = split[18].strip()

                                if not name_or_email or name_or_email not in participant_id_map:
                                    print(f"ERROR: participant '{name_or_email}' on line {i} not found in the participant map.")
                                    continue

                                if not task_type or task_type not in ['questionnaire', 'multiMetric']:
                                    print(f"ERROR: task type on line {i} not (yet) supported, only 'questionnaire' tasks supported.")
                                    continue

                                if task_title not in experiment_configuration_map:
                                    print(f"ERROR: experiment title '{task_title}' on line {i} not found in the questionnaire map.")
                                    continue

                                if not start_date_string or task_days_from_start is None or not task_availability_start_time_string:
                                    print(f"ERROR: start date and/or days from start and/or start time not set or invalid on line {i}.")
                                    continue

                                if not participant_timezone:
                                    print(f"ERROR: participant timezone not set on line {i}.")
                                    continue

                                participant_id = participant_id_map[name_or_email]

                                if start_date_string.lower() == 'firstlogin':

                                    if participant_id not in participant_startdate_map:
                                        response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),"GET", f"/patient/{participant_id}" )

                                    anonymized_data_usage = next((item for item in response['consents'] if item["policyName"] == "AnonymizedDataUsage"), None)

                                    start_date_string_from_consent = None

                                    if anonymized_data_usage:
                                        start_date_string_from_consent = anonymized_data_usage['createdAt'].split('T')[0]
                                        participant_startdate_map[participant_id] = start_date_string_from_consent

                                    start_date_string = participant_startdate_map[participant_id]

                                if start_date_string is None:
                                    print(f"ERROR: start date could not be determined for line {i}.")
                                    continue

                                try:

                                    date = datetime.datetime.strptime(f"{start_date_string} {task_availability_start_time_string}", "%Y-%m-%d %H:%M")
                                    date = date + datetime.timedelta(days=task_days_from_start)

                                    tz1 = pytz.timezone('UTC')
                                    tz2 = pytz.timezone(participant_timezone)

                                    delta = int((tz1.localize(date).utcoffset() - tz2.localize(date).utcoffset()).total_seconds() / 3600)
                                    date = date + datetime.timedelta(hours=delta)

                                except ValueError:
                                    print(f"ERROR: start date and/or start time and/or timezone are not valid on line {i}.")
                                    continue

                                # if date < now:
                                #     print(f"WARNING: date of workflow #{i} in '{filename}' is in the past.")

                                yn_values = [
                                    task_notification_push, task_notification_email,
                                    task_reminder_1_push, task_reminder_1_email,
                                    task_reminder_2_push, task_reminder_2_email,
                                    task_reminder_3_push, task_reminder_3_email,
                                ]
                                invalid_yn = next((v for v in yn_values if v not in ('', 'y', 'n')), None)
                                if invalid_yn is not None:
                                    print(f"ERROR: invalid Y/N value '{invalid_yn}' on line {i}.")
                                    continue

                                workflow_json = json.loads(workflow_source_json)

                                workflow_json['userId'] = participant_id
                                workflow_json['projectId'] = study_id
                                workflow_json['eventDuration'] = task_availability_duration

                                workflow_json['action']['configuration'] = experiment_configuration_map[task_title]

                                workflow_json['startOn']['startDatetime'] = date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                                workflow_json['seriesStartDatetime'] = date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                                workflow_json['seriesEndDatetime'] = (date + datetime.timedelta(weeks=208)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

                                # Notification section
                                if task_notification_push == 'y' or task_notification_email == 'y':
                                    workflow_json['notification'] = {"channels": []}
                                    for channel, value in {
                                        'push': task_notification_push,
                                        'email': task_notification_email
                                    }.items():
                                        if value == 'y':
                                            workflow_json['notification']['channels'].append(channel)

                                # Reminders section
                                reminders = []
                                for offset, push, email in [
                                    (task_reminder_1_offset, task_reminder_1_push, task_reminder_1_email),
                                    (task_reminder_2_offset, task_reminder_2_push, task_reminder_2_email),
                                    (task_reminder_3_offset, task_reminder_3_push, task_reminder_3_email)
                                ]:
                                    if offset is not None and (push == 'y' or email == 'y'):
                                        reminder = {"timeOffset": offset, "channels": []}
                                        if push == 'y':
                                            reminder['channels'].append('push')
                                        if email == 'y':
                                            reminder['channels'].append('email')
                                        reminders.append(reminder)

                                if reminders:
                                    workflow_json['reminders'] = reminders

                                if participant_id not in schedule_map:
                                    schedule_map[participant_id] = {"schedules":[]}

                                schedule_map[participant_id]['schedules'].append(workflow_json)

    else:
        schedule_map[participant_id] = {"schedules":[]}

    for user_id, schedules in schedule_map.items():
        # print(json.dumps(schedules, indent=4))
        response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{user_id}", None, schedules )
        print(f"{user_id} -> {json.dumps(response)}")

