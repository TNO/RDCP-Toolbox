from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import requests
import json

def api_call( api_token, base_url, method, endpoint, request_params=None, request_data=None ):

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

        response = requests.request(method, url, headers=request_headers, params=request_params, json=request_data)
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

    if not response:
        print("ERROR: Study call failed")
        return None

    study = next((item for item in response if item["title"].lower() == study_title.lower()), None )

    if study:
        study_id = study['_id']
    else:
        print(f"ERROR: Study with title '{study_title}' not found")

    return study_id

def get_participant( api_token, base_url, participant_id ):

    response = api_call( api_token, base_url, "GET", f"/patient/{participant_id}" )

    if not response:
        print(f"ERROR: Participant call failed for participant ID '{participant_id}'")
        return None

    if response['status'] not in ['Active', 'Invited', 'Expired']:
        print(f"WARNING: Unknown participant status: {response['status']}")

    return format_participant_info(response)

def get_all_participants( api_token, base_url, study_id=None, created_after_string=None, created_before_string=None ):

    participants = []
    total_count = 1

    while len(participants) < total_count:

        try:
            response = api_call( api_token, base_url, "GET", "/organization/patients", { "order": "desc", "skip": len(participants), "limit": 1000 } )

        except requests.RequestException as e:
            print(f"ERROR: {e}")

        if not response or not response['items']:
            return []

        total_count = response['totalCount']

        for item in response['items']:

            if item['status'] not in ['Active', 'Invited', 'Expired']:
                print(f"WARNING: Unknown participant status: {item['status']}")

            participants.append(format_participant_info(item))

    if study_id:
        participants = [p for p in participants if study_id in p['studies']]

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

    for participant in participants:
        participant['createdAt'] = participant['createdAt'].isoformat(timespec="minutes")
        participant['invitedAt'] = participant['invitedAt'].isoformat(timespec="minutes")

    return participants

def get_all_participants_as_dict( api_token, base_url, study_id=None, created_after_string=None, created_before_string=None ):

    participants = get_all_participants( api_token, base_url, study_id, created_after_string, created_before_string )

    return { p['id']: p for p in participants }

def get_all_health_records( api_token, base_url, participant_id, param, start_date = None, end_date = None, page_limit= 10000 ):

    response_records = []
    total_count = 1
    metadata = None

    request_params = { "user_id": participant_id, "limit": page_limit }

    if start_date:
        request_params['start_date'] = start_date
    if end_date:
        request_params['end_date'] = end_date

    while len(response_records) < total_count:

        if len(response_records) > 0:
            request_params['skip'] = len(response_records)

        response = api_call(
            api_token,
            base_url,
            "GET",
            f"/health/{param}",
            request_params
        )

        if not response:
            return None

        records = response['records']
        page_metadata = response['metadata']
        metadata = page_metadata
        total_count = page_metadata['total_count']

        if len(records) == 0:
            break

        response_records.extend(records)

        print(f"  - Calling API for '{param}' records...{len(response_records)}/{total_count} records fetched so far")

    if metadata is None:
        metadata = { 'count': 0, 'total_count': 0 }

    metadata['count'] = len(response_records)

    return {
        'records': response_records,
        'metadata': metadata
    }

def requests_to_curl( method, url, headers=None, params=None, data=None ):
    # Start building the curl command
    curl_command = f'curl -X {method} "{url}"'

    # Add headers to curl command
    if headers:
        for key, value in headers.items():
            curl_command += f' -H "{key}: {value}"'

    # Add URL parameters if present
    if params:
        param_str = '&'.join([f"{key}={value}" for key, value in params.items()])
        # If params are present, append them to the URL
        curl_command = curl_command.replace(f'"{url}"', f'"{url}?{param_str}"')

    # Add data (body) if present
    if data:
        if isinstance(data, dict):
            data = json.dumps(data)
        curl_command += f' -d {json.dumps(data)}'

    return curl_command

def has_admin_rights( user ):
    return 'OrganizationAdmin' in user['https://krane.one/roles']

def is_participant( user ):
    return True

def adjust_timestamp( timestamp, timezone_name, return_as_string=True ):

    if not isinstance(timestamp, str):
        print(f"WARNING: Invalid timestamp format: {timestamp}, returning original timestamp.")
        return timestamp

    normalized_timestamp = timestamp.replace("Z", "+00:00")

    try:
        timezone_info = ZoneInfo(timezone_name)
        parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    except (ZoneInfoNotFoundError, ValueError):
        print(f"WARNING: Invalid timestamp '{timestamp}' or timezone '{timezone_name}', returning original timestamp.")
        return timestamp

    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)

    adjusted_timestamp = parsed_timestamp.astimezone(timezone_info)

    if return_as_string == True:

        if "." in timestamp:
            adjusted_timestamp =  adjusted_timestamp.isoformat(timespec="milliseconds")
        else:
            adjusted_timestamp =  adjusted_timestamp.isoformat(timespec="seconds")

    return adjusted_timestamp

def format_participant_info(participant):
    return {
        "id": participant['_id'],
        "firstname": participant.get('firstname', None),
        "lastname": participant.get('lastname', None),
        "email": participant['email'],
        "patientId": participant['patientId'],
        "customId": participant.get('customId', None),
        "studies": participant['studies'],
        "invitedAt": adjust_timestamp(participant['invitedAt'], 'Europe/Amsterdam', False),
        "createdAt": adjust_timestamp(participant['createdAt'], 'Europe/Amsterdam', False),
        "active": participant['status'] == 'Active',
        "consentCount": len(participant['consents']) if 'consents' in participant else 0
    }
