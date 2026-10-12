import rdcp_utils
import rdcp_script_utils
import json

study_id = '6ab97a197ab7660014bc1480'

participant_ids = []

workflow_start_date = '2026-10-01T04:00:00.000Z'
workflow_end_date = '2030-10-01T04:00:00.000Z'

start_questionnaires = [
    { "id": "6ab98305fe2f228f45249c06", "label": "Thuistest vezelstudie 1/4", "eventDuration": 20160 },
    { "id": "6ab983041f8e702dc189f0cf", "label": "Thuistest vezelstudie 2/4", "eventDuration": 20160, "delayDays": 10 },
    { "id": "6ab98304fe2f228f45249bc6", "label": "Thuistest vezelstudie 3/4", "eventDuration": 20160, "delayDays": 10 },
    { "id": "6ab98305fe2f228f45249beb", "label": "Thuistest vezelstudie 4/4", "eventDuration": 20160, "delayDays": 10 }
]

followup_questionnaires = [
    { "eventDuration": 5760, "delay": 0.1 },
    { "eventDuration": 1440, "delay": 0.25 },
    { "eventDuration": 1440, "delay": 0.5  },
    { "eventDuration": 1440, "delay": 0.75 },
    { "eventDuration": 1440, "delay": 1    },
    { "eventDuration": 1440, "delay": 1.5  },
    { "eventDuration": 1440, "delay": 2    },
    { "eventDuration": 1440, "delay": 2.5  },
    { "eventDuration": 1440, "delay": 3    },
    { "eventDuration": 1440, "delay": 3.5  },
    { "eventDuration": 1440, "delay": 4    },
]

questionnaire_dict = {}

response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "GET", "/questionnaire", { "order": "desc", "studies": study_id, "showAllPreviousVersions": True } )

if not response or not response['items']:
    print("ERROR: GET questionnaire call failed")
    exit()

for item in response['items']:
    questionnaire_dict[item['title']['nl_NL']] = item['_id']

def make_first_start_schedule(participant_id, sq):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": True,
        "eventDuration": sq['eventDuration'],
        "reminders": [],
        "startOn": {
            "event": "StartDate",
            "startDatetime": f"{workflow_start_date}"
        },
        "timezone": "Europe/Amsterdam",
        "tenantName": "tno",
        "seriesStartDatetime": f"{workflow_start_date}",
        "seriesEndDatetime": f"{workflow_end_date}",
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

def make_start_schedule(participant_id, sq, psq ):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": False,
        "eventDuration": sq['eventDuration'],
        "reminders": [],
        "startOn": {
            "event": "ExperimentCompleted",
            "configuration": {
                "experimentType": "questionnaire",
                "featureId": psq['id'],
                "conditionScript": "function evaluate(user, results) {\n  return true\n}",
                "delay": {
                    "delayDuration": sq['delayDays'],
                    "durationUnit": "day",
                    "hour": 4,
                    "minute": 0
                }
            }
        },
        "timezone": "Europe/Amsterdam",
        "tenantName": "tno",
        "seriesStartDatetime": f"{workflow_start_date}",
        "seriesEndDatetime": f"{workflow_end_date}",
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

def make_followup_schedule(participant_id, sq, fq, set_notifications):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": False,
        "eventDuration": fq['eventDuration'],
        "reminders": [{"timeOffset": 3, "channels": ["push"]}] if set_notifications else [],
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
        "seriesStartDatetime": f"{workflow_start_date}",
        "seriesEndDatetime": f"{workflow_end_date}",
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
            "channels": ["push"] if set_notifications else []
        }
    }

def make_wearable_workflow(participant_id):
    return {
        "projectId": study_id,
        "userId": participant_id,
        "active": True,
        "eventDuration": 40320,
        "reminders": [],
        "startOn": {
            "event": "StartDate",
            "startDatetime": f"{workflow_start_date}"
        },
        "timezone": "Europe/Amsterdam",
        "tenantName": "tno",
        "seriesStartDatetime": f"{workflow_start_date}",
        "seriesEndDatetime": f"{workflow_end_date}",
        "action": {
            "configuration": {
                "experimentType": "multiMetric",
                "name": "Smartwatch koppeling",
                "description": "Smartwatch koppeling",
                "duration": 70,
                "historicDataDuration": 0,
                "healthMetrics": [
                    "HeartRate",
                    "HeartRateVariability",
                    "HeartRateResting",
                    "Sleep",
                    "Steps"
                ],
                "dataSources": [
                    {
                        "name": "byod",
                        "required": True,
                    }
                ]
            },
            "scheduleAction": "CreateExperimentTask",
            "expireAction": "ExpireExperimentTask",
            "remindAction": "CheckIfExperimentTaskIsToBeReminded"
        },
        "notification": {
            "channels": []
        }
    }

for participant_id in participant_ids:

    schedules = []

    for sq in start_questionnaires:

        if start_questionnaires.index(sq) == 0:
            schedules.append(make_first_start_schedule(participant_id, sq))
        else:
            schedules.append(make_start_schedule(participant_id, sq, start_questionnaires[start_questionnaires.index(sq)-1]))

        for fq in followup_questionnaires:

            label = sq['label'].rsplit(' ', 1)[0]

            index = followup_questionnaires.index(fq)

            if index == 0:
                label += ' tijdstip'
            else:
                label += f' opvolging {index}/10'

            fq['id'] = questionnaire_dict[label]

            schedules.append(make_followup_schedule(participant_id, sq, fq, followup_questionnaires.index(fq) != 0))

    schedules.append(make_wearable_workflow(participant_id))

    response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/user/{participant_id}", None, { "schedules": schedules } )
