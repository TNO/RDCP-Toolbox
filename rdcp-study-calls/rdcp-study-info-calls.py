# RDCP Toolbox - Study info calls
# This script retrieves study information using the study ID.

import rdcp_utils
import rdcp_script_utils
import json

study_id = '69899b4df8ef4e00135c46de' #GLP1

registered_users = 0
installed_users = 0
active_users = 0
excluded_users = 0
completed_users = 0

excluded_reasons = {}

participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), study_id, '2026-03-05T09:00' )

for participant in participants:

    if participant['email'].endswith('@tno.nl') or participant['email'].endswith('@orikami.nl'):

        if participant['firstname'] in ['Karleen', 'Kristel', 'Andres', 'Ferry']:
            continue

    if participant['active']:
        if participant['consentCount'] > 0:

            registered_users += 1
            installed_users += 1
            active_users += 1

            response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant['id']}/experiments/questionnaire", { "user_id": participant['id'] } )

            if response['totalCount'] > 0:

                if response['totalCount'] > 1:
                    print(f"Warning: Participant {participant['id']} has {response['totalCount']} questionnaires, picking last created for analysis")

                answers_in_questionnaire = response['items'][0]['result']['answers']
                answers_in_questionnaire_count = len(answers_in_questionnaire)

                if answers_in_questionnaire_count > 20:
                    completed_users += 1
                else:

                    exclude_question_name = answers_in_questionnaire[answers_in_questionnaire_count - 1]['questionName']

                    if exclude_question_name not in excluded_reasons:
                        excluded_reasons[exclude_question_name] = 0

                    excluded_reasons[exclude_question_name] += 1
                    excluded_users += 1

        else:
            installed_users += 1
            registered_users += 1
    else:
        registered_users += 1

print(f"Geregistreerd: {registered_users}")
print(f"Account geactiveerd: {installed_users}")
print(f"App geinstalleerd en ingelogd: {active_users}")
print(f"Vragenlijst geexcludeerd: {excluded_users}")
print(f"Vragenlijst volledig ingevuld: {completed_users}")

for reason, count in excluded_reasons.items():
    print(f"Reden voor uitsluiting '{reason}': {count}")
