import json
import re

def sanitize_text(text: str) -> str:
    # Remove duplicates by splitting and rejoining
    text = text.rstrip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('?', '').replace('"', '').replace('\\', '')
    words = text.lower().split()
    unique_words = []
    for word in words:
        if word not in unique_words:
            unique_words.append(word)
    text = ' '.join(unique_words)
    
    # Remove common suffixes
    text = re.sub(r'\s*\(?required\)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(\s*\(?yes\/no\)?|\s*\(?yes\)?|\s*\(?no\)?|\?)$', '', text, flags=re.IGNORECASE)
    sanitized_text = re.sub(r'[^[:ascii:]]','', text)
    return sanitized_text

def cleanse_answers_json(input_file: str, output_file: str):
    with open(input_file, 'r') as f:
        data = json.load(f)

    cleansed_data = []
    seen_questions = set()

    for item in data:
        sanitized_question = sanitize_text(item['question'])
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
