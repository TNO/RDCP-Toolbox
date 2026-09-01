# RDCP Toolbox - Study info calls
# This script retrieves study information using the study ID.

import rdcp_utils
import rdcp_script_utils
import json

study_id = '67f3e3abfdf52f00133c3240'
# users_created_after = '2026-03-05T09:00'
users_created_after = None

registered_users = 0
installed_users = 0
active_users = 0
experiment_completed_users = 0

excluded_reasons = {}

participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), study_id, users_created_after )

for participant in participants:

    if participant['email'].endswith('@tno.nl') or participant['email'].endswith('@orikami.nl'):

        if participant['firstname'] in ['Karleen', 'Kristel', 'Andres', 'Luna', 'Nina', 'Ferry']:
            continue
        else:
            print(json.dumps(participant))

    if participant['active']:

        if participant['consentCount'] > 0:

            registered_users += 1
            installed_users += 1
            active_users += 1

            response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant['id']}/experiments/questionnaire", { "user_id": participant['id'] } )

            if response['totalCount'] > 0:

                answers_in_questionnaire = response['items'][0]['result']['answers']
                answers_in_questionnaire_count = len(answers_in_questionnaire)

                experiment_completed_users += 1

        else:
            installed_users += 1
            registered_users += 1
    else:
        registered_users += 1

print(f"Geregistreerd: {registered_users}")
print(f"Account geactiveerd: {installed_users}")
print(f"App geinstalleerd en ingelogd: {active_users}")
print(f"Tenminste één experiment afgerond: {experiment_completed_users}")
