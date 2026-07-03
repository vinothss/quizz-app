import json
import random
from pathlib import Path

import streamlit as st

QUESTIONS_PATH = Path(__file__).with_name("questions.json")
CHAPTERS_PATH = Path(__file__).with_name("chapters.json")


def load_questions(path: Path | None = None) -> list[dict]:
    path = path or QUESTIONS_PATH
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_chapters(path: Path | None = None) -> list[dict]:
    path = path or CHAPTERS_PATH
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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


def reset_quiz_state() -> None:
    for key in ["quiz", "player_name", "current_index", "responses", "show_feedback", "last_response"]:
        st.session_state.pop(key, None)


st.set_page_config(page_title="Quiz App", page_icon="🧠", layout="centered")
st.title("🧠 Quiz App")
st.write("Take a chapter-based quiz with randomized questions and instant scoring.")


if "quiz" not in st.session_state:
    st.session_state.quiz = None
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


if st.session_state.quiz is None:
    chapters = load_chapters()
    chapter_options = [chapter["id"] for chapter in chapters]
    questions = load_questions()

    with st.form("start_quiz"):
        player_name = st.text_input("Your name", value=st.session_state.player_name)
        selected_chapters = st.multiselect(
            "Select chapters",
            options=chapter_options,
            default=chapter_options,
            help="Questions will be drawn from the selected chapters only.",
        )
        available_question_count = max(1, sum(1 for question in questions if question.get("chapter") in selected_chapters))
        question_count = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=available_question_count,
            value=min(5, available_question_count),
            step=1,
        )
        submitted = st.form_submit_button("Start quiz")

        if submitted:
            if not player_name.strip():
                st.error("Please enter your name before starting.")
            elif not selected_chapters:
                st.error("Select at least one chapter to begin.")
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
                    st.session_state.quiz = quiz_session
                    st.session_state.player_name = player_name.strip()
                    st.session_state.current_index = 0
                    st.session_state.responses = []
                    st.session_state.show_feedback = False
                    st.session_state.last_response = None
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
            "Chapter: "
            f"{current_question['chapter']}"
            f" • Subject: {quiz_session['chapter_lookup'].get(current_question['chapter'], 'Unknown')}"
        )
        st.write(f"Question {st.session_state.current_index + 1} of {len(quiz_session['questions'])}")
        st.write(current_question["question"])

        selected_choice = st.radio(
            "Choose one answer",
            current_question["choices"],
            key=f"choice_{st.session_state.current_index}",
            index=None,
        )

        col1, col2 = st.columns(2)
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
