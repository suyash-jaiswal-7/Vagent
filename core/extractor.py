from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.2
    )


def build_chain(system_prompt: str):
    llm = get_llm()

    return (
        ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}")
        ])
        | llm
        | StrOutputParser()
    )


def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )

    return splitter.split_text(transcript)


def extract_all(transcript: str) -> dict:
    chunks = split_transcript(transcript)

    extraction_chain = build_chain(
        """
You are an expert meeting analyst.

Analyze the provided portion of a meeting transcript and extract
ONLY information explicitly supported by the transcript.

Extract three categories:

1. ACTION ITEMS

For each action item provide:
- Task description
- Owner (who is responsible)
- Deadline (if mentioned, otherwise "Not specified")

2. DECISIONS

For each decision provide:
- Decision
- Context or reason (if mentioned)
- Owner (if mentioned, otherwise "Not specified")

3. QUESTIONS

For each important question provide:
- Question
- Asked by (if mentioned, otherwise "Not specified")
- Answer or status (if answered, otherwise "Unanswered")

Use exactly this format:

ACTION ITEMS:
- Task: ...
  Owner: ...
  Deadline: ...

DECISIONS:
- Decision: ...
  Context: ...
  Owner: ...

QUESTIONS:
- Question: ...
  Asked by: ...
  Answer/Status: ...

If a category has nothing relevant, write:
None

Do not invent information.
Do not include general statements as action items or decisions.
"""
    )

    chunk_results = []

    for i, chunk in enumerate(chunks):
        print(
            f"Extracting meeting insights "
            f"from chunk {i + 1}/{len(chunks)}..."
        )

        result = extraction_chain.invoke({
            "text": chunk
        })

        chunk_results.append(result)

    combined = "\n\n".join(chunk_results)

    final_chain = build_chain(
        """
You are an expert meeting analyst.

Below are extraction results from different portions of the
same meeting transcript.

Create one clean final result.

Your tasks:

1. Combine duplicate or repeated action items.
2. Combine duplicate or repeated decisions.
3. Combine duplicate or repeated questions.
4. Merge similar items when they refer to the same thing.
5. Preserve owners and deadlines when available.
6. Preserve answers/status for questions when available.
7. Do not invent information.

Return exactly these three sections:

ACTION ITEMS:
1. Task: ...
   Owner: ...
   Deadline: ...

DECISIONS:
1. Decision: ...
   Context: ...
   Owner: ...

QUESTIONS:
1. Question: ...
   Asked by: ...
   Answer/Status: ...

If a section has no items, write:
None

Only include information supported by the provided extraction results.
"""
    )

    final_result = final_chain.invoke({
        "text": combined
    })

    return parse_extraction_result(final_result)


def parse_extraction_result(result: str) -> dict:
    sections = {
        "action_items": "None",
        "decisions": "None",
        "questions": "None"
    }

    current_section = None

    for line in result.splitlines():
        line = line.strip()

        if not line:
            continue

        upper_line = line.upper()

        if upper_line.startswith("ACTION ITEMS:"):
            current_section = "action_items"
            continue

        if upper_line.startswith("DECISIONS:"):
            current_section = "decisions"
            continue

        if upper_line.startswith("QUESTIONS:"):
            current_section = "questions"
            continue

        if current_section:
            if sections[current_section] == "None":
                sections[current_section] = line
            else:
                sections[current_section] += "\n" + line

    return sections


def extract_action_items(transcript: str) -> str:
    return extract_all(transcript)["action_items"]


def extract_decisions(transcript: str) -> str:
    return extract_all(transcript)["decisions"]


def extract_questions(transcript: str) -> str:
    return extract_all(transcript)["questions"]