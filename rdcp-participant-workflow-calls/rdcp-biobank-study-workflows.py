import rdcp_utils
import rdcp_script_utils
import json

study_id = '69e778399221700014899c79'
workflow_date = '2026-04-24T07:00:00'

schedules = {
    "schedules": [
        {
            "projectId": study_id,
            "active": True,
            "eventDuration": 4320,
            "reminders": [],
            "startOn": {
                "event": "StartDate",
                "startDatetime": f"{workflow_date}.000Z"
            },
            "timezone": "Europe/Amsterdam",
            "tenantName": "tno",
            "seriesStartDatetime": f"{workflow_date}.000Z",
            "seriesEndDatetime": "2030-04-21T08:00:00.000Z",
            "action": {
                "configuration": {
                    "experimentType": "questionnaire",
                    "featureId": "69eb1fad0af5cfcf05575621"
                },
                "scheduleAction": "CreateExperimentTask",
                "expireAction": "ExpireExperimentTask",
                "remindAction": "CheckIfExperimentTaskIsToBeReminded"
            },
            "notification": {
                "channels": [
                    "push"
                ]
            }
        },
        {
            "projectId": study_id,
            "active": False,
            "eventDuration": 1080,
            "reminders": [
                {
                    "timeOffset": 3,
                    "channels": [
                        "push"
                    ]
                },
                {
                    "timeOffset": 6,
                    "channels": [
                        "push"
                    ]
                }
            ],
            "startOn": {
                "event": "ExperimentCompleted",
                "configuration": {
                    "experimentType": "questionnaire",
                    "featureId": "69eb1fad0af5cfcf05575621",
                    "conditionScript": "function evaluate(user, results) {\n  return true\n}",
                    "delay": {
                        "delayDuration": 0.25,
                        "durationUnit": "hour"
                    }
                }
            },
            "timezone": "Europe/Amsterdam",
            "tenantName": "tno",
            "seriesStartDatetime": f"{workflow_date}.000Z",
            "seriesEndDatetime": "2030-04-21T08:00:00.000Z",
            "action": {
                "configuration": {
                    "experimentType": "questionnaire",
                    "featureId": "69eb1fac35e9fe33c697ee9b"
                },
                "scheduleAction": "CreateExperimentTask",
                "expireAction": "ExpireExperimentTask",
                "remindAction": "CheckIfExperimentTaskIsToBeReminded"
            },
            "notification": {
                "channels": [
                    "push"
                ]
            }
        }
    ]
}

response = rdcp_utils.api_call( rdcp_script_utils.get_api_token(), rdcp_script_utils.get_base_url(), "PATCH", f"/study/{study_id}", None, schedules )
print(json.dumps(response, indent=4))
