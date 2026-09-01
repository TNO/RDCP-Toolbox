# RDCP Toolbox - Questionnaire Generator
# Script to read questionnaire definitions from TSV files in the 'input' folder
# and generate corresponding FHIR Questionnaire JSON files in the 'output' folder
# that can be used as input for the questionnaire API calls.

import uuid
import json
import re
import os

language = "nl_NL"
input_folder_path = "input"
# Optional, only needed when you want to manually post the questionnaires
study_id = None

if not os.path.exists('input'):
    os.makedirs('input')

if not os.path.exists('output'):
    os.makedirs('output')

uuid_namespace = uuid.NAMESPACE_DNS

questionnaire_source_json = """{"projectId":"","language":"","fhir":{"resourceType":"Questionnaire","language":"nl_NL","title":"","description":"This questionnaire includes multiple types of questions.","version":"1","status":"draft","publisher":"TNO","meta":{"profile":["http://ehelse.no/fhir/StructureDefinition/sdf-Questionnaire"],"tag":[{"system":"urn:ietf:bcp:47","code":"en-US","display":"English"}],"security":[{"code":"3","display":"Helsehjelp (Full)","system":"urn:oid:2.16.578.1.12.4.1.1.7618"}]},"contact":[{"name":"http://www.tno.nl"}],"subjectType":["Patient"],"extension":[{"url":"http://helsenorge.no/fhir/StructureDefinition/sdf-sidebar","valueCoding":{"system":"http://helsenorge.no/fhir/ValueSet/sdf-sidebar","code":"1"}},{"url":"http://helsenorge.no/fhir/StructureDefinition/sdf-information-message","valueCoding":{"system":"http://helsenorge.no/fhir/ValueSet/sdf-information-message","code":"1"}},{"url":"http://helsenorge.no/fhir/StructureDefintion/sdf-itemControl-visibility","valueCodeableConcept":{"coding":[{"system":"http://helsenorge.no/fhir/CodeSystem/AttachmentRenderOptions","code":"hide-help","display":"Hide help texts"},{"system":"http://helsenorge.no/fhir/CodeSystem/AttachmentRenderOptions","code":"hide-sublabel","display":"Hide sublabel texts"}]}}],"item":[]}}"""
display_source_json = """{"linkId":"","type":"display","text":"","required":false}"""
open_question_source_json = """{"linkId":"","type":"","text":"","required":true}"""
choice_question_source_json = """{"linkId":"","type":"choice","text":"Checkbox Question","required":true,"answerOption":[],"extension":[{"url":"http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl","valueCodeableConcept":{"coding":[{"system":"http://hl7.org/fhir/ValueSet/questionnaire-item-control","code":""}]}}]}"""
choice_question_option_source_json = """{"valueCoding":{"id":"","code":"","system":"","display":""}}"""

extension_sublabel_source_json = """{"url":"http://helsenorge.no/fhir/StructureDefinition/sdf-sublabel","valueMarkdown":""}"""
extension_placeholder_source_json = """{"url":"http://hl7.org/fhir/StructureDefinition/entryFormat","valueString":""}"""
extension_min_integer_source_json = """{"url":"http://hl7.org/fhir/StructureDefinition/minValue","valueInteger":0}"""
extension_max_integer_source_json = """{"url":"http://hl7.org/fhir/StructureDefinition/maxValue","valueInteger":0}"""
extension_rendering_markdown_source_json = """{"url":"http://hl7.org/fhir/StructureDefinition/rendering-markdown","valueMarkdown":""}"""

def get_line_value_for_header( split, headers, target_header ):

    value = None

    headers = [header.lower().replace('(optional)', '').strip() for header in headers]
    target_header = target_header.lower().replace('(optional)', '').strip()

    for i, header_in_headers in enumerate(headers):

        if header_in_headers == target_header and i < len(split) and split[i] != "":
            value = split[i]

    return value

def set_general_properties_for_item(item, item_name):

    item['linkId'] = item_name

    return item

