import json
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def api_call(api_token, base_url, method, endpoint, request_params=None, request_data=None):

    if request_params is None:
        request_params = {}
    if request_data is None:
        request_data = {}

    request_headers = {
        'Authority': 'gateway.krane.one',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://gateway.krane.one/api-docs/',
        'Authorization': f'bearer {api_token}'
    }

    try:

        url = f"{base_url}{endpoint}"

        # print(requests_to_curl(method, url, request_headers, request_params, request_data))

        response = requests.request(
            method,
            url,
            headers=request_headers,
            params=request_params,
            json=request_data,
            timeout=(5, 30),
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(f"ERROR: HTTP request failed: {e}")
        return None

    try:
        response_json = response.json()
    except ValueError:
        print("ERROR: Invalid JSON response")
        return None

    return response_json

def get_study_id_by_study_title( api_token, base_url, study_title):

    study_id = None

    response = api_call( api_token, base_url, "GET", "/study", {'order': 'desc'})

    if not response or not isinstance(response, list):
        print("ERROR: Study call failed")
        return None

    study = next((item for item in response if item['title'].lower() == study_title.lower()), None)

    if study:
        study_id = study['_id']
    else:
        print(f"ERROR: Study with title '{study_title}' not found")

    return study_id

def get_participant( api_token, base_url, participant_id ):

    response = api_call( api_token, base_url, "GET", f"/patient/{participant_id}" )

    if not response or not isinstance(response, dict):
        print(f"ERROR: Participant call failed for participant ID '{participant_id}'")
        return None

    if not response['status'] or response['status'] not in ['Active', 'Invited', 'Expired']:
        print(f"WARNING: Unknown participant status: {response['status']}")

    return format_participant_info(response)

def get_all_participants(api_token, base_url, study_id=None, created_after_string=None, created_before_string=None):

    participants = []
    participant_ids = set()
    total_count = None
    page_size = 1000

    while total_count is None or len(participants) < total_count:

        response = api_call(api_token, base_url, "GET", "/organization/patients", {"order": "desc", "skip": len(participants), "limit": page_size})

        if not isinstance(response, dict) or not isinstance(response['items'], list) or not isinstance(response['totalCount'], int):
            return None

        if total_count is None:
            total_count = response['totalCount']

        if not isinstance(total_count, int):
            return None

        page_items = response['items']

        required_fields = {
            "_id", "status", "email", "patientId", "studies", "invitedAt", "createdAt"
        }

        for item in page_items:

            if not isinstance(item, dict) or not required_fields.issubset(item):
                return None
            if item['_id'] in participant_ids:
                return None

            participant_ids.add(item['_id'])

            if item['status'] not in ['Active', 'Invited', 'Expired']:
                print(f"WARNING: Unknown participant status: {item['status']}")

            participants.append(item)

        if len(participants) > total_count:
            return None

    if study_id:

        participants = [
            p for p in participants if study_id in p['studies']
        ]

        if created_after_string or created_before_string:

            timezone_info = ZoneInfo('Europe/Amsterdam')
            current_time = datetime.now(timezone.utc)
            current_time_in_timezone = current_time.astimezone(timezone_info)
            utc_offset = current_time_in_timezone.utcoffset()
            utc_offset_str = f"{utc_offset.total_seconds() / 3600:+03.0f}:{abs(utc_offset.total_seconds() / 60) % 60:02.0f}"

            if created_after_string:
                participants = [p for p in participants if p['createdAt'] >= datetime.fromisoformat(f"{created_after_string}:00{utc_offset_str}")]

            if created_before_string:
                participants = [p for p in participants if p['createdAt'] <= datetime.fromisoformat(f"{created_before_string}:00{utc_offset_str}")]

    return [format_participant_info(p) for p in participants]

def get_all_participants_as_dict(api_token, base_url, study_id=None, created_after_string=None, created_before_string=None):

    participants = get_all_participants(api_token, base_url, study_id, created_after_string, created_before_string)

    if participants is None:
        return None

    return { p['id']: p for p in participants }


def get_all_health_records(api_token, base_url, participant_id, param, start_date=None, end_date=None, page_limit=5000):

    result_records = []
    total_count = None

    request_params = { "user_id": participant_id, "limit": page_limit }

    if start_date:
        request_params['start_date'] = start_date+'T00:00:00Z'
    if end_date:
        request_params['end_date'] = end_date+'T23:59:59Z'

    next_timestamp = None
    current_cursor = request_params['start_date']

    while total_count is None or len(result_records) < total_count:

        if next_timestamp:
            request_params['start_date'] = next_timestamp

        response = api_call(
            api_token,
            base_url,
            "GET",
            f"/health/{param}",
            request_params
        )

        if not isinstance(response, dict) or not isinstance(response['records'], list) or not isinstance(response['metadata'], dict):
            return None

        if total_count is None:
            total_count = response['metadata']['total_count']

        if not isinstance(total_count, int):
            return None

        records = response['records']

        # if len(result_records) + len(records) < total_count and not records:
        #     return None
        # if len(result_records) + len(records) > total_count:
        #     return None

        result_records.extend(records)

        if len(result_records) < total_count:

            next_timestamp = response['metadata']['next_timestamp']

            if not next_timestamp or not isinstance(next_timestamp, str):
                return None

            if next_timestamp == current_cursor:
                return None

            current_cursor = next_timestamp

    return {
        'records': result_records,
        'metadata': { 'count': len(result_records), 'total_count': total_count if total_count is not None else 0 }
    }

def requests_to_curl( method, url, headers=None, params=None, data=None ):

    curl_command = f'curl -X {method} "{url}"'

    if headers:
        for key, value in headers.items():
            curl_command += f' -H "{key}: {value}"'

    if params:
        param_str = '&'.join([f"{key}={value}" for key, value in params.items()])
        curl_command = curl_command.replace(f'"{url}"', f'"{url}?{param_str}"')

    if data:
        if isinstance(data, dict):
            data = json.dumps(data)
        curl_command += f' -d {json.dumps(data)}'

    return curl_command

def has_admin_rights( user ):
    return bool(user) and "https://krane.one/roles" in user and 'OrganizationAdmin' in user['https://krane.one/roles']

def is_participant( user ):
    return bool(user) and "https://krane.one/roles" in user and 'Patient' in user['https://krane.one/roles']

def adjust_timestamp(timestamp, timezone_name, return_as_string=True):

    if not timestamp or not isinstance(timestamp, str):
        print("ERROR: Invalid timestamp provided.")
        return None

    if not timezone_name or not isinstance(timezone_name, str):
        print("ERROR: Invalid timezone name provided.")
        return None

    normalized_timestamp = timestamp.replace("Z", "+00:00")

    try:
        timezone_info = ZoneInfo(timezone_name)
        parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    except (ZoneInfoNotFoundError, ValueError) as error:
        print(f"ERROR: Invalid timestamp {timestamp!r} or timezone {timezone_name!r}")
        return None

    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)

    adjusted_timestamp = parsed_timestamp.astimezone(timezone_info)

    if return_as_string:
        timespec = "milliseconds" if "." in timestamp else "seconds"
        return adjusted_timestamp.isoformat(timespec=timespec)
    else:
        return adjusted_timestamp

