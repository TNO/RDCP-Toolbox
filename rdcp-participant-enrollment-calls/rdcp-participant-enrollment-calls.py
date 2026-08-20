# RDCP Toolbox - Participant enrollment calls
# This script enrolls participants from a TSV file.
import rdcp_utils
import rdcp_script_utils

study_id = '6a5505f91861960014e88fc1'
project_slug = 'verzadigingsonderzoek'

existing_participant_email_map = {}
participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url() )

for participant in participants:
    existing_participant_email_map[participant['email'].lower()] = participant['id']

participant_ids = []

with open('input/verzadigingsonderzoek-enrollment.tsv', "r") as workflow_file:

    for i, line in enumerate(workflow_file):

        split = line.strip().split("\t")

        if len(split) == 2:

            email = split[0].strip().lower()

            if email not in existing_participant_email_map:

                name = split[1].strip()

                user = {
                    "email": email,
                    "name": name,
                    "organizationName": "tno",
                    "projectSlug": project_slug,
                    "agreements": []
                }

                response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),"POST", "/enroll", None, user)

                if response and '_id' in response:
                    participant_ids.append(response['_id'])

            else:
                print(f"Participant '{email}' already exists in study {study_id}")

print(f"{len(participant_ids)} participants to activate:")
print(participant_ids)
