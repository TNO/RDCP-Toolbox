import rdcp_utils
import rdcp_script_utils
import json

participants = rdcp_utils.get_all_participants(rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url())

participant_ids = []

for participant in participants:

    if participant['firstname'].endswith('045'):
        print( participant['email'] )
        print( json.dumps(participant, indent=4) )
        # participant_ids.append(participant['id'])

    # if 'ferry' in participant['firstname'].lower() and 'jagers' in participant['lastname'].lower():
    #     print( participant['email'] )
    #     print( json.dumps(participant, indent=4) )
    #     participant_ids.append(participant['id'])

# print('["'+'", "'.join(participant_ids)+'"]')
