import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_all
from core.ragengine import (
    build_rag_chain,
    load_rag_chain,
    ask_question
)

load_dotenv()

CACHE_DIR = "meeting_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def get_meeting_id(source: str) -> str:
    source = source.strip()

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):
        identity = source.lower()
    else:
        if not os.path.exists(source):
            identity = os.path.abspath(source).lower()
        else:
            hasher = hashlib.sha256()

            with open(source, "rb") as file:
                for chunk in iter(
                    lambda: file.read(1024 * 1024),
                    b""
                ):
                    hasher.update(chunk)

            identity = hasher.hexdigest()

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


def get_cache_path(meeting_id: str) -> str:
    return os.path.join(
        CACHE_DIR,
        f"{meeting_id}.json"
    )


def load_cached_meeting(meeting_id: str):
    cache_path = get_cache_path(meeting_id)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(
            cache_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return None


def save_cached_meeting(
    meeting_id: str,
    source: str,
    language: str,
    result: dict
):
    cache_path = get_cache_path(meeting_id)

    cache_data = {
        "meeting_id": meeting_id,
        "source": source,
        "language": language,
        "title": result["title"],
        "transcript": result["transcript"],
        "summary": result["summary"],
        "action_items": result["action_items"],
        "key_decisions": result["key_decisions"],
        "open_questions": result["open_questions"]
    }

    with open(
        cache_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            cache_data,
            file,
            ensure_ascii=False,
            indent=2
        )


def run_analysis_tasks(transcript: str, meeting_id: str):
    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        title_future = executor.submit(
            generate_title,
            transcript
        )

        summary_future = executor.submit(
            summarize,
            transcript
        )

        extraction_future = executor.submit(
            extract_all,
            transcript
        )

        rag_future = executor.submit(
            build_rag_chain,
            transcript,
            meeting_id
        )

        title = title_future.result()
        summary = summary_future.result()
        extracted = extraction_future.result()
        rag_chain = rag_future.result()

    return (
        title,
        summary,
        extracted,
        rag_chain
    )


def run_pipeline(
    source: str,
    language: str = "english"
) -> dict:

    print("Starting AI Video Assistant")

    meeting_id = get_meeting_id(source)

    print(f"Meeting ID: {meeting_id}")

    cached_result = load_cached_meeting(
        meeting_id
    )

    if cached_result:
        print(
            "Cached meeting found."
        )

        print(
            "Loading existing vector store..."
        )

        rag_chain = load_rag_chain(
            meeting_id
        )

        cached_result["rag_chain"] = rag_chain

        return cached_result

    print(
        "No cached meeting found. "
        "Processing from scratch..."
    )

    chunks = process_input(source)

    transcript = transcribe_all(
        chunks,
        language
    )

    print(
        f"Raw transcription "
        f"(first 300 characters): "
        f"{transcript[:300]}"
    )

    print(
        "Running title, summary, extraction, "
        "and RAG tasks in parallel..."
    )

    (
        title,
        summary,
        extracted,
        rag_chain
    ) = run_analysis_tasks(
        transcript,
        meeting_id
    )

    action_items = extracted[
        "action_items"
    ]

    decisions = extracted[
        "decisions"
    ]

    questions = extracted[
        "questions"
    ]

    result = {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain
    }

    save_cached_meeting(
        meeting_id,
        source,
        language,
        result
    )

    print(
        "Meeting analysis cached successfully."
    )

    return result


if __name__ == "__main__":

    source = input(
        "Enter YouTube URL or local file path: "
    ).strip()

    language = input(
        "Language (english/hinglish): "
    ).strip() or "english"

    result = run_pipeline(
        source,
        language
    )

    print("\n" + "=" * 60)

    print(
        f"📌 Title: {result['title']}"
    )

    print(
        f"\n📋 Summary:\n"
        f"{result['summary']}"
    )

    print(
        f"\n✅ Action Items:\n"
        f"{result['action_items']}"
    )

    print(
        f"\n🔑 Key Decisions:\n"
        f"{result['key_decisions']}"
    )

    print(
        f"\n❓ Open Questions:\n"
        f"{result['open_questions']}"
    )

    print("=" * 60)

    print(
        "\n💬 Chat with your meeting "
        "(type 'exit' to quit)\n"
    )

    rag_chain = result["rag_chain"]

    while True:

        question = input(
            "You: "
        ).strip()

        if question.lower() in [
            "exit",
            "quit",
            "q"
        ]:
            print("👋 Goodbye!")
            break

        if not question:
            continue

        answer = ask_question(
            rag_chain,
            question
        )

        print(
            f"\n🤖 Milo: {answer}\n"
        )