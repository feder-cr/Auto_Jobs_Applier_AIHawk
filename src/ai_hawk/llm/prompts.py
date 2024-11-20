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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
"""

# Languages Template
languages_template = """
Answer the following question based on the provided language skills.

## Rules
- Answer questions directly.
- If it seems likely that you have the experience, even if not explicitly defined, answer as if you have the experience.
- If unsure, respond with "I have no experience with that, but I learn fast" or "Not yet, but willing to learn."
- Keep the answer under 140 characters. Do not add any additional languages what is not in my experience

## Example
My resume: Fluent in Italian and English.
Question: What languages do you speak?
Fluent in Italian and English.

Languages: {resume_section}
Question: {question}
Do not output anything else in the response other than the answer.
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
Do not output anything else in the response other than the answer.
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
Compose a brief and impactful cover letter based on the provided job description and resume. The letter should be no longer than three paragraphs and should be written in a professional, yet conversational tone. Avoid using any placeholders, and ensure that the letter flows naturally and is tailored to the job.

Analyze the job description to identify key qualifications and requirements. Introduce the candidate succinctly, aligning their career objectives with the role. Highlight relevant skills and experiences from the resume that directly match the job’s demands, using specific examples to illustrate these qualifications. Reference notable aspects of the company, such as its mission or values, that resonate with the candidate’s professional goals. Conclude with a strong statement of why the candidate is a good fit for the position, expressing a desire to discuss further.

Please write the cover letter in a way that directly addresses the job role and the company’s characteristics, ensuring it remains concise and engaging without unnecessary embellishments. The letter should be formatted into paragraphs and should not include a greeting or signature.

## Rules:
- Provide only the text of the cover letter.
- Do not include any introductions, explanations, or additional information.
- Use paragraphs to separate key points for clarity.
- Ensure that each paragraph is separated by a double line break (`\n\n`) for readability.
- Highlight key skills, achievements, and percentages using bold text (<b> and </b>).

## Formatting rules:
- The letter should contain 2-3 paragraphs for brevity.
- Use `<b>` and `</b>` to bold key qualifications, skills, and experiences.
- Separate each paragraph with a double line break (`\n\n`) for better readability.
- The letter should not include greetings or signatures.


## Company Name:
{company}

## Job Description:
```
{job_description}
```
## My resume:
```
{resume}
```
"""

numeric_question_template = """
Read the following resume carefully and answer the specific questions regarding the candidate's experience with a number of years. Follow these strategic guidelines when responding:

1. **Related and Inferred Experience:**
   - **Similar Technologies:** If experience with a specific technology is not explicitly stated, but the candidate has experience with similar or related technologies, provide a plausible number of years reflecting this related experience. For instance, if the candidate has experience with Python and projects involving technologies similar to Java, estimate a reasonable number of years for Java.
   - **Projects and Studies:** Examine the candidate’s projects and studies to infer skills not explicitly mentioned. Advanced and complex projects often indicate deeper expertise.

2. **Addressing Non-Relevant Questions:**
   - **Mismatch Between Question and Numeric Expectation:** If a question logically does not require a numerical response (e.g., "Are you available to start immediately? If not, what's your current notice period?"), but the system requires a numeric answer, **provide a meaningful placeholder value**:
     - For example, return "1" to indicate immediate availability.
     - If the question involves notice periods, return a plausible default numeric value such as "2" (for 2 weeks).
     - Ensure the value adheres to any constraints mentioned in the question (e.g., "larger than 0.0").

3. **Indirect Experience and Academic Background:**
   - **Type of University and Studies:** Consider the type of university and course followed.
   - **Exam Grades:** Consider exam grades achieved. High grades in relevant subjects can indicate stronger proficiency and understanding.
   - **Relevant Thesis:** If the candidate has worked on a thesis, advanced projects suggest deeper skills.
   - **Roles and Responsibilities:** Evaluate the roles and responsibilities held to estimate experience with specific technologies or skills.

4. **Experience Estimates for Quantitative Questions:**
   - **No Zero Experience:** A response of "0" is prohibited unless explicitly indicated in the question. If direct experience cannot be confirmed, provide at least "2" years based on inferred or related experience.
   - **For Low Experience (up to 5 years):** Base your estimate on inferred bachelor’s education, skills, and projects, always providing at least "2" years when relevant.
   - **For High Experience:** For high levels of experience, provide a number based on clear evidence from the resume. Avoid making inferences for high experience levels unless the evidence is strong.

5. **Rules for Ambiguous Questions:**
   - For questions that explicitly ask for years of experience, respond with a plausible number based on resume content.
   - For questions where the numeric expectation is unclear but required by the system:
     - Provide a sensible placeholder or default numeric value relevant to the context.
     - Avoid forcing unrelated answers; instead, focus on satisfying the system’s requirement in a logical manner.

