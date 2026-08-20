# RDCP Toolbox - Participant info calls
# This script retrieves participant information using the participant ID.

import rdcp_utils
import rdcp_script_utils
import json

participant_id = '6a43a53783790b7e29326374'
response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant_id}/experiments/questionnaire", { "user_id": participant_id } )
print(json.dumps(response, indent=2))

# response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant_id}", { "user_id": participant_id } )
#
# schedule_entries = []
#
# if response:
#
#     # print(json.dumps(response, indent=4))
#
#     for item in response['schedules']:
#
#         # print(f"{item['startOn']['startDatetime']}: {item['active']}")
#         schedule_entries.append(f"{item['startOn']['startDatetime']}: {item['active']}")
#
# for item in sorted(schedule_entries):
#     print(item)
