resume_markdown_template = """
Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is twofold:

1. **Review and Extract Information**: Carefully examine the candidate's current resume to extract the following critical details:
   - Work experience
   - Educational background
   - Relevant skills
   - Achievements
   - Certifications

2. **Optimize the Resume**: Using the provided template, create a highly optimized resume for the relevant industry. The resume should:
   - Include commonly required skills and keywords for the industry
   - Utilize ATS-friendly phrases and terminology to ensure compatibility with automated systems
   - Highlight strengths and achievements relevant to the industry
   - Present experience, skills, and accomplishments in a compelling and professional manner
   - Maintain a clear, that is easily readable by both ATS and human reviewers

Provide guidance on how to enhance the presentation of the information to maximize impact and readability. Offer advice on tailoring the content to general industry standards, ensuring the resume passes ATS filters and captures the attention of recruiters, thereby increasing the candidate’s chances of securing an interview.

## Information to Collect and Analyze
- **My information eesume:**  
  {resume}

## Template to Use
```
# [Full Name]

## Summary

[Brief professional summary highlighting your experience, key skills, and career objectives. 2-3 sentences.]

## Skills

- **Skill1:** [details (max 15 word)]
- **Skill2:** [details (max 15 word)]
- **Skill3:** [details (max 15 word)]
- **Skill4:** [details (max 15 word)]
- **Skill4:** [details (max 15 word)]
- **Skill5:** [details (max 15 word)]

## Professional Experience

### [Job Title]
**[Company Name]** – [City, State]
*[Start Date – End Date]*

1. [Achievement or responsibility]
2. [Achievement or responsibility]
3. [Achievement or responsibility]
4. [Achievement or responsibility]
5. [Achievement or responsibility]

### [Job Title]
**[Company Name]** – [City, State]
*[Start Date – End Date]*

1. [Achievement or responsibility]
2. [Achievement or responsibility]
3. [Achievement or responsibility]
4. [Achievement or responsibility]
5. [Achievement or responsibility]

### [Job Title]
**[Company Name]** – [City, State]
*[Start Date – End Date]*

1. [Achievement or responsibility]
2. [Achievement or responsibility]
3. [Achievement or responsibility]
4. [Achievement or responsibility]
5. [Achievement or responsibility]

## Education

**[Degree] in [Field of Study]**
[University Name] – [City, State]
*Graduated: [Month Year]*

## Certifications

1. [Certification Name]
2. [Certification Name]
3. [Certification Name]

## Projects

### [Project Name]
1. [Brief description of the project and your role]

### [Project Name]
1. [Brief description of the project and your role]

### [Project Name]
1. [Brief description of the project and your role]

## Languages

1. **[Language]:** [Proficiency Level]
2. **[Language]:** [Proficiency Level]
```
The results should be provided in **markdown** format, Provide only the markdown code for the resume, without any explanations or additional text and also without ```markdown ```
"""

fusion_job_description_resume_template = """

Act as an HR expert and resume writer with a strategic approach. Customize the resume to highlight the candidate’s
strengths, skills, and achievements that are most relevant to the provided job description. 
Use a smart and targeted approach, incorporating key skills and abilities as well as important aspects of the job 
description into the resume. 
Ensure that the resume grabs the attention of hiring managers within the first few seconds and uses specific keywords and phrases from the job description to pass through Applicant Tracking Systems (ATS).

Important Note: While making the necessary adjustments to align the resume with the job description, ensure that the overall structure of the resume remains intact. Do not drastically alter the organization of the document, but optimize it to highlight the most relevant points for the desired position.

- **Most important infomation on job descrptio:**  
  {job_description}

- **My information eesume:**  
  {formatted_resume}

The results should be provided in **markdown** format, Provide only the markdown code for the resume, without any explanations or additional text and also without ```markdown ```
  """



html_template = """
<!DOCTYPE html>
<title>Resume</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/casualwriter/casual-markdown/dist/casual-markdown.css">
<script src="https://cdn.jsdelivr.net/gh/casualwriter/casual-markdown/dist/casual-markdown.js"></script>
<style>  
  body {{ line-height:1.5; margin:auto; padding:3px; max-width:1024px; display:none; FONT-FAMILY:"Segoe UI",ARIAL; }}
  h1  {{ font-size:200%; padding:16px; border:1px solid lightgrey; BACKGROUND:#f0f0f0; }}
  h2  {{ border-bottom:1px solid grey; padding:2px }}
</style>
<body onload="document.body.innerHTML=md.html(document.body.innerHTML); document.body.style.display='block';">
<span style="float:right; padding:6px; display:block; text-align: center; width:250px;"> 
  {email_address} <br> {phone_number} <a href="{github_link}" style="color: #0366d6; text-decoration: none;">GitHub</a> - <a href="{linkedin_link}" style="color: #0366d6; text-decoration: none;">LinkedIn</a>
</span>
<span style="
  position: fixed;
  top: 16.5%;
  left: 18%; 
  transform: translate(-50%, -50%);
  padding: 6px;
  text-align: center;
  z-index: 1000; 
">
  {city}, {country}
</span>
"""