**Example 1 (Relevant Numeric Question):**
Resume:
- I had a degree in computer science.
- I have worked 3 years with MQTT protocol.

Question:
How many years of experience do you have with IoT?

Answer:
4

**Example 2 (Mismatch with Numeric Expectation):**
Resume:
- I am a software engineer with a bachelor’s degree in computer science.
- 5 years of experience in Swift and Python.

Question:
Are you available to start immediately? If not, what's your current notice period?

Answer:
1

**Example 3 (Ambiguous Context):**
Resume:
- I have a background in data engineering.
- Worked on distributed systems and ETL pipelines for over 6 years.

Question:
How many years of experience do you have with cloud computing?

Answer:
2

Resume:
```
{resume_educations}
{resume_jobs}
{resume_projects}
```
        
## Question:
{question}

---

When responding, consider all available information, including projects, work experience, and academic background, to provide an accurate and well-reasoned answer. Make every effort to infer relevant experience and avoid defaulting to 0 if any related experience can be estimated.
Do not output anything else in the response other than the answer.

When responding, carefully consider all available information, including projects, work experience, and academic background. If a numeric answer is required despite the question’s non-numeric nature, provide a meaningful default value such as "1" or "2" in line with logical assumptions. Always ensure the response meets any constraints in the question.
"""

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
{job_application_profile}
```

## Question:
{question}

## Options:
{options}
-----
Do not output anything else in the response other than the answer.
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

is_relavant_position_template = """
Evaluate whether the provided resume meets the requirements outlined in the job description. 
Assess the candidate's suitability for the role based on the given information, including partial matches where applicable.

Job Description:
{job_description}

Resume:
{resume}

Instructions:

1. Extract Key Requirements:
   - Divide the requirements into:
     - Hard Requirements (must-haves): Mandatory skills, technologies, experience, certifications, and knowledge.
     - Soft Requirements (nice-to-haves): Desired skills, tools, methodologies, and personal qualities.
   - If the job description uses generalized terms (e.g., "experience with cloud platforms") and the resume includes an equivalent experience (e.g., Azure instead of AWS), consider the requirement fulfilled.
   - Do not assume the presence of tools or experience that are not explicitly mentioned in the resume.

2. Analyze Resume:
   - Map the candidate's skills and experience against the job requirements.
   - Full Match: When the specified skills or experience align with the job requirements, even through equivalent tools.
   - Partial Match: When the skills cover part of the requirement. For instance:
     - The job description requires "experience with orchestrators," and the resume mentions only Airflow.
   - Adjacent Experience: Evaluate transferable skills and similar experiences that align with the job requirements.

3. Adjust for Context:
   - Generalized Requirements: If the job description uses broad terms like "cloud platform" or "orchestrator," and the candidate's experience includes Azure, AWS, GCP, or Airflow, consider the requirement fulfilled.
   - Specific Requirements: If specific tools are mentioned (e.g., "AWS"), alternative experience (e.g., Azure) may partially fulfill the requirement unless the job description explicitly states a preference.
   - Experience Gap: Allow a one-year gap in experience if other qualifications are strong and meet the hard requirements.

4. Suitability Score Criteria:
   - 10: Full alignment with all hard and soft requirements, including equivalent substitutions.
   - 8-9: All hard requirements fulfilled, with partial fulfillment of soft requirements.
   - 6-7: Most hard requirements fulfilled; soft requirements partially fulfilled or adjacent skills are strong.
   - 4-5: Several hard requirements unfulfilled; soft requirements largely absent.
   - 2-3: Minimal fulfillment of hard requirements; no relevant soft requirements.
   - 1: No alignment with job requirements.

5. Provide Reasoning:
   - Explain which requirements are fully met, partially met, or unmet.
   - Highlight how transferable skills or alternative experiences were considered.
   - Clearly state how the score was derived.

Output Format (Strictly follow this format):
Score: [numerical score]
Reasoning: [brief explanation of matches, gaps, and considerations for alternative qualifications].
Do not output anything else in the response other than the score and reasoning.

Universal Principles:
1. Generalized Requirements:
   - Broadly stated requirements (e.g., "cloud platform") are fulfilled by equivalent experience with Azure, AWS, GCP, etc.

2. Specific Requirements:
   - If specific tools are mentioned (e.g., "AWS"), alternative experience (e.g., Azure) counts as partial fulfillment unless explicitly stated otherwise.

3. Transferable Skills:
   - Skills with similar principles (e.g., Airflow and Prefect for orchestrators) are considered relevant.

4. Weighting Partial Matches:
   - Generalized Requirements: Considered fulfilled by equivalent tools or experience.
   - Specific Tools: Fulfillment is proportional to their interchangeability in context.

