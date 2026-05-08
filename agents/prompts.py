# prompts.py

STRUCTURE_PROMPT = """
You are a legal AI specialist. Your task is to extract a structured legal position from the provided text segment.

### Text to Analyze:
{text}

### Instructions:
1.  **Extract the Core Legal Position (Teza)**: A concise, high-level legal rule or conclusion.
2.  **Summarize the Case Circumstances (Обставини справи)**: Briefly describe what happened in the case.
3.  **Extract Legal Reasoning (Правовий висновок)**: The specific justification or article of law applied.
4.  **Extract Identifiers strictly from the text**:
    - **Case Number**: The number is ALWAYS in the very first line of the text, usually in parentheses like (№ 12345/67). DO NOT use case numbers mentioned later in the legal reasoning (these are often citations).
    - **Decision Date**: Look for the date at the very end of the text (e.g. "10 жовтня 2024 року"). Convert to YYYY-MM-DD.
    - **Court**: Identify the specific court (e.g. Європейський суд з прав людини).
    - **URL**: The link is ALWAYS in the very first line of the text, inside a markdown link: [Title](URL). Extract the FULL URL part.
5.  **Assign Category**: Use the provided context ({category}).

### Output JSON Format (STRICT ADHERENCE REQUIRED):
{{
  "category": "...",
  "teza": "...",
  "summary": "...",
  "circumstances": "...",
  "reasoning": "...",
  "case_number": "...",
  "date": "YYYY-MM-DD",
  "url": "...",
  "metadata": {{
    "court": "...",
    "source_digest": "{source}"
  }}
}}

### CRITICAL RULES:
1. Return ONLY the JSON object. Do NOT include any preamble, explanations, or extra fields.
2. Every field in the template above MUST be present.
3. Use ONLY information present in the provided text.
4. If a specific identifier (like case_number, date, or url) is not found in the text, use "N/A".
5. DO NOT copy example values from these instructions (like 'YYYY-MM-DD' or 'XXXX/XX').
6. Ensure the JSON is valid and properly escaped.
7. Respond strictly in Ukrainian.
"""

SEGMENT_PROMPT = """
You are an expert legal document analyst. Your task is to analyze the provided text and split it into individual, semantically complete "legal articles" or "case summaries".

### CRITICAL INSTRUCTION:
Do NOT rely solely on headers or numbering. A single section or paragraph block might contain:
1. One distinct legal position.
2. Multiple distinct legal positions (each should be a separate article).
3. Purely introductory text or noise (should be ignored).

### Semantic Grouping Rule:
Each "article" must be a self-contained legal unit that includes:
- The case identifier (if present).
- The circumstances of the case.
- The court's reasoning and final conclusion (the "teza").

If a block of text discusses two different cases or two unrelated legal points, you MUST split them into two separate strings in the output list.

### Text to Analyze:
{text}

### Output Format:
Return a JSON list of strings. Each string must contain the FULL text of one identified legal article.
Example:
[
  "Text of the first identified legal article...",
  "Text of the second identified legal article...",
  ...
]

If no valid legal articles are found, return an empty list [].
"""