def adjust_experiment_timestamp(timestamp, experiment, return_as_string=True):

    device_metadata = experiment['deviceMetadata'] if 'deviceMetadata' in experiment else None

    if device_metadata and isinstance(device_metadata, dict) and device_metadata['timezoneName'] and isinstance(device_metadata['timezoneName'], str):
        timezone_name = device_metadata['timezoneName']
    else:
        print(f"WARNING: No device metadata found for experiment '{experiment.get('_id', 'unknown')}', defaulting to timezone 'Europe/Amsterdam'.")
        timezone_name = 'Europe/Amsterdam'

    return adjust_timestamp(timestamp, timezone_name, return_as_string=return_as_string)

def format_participant_info(participant):

    def format_participant_timestamp(value):

        adjusted = adjust_timestamp(value, 'Europe/Amsterdam')

        if adjusted is None:
            return None

        return datetime.fromisoformat(adjusted).isoformat(timespec="minutes")

    return {
        "id": participant['_id'],
        "firstname": participant.get('firstname', None),
        "lastname": participant.get('lastname', None),
        "email": participant['email'],
        "patientId": participant['patientId'],
        "customId": participant.get('customId', None),
        "studies": participant['studies'],
        "invitedAt": format_participant_timestamp(participant['invitedAt']),
        "createdAt": format_participant_timestamp(participant['createdAt']),
        "active": participant['status'] == 'Active',
        "consentCount": len(participant['consents']) if 'consents' in participant else 0
    }
