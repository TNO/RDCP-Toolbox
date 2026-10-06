# RDCP Toolbox - Participant info calls
# This script retrieves participant information using the participant ID.

import rdcp_utils
import rdcp_script_utils
import json
import re

study_id = '6a32724a93932d0014276eca'
participants = rdcp_utils.get_all_participants( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), study_id )

regex = r'^\d\.\d{3}$'

for participant in participants:

    # If the participant firstname matches x.xxx (e.g. 1.078 or 2.054), then rename the participant to match this format
    if participant['firstname'] and not re.match(regex, participant['firstname']):

        firstname = participant['firstname']

        if len(firstname) == 4:
            firstname = f"{firstname[0]}.{firstname[1:]}"

        if ',' in firstname:
            firstname = firstname.replace(',', '.')

        if re.match(regex, firstname):

            patch = {
                "firstname": firstname
            }

            # response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{participant['id']}", None, patch )

            print(f"Renaming participant '{participant['id']}' from {participant['firstname']} to {firstname}")

        else:
            print(f"Could not rename participant '{participant['id']}' from '{participant['firstname']}' to '{firstname}' - does not match regex")
