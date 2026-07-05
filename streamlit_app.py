import html
import json
import random
from pathlib import Path

import streamlit as st

QUESTIONS_PATH = Path(__file__).with_name("questions.json")
CHAPTERS_PATH = Path(__file__).with_name("chapters.json")
FLASHCARDS_PATH = Path(__file__).with_name("flashcards.json")
FLAGS_PATHS = [Path(__file__).with_name("flag.json"), Path(__file__).with_name("flags.json")]


def load_questions(path: Path | None = None) -> list[dict]:
    path = path or QUESTIONS_PATH
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_chapters(path: Path | None = None) -> list[dict]:
    path = path or CHAPTERS_PATH
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_flashcards(path: Path | None = None) -> list[dict]:
    path = path or FLASHCARDS_PATH
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_flags(path: Path | None = None) -> list[dict]:
    if path is None:
        for candidate in FLAGS_PATHS:
            if candidate.exists():
                path = candidate
                break
        if path is None:
            path = FLAGS_PATHS[0]

    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        if isinstance(payload.get("flags"), list):
            return payload["flags"]
        if isinstance(payload.get("items"), list):
            return payload["items"]
    if isinstance(payload, list):
        return payload
    return []


def get_subject_options(chapters: list[dict]) -> list[str]:
    return sorted({chapter.get("subject", "Unknown") for chapter in chapters if chapter.get("subject")})


def get_filtered_chapter_options(chapters: list[dict], selected_subjects: list[str] | None = None) -> list[str]:
    if not selected_subjects:
        return [chapter["id"] for chapter in chapters]
    return [chapter["id"] for chapter in chapters if chapter.get("subject") in selected_subjects]


def build_quiz_session(
    questions: list[dict],
    chapters: list[dict],
    selected_chapters: list[str] | None = None,
    total_questions: int | None = None,
) -> dict:
    chapter_lookup = {chapter["id"]: chapter.get("subject", "Unknown") for chapter in chapters}
    selected = selected_chapters or list(chapter_lookup)

    filtered_questions = [
        question for question in questions if question.get("chapter") in selected
    ]

    unique_questions: list[dict] = []
    seen_ids: set[int] = set()
    for question in filtered_questions:
        question_id = question.get("id")
        if question_id not in seen_ids:
            unique_questions.append(question)
            seen_ids.add(question_id)

    if not unique_questions:
        return {
            "questions": [],
            "selected_chapters": selected,
            "chapter_lookup": chapter_lookup,
        }

    if total_questions is None:
        total_questions = len(unique_questions)

    total_questions = min(total_questions, len(unique_questions))
    shuffled_questions = unique_questions[:]
    random.shuffle(shuffled_questions)

    return {
        "questions": shuffled_questions[:total_questions],
        "selected_chapters": selected,
        "chapter_lookup": chapter_lookup,
    }


def build_flag_quiz_session(flags: list[dict], total_questions: int | None = None) -> dict:
    unique_flags: list[dict] = []
    seen_countries: set[str] = set()
    for flag in flags:
        country = flag.get("country")
        if country and country not in seen_countries:
            unique_flags.append(flag)
            seen_countries.add(country)

    if not unique_flags:
        return {"flags": []}

    if total_questions is None:
        total_questions = len(unique_flags)

    total_questions = min(total_questions, len(unique_flags))
    shuffled_flags = unique_flags[:]
    random.shuffle(shuffled_flags)

    return {"flags": shuffled_flags[:total_questions]}


def reset_quiz_state() -> None:
    for key in ["quiz", "flag_quiz", "player_name", "current_index", "responses", "show_feedback", "last_response"]:
        st.session_state.pop(key, None)
    st.session_state.mode = "quiz"


