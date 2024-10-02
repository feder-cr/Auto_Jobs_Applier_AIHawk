from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from pathlib import Path
from flask_bootstrap import Bootstrap

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
                print(data)
        return render_template('index.html', data=data if isinstance(data, list) else [])

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
                item['answer'] = request.form.get(f'answer_{i}_radio', item['answer'])
            else:
                item['answer'] = request.form.get(f'answer_{i}', item['answer'])
            updated_data.append(item)

    with open(JSON_FILE, 'w') as f:
        json.dump(updated_data, f, indent=2)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