def set_general_properties_for_question(question, item_text, item_required):

    question['text'] = item_text

    # if '**' in item_text:
    #
    #     text_markdown_json = json.loads(extension_rendering_markdown_source_json)
    #     text_markdown_json['valueMarkdown'] = item_text
    #
    #     question['_text'] = { "extension": [text_markdown_json] }

    question['required'] = item_required

    return question

def open_question( item_name, item_type, text, placeholder=None, min=None, max=None, item_required=True ):

    open_question_json = {}

    if item_type in ['string', 'integer', 'date']:

        open_question_json = json.loads( open_question_source_json )
        open_question_json = set_general_properties_for_item( open_question_json, item_name )
        open_question_json = set_general_properties_for_question( open_question_json, text, item_required )

        open_question_json['type'] = item_type

        if min is not None or max is not None or placeholder is not None:

            open_question_json['extension'] = []

            if min is not None:
                min_integer_json = json.loads( extension_min_integer_source_json )
                min_integer_json['valueInteger'] = int(min)
                open_question_json['extension'].append(min_integer_json)

            if max is not None:
                max_integer_json = json.loads( extension_max_integer_source_json )
                max_integer_json['valueInteger'] = int(max)
                open_question_json['extension'].append(max_integer_json)

            # if placeholder is not None:
            #     placeholder_json = json.loads( extension_placeholder_source_json )
            #     placeholder_json['valueString'] = placeholder
            #     open_question_json['extension'].append(placeholder_json)

    else:
        raise Exception("Invalid item type")

    return open_question_json

def choice_question( item_name, item_type, text, item_options, item_option_values, item_required=True ):

    choice_question_json = {}

    if item_type in ['radio-button', 'check-box', 'drop-down', 'slider']:

        choice_question_json = json.loads( choice_question_source_json )
        choice_question_json = set_general_properties_for_item( choice_question_json, item_name )
        choice_question_json = set_general_properties_for_question( choice_question_json, text, item_required )

        extension_index = next((i for i, item in enumerate(choice_question_json['extension']) if item.get("url", "").endswith("fhir/StructureDefinition/questionnaire-itemControl")), -1)
        coding_index = next((i for i, item in enumerate(choice_question_json['extension'][extension_index]['valueCodeableConcept']['coding']) if item.get("url", "").endswith("fhir/ValueSet/questionnaire-item-control")), -1)

        choice_question_json['extension'][extension_index]['valueCodeableConcept']['coding'][coding_index]['code'] = item_type

        option_system_uuid = f"urn:uuid:{uuid.uuid5(uuid_namespace, '_'.join(item_options + item_option_values if item_option_values else item_options))}"

        if item_option_values is None:
            item_option_values = [re.sub(r'[^a-zA-Z0-9_\- ]', '', o.split("(")[0].replace(' ','_')).strip().lower() for o in item_options]

        item_option_values_all_numeric = all(o.isdigit() for o in item_option_values)

        if len(item_option_values) != len(item_options):
            raise Exception(f"Number of option values is not equals to number of options")

        option_index = 0

        for option in item_options:

            choice_question_option_json = json.loads(choice_question_option_source_json)
            choice_question_option_code = item_option_values[option_index]

            choice_question_option_json['valueCoding']['id'] = str(uuid.uuid5(uuid_namespace, str(f"{item_name}_{choice_question_option_code}")))
            choice_question_option_json['valueCoding']['system'] = option_system_uuid
            choice_question_option_json['valueCoding']['code'] = choice_question_option_code
            # choice_question_option_json['valueCoding']['code'] = int(choice_question_option_code) if item_option_values_all_numeric else choice_question_option_code
            choice_question_option_json['valueCoding']['display'] = option if option.strip() != "" else '-'

            choice_question_json['answerOption'].append(choice_question_option_json)
            option_index += 1

    else:
        raise Exception(f"Invalid item type")

    return choice_question_json

if study_id is None:
    print("NOTE: output will be just the FHIR questionnaire object, manual POSTs (via Postman) will required 'projectId' and 'language' properties.")