5. Context Overlap:
   - Adjacent roles (e.g., Data Engineer vs. Big Data Architect) are relevant if the tasks and skills overlap.

Example:
Job Description: Requires experience with orchestrators, cloud platforms (AWS/GCP), Spark optimization skills, and big data experience.

Resume: Mentions Airflow, Azure, Spark, but lacks GCP experience.

Output:
Score: 8
Reasoning: Candidate meets the hard requirements for orchestrators (Airflow) and big data (Spark). The cloud experience (Azure) is equivalent to AWS/GCP since no explicit preference was stated in the job description. However, GCP experience is missing, which partially fulfills the cloud platform requirement.
"""

resume_or_cover_letter_template = """
Given the following phrase, respond with only 'resume' if the phrase is about a resume, or 'cover' if it's about a cover letter.
If the phrase contains only one word 'upload', consider it as 'cover'.
If the phrase contains 'upload resume', consider it as 'resume'.
Do not provide any additional information or explanations.

phrase: {phrase}
"""

determine_section_template = """You are assisting a bot designed to automatically apply for jobs on AIHawk. The bot receives various questions about job applications and needs to determine the most relevant section of the resume to provide an accurate response.

For the following question: '{question}', determine which section of the resume is most relevant. 
Respond with exactly one of the following options:
- Personal information
- Self Identification
- Legal Authorization
- Work Preferences
- Education Details
- Experience Details
- Projects
- Availability
- Salary Expectations
- Certifications
- Languages
- Interests
- Cover letter

Here are detailed guidelines to help you choose the correct section:

1. **Personal Information**:
- **Purpose**: Contains your basic contact details and online profiles.
- **Use When**: The question is about how to contact you or requests links to your professional online presence.
- **Examples**: Email address, phone number, AIHawk profile, GitHub repository, personal website.

2. **Self Identification**:
- **Purpose**: Covers personal identifiers and demographic information.
- **Use When**: The question pertains to your gender, pronouns, veteran status, disability status, or ethnicity.
- **Examples**: Gender, pronouns, veteran status, disability status, ethnicity.

3. **Legal Authorization**:
- **Purpose**: Details your work authorization status and visa requirements.
- **Use When**: The question asks about your ability to work in specific countries or if you need sponsorship or visas.
- **Examples**: Work authorization in EU and US, visa requirements, legally allowed to work.

4. **Work Preferences**:
- **Purpose**: Specifies your preferences regarding work conditions and job roles.
- **Use When**: The question is about your preferences for remote work, in-person work, relocation, and willingness to undergo assessments or background checks.
- **Examples**: Remote work, in-person work, open to relocation, willingness to complete assessments.

5. **Education Details**:
- **Purpose**: Contains information about your academic qualifications.
- **Use When**: The question concerns your degrees, universities attended, GPA, and relevant coursework.
- **Examples**: Degree, university, GPA, field of study, exams.

6. **Experience Details**:
- **Purpose**: Details your professional work history and key responsibilities.
- **Use When**: The question pertains to your job roles, responsibilities, and achievements in previous positions.
- **Examples**: Job positions, company names, key responsibilities, skills acquired.

7. **Projects**:
- **Purpose**: Highlights specific projects you have worked on.
- **Use When**: The question asks about particular projects, their descriptions, or links to project repositories.
- **Examples**: Project names, descriptions, links to project repositories.

8. **Availability**:
- **Purpose**: Provides information on your availability for new roles.
- **Use When**: The question is about how soon you can start a new job or your notice period.
- **Examples**: Notice period, availability to start.

9. **Salary Expectations**:
- **Purpose**: Covers your expected salary range.
- **Use When**: The question pertains to your salary expectations or compensation requirements.
- **Examples**: Desired salary range.

10. **Certifications**:
   - **Purpose**: Lists your professional certifications or licenses.
   - **Use When**: The question involves your certifications or qualifications from recognized organizations.
   - **Examples**: Certification names, issuing bodies, dates of validity.

11. **Languages**:
   - **Purpose**: Describes the languages you can speak and your proficiency levels.
   - **Use When**: The question asks about your language skills or proficiency in specific languages.
   - **Examples**: Languages spoken, proficiency levels.

12. **Interests**:
   - **Purpose**: Details your personal or professional interests.
   - **Use When**: The question is about your hobbies, interests, or activities outside of work.
   - **Examples**: Personal hobbies, professional interests.

13. **Cover Letter**:
   - **Purpose**: Contains your personalized cover letter or statement.
   - **Use When**: The question involves your cover letter or specific written content intended for the job application.
   - **Examples**: Cover letter content, personalized statements.

Provide only the exact name of the section from the list above with no additional text.
"""
