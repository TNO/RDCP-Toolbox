# RDCP Toolbox - Participant info calls
# This script retrieves participant information using the participant ID.

import rdcp_utils
import rdcp_script_utils
import json

participant_ids = [
    '6a5601810c5fe0562dbac339'
]

for participant_id in participant_ids:

    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant_id}" )

    if response and '+' not in response['email']:

        new_email = f"ferry.jagers+{response['email'].replace('@', '-').replace('.', '-')}@tno.nl"
        # new_email = response['email'].split('@')[0] + '+renametest' + '@' + response['email'].split('@')[1]

        print(new_email)

        patch = {
            "email": new_email
        }

        response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{participant_id}", None, patch )