def render_flashcard(content: str, title: str, subtitle: str | None = None) -> None:
    escaped_content = html.escape(content)
    escaped_title = html.escape(title)
    subtitle_html = f"<div class='flashcard-subtitle'>{html.escape(subtitle)}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="flashcard-shell">
            <div class="flashcard-tag">{escaped_title}</div>
            {subtitle_html}
            <div class="flashcard-body">{escaped_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Quiz App", page_icon="🧠", layout="wide")
st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f8faff 0%, #f2f6ff 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1100px;
        }
        [data-testid="stForm"] {
            background: white;
            border: 1px solid #e2eafc;
            border-radius: 22px;
            padding: 1.1rem 1.2rem 0.8rem;
            box-shadow: 0 10px 25px rgba(74, 96, 162, 0.08);
        }
        .flashcard-shell {
            background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
            border: 1px solid #c9d8ff;
            border-radius: 24px;
            box-shadow: 0 12px 35px rgba(56, 88, 167, 0.16);
            padding: 1.25rem 1.25rem 1.4rem;
            margin: 0.4rem 0 1rem;
            min-height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .flashcard-tag {
            display: inline-block;
            width: fit-content;
            background: #4f6ef7;
            color: white;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            margin-bottom: 0.7rem;
            text-transform: uppercase;
        }
        .flashcard-subtitle {
            color: #5b6b8a;
            font-size: 0.95rem;
            margin-bottom: 0.8rem;
            font-weight: 600;
        }
        .flashcard-body {
            font-size: 1.15rem;
            line-height: 1.6;
            color: #21314d;
            font-weight: 500;
            word-break: break-word;
        }
        div.stButton > button {
            border-radius: 999px;
            padding: 0.5rem 1rem;
            border: 1px solid #d2dcff;
            background: white;
            color: #3554c7;
            font-weight: 600;
            width: 100%;
        }
        div.stButton > button:hover {
            border-color: #4f6ef7;
            background: #eef3ff;
        }
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }
            .flashcard-shell {
                min-height: 220px;
                padding: 1rem;
                border-radius: 18px;
            }
            .flashcard-body {
                font-size: 1rem;
            }
            div.stButton > button {
                padding: 0.6rem 0.8rem;
                margin-top: 0.25rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("🧠 Quiz App")
st.write("Take a chapter-based quiz with randomized questions and instant scoring.")


if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "flag_quiz" not in st.session_state:
    st.session_state.flag_quiz = None
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "mode" not in st.session_state:
    st.session_state.mode = "quiz"
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "show_back" not in st.session_state:
    st.session_state.show_back = False


if st.session_state.quiz is None and st.session_state.mode == "quiz":
    chapters = load_chapters()
    questions = load_questions()
    subject_options = get_subject_options(chapters)

    with st.form("start_quiz"):
        st.write("Choose how you want to study:")
        mode = st.radio("Mode", ["quiz", "flashcards", "flag_quiz"], horizontal=True, index=0)
        player_name = st.text_input(
            "Your name",
            value=st.session_state.player_name or "Anvitha",
        )

        selected_subjects: list[str] = []
        selected_chapters: list[str] = []

        if mode == "flag_quiz":
            st.info("This mode shows a flag and asks you to guess the country name.")
            available_question_count = max(1, len(load_flags()))
            question_count = st.number_input(
                "Number of flags",
                min_value=1,
                max_value=available_question_count,
                value=min(10, available_question_count),
                step=1,
            )
        else:
            selected_subjects = st.multiselect(
                "Select subjects",
                options=subject_options,
                default=subject_options,
                help="Choose one or more subjects to narrow the chapter list.",
            )
            chapter_options = get_filtered_chapter_options(chapters, selected_subjects)
            selected_chapters = st.multiselect(
                "Select chapters",
                options=chapter_options,
                default=chapter_options,
                help="Only questions from the selected chapters will be included in the quiz.",
            )
            if selected_subjects or selected_chapters:
                selected_labels = [f"{chapter['subject']}: {chapter['id']}" for chapter in chapters if chapter["id"] in selected_chapters]
                st.caption(f"Filtering by: {', '.join(selected_labels) if selected_labels else 'No chapters selected'}")
            available_question_count = max(1, sum(1 for question in questions if question.get("chapter") in selected_chapters))
            question_count = st.number_input(
                "Number of questions",
                min_value=1,
                max_value=available_question_count,
                value=min(10, available_question_count),
                step=1,
            )

        submitted = st.form_submit_button("Start")

        if submitted:
            if not player_name.strip():
                st.error("Please enter your name before starting.")
            elif mode == "quiz" and not selected_chapters:
                st.error("Select at least one chapter to begin.")
            else:
                if mode == "flashcards":
                    flashcards = load_flashcards()
                    if not flashcards:
                        st.error("No flashcards are available.")
                    else:
                        st.session_state.mode = "flashcards"
                        st.session_state.flashcards = flashcards
                        st.session_state.flashcard_index = 0
                        st.session_state.show_back = False
                        st.session_state.player_name = player_name.strip()
                        st.rerun()
                elif mode == "flag_quiz":
                    flags = load_flags()
                    if not flags:
                        st.error("No flag quiz data is available.")
                    else:
                        flag_quiz_session = build_flag_quiz_session(
                            flags=flags,
                            total_questions=int(question_count),
                        )
                        if not flag_quiz_session["flags"]:
                            st.error("No flags are available for the selected quiz.")
                        else:
                            st.session_state.mode = "flag_quiz"
                            st.session_state.flag_quiz = flag_quiz_session
                            st.session_state.player_name = player_name.strip()
                            st.session_state.current_index = 0
                            st.session_state.responses = []
                            st.session_state.show_feedback = False
                            st.session_state.last_response = None
                            st.session_state.quiz = None
                            st.rerun()
                else:
                    quiz_session = build_quiz_session(
                        questions=questions,
                        chapters=chapters,
                        selected_chapters=selected_chapters,
                        total_questions=int(question_count),
                    )
                    if not quiz_session["questions"]:
                        st.error("No questions are available for the selected chapters.")
                    else:
                        st.session_state.mode = "quiz"
                        st.session_state.quiz = quiz_session
                        st.session_state.player_name = player_name.strip()
                        st.session_state.current_index = 0
                        st.session_state.responses = []
                        st.session_state.show_feedback = False
                        st.session_state.last_response = None
                        st.rerun()

elif st.session_state.mode == "flashcards":
    flashcards = st.session_state.flashcards
    if not flashcards:
        flashcards = load_flashcards()
        st.session_state.flashcards = flashcards

    if st.session_state.flashcard_index >= len(flashcards):
        st.success(f"{st.session_state.player_name}, you finished the flashcards!")
        if st.button("Start again"):
            st.session_state.flashcard_index = 0
            st.session_state.show_back = False
            st.rerun()
    else:
        card = flashcards[st.session_state.flashcard_index]
        st.subheader(f"Welcome, {st.session_state.player_name}")
        st.caption(f"Subject: {card.get('chapter', 'Unknown')}")
        st.write(f"Flashcard {st.session_state.flashcard_index + 1} of {len(flashcards)}")

        if st.session_state.show_back:
            render_flashcard(
                card.get("back", "No answer available."),
                title="Answer",
                subtitle=f"{st.session_state.flashcard_index + 1} of {len(flashcards)} • {card.get('chapter', 'Unknown')}",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Next"):
                    st.session_state.flashcard_index += 1
                    st.session_state.show_back = False
                    st.rerun()
            with col2:
                if st.button("Previous"):
                    if st.session_state.flashcard_index > 0:
                        st.session_state.flashcard_index -= 1
                        st.session_state.show_back = False
                        st.rerun()
        else:
            render_flashcard(
                card.get("front", "No prompt available."),
                title="Question",
                subtitle=f"{st.session_state.flashcard_index + 1} of {len(flashcards)} • {card.get('chapter', 'Unknown')}",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Show answer"):
                    st.session_state.show_back = True
                    st.rerun()
            with col2:
                if st.button("Back to quiz"):
                    st.session_state.mode = "quiz"
                    st.session_state.quiz = None
                    st.rerun()

elif st.session_state.mode == "flag_quiz":
    flag_quiz_session = st.session_state.flag_quiz
    player_name = st.session_state.player_name
    responses = st.session_state.responses

    if st.session_state.current_index >= len(flag_quiz_session["flags"]):
        correct_answers = sum(1 for response in responses if response["is_correct"])
        total_questions = len(flag_quiz_session["flags"])
        percentage = round((correct_answers / total_questions) * 100, 1) if total_questions else 0.0

        st.success(f"{player_name}, your flag quiz is complete!")
        st.metric("Score", f"{correct_answers}/{total_questions}")
        st.metric("Percentage", f"{percentage}%")

        st.subheader("Results")
        for index, response in enumerate(responses, start=1):
            if response["skipped"]:
                status = "⏭️ Skipped"
            elif response["is_correct"]:
                status = "✅ Correct"
            else:
                status = "❌ Incorrect"

            st.write(f"{index}. {response['question']}")
            st.write(f"   Status: {status}")
            st.write(f"   Your answer: {response['selected'] or 'No answer'}")
            st.write(f"   Correct answer: {response['correct_answer']}")
            st.write("")

        if st.button("Start a new flag quiz"):
            reset_quiz_state()
            st.rerun()
    else:
        current_flag = flag_quiz_session["flags"][st.session_state.current_index]

        if st.session_state.show_feedback:
            response = st.session_state.last_response
            if response["skipped"]:
                st.info("You skipped this flag.")
            elif response["is_correct"]:
                st.success("Correct answer!")
            else:
                st.error("That answer was not correct.")

            st.write(f"Your answer: {response['selected'] or 'No answer'}")
            st.write(f"Correct answer: {response['correct_answer']}")

            if st.button("Next flag"):
                st.session_state.show_feedback = False
                st.session_state.last_response = None
                st.session_state.current_index += 1
                st.rerun()
            st.stop()

        st.subheader(f"Welcome, {player_name}")
        st.caption("Guess the country for each flag.")
        st.write(f"Flag {st.session_state.current_index + 1} of {len(flag_quiz_session['flags'])}")
        image_url = current_flag.get("flag_url") or current_flag.get("image_url")
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            st.warning("No flag image is available for this entry.")

        guess = st.text_input(
            "Type the country name",
            key=f"flag_guess_{st.session_state.current_index}",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Submit answer"):
                if not guess.strip():
                    st.warning("Please type a country name or use Skip flag.")
                else:
                    normalized_guess = guess.strip().lower()
                    normalized_answer = current_flag.get("country", "").strip().lower()
                    response = {
                        "question": "Which country does this flag belong to?",
                        "selected": guess.strip(),
                        "correct_answer": current_flag.get("country", "Unknown"),
                        "chapter": "Flags",
                        "skipped": False,
                        "is_correct": normalized_guess == normalized_answer,
                    }
                    responses.append(response)
                    st.session_state.responses = responses
                    st.session_state.last_response = response
                    st.session_state.show_feedback = True
                    st.rerun()

        with col2:
            if st.button("Skip flag"):
                response = {
                    "question": "Which country does this flag belong to?",
                    "selected": None,
                    "correct_answer": current_flag.get("country", "Unknown"),
                    "chapter": "Flags",
                    "skipped": True,
                    "is_correct": False,
                }
                responses.append(response)
                st.session_state.responses = responses
                st.session_state.last_response = response
                st.session_state.show_feedback = True
                st.rerun()

        with col3:
            if st.button("Back to main menu"):
                reset_quiz_state()
                st.rerun()
else:
    quiz_session = st.session_state.quiz
    player_name = st.session_state.player_name
    responses = st.session_state.responses

    if st.session_state.current_index >= len(quiz_session["questions"]):
        correct_answers = sum(1 for response in responses if response["is_correct"])
        total_questions = len(quiz_session["questions"])
        percentage = round((correct_answers / total_questions) * 100, 1) if total_questions else 0.0

        st.success(f"{player_name}, your quiz is complete!")
        st.metric("Score", f"{correct_answers}/{total_questions}")
        st.metric("Percentage", f"{percentage}%")

        st.subheader("Results")
        for index, response in enumerate(responses, start=1):
            if response["skipped"]:
                status = "⏭️ Skipped"
            elif response["is_correct"]:
                status = "✅ Correct"
            else:
                status = "❌ Incorrect"

            st.write(f"{index}. {response['question']}")
            st.write(f"   Status: {status}")
            st.write(f"   Your answer: {response['selected'] or 'No answer'}")
            st.write(f"   Correct answer: {response['correct_answer']}")
            st.write(f"   Chapter: {response['chapter']}")
            st.write("")

        if st.button("Start a new quiz"):
            reset_quiz_state()
            st.rerun()
    else:
        current_question = quiz_session["questions"][st.session_state.current_index]

        if st.session_state.show_feedback:
            response = st.session_state.last_response
            if response["skipped"]:
                st.info("You skipped this question.")
            elif response["is_correct"]:
                st.success("Correct answer!")
            else:
                st.error("That answer was not correct.")

            st.write(f"Your answer: {response['selected'] or 'No answer'}")
            st.write(f"Correct answer: {response['correct_answer']}")
            explanation = current_question.get("explanation") or "No explanation available for this question."
            st.write(f"Explanation: {explanation}")

            if st.button("Next question"):
                st.session_state.show_feedback = False
                st.session_state.last_response = None
                st.session_state.current_index += 1
                st.rerun()
            st.stop()

        st.subheader(f"Welcome, {player_name}")
        st.caption(
            f"Subject: {quiz_session['chapter_lookup'].get(current_question['chapter'], 'Unknown')}"
            f" • Chapter: {current_question['chapter']}"
        )
        st.write(f"Question {st.session_state.current_index + 1} of {len(quiz_session['questions'])}")
        st.write(current_question["question"])

        selected_choice = st.radio(
            "Choose one answer",
            current_question["choices"],
            key=f"choice_{st.session_state.current_index}",
            index=None,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Submit answer"):
                if selected_choice is None:
                    st.warning("Please choose an answer or use Skip question.")
                else:
                    response = {
                        "question": current_question["question"],
                        "selected": selected_choice,
                        "correct_answer": current_question["answer"],
                        "chapter": current_question["chapter"],
                        "skipped": False,
                        "is_correct": selected_choice == current_question["answer"],
                    }
                    responses.append(response)
                    st.session_state.responses = responses
                    st.session_state.last_response = response
                    st.session_state.show_feedback = True
                    st.rerun()

        with col2:
            if st.button("Skip question"):
                response = {
                    "question": current_question["question"],
                    "selected": None,
                    "correct_answer": current_question["answer"],
                    "chapter": current_question["chapter"],
                    "skipped": True,
                    "is_correct": False,
                }
                responses.append(response)
                st.session_state.responses = responses
                st.session_state.last_response = response
                st.session_state.show_feedback = True
                st.rerun()

        with col3:
            if st.button("End quiz"):
                st.session_state.current_index = len(quiz_session["questions"])
                st.rerun()
