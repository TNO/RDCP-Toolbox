# RDCP Toolbox - Questionnaire calls
# Script to get, post, update or delete questionnaires.

import rdcp_utils
import rdcp_script_utils
import os
import json

language = "nl_NL"
endpoint = "/questionnaire"

if not os.path.exists('input'):
    os.makedirs('input')

method = None
study_id = None
questionnaire_id = None
version_group_id = None

request_params = {}
request_data = {}

json_files = []
selected_files = []

option_input = input("Do you want to:\n(1) Get questionnaires for study\n(2) Post a new questionnaire to study\n(3) Update an existing questionnaire\n(4) Delete an existing questionnaire\n(5) Exit\n\nYour input: ").strip().lower()

if option_input == "2" or option_input == "3":

    json_files = [f for f in os.listdir('input') if f.endswith('.json')]

    if len(json_files) == 0:
        print("ERROR: No json files found")
        exit()

if option_input == "4":
    questionnaire_id = input("Enter questionnaire ID: ").strip().lower()
    endpoint += f"/{questionnaire_id}"
    method = "DELETE"
elif option_input == "3":

    study_id = rdcp_script_utils.id_input('study')
    version_group_id = input("Enter version group ID: ").strip().lower()

    if len(json_files) == 1:
        selected_files.append(json_files[0])
    else:

        file_name = input("Enter the filename of the questionnaire to update: ").strip().lower()

        if file_name in {f.lower(): f for f in json_files}:
            selected_files.append(file_name)
        else:
            print("ERROR: File not found")
            exit()

    request_data['projectId'] = study_id
    request_data['versionGroupId'] = version_group_id
    endpoint += "/fhir"
    method = "PUT"
elif option_input == "2":
    study_id = rdcp_script_utils.id_input('study')
    request_data['projectId'] = study_id
    endpoint += "/fhir"
    method = "POST"
    selected_files = json_files
elif option_input == "1":
    study_id = rdcp_script_utils.id_input('study')

    show_all_previous_versions = input("Do you want to show all previous versions of the questionnaires? (y/N)? ")
    show_deleted = input("Do you want to show deleted questionnaires? (y/N)? ")

    request_params['studies'] = study_id
    request_params['showDeleted'] = show_deleted.lower() == 'y'
    request_params['showAllPreviousVersions'] = show_all_previous_versions.lower() == 'y'
    method = "GET"
else:
    if option_input != "5":
        print("ERROR: Wrong input")
    exit()

if option_input == "2" or option_input == "3":
    request_data['language'] = language

if option_input == "2" or option_input == "3":

    for filename in selected_files:

        name = filename.split('.')[0]
        file_path = os.path.join('input', filename)

        with open(file_path, 'r') as json_content:

            request_data['fhir'] = json.load(json_content)
            response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),method, endpoint, request_params, request_data )
            print(response)
else:

    if option_input == "1":

        with open(f"./output/{study_id}-questionnaires-output.tsv", 'w') as json_file:

            questionnaires = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),method, endpoint, request_params )

            # questionnaires = []
            #
            # for questionnaire in rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),method, endpoint, request_params )['items']:
            #
            #     if questionnaire['_id'] in ['69e0f803f47d5c5dd2072615','69a938a183ee83a60635a403']:
            #
            #         for question in questionnaire['questionObjects']:
            #
            #             if isinstance(question, dict):
            #                 for key in ('questionnaireId', 'createdAt', 'updatedAt', '_id'):
            #                     question.pop(key, None)
            #
            #         questionnaires.append(questionnaire)

            json_file.write(json.dumps(questionnaires, indent=4))

    else:
        print(json.dumps(rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), method, endpoint, request_params ), indent=4))