# Personal Information Template
personal_information_template = """
Answer the following question based on the provided personal information.

## Rules
- Answer questions directly.

## Example
My resume: John Doe, born on 01/01/1990, living in Milan, Italy.
Question: What is your city?
 Milan

Personal Information: {resume_section}
Question: {question}
"""



# Personal Information Template
personal_information_template = """
Answer the following question based on the provided personal information.

## Rules
- Answer questions directly.

## Example
My resume: John Doe, born on 01/01/1990, living in Milan, Italy.
Question: What is your city?
 Milan

Personal Information: {resume_section}
Question: {question}
"""

# Self Identification Template
self_identification_template = """
Answer the following question based on the provided self-identification details.

## Rules
- Answer questions directly.

## Example
My resume: Male, uses he/him pronouns, not a veteran, no disability.
Question: What are your gender?
Male

Self-Identification: {resume_section}
Question: {question}
"""

# Legal Authorization Template
legal_authorization_template = """
Answer the following question based on the provided legal authorization details.

## Rules
- Answer questions directly.

## Example
My resume: Authorized to work in the EU, no US visa required.
Question: Are you legally allowed to work in the EU?
Yes

Legal Authorization: {resume_section}
Question: {question}
"""

# Work Preferences Template
work_preferences_template = """
Answer the following question based on the provided work preferences.

## Rules
- Answer questions directly.

## Example
My resume: Open to remote work, willing to relocate.
Question: Are you open to remote work?
Yes

Work Preferences: {resume_section}
Question: {question}
"""

# Education Details Template
education_details_template = """
Answer the following question based on the provided education details.

## Rules
- Answer questions directly.
- If it seems likely that you have the experience, even if not explicitly defined, answer as if you have the experience.
- If unsure, respond with "I have no experience with that, but I learn fast" or "Not yet, but willing to learn."
- Keep the answer under 140 characters.

## Example
My resume: Bachelor's degree in Computer Science with experience in Python.
Question: Do you have experience with Python?
Yes, I have experience with Python.

Education Details: {resume_section}
Question: {question}
"""

# Experience Details Template
experience_details_template = """
Answer the following question based on the provided experience details.

## Rules
- Answer questions directly.
- If it seems likely that you have the experience, even if not explicitly defined, answer as if you have the experience.
- If unsure, respond with "I have no experience with that, but I learn fast" or "Not yet, but willing to learn."
- Keep the answer under 140 characters.

## Example
My resume: 3 years as a software developer with leadership experience.
Question: Do you have leadership experience?
Yes, I have 3 years of leadership experience.

Experience Details: {resume_section}
Question: {question}
"""

# Projects Template
projects_template = """
Answer the following question based on the provided project details.

## Rules
- Answer questions directly.
- If it seems likely that you have the experience, even if not explicitly defined, answer as if you have the experience.
- Keep the answer under 140 characters.

## Example
My resume: Led the development of a mobile app, repository available.
Question: Have you led any projects?
Yes, led the development of a mobile app

Projects: {resume_section}
Question: {question}
"""

# Availability Template
availability_template = """
Answer the following question based on the provided availability details.

## Rules
- Answer questions directly.
- Keep the answer under 140 characters.
- Use periods only if the answer has multiple sentences.

## Example
My resume: Available to start immediately.
Question: When can you start?
I can start immediately.

Availability: {resume_section}
Question: {question}
"""

# Salary Expectations Template
salary_expectations_template = """
Answer the following question based on the provided salary expectations.

## Rules
- Answer questions directly.
- Keep the answer under 140 characters.
- Use periods only if the answer has multiple sentences.

## Example
My resume: Looking for a salary in the range of 50k-60k USD.
Question: What are your salary expectations?
55000.

Salary Expectations: {resume_section}
Question: {question}
"""

# Certifications Template
certifications_template = """
Answer the following question based on the provided certifications.

## Rules
- Answer questions directly.
- If it seems likely that you have the experience, even if not explicitly defined, answer as if you have the experience.
- If unsure, respond with "I have no experience with that, but I learn fast" or "Not yet, but willing to learn."
- Keep the answer under 140 characters.

## Example
My resume: Certified in Project Management Professional (PMP).
Question: Do you have PMP certification?
Yes, I am PMP certified.

Certifications: {resume_section}
Question: {question}
"""

# Languages Template
languages_template = """
Answer the following question based on the provided language skills.

## Rules
- Answer questions directly.
- If it seems likely that you have the experience, even if not explicitly defined, answer as if you have the experience.
- If unsure, respond with "I have no experience with that, but I learn fast" or "Not yet, but willing to learn."
- Keep the answer under 140 characters.

## Example
My resume: Fluent in Italian and English.
Question: What languages do you speak?
Fluent in Italian and English.

Languages: {resume_section}
Question: {question}
"""

# Interests Template
interests_template = """
Answer the following question based on the provided interests.

## Rules
- Answer questions directly.
- Keep the answer under 140 characters.
- Use periods only if the answer has multiple sentences.

## Example
My resume: Interested in AI and data science.
Question: What are your interests?
AI and data science.

Interests: {resume_section}
Question: {question}
"""

