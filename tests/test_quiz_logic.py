import json
from pathlib import Path

from streamlit_app import build_quiz_session, load_questions, load_chapters, get_filtered_chapter_options


def test_build_quiz_session_uses_unique_randomized_questions(tmp_path):
    questions_path = tmp_path / "questions.json"
    chapters_path = tmp_path / "chapters.json"

    questions = [
        {"id": 1, "question": "Q1", "choices": ["A", "B", "C", "D"], "answer": "A", "chapter": "Alpha"},
        {"id": 2, "question": "Q2", "choices": ["A", "B", "C", "D"], "answer": "A", "chapter": "Alpha"},
        {"id": 3, "question": "Q3", "choices": ["A", "B", "C", "D"], "answer": "A", "chapter": "Beta"},
    ]
    chapters = [{"id": "Alpha", "subject": "Math"}, {"id": "Beta", "subject": "Science"}]

    questions_path.write_text(json.dumps(questions), encoding="utf-8")
    chapters_path.write_text(json.dumps(chapters), encoding="utf-8")

    loaded_questions = load_questions(questions_path)
    loaded_chapters = load_chapters(chapters_path)
    session = build_quiz_session(loaded_questions, loaded_chapters, selected_chapters=["Alpha"], total_questions=2)

    assert len(session["questions"]) == 2
    assert len({q["id"] for q in session["questions"]}) == 2
    assert all(q["chapter"] == "Alpha" for q in session["questions"])


def test_build_quiz_session_honors_requested_question_count(tmp_path):
    questions_path = tmp_path / "questions.json"
    chapters_path = tmp_path / "chapters.json"

    questions = [
        {"id": 1, "question": "Q1", "choices": ["A", "B", "C", "D"], "answer": "A", "chapter": "Alpha"},
        {"id": 2, "question": "Q2", "choices": ["A", "B", "C", "D"], "answer": "A", "chapter": "Alpha"},
        {"id": 3, "question": "Q3", "choices": ["A", "B", "C", "D"], "answer": "A", "chapter": "Beta"},
    ]
    chapters = [{"id": "Alpha", "subject": "Math"}, {"id": "Beta", "subject": "Science"}]

    questions_path.write_text(json.dumps(questions), encoding="utf-8")
    chapters_path.write_text(json.dumps(chapters), encoding="utf-8")

    loaded_questions = load_questions(questions_path)
    loaded_chapters = load_chapters(chapters_path)
    session = build_quiz_session(loaded_questions, loaded_chapters, selected_chapters=["Alpha", "Beta"], total_questions=1)

    assert len(session["questions"]) == 1


def test_get_filtered_chapter_options_uses_selected_subjects():
    chapters = [{"id": "Alpha", "subject": "Math"}, {"id": "Beta", "subject": "Science"}]

    assert get_filtered_chapter_options(chapters, selected_subjects=["Science"]) == ["Beta"]
