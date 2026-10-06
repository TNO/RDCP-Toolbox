# RDCP Toolbox - Participant enrollment calls
# This script enrolls participants from a TSV file.
import json

import rdcp_utils
import rdcp_script_utils

study_id = '6ab97a197ab7660014bc1480'
project_slug = 'gut-health-vezelstudie'

participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url() )
existing_participant_email_dict = { p['email'].lower(): p['id'] for p in participants }

participant_ids = []

with open('input/gut-health-vezelstudie-enrollment.tsv', "r") as workflow_file:

    for i, line in enumerate(workflow_file):

        split = line.strip().split("\t")

        if len(split) == 2:

            email = split[0].strip().lower()

            if email not in existing_participant_email_dict:

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

                participant = next((p for p in participants if p['id'] == existing_participant_email_dict[email]), None)

                if study_id not in participant.get('studies', []):
                    print(f"Participant '{email}' already exists in other study")
                else:
                    print(f"Participant '{email}' already exists in this study")



print(f"{len(participant_ids)} participants to activate:")
print(participant_ids)