for filename in os.listdir(input_folder_path):

    if filename.endswith('.tsv'):

        filename_without_extension = filename.split('.')[0]
        file_path = os.path.join(input_folder_path, filename)

        with open(file_path, "r") as questionnaire_file:

            questionnaire_map = {}
            questionnaire_link_ids = []

            for i, line in enumerate(questionnaire_file):

                line = line.strip()
                split = line.split('\t')

                if i == 0:

                    headers = split

                else:

                    questionnaire_name = get_line_value_for_header( split, headers, 'Questionnaire name' )
                    questionnaire_title = get_line_value_for_header( split, headers, 'Questionnaire title' )
                    item_name = get_line_value_for_header( split, headers, 'Item name' )
                    item_text = get_line_value_for_header( split, headers, 'Item text' )
                    item_type = get_line_value_for_header( split, headers, 'Item type' )

                    if questionnaire_name not in questionnaire_map:

                        questionnaire_json = json.loads(questionnaire_source_json)

                        if study_id is not None:
                            questionnaire_json['projectId'] = study_id

                        questionnaire_json['language'] = language

                        questionnaire_json['fhir']['title'] = questionnaire_title
                        # questionnaire_json['fhir']['id'] = str(uuid.uuid5(uuid_namespace, questionnaire_title))
                        questionnaire_json['fhir']['name'] = questionnaire_name
                        questionnaire_map[questionnaire_name] = questionnaire_json

                    if questionnaire_name is None or questionnaire_title is None or item_text is None or item_type is None:
                        print(f"ERROR: Invalid item on line {i+1}")
                        continue

                    item_required = get_line_value_for_header( split, headers, 'Item required' )
                    item_text = item_text.replace("\\n", "\n")

                    question_index = len(questionnaire_map[questionnaire_name]['fhir']['item'])

                    if item_name is None:

                        item_name_index = 0
                        existing_item_names = {q['linkId'] for q in questionnaire_map[questionnaire_name]['fhir']['item']}
                        base_name = re.sub(r'[^a-zA-Z0-9_-]', '', item_text.replace(' ', '_')).strip().lower() or "item"

                        while item_name is None or item_name in existing_item_names:
                            candidate_name = f"{base_name}-{item_name_index+1}" if item_name_index else base_name
                            candidate_uuid = str(uuid.uuid5(uuid_namespace, f"{questionnaire_name}_{candidate_name}"))[:8]
                            item_name = f"{candidate_name}-{candidate_uuid}"
                            item_name_index += 1

                        if item_name_index > 1:
                            print(f"NOTE: duplicate item name generated, adding index to name to ensure uniqueness for line #{i+1}.")

                        # item_uuid = None
                        # item_name_index = 0
                        # existing_item_names = [q['linkId'] for q in questionnaire_map[questionnaire_name]['fhir']['item']]
                        #
                        # while (item_name is None or item_uuid is None) or f"{item_name}-{item_uuid}" in existing_item_names:
                        #
                        #     item_name = f"{re.sub(r'[^a-zA-Z0-9_-]', '', item_text.replace(' ', '_')).strip().lower()}"
                        #
                        #     if item_name_index != 0:
                        #         print(f"NOTE: Duplicate item name generated, adding index to name to ensure uniqueness for line #{i+1}.")
                        #         item_name = f"{item_name}-{item_name_index}"
                        #
                        #     item_uuid = str(uuid.uuid5(uuid_namespace, f"{questionnaire_name}_{item_name}"))[:8]
                        #
                        #     item_name_index += 1
                        #
                        # item_name = f"{item_name}-{item_uuid}"

                    if item_required is None:
                        item_required = True
                    else:
                        item_required = item_required.lower() != 'false'

                    item_json = {}

                    if item_type == 'display':

                        item_json = json.loads(display_source_json)
                        item_json = set_general_properties_for_item( item_json, item_name )
                        item_json['text'] = item_text

                    elif item_type in ['string', 'integer', 'date']:

                        placeholder = get_line_value_for_header( split, headers, 'Item placeholder (optional)' )
                        min = get_line_value_for_header( split, headers, 'Item min (optional)' )
                        max = get_line_value_for_header( split, headers, 'Item max (optional)' )

                        try:
                            item_json = open_question(item_name, item_type, item_text, placeholder, min, max, item_required)
                        except Exception as e:
                            print(f"ERROR: {e} on line #{i+1}.")

                    elif item_type in ['radio-button', 'check-box', 'drop-down', 'slider']:

                        item_options = get_line_value_for_header( split, headers, 'Item options' )
                        item_option_values = get_line_value_for_header( split, headers, 'Item option values (optional)' )

                        if item_options is None:
                            print(f"ERROR: Choice question without options on line #{i+1}.")
                            continue

                        item_options = item_options.split('|')

                        if len(item_options) <= 1 or ( item_option_values is not None and ( len(item_option_values.split('|')) <= 1 or len(item_option_values.split('|')) != len(item_options) ) ):
                            print(f"ERROR: Choice question has errors in option (value) definition(s) on line #{i+1}.")
                            continue

                        if item_option_values is not None:
                            item_option_values = item_option_values.split('|')

                        try:
                            item_json = choice_question( item_name, item_type, item_text, item_options, item_option_values, item_required)
                        except Exception as e:
                            print(f"ERROR: {e} on line #{i+1}.")

                    else:
                        print(f"ERROR: Invalid question type on line #{i+1}.")

                    sublabel = get_line_value_for_header( split, headers, 'Item sublabel (optional)' )

                    if sublabel is not None:

                        if 'extension' not in item_json:
                            item_json['extension'] = []

                        extension_sublabel_json = json.loads(extension_sublabel_source_json)
                        extension_sublabel_json['valueMarkdown'] = sublabel
                        item_json['extension'].append(extension_sublabel_json)

                    conditions = get_line_value_for_header( split, headers, 'Item enableWhen (optional)' )

                    if conditions is not None:

                        item_json['enableWhen'] = []

                        conditions = json.loads(conditions)

                        for condition in conditions:

                            target_question = None

                            if 'targetQuestionRelativeIndex' in condition:

                                target_question = questionnaire_map[questionnaire_name]['fhir']['item'][question_index+condition['targetQuestionRelativeIndex']]

                            elif 'targetQuestionText' in condition:

                                try:

                                    matches = [
                                        q for q in questionnaire_map[questionnaire_name]['fhir']['item']
                                        if q.get("text") == condition['targetQuestionText']
                                    ]

                                    if len(matches) == 0:
                                        print("ERROR: enableWhen target question cannot be found.")
                                    elif len(matches) > 1:
                                        print("ERROR: enableWhen target question has multiple matches.")
                                    else:
                                        target_question = matches[0]

                                except StopIteration:
                                    pass

                            if target_question is not None:

                                target_option = next(
                                    option for option in target_question['answerOption']
                                    if option['valueCoding'].get('display') == condition['value']
                                )

                                item_json['enableWhen'].append({
                                    "question": target_question['linkId'],
                                    "operator": condition['operator'],
                                    "answerCoding": {
                                        "system": target_option['valueCoding']['system'],
                                        "code": target_option['valueCoding']['code']
                                    }
                                })

                            else:
                                print(f"ERROR: enableWhen on line #{i+1} cannot be set.")

                        enable_when_behaviour = get_line_value_for_header( split, headers, 'Item enableWhen behaviour (optional, default is any)' )

                        if enable_when_behaviour == 'all':
                            item_json['enableBehavior'] = enable_when_behaviour

                    if item_json['linkId'] not in questionnaire_link_ids:
                        questionnaire_link_ids.append(item_json['linkId'])
                        questionnaire_map[questionnaire_name]['fhir']['item'].append(item_json)

                    else:
                        print(f"ERROR linkId for question {i} must be unique!")

        for name, questionnaire in questionnaire_map.items():

            with open(f"./output/{filename_without_extension}_{name.lower()}.json", 'w') as output_file:

                questionnaire_json_string = ""

                if study_id is not None:
                    questionnaire_json_string = json.dumps(questionnaire)
                else:
                    questionnaire_json_string = json.dumps(questionnaire['fhir'])

                output_file.write(questionnaire_json_string)

            output_file.close()
