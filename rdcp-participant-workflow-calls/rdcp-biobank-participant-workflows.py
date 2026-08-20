import rdcp_utils
import rdcp_script_utils
import json

study_id = '69e778399221700014899c79'
# study_id = rdcp_script_utils.id_input('study')

workflow_start_date = '2026-08-067T07:00:00'
workflow_end_date = "2030-07-27T07:00:00.000Z"

q_start = { "id": "6a16a60b6e4412760076e8d7", "eventDuration": 43200 }
q_end = { "id": "69eb1fae0af5cfcf05575645", "eventDuration": 43200, "delay": 2 }

followup_questionnaires = [
    { "id": "6a16a62b282e2feb359962c4", "eventDuration": 1440, "delay": 0.25 },
    { "id": "6a16a6586e4412760076e8ea", "eventDuration": 1440, "delay": 0.5 },
    { "id": "6a16a68f282e2feb359962cb", "eventDuration": 1440, "delay": 0.75 },
    { "id": "6a16a6c36e4412760076e8f0", "eventDuration": 1440, "delay": 1 },
    { "id": "6a16a6ec282e2feb359962d1", "eventDuration": 1440, "delay": 1.5 },
    { "id": "6a16a70c6e4412760076e8f6", "eventDuration": 1440, "delay": 2 },
    { "id": "6a16a742282e2feb359962d7", "eventDuration": 1440, "delay": 2.5 },
    { "id": "6a16a7626e4412760076e8fd", "eventDuration": 1440, "delay": 3 },
    { "id": "6a16a780282e2feb359962dd", "eventDuration": 1440, "delay": 3.5 },
    { "id": "6a16a7c16e4412760076e903", "eventDuration": 1440, "delay": 4 },
]

# participant_ids = ['6a6723e0a01e869849347c1f', '6a6723e5e1187ea5ba608db0', '6a6723e8a01e869849347c20', '6a6723ece1187ea5ba608db1', '6a6723f2a01e869849347c21', '6a6723f4e1187ea5ba608db2', '6a6723faa01e869849347c22', '6a32c9f441ee5fcafffbf392', '6a6723fee1187ea5ba608db3', '6a672403a01e869849347c23', '6a672405e1187ea5ba608db4', '6a672408a01e869849347c24', '6a67240de1187ea5ba608db5', '6a672412a01e869849347c25', '6a672418e1187ea5ba608db6', '6a67241da01e869849347c26']

participant_id = rdcp_script_utils.id_input('participant')
participant_ids = [participant_id]

def make_start_schedule(participant_id, q, workflow_start_date, study_id):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": True,
        "eventDuration": q['eventDuration'],
        "reminders": [],
        "startOn": {
            "event": "StartDate",
            "startDatetime": f"{workflow_start_date}.000Z"
        },
        "timezone": "Europe/Amsterdam",
        "tenantName": "tno",
        "seriesStartDatetime": f"{workflow_start_date}.000Z",
        "seriesEndDatetime": workflow_end_date,
        "action": {
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": q['id']
            },
            "scheduleAction": "CreateExperimentTask",
            "expireAction": "ExpireExperimentTask",
            "remindAction": "CheckIfExperimentTaskIsToBeReminded"
        },
        "notification": {
            "channels": []
        }
    }

def make_end_schedule(participant_id, q_start, q_end, workflow_start_date, study_id):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": False,
        "eventDuration": q_end['eventDuration'],
        "reminders": [],
        "startOn": {
            "event": "ExperimentCompleted",
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": q_start['id'],
                "conditionScript": "function evaluate(user, results) {\n  return true\n}",
                "delay": {
                    "delayDuration": q_end['delay'],
                    "durationUnit": "hour"
                }
            }
        },
        "timezone": "Europe/Amsterdam",
        "tenantName": "tno",
        "seriesStartDatetime": f"{workflow_start_date}.000Z",
        "seriesEndDatetime": workflow_end_date,
        "action": {
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": q_end['id']
            },
            "scheduleAction": "CreateExperimentTask",
            "expireAction": "ExpireExperimentTask",
            "remindAction": "CheckIfExperimentTaskIsToBeReminded"
        },
        "notification": {
            "channels": []
        }
    }

def make_followup_schedule(participant_id, q_start, q_followup, workflow_start_date, study_id):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": False,
        "eventDuration": q_followup['eventDuration'],
        "reminders": [{"timeOffset": 3, "channels": ["push"]}],
        "startOn": {
            "event": "ExperimentCompleted",
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": q_start['id'],
                "conditionScript": "function evaluate(user, results) {\n  return true\n}",
                "delay": {
                    "delayDuration": q_followup['delay'],
                    "durationUnit": "hour"
                }
            }
        },
        "timezone": "Europe/Amsterdam",
        "tenantName": "tno",
        "seriesStartDatetime": f"{workflow_start_date}.000Z",
        "seriesEndDatetime": workflow_end_date,
        "action": {
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": q_followup['id']
            },
            "scheduleAction": "CreateExperimentTask",
            "expireAction": "ExpireExperimentTask",
            "remindAction": "CheckIfExperimentTaskIsToBeReminded"
        },
        "notification": {
            "channels": ["push"]
        }
    }

for participant_id in participant_ids:

    schedules = [make_start_schedule(participant_id, q_start, workflow_start_date, study_id)]
    schedules.append(make_end_schedule(participant_id, q_start, q_end, workflow_start_date, study_id))

    for q in followup_questionnaires:
        schedules.append(make_followup_schedule(participant_id, q_start, q, workflow_start_date, study_id))

    # response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{participant_id}", None, { "schedules": [] } )
    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(),"PATCH", f"/user/{participant_id}", None, { "schedules": schedules } )
    # response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", f"/patient/{participant_id}" )
    # print(json.dumps(response['schedules'], indent=4))

