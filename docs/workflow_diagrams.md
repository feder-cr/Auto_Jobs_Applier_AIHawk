# Dev diagrams

Note: All diagrams are created using [Mermaid](https://mermaid.js.org/).

## 1. Application flow

```mermaid
graph TD
    A[Start] --> B[Parse Command Line Arguments]
    B --> C[Validate Data Folder]
    C --> D[Load Configuration]
    D --> E[Initialize Components]
    E --> F{Collect Mode?}
    F -->|Yes| G[Collect Job Data]
    F -->|No| H[Start Job Application Process]
    G --> I[Save Data to JSON]
    H --> J[Login to AIHawk]
    J --> K[Search for Jobs]
    K --> L[Apply to Jobs]
    L --> M[Generate Reports]
    I --> N[End]
    M --> N
```

## 2. Job application process

```mermaid
sequenceDiagram
    participant User
    participant AIHawkBot
    participant AIHawk
    participant GPTAnswerer
    participant ResumeGenerator

    User->>AIHawkBot: Start application process
    AIHawkBot->>AIHawk: Login
    AIHawkBot->>AIHawk: Search for jobs
    loop For each job
        AIHawkBot->>AIHawk: Open job listing
        AIHawkBot->>GPTAnswerer: Generate answers for application questions
        AIHawkBot->>ResumeGenerator: Generate tailored resume
        AIHawkBot->>AIHawk: Fill application form
        AIHawkBot->>AIHawk: Upload resume and cover letter
        AIHawkBot->>AIHawk: Submit application
        AIHawkBot->>AIHawkBot: Log application result
    end
    AIHawkBot->>User: Display application summary
```

## 3. Resume generation process

```mermaid
graph TD
    A[Start Resume Generation] --> B[Extract Job Description]
    B --> C[Analyze Job Requirements]
    C --> D[Retrieve User Profile]
    D --> E[Generate Tailored Content]
    E --> F[Create PDF Resume]
    F --> G[Return Base64 Encoded PDF]
    G --> H[End Resume Generation]
```

## 4. GPTAnswerer workflow

```mermaid
graph LR
    A[Receive Question] --> B[Prepare Prompt]
    B --> C[Send to LLM Model]
    C --> D[Receive Response]
    D --> E[Parse Response]
    E --> F[Return Formatted Answer]
```
