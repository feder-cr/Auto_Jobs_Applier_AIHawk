import json
import re

from src.ai_hawk.linkedIn_easy_applier import AIHawkEasyApplier

easy_applier = AIHawkEasyApplier(
    driver=None,
    resume_dir=None,
    set_old_answers=[],
    gpt_answerer=None,
    resume_generator_manager=None,
    job_application_profile=None
)

def cleanse_answers_json(input_file: str, output_file: str):
    with open(input_file, 'r') as f:
        data = json.load(f)

    cleansed_data = []
    seen_questions = set()

    for item in data:
        sanitized_question = easy_applier._sanitize_text(item['question'])
        if sanitized_question not in seen_questions:
            seen_questions.add(sanitized_question)
            cleansed_item = {
                'type': item['type'],
                'question': sanitized_question,
                'answer': item['answer']
            }
            cleansed_data.append(cleansed_item)

    with open(output_file, 'w') as f:
        json.dump(cleansed_data, f, indent=4)

if __name__ == "__main__":
    input_file = "answers.json"
    output_file = "cleansed_answers.json"
    cleanse_answers_json(input_file, output_file)
    print(f"Cleansed answers have been saved to {output_file}")
