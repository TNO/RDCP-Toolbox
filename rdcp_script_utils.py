import json
import os
import re

_ROOT = os.path.dirname(os.path.abspath(__file__))

def _root_path(filename):
    return os.path.join(_ROOT, filename)

def get_base_url():

    base_url = None

    try:
        with open(_root_path('base-url.config'), 'r') as file:
            base_url_config = json.loads(file.read().strip())
            base_url = base_url_config['environments'][base_url_config['active']]

    except FileNotFoundError:
        print("ERROR: Base URL configuration file not found.")

    return base_url


def get_api_token():

    api_token = None

    try:
        with open(_root_path('api-token.config'), 'r') as file:
            api_token = file.read().strip()
    except FileNotFoundError:
        print("ERROR: API token configuration file not found.")

    return api_token

def id_input(id_type, confirmation_needed = False):

    alias = None
    result_id = None

    id_types = ["study", "participant"]

    if id_type not in id_types:
        return None

    try:
        with open(_root_path('id-dictionary.json'), 'r') as file:

            file_content = file.read().strip()

            if not file_content:
                raise ValueError

            id_dict = json.loads(file_content)

    except (FileNotFoundError, ValueError):
        id_dict = {id_type: {} for id_type in id_types}

    if id_dict[id_type]:

        id_alias_input = input(f"Please enter the {id_type} ID or alias: ").strip().lower()

        if id_alias_input:

            hex_pattern = re.compile(r'^[0-9a-z]{24}$')

            if hex_pattern.match(id_alias_input):
                result_id = id_alias_input
            else:

                alias = id_alias_input

                if alias in id_dict[id_type]:
                    result_id = id_dict[id_type][alias]
                else:
                    result_id = input(f"{id_type.capitalize()} alias not found in ID Dictionary, please enter the {id_type} ID: ").strip().lower()
    else:
        result_id = input(f"No {id_type} aliases in ID Dictionary yet, please enter the {id_type} ID: ").strip().lower()

    if not alias:
        alias = input(f"Please enter an alias for the given {id_type} ID if you want to save it in the ID Dictionary: ").strip().lower()

    if alias and result_id:
        id_dict[id_type][alias] = result_id

    with open(_root_path('id-dictionary.json'), 'w') as file:
        json.dump(id_dict, file, indent=4)

    if confirmation_needed:
        confirmation = input(f"Are you sure you want to perform this action for {alias}? (y/N) ").strip().lower()

        if confirmation != "y":
            result_id = None

    return result_id
