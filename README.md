<img src="./assets/linkedin_aihawk.png">

<!-- At first glance, the branding and messaging clearly conveys what to expect -->
<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/federico-elia-5199951b6/)
[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:federico.elia.majo@gmail.com)

# LinkedIn_AIHawk

#### 🤖🔍 Your AI-powered job search assistant. Automate applications, get personalized recommendations, and land your dream job faster.

</div>
<br />

<!-- Message Clarity -->
## 🚀 Join the AIHawk Community 🚀 

Connect with like-minded individuals and get the most out of AIHawk.

💡 **Get support:** Ask questions, troubleshoot issues, and find solutions.

🗣️ **Share knowledge:** Share your experiences, tips, and best practices.

🤝 **Network:** Connect with other professionals and explore new opportunities.

🔔 **Stay updated:** Get the latest news and updates on AIHawk.

<!-- Strong Call to Action -->
### Join Now 👇
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white
)](https://t.me/AIhawkCommunity)




<!-- 🚀 **Join Our Telegram Community!** 🚀

Join our **Telegram community** for:
- **Support with AIHawk software**
- **Share your experiences** with AIhawk and learn from others
- **Job search tips** and **resume advice**
- **Idea exchange** and resources for your projects

📲 **[Join now!](https://t.me/AIhawkCommunity)** -->

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Documentation](#Documentation)
7. [Troubleshooting](#troubleshooting)
8. [Conclusion](#conclusion)
9. [Contributors](#contributors)
10. [License](#license)
11. [Disclaimer](#Disclaimer)

## Introduction

LinkedIn_AIHawk is a cutting-edge, automated tool designed to revolutionize the job search and application process on LinkedIn. In today's fiercely competitive job market, where opportunities can vanish in the blink of an eye, this program offers job seekers a significant advantage. By leveraging the power of automation and artificial intelligence, LinkedIn_AIHawk enables users to apply to a vast number of relevant positions efficiently and in a personalized manner, maximizing their chances of landing their dream job.

### The Challenge of Modern Job Hunting

In the digital age, the job search landscape has undergone a dramatic transformation. While online platforms like LinkedIn have opened up a world of opportunities, they have also intensified competition. Job seekers often find themselves spending countless hours scrolling through listings, tailoring applications, and repetitively filling out forms. This process can be not only time-consuming but also emotionally draining, leading to job search fatigue and missed opportunities.

### Enter LinkedIn_AIHawk: Your Personal Job Search Assistant

LinkedIn_AIHawk steps in as a game-changing solution to these challenges. It's not just a tool; it's your tireless, 24/7 job search partner. By automating the most time-consuming aspects of the job search process, it allows you to focus on what truly matters - preparing for interviews and developing your professional skills.

## Features

1. **Intelligent Job Search Automation**
   - Customizable search criteria
   - Continuous scanning for new openings
   - Smart filtering to exclude irrelevant listings

2. **Rapid and Efficient Application Submission**
   - One-click applications using LinkedIn's "Easy Apply" feature
   - Form auto-fill using your profile information
   - Automatic document attachment (resume, cover letter)

3. **AI-Powered Personalization**
   - Dynamic response generation for employer-specific questions
   - Tone and style matching to fit company culture
   - Keyword optimization for improved application relevance

4. **Volume Management with Quality**
   - Bulk application capability
   - Quality control measures
   - Detailed application tracking

5. **Intelligent Filtering and Blacklisting**
   - Company blacklist to avoid unwanted employers
   - Title filtering to focus on relevant positions

6. **Dynamic Resume Generation**
   - Automatically creates tailored resumes for each application
   - Customizes resume content based on job requirements

7. **Secure Data Handling**
   - Manages sensitive information securely using YAML files

## Installation

**Please watch this video to set up your LinkedIn_AIHawk: [How to set up LinkedIn_AIHawk](https://youtu.be/gdW9wogHEUM) - https://youtu.be/gdW9wogHEUM**
0. **Confirmed succesfull runs OSs & Python**: Python 3.10, 3.11.9(64b), 3.12.5(64b) . Windows 10, Ubuntu 22
1. **Download and Install Python:**

   Ensure you have the last Python version  installed. If not, download and install it from Python's official website. For detailed instructions, refer to the tutorials:

   - [How to Install Python on Windows](https://www.geeksforgeeks.org/how-to-install-python-on-windows/)
   - [How to Install Python on Linux](https://www.geeksforgeeks.org/how-to-install-python-on-linux/)
   - [How to Download and Install Python on macOS](https://www.geeksforgeeks.org/how-to-download-and-install-python-latest-version-on-macos-mac-os-x/)

2. **Download and Install Google Chrome:**
   - Download and install the latest version of Google Chrome in its default location from the [official website](https://www.google.com/chrome).

3. **Clone the repository:**
   ```bash
   git clone https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application
   cd LinkedIn_AIHawk_automatic_job_application
   ```

4. **Activate virtual environment:**
   ```bash
   python3 -m venv virtual
   ```

   ```bash
   source virtual/bin/activate
   ```

5. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. secrets.yaml

This file contains sensitive information. Never share or commit this file to version control.

- `email: [Your LinkedIn email]`
  - Replace with your LinkedIn account email address
- `password: [Your LinkedIn password]`
  - Replace with your LinkedIn account password
- `openai_api_key: [Your OpenAI API key]`
  - Replace with your OpenAI API key for GPT integration
  - To obtain an API key, follow the tutorial at: https://medium.com/@lorenzozar/how-to-get-your-own-openai-api-key-f4d44e60c327
  - Note: You need to add credit to your OpenAI account to use the API. You can add credit by visiting the [OpenAI billing dashboard](https://platform.openai.com/account/billing).



### 2. config.yaml

This file defines your job search parameters and bot behavior. Each section contains options that you can customize:

- `remote: [true/false]`
  - Set to `true` to include remote jobs, `false` to exclude them

- `experienceLevel:`
  - Set desired experience levels to `true`, others to `false`

- `jobTypes:`
  - Set desired job types to `true`, others to `false`

- `date:`
  - Choose one time range for job postings by setting it to `true`, others to `false`


- `positions:`
  - List job titles you're interested in, one per line
  - Example:
    ```yaml
    positions:
      - Software Developer
      - Data Scientist
    ```

- `locations:`
  - List locations you want to search in, one per line
  - Example:
    ```yaml
    locations:
      - Italy
      - London
    ```

- `distance: [number]`
  - Set the radius for your job search in miles
  - Example: `distance: 50`

- `companyBlacklist:`
  - List companies you want to exclude from your search, one per line
  - Example:
    ```yaml
    companyBlacklist:
      - Company X
      - Company Y
    ```

- `titleBlacklist:`
  - List keywords in job titles you want to avoid, one per line
  - Example:
    ```yaml
    titleBlacklist:
      - Sales
      - Marketing
    ```

### 3. plain_text_resume.yaml

This file contains your resume information in a structured format. Fill it out with your personal details, education, work experience, and skills. This information is used to auto-fill application forms and generate customized resumes.

Each section has specific fields to fill out:

- `personal_information:`
  - This section contains basic personal details to identify yourself and provide contact information.
    - **name**: Your first name.
    - **surname**: Your last name or family name.
    - **date_of_birth**: Your birth date in the format DD/MM/YYYY.
    - **country**: The country where you currently reside.
    - **city**: The city where you currently live.
    - **address**: Your full address, including street and number.
    - **phone_prefix**: The international dialing code for your phone number (e.g., +1 for the USA, +44 for the UK).
    - **phone**: Your phone number without the international prefix.
    - **email**: Your primary email address.
    - **github**: URL to your GitHub profile, if applicable.
    - **linkedin**: URL to your LinkedIn profile, if applicable.
  - Example
  ```yaml
  personal_information:
    name: "Jane"
    surname: "Doe"
    date_of_birth: "01/01/1990"
    country: "USA"
    city: "New York"
    address: "123 Main St"
    phone_prefix: "+1"
    phone: "5551234567"
    email: "jane.doe@example.com"
    github: "https://github.com/janedoe"
    linkedin: "https://www.linkedin.com/in/janedoe/"
  ```

- `education_details:`
  - This section outlines your academic background, including degrees earned and relevant coursework.
    - **degree**: The type of degree obtained (e.g., Bachelor's Degree, Master's Degree).
    - **university**: The name of the university or institution where you studied.
    - **gpa**: Your Grade Point Average or equivalent measure of academic performance.
    - **graduation_year**: The year you graduated.
    - **field_of_study**: The major or focus area of your studies.
    - **exam**: A list of courses or subjects taken along with their respective grades.

  - Example:
  ```yaml
  education_details:
    - degree: "Bachelor's Degree"
      university: "University of Example"
      gpa: "3.8/4"
      graduation_year: "2022"
      field_of_study: "Software Engineering"
      exam:
        Algorithms: "A"
        Data Structures: "B+"
        Database Systems: "A"
        Operating Systems: "A-"
        Web Development: "B"
  ```

- `experience_details:`
  - This section details your work experience, including job roles, companies, and key responsibilities.
    - **position**: Your job title or role.
    - **company**: The name of the company or organization where you worked.
    - **employment_period**: The timeframe during which you were employed in the role (e.g., MM/YYYY - MM/YYYY).
    - **location**: The city and country where the company is located.
    - **industry**: The industry or field in which the company operates.
    - **key_responsibilities**: A list of major responsibilities or duties you had in the role.
    - **skills_acquired**: Skills or expertise gained through this role.

  - Example:
  ```yaml
  experience_details:
    - position: "Software Developer"
      company: "Tech Innovations Inc."
      employment_period: "06/2021 - Present"
      location: "San Francisco, CA"
      industry: "Technology"
      key_responsibilities:
        - "Developed web applications using React and Node.js"
        - "Collaborated with cross-functional teams to design and implement new features"
        - "Troubleshot and resolved complex software issues"
      skills_acquired:
        - "React"
        - "Node.js"
        - "Software Troubleshooting"
  ```

- `projects:`
  - Include notable projects you have worked on, including personal or professional projects.
    - **name**: The name or title of the project.
    - **description**: A brief summary of what the project involves or its purpose.
    - **link**: URL to the project, if available (e.g., GitHub repository, website).

   - Example:
    ```yaml
    projects:
      - name: "Weather App"
        description: "A web application that provides real-time weather information using a third-party API."
        link: "https://github.com/janedoe/weather-app"
      - name: "Task Manager"
        description: "A task management tool with features for tracking and prioritizing tasks."
        link: "https://github.com/janedoe/task-manager"
    ```

- `achievements:`
  - Highlight notable accomplishments or awards you have received.
    - **name**: The title or name of the achievement.
    - **description**: A brief explanation of the achievement and its significance.

  - Example:
  ```yaml
  achievements:
    - name: "Employee of the Month"
      description: "Recognized for exceptional performance and contributions to the team."
    - name: "Hackathon Winner"
      description: "Won first place in a national hackathon competition."
  ```

- `certifications:`
  - Include any professional certifications you have earned.
    - **certification_name**: The name of the certification.

  - Example:
  ```yaml
  certifications:
    - "Certified Scrum Master"
    - "AWS Certified Solutions Architect"
  ```

- `languages:`
  - Detail the languages you speak and your proficiency level in each.
    - **language**: The name of the language.
    - **proficiency**: Your level of proficiency (e.g., Native, Fluent, Intermediate).

  - Example:
  ```yaml
  languages:
    - language: "English"
      proficiency: "Fluent"
    - language: "Spanish"
      proficiency: "Intermediate"
  ```

- `interests:`

  - Mention your professional or personal interests that may be relevant to your career.
    - **interest**: A list of interests or hobbies.

  - Example:
  ```yaml
  interests:
    - "Machine Learning"
    - "Cybersecurity"
    - "Open Source Projects"
    - "Digital Marketing"
    - "Entrepreneurship"
  ```

- `availability:`
  - State your current availability or notice period.
    - **notice_period**: The amount of time required before you can start a new role (e.g., "2 weeks", "1 month").

  - Example:
  ```yaml
  availability:
    notice_period: "2 weeks"
  ```

- `salary_expectations:`
  - Provide your expected salary range.
    - **salary_range_usd**: The salary range you are expecting, expressed in USD.

  - Example:
  ```yaml
  salary_expectations:
    salary_range_usd: "80000 - 100000"
  ```

- `self_identification:`
  - Provide information related to personal identity, including gender and pronouns.
    - **gender**: Your gender identity.
    - **pronouns**: The pronouns you use (e.g., He/Him, She/Her, They/Them).
    - **veteran**: Your status as a veteran (e.g., Yes, No).
    - **disability**: Whether you have a disability (e.g., Yes, No).
    - **ethnicity**: Your ethnicity.

  - Example:
  ```yaml
  self_identification:
    gender: "Female"
    pronouns: "She/Her"
    veteran: "No"
    disability: "No"
    ethnicity: "Asian"
  ```

- `legal_authorization:`
  - Indicate your legal ability to work in various locations.
    - **eu_work_authorization**: Whether you are authorized to work in the European Union (Yes/No).
    - **us_work_authorization**: Whether you are authorized to work in the United States (Yes/No).
    - **requires_us_visa**: Whether you require a visa to work in the US (Yes/No).
    - **requires_us_sponsorship**: Whether you require sponsorship to work in the US (Yes/No).
    - **requires_eu_visa**: Whether you require a visa to work in the EU (Yes/No).
    - **legally_allowed_to_work_in_eu**: Whether you are legally allowed to work in the EU (Yes/No).
    - **legally_allowed_to_work_in_us**: Whether you are legally allowed to work in the US (Yes/No).
    - **requires_eu_sponsorship**: Whether you require sponsorship to work in the EU (Yes/No).

  - Example:
     ```yaml
     legal_authorization:
       eu_work_authorization: "Yes"
       us_work_authorization: "No"
       requires_us_visa: "Yes"
       requires_us_sponsorship: "Yes"
       requires_eu_visa: "No"
       legally_allowed_to_work_in_eu: "Yes"
       legally_allowed_to_work_in_us: "No"
       requires_eu_sponsorship: "No"
     ```

- `work_preferences:`
  - Specify your preferences for work arrangements and conditions.
    - **remote_work**: Whether you are open to remote work (Yes/No).
    - **in_person_work**: Whether you are open to in-person work (Yes/No).
    - **open_to_relocation**: Whether you are willing to relocate for a job (Yes/No).
    - **willing_to_complete_assessments**: Whether you are willing to complete job assessments (Yes/No).
    - **willing_to_undergo_drug_tests**: Whether you are willing to undergo drug testing (Yes/No).
    - **willing_to_undergo_background_checks**: Whether you are willing to undergo background checks (Yes/No).

  - Example:
  ```yaml
  work_preferences:
    remote_work: "Yes"
    in_person_work: "No"
    open_to_relocation: "Yes"
    willing_to_complete_assessments: "Yes"
    willing_to_undergo_drug_tests: "No"
    willing_to_undergo_background_checks: "Yes"
  ```

### PLUS. data_folder_example

The `data_folder_example` folder contains a working example of how the files necessary for the bot's operation should be structured and filled out. This folder serves as a practical reference to help you correctly set up your work environment for the LinkedIn job search bot.

#### Contents

Inside this folder, you'll find example versions of the key files:

- `secrets.yaml`
- `config.yaml`
- `plain_text_resume.yaml`

These files are already populated with fictitious but realistic data. They show you the correct format and type of information to enter in each file.

#### Usage

Using this folder as a guide can be particularly helpful for:

1. Understanding the correct structure of each configuration file
2. Seeing examples of valid data for each field
3. Having a reference point while filling out your personal files


## Usage
0. **LinkedIn language**
   To ensure the bot works, your LinkedIn language must be set to English.
   
2. **Data Folder:**
   Ensure that your data_folder contains the following files:
   - `secrets.yaml`
   - `config.yaml`
   - `plain_text_resume.yaml`

3. **Run the Bot:**

   LinkedIn_AIHawk offers flexibility in how it handles your pdf resume:

- **Dynamic Resume Generation:**
  If you don't use the `--resume` option, the bot will automatically generate a unique resume for each application. This feature uses the information from your `plain_text_resume.yaml` file and tailors it to each specific job application, potentially increasing your chances of success by customizing your resume for each position.
   ```bash
   python main.py
   ```
- **Using a Specific Resume:**
  If you want to use a specific PDF resume for all applications, place your resume PDF in the `data_folder` directory and run the bot with the `--resume` option:
  ```bash
  python main.py --resume /path/to/your/resume.pdf
  ```

## Documentation

TODO ):

## Troubleshooting

- **Carefully read logs and output :** Most of the errors are verbosely reflected just watch the output and try to find the root couse. 
- **If nothing works by unknown reason:**  Use tested OS. Reboot and/or update OS.  Use new clean venv. Try update Python to the tested version.  
- **ChromeDriver Issues:** Ensure ChromeDriver is compatible with your installed Chrome version.
- **Missing Files:** Verify that all necessary files are present in the data folder.
- **Invalid YAML:** Check your YAML files for syntax errors . Try to use external YAML validators e.g. https://www.yamllint.com/
- **OpenAI endpoint isues**: Try to check possible limits\blocking at their side 
  
If you encounter any issues, you can open an issue on [GitHub](https://github.com/feder-cr/linkedIn_auto_jobs_applier_with_AI/issues).
  Please add valuable details to the subject and to the description. If you need new feature then please reflect this.  
  I'll be more than happy to assist you!

## Conclusion

LinkedIn_AIHawk provides a significant advantage in the modern job market by automating and enhancing the job application process. With features like dynamic resume generation and AI-powered personalization, it offers unparalleled flexibility and efficiency. Whether you're a job seeker aiming to maximize your chances of landing a job, a recruiter looking to streamline application submissions, or a career advisor seeking to offer better services, LinkedIn_AIHawk is an invaluable resource. By leveraging cutting-edge automation and artificial intelligence, this tool not only saves time but also significantly increases the effectiveness and quality of job applications in today's competitive landscape.

## Contributors

- [feder-cr](https://github.com/feder-cr) - Creator and Lead Developer

LinkedIn_AIHawk is still in beta, and your feedback, suggestions, and contributions are highly valued. Feel free to open issues, suggest enhancements, or submit pull requests to help improve the project. Let's work together to make LinkedIn_AIHawk an even more powerful tool for job seekers worldwide.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer
LinkedIn_AIHawk is developed for educational purposes only. The creator does not assume any responsibility for its use. Users should ensure they comply with LinkedIn's terms of service, any applicable laws and regulations, and ethical considerations when using this tool. The use of automated tools for job applications may have implications on user accounts, and caution is advised.
