# Answer Editor and Cleaner

This project consists of two main Python scripts: `answer_editor.py` and `cleanse_answers.py`. These scripts work together to manage and clean a set of questions and answers stored in JSON format.

## answer_editor.py

This script is a Flask web application that provides a user interface for viewing and editing a set of questions and answers.

### Key Features:
- Uses Flask and Flask-Bootstrap for the web interface
- Reads and writes data to a JSON file (`answers.json`)
- Allows viewing all questions and answers
- Supports editing answers
- Handles both radio button and text input answers
- Allows deletion of individual question-answer pairs

### How it works:
1. The main route (`/`) displays all questions and answers when accessed via GET request
2. When a POST request is made (i.e., when the form is submitted), it updates the answers in the JSON file
3. It uses a template (`index.html`, not shown in the provided code) to render the web interface

## cleanse_answers.py

This script is designed to clean and sanitize the questions and answers stored in the JSON file.

### Key Features:
- Removes duplicate words in questions
- Converts text to lowercase
- Removes common suffixes and unnecessary characters
- Eliminates non-ASCII characters
- Removes duplicate questions

### How it works:
1. Reads the input JSON file (`answers.json`)
2. Sanitizes each question using the `sanitize_text` function
3. Removes duplicate questions
4. Writes the cleansed data to a new JSON file (`cleansed_answers.json`)

## Usage

1. Run `answer_editor.py` to start the web application for viewing and editing answers:
   ```
   python answer_editor.py
   ```
   Then open a web browser and navigate to `http://localhost:5000`

2. After editing answers, run `cleanse_answers.py` to clean the data:
   ```
   python cleanse_answers.py
   ```

This will create a new file `cleansed_answers.json` with the sanitized data.

Note: Make sure you have Flask and Flask-Bootstrap installed (`pip install flask flask-bootstrap`) before running `answer_editor.py`. (they are inlcuded in the requirements.txt file)