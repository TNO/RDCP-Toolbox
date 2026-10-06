import rdcp_utils
import rdcp_script_utils

study_id = '6a5505f91861960014e88fc1'

participant_ids = ['6ab22968bd77d42c2207db18']
workflow_month_day = '09-22' ## MM-dd

workflow_start_date = f'2026-{workflow_month_day}T06:00:00'
workflow_end_date = f'2030-{workflow_month_day}T06:00:00.000Z'

start_questionnaires = [
    { "id": "6a6c850d6de19ed6f0863095", "label": "Ontbijt A",  "eventDuration": 86400 },
    { "id": "6a6c852ddf181c046b625f66", "label": "Ontbijt B",  "eventDuration": 86400 },
    { "id": "6a6c85416de19ed6f08630a8", "label": "Ontbijt C",  "eventDuration": 86400 },
    { "id": "6a6c8554df181c046b625f7f", "label": "Ontbijt D1", "eventDuration": 86400 },
    { "id": "6a6c85836de19ed6f08630c3", "label": "Ontbijt D2", "eventDuration": 86400 }
]

followup_questionnaires = [
    { "eventDuration": 10, "delay": 0.01 },
    { "eventDuration": 15, "delay": 0.25 },
    { "eventDuration": 15, "delay": 0.5  },
    { "eventDuration": 15, "delay": 0.75 },
    { "eventDuration": 30, "delay": 1    },
    { "eventDuration": 30, "delay": 1.5  },
    { "eventDuration": 30, "delay": 2    },
    { "eventDuration": 30, "delay": 2.5  },
    { "eventDuration": 30, "delay": 3    },
    { "eventDuration": 30, "delay": 3.5  },
    { "eventDuration": 30, "delay": 4    },
]

questionnaire_dict = {}

response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", "/questionnaire", { "order": "desc", "studies": study_id, "showAllPreviousVersions": True } )

if not response or not response['items']:
    print("ERROR: GET questionnaire call failed")
    exit()

for item in response['items']:
    questionnaire_dict[item['title']['nl_NL']] = item['_id']

def make_start_schedule(participant_id, sq, workflow_start_date, study_id):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": True,
        "eventDuration": sq['eventDuration'],
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
                "featureId": sq['id']
            },
            "scheduleAction": "CreateExperimentTask",
            "expireAction": "ExpireExperimentTask",
            "remindAction": "CheckIfExperimentTaskIsToBeReminded"
        },
        "notification": {
            "channels": []
        }
    }

def make_followup_schedule(participant_id, sq, fq, workflow_start_date, study_id):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": False,
        "eventDuration": fq['eventDuration'],
        "reminders": [{"timeOffset": 3, "channels": ["push"]}],
        "startOn": {
            "event": "ExperimentCompleted",
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": sq['id'],
                "conditionScript": "function evaluate(user, results) {\n  return true\n}",
                "delay": {
                    "delayDuration": fq['delay'],
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
                "featureId": fq['id']
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

    schedules = []

    for sq in start_questionnaires:

        workflow_start_date_in_list = workflow_start_date.replace("00:00", f"0{(start_questionnaires.index(sq)+1)}:00")

        schedules.append(make_start_schedule(participant_id, sq, workflow_start_date_in_list, study_id))

        for fq in followup_questionnaires:

            label = sq['label']
            index = followup_questionnaires.index(fq)

            if index == 0:
                label += ' beoordeling'
            else:
                label += f' opvolging {index}/10'

            fq['id'] = questionnaire_dict[label]

            schedules.append(make_followup_schedule(participant_id, sq, fq, workflow_start_date, study_id))

    # response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{participant_id}", None, { "schedules": [] } )
    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{participant_id}", None, { "schedules": schedules } )