summarize_prompt_template = """
As a seasoned HR expert, your task is to identify and outline the key skills and requirements necessary for the position of this job. Use the provided job description as input to extract all relevant information. This will involve conducting a thorough analysis of the job's responsibilities and the industry standards. You should consider both the technical and soft skills needed to excel in this role. Additionally, specify any educational qualifications, certifications, or experiences that are essential. Your analysis should also reflect on the evolving nature of this role, considering future trends and how they might affect the required competencies.

Rules:
Remove boilerplate text
Include only relevant information to match the job description against the resume

# Analysis Requirements
Your analysis should include the following sections:
Technical Skills: List all the specific technical skills required for the role based on the responsibilities described in the job description.
Soft Skills: Identify the necessary soft skills, such as communication abilities, problem-solving, time management, etc.
Educational Qualifications and Certifications: Specify the essential educational qualifications and certifications for the role.
Professional Experience: Describe the relevant work experiences that are required or preferred.
Role Evolution: Analyze how the role might evolve in the future, considering industry trends and how these might influence the required skills.

# Final Result:
Your analysis should be structured in a clear and organized document with distinct sections for each of the points listed above. Each section should contain:
This comprehensive overview will serve as a guideline for the recruitment process, ensuring the identification of the most qualified candidates.

# Job Description:
```
{text}
```

---

# Job Description Summary"""


coverletter_template = """
The following is a resume, a job description, and an answered question using this information, being answered by the person who's resume it is (first person).

## Rules
- Answer questions directly.
- If seems likely that you have the experience, even if is not explicitly defined, answer as if you have the experience.
- Find relations between the job description and the resume, and answer questions about that.
- Only add periods if the answer has multiple sentences/paragraphs.
- If the question is "cover letter," answer with a cover letter based on job_description, but using my resume details

## Job Description:
```
{job_description}
```

## My resume:
```
{resume}
```

## Question:
{question}

## """


resume_stuff_template = """
The following is a resume, personal data, and an answered question using this information, being answered by the person who's resume it is (first person).

## Rules
- Answer questions directly
- If seems likely that you have the experience, even if is not explicitly defined, answer as if you have the experience
- If you cannot answer the question, answer things like "I have no experience with that, but I learn fast, very fast", "not yet, but I will learn"...
- The answer must not be longer than a tweet (140 characters)
- Only add periods if the answer has multiple sentences/paragraphs

## Example 1
My resume: I'm a software engineer with 10 years of experience in  swift .
Question: What is your experience with swift?
10 years

-----

## My resume:
```
{resume}
```
        
## Question:
{question}

## """


numeric_question_template = """The following is a resume and an answered question about the resume, being answered by the person who's resume it is (first person).

## Rules
- Answer the question directly (only number).
- Regarding work experience just check the Experience Details -> Skills Acquired section.
- Regarding experience in general just check the section Experience Details -> Skills Acquired and also Education Details -> Skills Acquired.
- If it seems likely that you have the experience based on the resume, even if not explicitly stated on the resume, answer as if you have the experience.
- If you cannot answer the question, provide answers like "I have no experience with that, but I learn fast, very fast", "not yet, but I will learn".
- The answer must not be larger than a tweet (140 characters).

## Example
My resume: I'm a software engineer with 10 years of experience on both swift and python.
Question: how much years experience with swift?
10

-----

## My resume:
```
{resume}
```
        
## Question:
{question}

## """

options_template = """The following is a resume and an answered question about the resume, the answer is one of the options.

## Rules
- Never choose the default/placeholder option, examples are: 'Select an option', 'None', 'Choose from the options below', etc.
- The answer must be one of the options.
- The answer must exclusively contain one of the options.

## Example
My resume: I'm a software engineer with 10 years of experience on swift, python, C, C++.
Question: How many years of experience do you have on python?
Options: [1-2, 3-5, 6-10, 10+]
10+

-----

## My resume:
```
{resume}
```

## Question:
{question}

## Options:
{options}

## """


try_to_fix_template = """\
The objective is to fix the text of a form input on a web page.

## Rules
- Use the error to fix the original text.
- The error "Please enter a valid answer" usually means the text is too large, shorten the reply to less than a tweet.
- For errors like "Enter a whole number between 3 and 30", just need a number.

-----

## Form Question
{question}

## Input
{input} 

## Error
{error}  

## Fixed Input
"""

func_summarize_prompt_template = """
        Following are two texts, one with placeholders and one without, the second text uses information from the first text to fill the placeholders.
        
        ## Rules
        - A placeholder is a string like "[[placeholder]]". E.g. "[[company]]", "[[job_title]]", "[[years_of_experience]]"...
        - The task is to remove the placeholders from the text.
        - If there is no information to fill a placeholder, remove the placeholder, and adapt the text accordingly.
        - No placeholders should remain in the text.
        
        ## Example
        Text with placeholders: "I'm a software engineer engineer with 10 years of experience on [placeholder] and [placeholder]."
        Text without placeholders: "I'm a software engineer with 10 years of experience."
        
        -----
        
        ## Text with placeholders:
        {text_with_placeholders}
        
        ## Text without placeholders:"""