from flask import Flask, render_template, request, redirect, url_for
import json
import os
from pathlib import Path
from flask_bootstrap import Bootstrap
from src.ai_hawk.linkedIn_easy_applier import AIHawkEasyApplier

app = Flask(__name__)
Bootstrap(app)

JSON_FILE = Path(__file__).parent / 'answers.json'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return update()
    else:
        if not JSON_FILE.exists():
            data = []  # Default empty list if file doesn't exist
        else:
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)

        # Ensure data is sorted alphabetically by question
        if isinstance(data, list):
            data.sort(key=lambda item: item['question'].lower())

        return render_template('index.html', data=data if isinstance(data, list) else [])

easy_applier = AIHawkEasyApplier(
    driver=None,
    resume_dir=None,
    set_old_answers=[],
    gpt_answerer=None,
    resume_generator_manager=None,
    job_application_profile=None
)

def update():
    if not JSON_FILE.exists():
        data = []
    else:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)

    updated_data = []
    for i, item in enumerate(data):
        if f'delete_{i}' not in request.form:
            if item['type'] == 'radio':
                item['answer'] = easy_applier._sanitize_text(request.form.get(f'answer_{i}_radio', item['answer']))
            else:
                item['answer'] = easy_applier._sanitize_text(request.form.get(f'answer_{i}', item['answer']))
            updated_data.append(item)

    # Sort updated data alphabetically by question
    updated_data.sort(key=lambda item: item['question'].lower())

    with open(JSON_FILE, 'w') as f:
        json.dump(updated_data, f, indent=2)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
