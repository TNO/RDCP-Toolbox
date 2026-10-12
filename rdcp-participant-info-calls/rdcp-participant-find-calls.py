import rdcp_utils
import rdcp_script_utils
import json

participants = rdcp_utils.get_all_participants(rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url())

participant_ids = []

for participant in participants:

    if participant['firstname'].endswith('086'):
        print( f"{participant['email']} -> {participant['id']}" )
        # print( json.dumps(participant, indent=4) )
