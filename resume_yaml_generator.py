import argparse
import yaml
from openai import OpenAI
import os
from typing import Dict, Any
import tiktoken
import re
from jsonschema import validate, ValidationError

def load_yaml(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def load_resume_text(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()

def get_api_key() -> str:
    secrets_path = os.path.join('data_folder', 'secrets.yaml')
    if not os.path.exists(secrets_path):
        raise FileNotFoundError(f"Secrets file not found at {secrets_path}")
    
    secrets = load_yaml(secrets_path)
    api_key = secrets.get('openai_api_key')
    if not api_key:
        raise ValueError("OpenAI API key not found in secrets.yaml")
    
    return api_key

def num_tokens_from_string(string: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(string))

def generate_yaml_from_resume(resume_text: str, schema: Dict[str, Any], api_key: str) -> str:
    client = OpenAI(api_key=api_key)

    prompt = f"""
    I'm sending you the content of a text-based resume. Your task is to interpret this content and generate a YAML file that conforms to the following schema structure.
    The generated YAML should include all required fields and follow the structure defined in the schema.

    Pay special attention to the property attributes in the schema. These indicate the expected type and format for each field:
    - 'type': Specifies the data type (e.g., string, object, array)
    - 'format': Indicates a specific format for certain fields:
    - 'date' format should be a valid date (e.g., YYYY-MM-DD)
    - 'phone_prefix' format should be a valid country code with a '+' prefix (e.g., +1 for US)
    - 'phone' format should be a valid phone number
    - 'email' format should be a valid email address
    - 'uri' format should be a valid URL
    - 'enum': Provides a list of allowed values for a field

    Important instructions:
    1. Ensure that the YAML structure matches exactly with the provided schema. Use a dictionary structure that mirrors the schema.
    2. For all sections, if information is not explicitly provided in the resume, make a best guess based on the context of the resume. This is CRUCIAL for the following fields:
    - languages: Infer from the resume content or make an educated guess. Use the 'enum' values for proficiency.
    - interests: Deduce from the overall resume or related experiences.
    - availability (notice_period): Provide a reasonable estimate (e.g., "2 weeks" or "1 month").
    - salary_expectations (salary_range_usd): Estimate based on experience level and industry standards.
    - self_identification: Make reasonable assumptions based on the resume context. Use 'enum' values where provided.
    - legal_authorization: Provide plausible values based on the resume information. Use 'Yes' or 'No' as per the 'enum' values.
    - work_preferences: Infer from job history, skills, and overall resume tone. Use 'Yes' or 'No' as per the 'enum' values.
    3. For the fields mentioned in point 2, always provide a value. Do not leave them blank or omit them.
    4. For the 'key_responsibilities' field in 'experience_details', format the responsibilities as follows:
    responsibility_1: "Description of first responsibility"
    responsibility_2: "Description of second responsibility"
    responsibility_3: "Description of third responsibility"
    responsibility_4: "Description of fourth responsibility"
    Continue this pattern for all responsibilities listed.
    5. In the 'experience_details' section, ensure that 'position' comes before 'company' in each entry.
    6. For the 'skills_acquired' field in 'experience_details', infer relevant skills based on the job responsibilities and industry. Do not leave this field empty.
    7. Make reasonable inferences for any missing dates, such as date_of_birth or employment dates, ensuring they follow the 'date' format.
    8. For array types (e.g., education_details, experience_details), ensure to include all required fields for each item as specified in the schema.

    Resume Text Content:
    {resume_text}

    YAML Schema:
    {yaml.dump(schema, default_flow_style=False)}

    Generate the YAML content that matches this schema based on the resume content provided, ensuring all format hints are followed and making educated guesses where necessary. Be sure to include best guesses for ALL fields, even if not explicitly mentioned in the resume.
    Enclose your response in <resume_yaml> tags. Only include the YAML content within these tags, without any additional text or code block markers.
    """
    
    model = "gpt-3.5-turbo-16k"  # This model has a 16k token limit
    tokens = num_tokens_from_string(prompt, model)
    max_tokens = min(16385 - tokens, 4000)  # Ensure we don't exceed model's limit

    if tokens > 16385:
        print(f"Warning: The input exceeds the model's context length. Tokens: {tokens}")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates structured YAML content from resume files, paying close attention to format requirements and schema structure."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=0.5,
    )

    yaml_content = response.choices[0].message.content.strip()
    
    # Extract YAML content from between the tags
    match = re.search(r'<resume_yaml>(.*?)</resume_yaml>', yaml_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("YAML content not found in the expected format")
                                                                                                                                                                                                                                                                                                                                                                                        
def save_yaml(data: str, output_file: str):
    with open(output_file, 'w') as file:
        file.write(data)

def validate_yaml(yaml_content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    try:
        yaml_dict = yaml.safe_load(yaml_content)
        validate(instance=yaml_dict, schema=schema)
        return {"valid": True, "errors": None}
    except ValidationError as e:
        return {"valid": False, "errors": str(e)}

def generate_report(validation_result: Dict[str, Any], output_file: str):
    report = f"Validation Report for {output_file}\n"
    report += "=" * 40 + "\n"
    if validation_result["valid"]:
        report += "YAML is valid and conforms to the schema.\n"
    else:
        report += "YAML is not valid. Errors:\n"
        report += validation_result["errors"] + "\n"
    
    print(report)

def main():
    parser = argparse.ArgumentParser(description="Generate a resume YAML file from a text resume using OpenAI API")
    parser.add_argument("--input", required=True, help="Path to the input text resume file")
    parser.add_argument("--output", default="data_folder/plain_text_resume.yaml", help="Path to the output YAML file")
    args = parser.parse_args()

    try:
        api_key = get_api_key()
        schema = load_yaml("assets/resume_schema.yaml")
        resume_text = load_resume_text(args.input)

        generated_yaml = generate_yaml_from_resume(resume_text, schema, api_key)
        save_yaml(generated_yaml, args.output)

        print(f"Resume YAML generated and saved to {args.output}")

        validation_result = validate_yaml(generated_yaml, schema)
        if validation_result["valid"]:
            print("YAML is valid and conforms to the schema.")
        else:
            print("YAML is not valid. Errors:")
            print(validation_result["errors"])

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()