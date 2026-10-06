# RDCP Toolbox - Questionnaire responses export
# This script retrieves questionnaire responses for a specified study and outputs them to a TSV file.
import rdcp_utils
import rdcp_script_utils

import os
import json
from datetime import datetime

if not os.path.exists('output'):
    os.makedirs('output')

def adjust_experiment_timestamp(timestamp, experiment, return_as_string=True):

    if 'deviceMetadata' in experiment:
        timezone_name = experiment['deviceMetadata']['timezoneName']
    else:
        print(f"WARNING: No device metadata found for experiment '{experiment['_id']}', defaulting to timezone 'Europe/Amsterdam'.")
        timezone_name = 'Europe/Amsterdam'

    return rdcp_utils.adjust_timestamp(timestamp, timezone_name, return_as_string)

study_id = None
export_with_ids = False
export_submit_timestamp = False
export_email_instead_of_firstname = False
option_input = input("Do you want to:\n(1) Export study questionnaire data to file\n(2) Get first and last experiment datapoint dates for users in study\n(3) Exit\n\nYour input: ").strip().lower()

if option_input in ['1','2']:

    study_id = rdcp_script_utils.id_input('study')

    if option_input == "1":

        export_with_ids_input = input("Do you want to export IDs? (y/N) ").strip().lower()
        export_with_ids = True if export_with_ids_input == 'y' or export_with_ids_input == 'yes' else False

        export_submit_timestamp_input = input("Do you want to export submission timestamps? (y/N) ").strip().lower()
        export_submit_timestamp = True if export_submit_timestamp_input == 'y' or export_submit_timestamp_input == 'yes' else False

        export_email_instead_of_firstname_input = input("Do you want to export email instead of firstname? (y/N) ").strip().lower()
        export_email_instead_of_firstname = True if export_email_instead_of_firstname_input == 'y' or export_email_instead_of_firstname_input == 'yes' else False
else:
    if option_input != "3":
        print("ERROR: Wrong input")
    exit()

participant_dict = rdcp_utils.get_all_participants_as_dict( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), study_id )

questionnaire_title_dict = {}
questionnaire_questions_dict = {}
response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", "/questionnaire", { "order": "desc", "studies": study_id, "showAllPreviousVersions": True } )

if not response or 'items' not in response:
    print("ERROR: GET questionnaire call failed")
    exit()

for item in response['items']:

    questionnaire_id = item['_id']

    if questionnaire_id not in questionnaire_questions_dict:
        questionnaire_questions_dict[questionnaire_id] = {}

    for questionObject in item['questionObjects']:
        questionnaire_questions_dict[questionnaire_id][questionObject['_id']] = { "label": questionObject['question'][next(iter(questionObject['question']))] }

    questionnaire_title_dict[questionnaire_id] = item['title'][next(iter(item['title']))]

if option_input == "1":

    timestamp = datetime.now().strftime("%Y%m%d%H%M")

    with open(f"./output/{timestamp}-{rdcp_script_utils.get_study_name_by_study_id(study_id)}-questionnaires.tsv", 'w') as output_file:

        header_list = [
            "User name",
            "User info",
            "Timestamp",
            "Questionnaire title",
            "Question label",
            "Question answer"
        ]

        output_file.write("\t".join(header_list) + "\n")

        response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/study/{study_id}/experiments", { "order": "desc", "sortBy": "createdAt", "studyId": study_id, "type": "questionnaire", "limit": 999999999999999999 } )

        if response:

            for item in response.get('items', []):

                if 'questionnaireId' not in item['result']:
                    print("Experiment other than questionnaire found, skipping for export...")
                    continue

                else:

                    if item['userId'] not in participant_dict:
                        print(f"WARNING: Participant '{item['userId']}' not found.")
                        continue

                    if item['result']['questionnaireId'] not in questionnaire_questions_dict:
                        print(f"WARNING: Questionnaire '{item['result']['questionnaireId']}' for user '{participant_dict[item['userId']]['email']}' not found, probably removed from study.")
                        continue

                    questionnaire_title = questionnaire_title_dict[item['result']['questionnaireId']]
                    participant_id = participant_dict[item['userId']]['patientId']
                    if export_email_instead_of_firstname:
                        username = participant_dict[item['userId']]['email']
                    else:
                        username = participant_dict[item['userId']]['firstname']

                    for answer in item['result']['answers']:

                        if answer['questionId'] not in questionnaire_questions_dict[item['result']['questionnaireId']]:
                            print(f"WARNING: Question '{answer['questionId']}' for user '{participant_dict[item['userId']]['email']}' not found, probably removed from questionnaire.")
                            continue

                        result_label = questionnaire_questions_dict[item['result']['questionnaireId']][answer['questionId']]['label']

                        if '\n' in result_label:
                            result_label = result_label.replace('\n','')

                        if isinstance(answer['value'], list):
                            value = ', '.join(answer['value'])
                        else:
                            value = str(answer['value'])

                            if '\n' in value:
                                value = value.replace('\n','')

                        timestamp = adjust_experiment_timestamp(answer['timestamp'], item)

                        line_list = [
                            participant_id,
                            f"{username} ({item['userId']})" if export_with_ids else username,
                            timestamp,
                            f"{questionnaire_title} ({item['result']['questionnaireId']})" if export_with_ids and item['result']['questionnaireId'] else questionnaire_title,
                            f"{result_label} ({answer['questionId']})" if export_with_ids and answer['questionId'] else result_label,
                            value
                        ]

                        output_file.write("\t".join(line_list) + "\n")

                    if export_submit_timestamp:

                        question_label = "Questionnaire submission timestamp"
                        timestamp = adjust_experiment_timestamp(item['createdAt'], item)

                        line_list = [
                            participant_id,
                            f"{username} ({item['userId']})" if export_with_ids else username,
                            timestamp,
                            f"{questionnaire_title} ({item['result']['questionnaireId']})" if export_with_ids and item['result']['questionnaireId'] else questionnaire_title,
                            question_label,
                            timestamp
                        ]

                        output_file.write("\t".join(line_list) + "\n")

    output_file.close()

elif option_input == "2":

    monitoring_dict = {}

    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),"GET", f"/study/{study_id}/experiments", { "order": "desc", "sortBy": "createdAt", "studyId": study_id, "type": "questionnaire", "limit": 999999999999999999 } )

    for item in response.get('items', []):

        participant_id = participant_dict[item['userId']]['patientId']
        timestamp = adjust_experiment_timestamp(item['createdAt'], item, False)

        if participant_id not in monitoring_dict:
            monitoring_dict[participant_id] = { "first": timestamp, "last": timestamp }
        else:
            if timestamp < monitoring_dict[participant_id]['first']:
                monitoring_dict[participant_id]['first'] = timestamp

            if timestamp > monitoring_dict[participant_id]['last']:
                monitoring_dict[participant_id]['last'] = timestamp

    # Cast timestamps to string for JSON serialization
    for participant_id in monitoring_dict:
        monitoring_dict[participant_id]['first'] = monitoring_dict[participant_id]['first'].isoformat(timespec="seconds")
        monitoring_dict[participant_id]['last'] = monitoring_dict[participant_id]['last'].isoformat(timespec="seconds")

    print(json.dumps(monitoring_dict, indent=4))
