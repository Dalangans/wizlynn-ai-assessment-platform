import json
import os
import re
from datetime import datetime, timezone
from io import BytesIO

from anthropic import AsyncAnthropic
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from pypdf import PdfReader

from database import exam_key_from_goal, has_assessment_attempt, init_db, save_exam_attempt


load_dotenv()

app = FastAPI(title="Wizlynn Assessment MVP")
init_db()


class KnowledgeRequest(BaseModel):
    source_text: str


class QuestionRequest(BaseModel):
    knowledge_points: list[dict]
    target_role: str
    topic_focus: str
    difficulty: str
    exam_mode: str = "practice"
    deadline: str = ""


class SubmitExamRequest(BaseModel):
    employee: dict
    exam_goal: dict
    knowledge_points: list[dict]
    questions: list[dict]
    answers: dict


def extract_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if not match:
            raise ValueError("AI response did not contain JSON.")
        return json.loads(match.group(1))


def normalize_questions(payload):
    if isinstance(payload, dict):
        payload = payload.get("questions") or payload.get("data") or payload.get("items")
    if not isinstance(payload, list):
        raise ValueError("AI question response must be a list of questions.")

    normalized = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue

        question_type = item.get("type") or item.get("questionType") or "multiple_choice"
        if question_type in ["mcq", "multiple-choice", "multiple choice"]:
            question_type = "multiple_choice"
        if question_type in ["essay", "short_essay", "short essay", "subjective"]:
            question_type = "open_ended"

        options = item.get("options") or []
        if isinstance(options, dict):
            options = list(options.values())
        if not isinstance(options, list):
            options = []

        normalized.append(
            {
                "id": item.get("id") or f"q-{index}",
                "knowledgePointId": item.get("knowledgePointId") or item.get("knowledge_point_id") or "",
                "type": question_type,
                "prompt": item.get("prompt") or item.get("question") or "",
                "options": options,
                "correctAnswer": item.get("correctAnswer") or item.get("correct_answer") or "",
                "rubric": item.get("rubric") or "",
                "status": "draft",
            }
        )

    if not normalized:
        raise ValueError("AI did not return any valid questions.")
    if not any(item["type"] == "open_ended" for item in normalized):
        raise ValueError("AI must return at least one open-ended question.")
    return normalized


def normalize_source_summary(payload, source_text: str):
    if isinstance(payload, list):
        if payload and isinstance(payload[0], dict):
            payload = payload[0]
        else:
            payload = {
                "summary": " ".join(str(item) for item in payload[:6]),
                "mainTopics": [str(item) for item in payload[:10]],
                "recommendedAssessmentFocus": "Use the summarized source material to assess the employee's understanding.",
                "assessmentSourceText": " ".join(str(item) for item in payload),
            }

    if not isinstance(payload, dict):
        payload = {
            "summary": str(payload),
            "mainTopics": [],
            "recommendedAssessmentFocus": "Use the summarized source material to assess the employee's understanding.",
            "assessmentSourceText": str(payload),
        }

    topics = payload.get("mainTopics") or payload.get("main_topics") or []
    if isinstance(topics, list):
        topics_text = ", ".join(str(item) for item in topics)
    else:
        topics_text = str(topics)

    summary = payload.get("summary") or payload.get("documentSummary") or ""
    assessment_focus = (
        payload.get("recommendedAssessmentFocus")
        or payload.get("recommended_assessment_focus")
        or "Use the summarized source material to assess the employee's understanding."
    )
    assessment_source_text = (
        payload.get("assessmentSourceText")
        or payload.get("assessment_source_text")
        or summary
        or source_text[:4000]
    )

    return summary, topics_text, assessment_focus, assessment_source_text


async def call_json_ai(prompt: str):
    ai_text = await call_anthropic(prompt)
    try:
        return extract_json(ai_text)
    except Exception:
        repair_prompt = f"""
Convert the following AI output into valid JSON only.
Do not add markdown or explanation.

AI OUTPUT:
{ai_text}
"""
        repaired_text = await call_anthropic(repair_prompt)
        return extract_json(repaired_text)


async def call_anthropic(prompt: str) -> str:
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    model = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6").strip()

    if not base_url or not token:
        raise RuntimeError("Missing ANTHROPIC_BASE_URL or ANTHROPIC_AUTH_TOKEN.")

    client = AsyncAnthropic(
        api_key=token,
        base_url=base_url.rstrip("/"),
    )
    message = await client.messages.create(
        model=model,
        max_tokens=1600,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return "\n".join(
        block.text for block in message.content if getattr(block, "type", "") == "text"
    ).strip()


def extract_text_from_file(filename: str, content: bytes) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError("No readable text found in PDF.")
        return text

    if lower_name.endswith((".txt", ".md", ".csv")):
        return content.decode("utf-8", errors="ignore").strip()

    return content.decode("utf-8", errors="ignore").strip()


async def summarize_source_text(source_text: str) -> tuple[str, str, str, str]:
    prompt = f"""
Summarize this business source material for an assessment manager.
Return JSON only with exactly these fields:
summary, mainTopics, recommendedAssessmentFocus, assessmentSourceText.

Rules:
- summary must be 4-6 sentences
- mainTopics must be an array of 5-10 short strings
- recommendedAssessmentFocus must be one sentence
- assessmentSourceText must be a concise but complete source text for downstream knowledge extraction
- assessmentSourceText must cover the whole uploaded material, not only the beginning
- assessmentSourceText should be 800-1500 words when possible
- do not include markdown

SOURCE MATERIAL:
{source_text[:50000]}
"""
    ai_text = await call_anthropic(prompt)
    result = extract_json(ai_text)
    return normalize_source_summary(result, source_text)


async def score_open_ended_answer(question: dict, answer: str, knowledge_point: dict | None):
    prompt = f"""
Score this open-ended exam answer.
Return JSON only with exactly these fields:
score, aiRationale.

Rules:
- score must be a number from 0 to 1
- aiRationale must explain why the score was given
- do not include markdown

QUESTION:
{json.dumps(question, indent=2)}

RELATED KNOWLEDGE POINT:
{json.dumps(knowledge_point or {}, indent=2)}

EMPLOYEE ANSWER:
{answer}
"""
    try:
        ai_text = await call_anthropic(prompt)
        result = extract_json(ai_text)
        return {
            "score": float(result.get("score", 0)),
            "aiRationale": result.get("aiRationale", "AI rationale was not provided."),
            "source": "anthropic",
        }
    except Exception as error:
        raise RuntimeError(f"AI open-ended scoring failed: {error}")


async def generate_learning_analysis(
    employee: dict,
    exam_goal: dict,
    wrong_answers: list[dict],
    weak_knowledge_points: list[dict],
):
    prompt = f"""
Create a short weakness analysis and learning suggestions.
Return JSON only with exactly these fields:
summary, suggestions.

Rules:
- suggestions must be an array of 2-4 short strings
- focus on the employee's weak knowledge points
- do not include markdown

EMPLOYEE:
{json.dumps(employee, indent=2)}

EXAM GOAL:
{json.dumps(exam_goal, indent=2)}

WRONG OR LOW-SCORING ANSWERS:
{json.dumps(wrong_answers, indent=2)}

WEAK KNOWLEDGE POINTS:
{json.dumps(weak_knowledge_points, indent=2)}
"""
    try:
        ai_text = await call_anthropic(prompt)
        result = extract_json(ai_text)
        return {
            "summary": result.get("summary", ""),
            "suggestions": result.get("suggestions", []),
            "source": "anthropic",
        }
    except Exception as error:
        raise RuntimeError(f"AI learning analysis failed: {error}")


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/source-file")
async def upload_source_file(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_file(file.filename or "source.txt", content)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Could not read source file: {error}")

    if len(text) > 30000:
        text = text[:30000]

    try:
        summary, main_topics, assessment_focus, assessment_source_text = await summarize_source_text(text)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"AI source summary failed: {error}")

    return {
        "filename": file.filename,
        "text": text,
        "assessmentSourceText": assessment_source_text,
        "summary": summary,
        "mainTopics": main_topics,
        "recommendedAssessmentFocus": assessment_focus,
        "characterCount": len(text),
    }


@app.post("/api/knowledge-points")
async def extract_knowledge_points(request: KnowledgeRequest):
    prompt = f"""
Extract 3-5 business knowledge points from the source material.
Return JSON only as an array.
Each item must have exactly these fields:
id, sourceDocumentId, title, description, importance, status.

Rules:
- sourceDocumentId must be "doc-1"
- status must be "draft"
- importance must be one of "low", "medium", "high"
- do not include markdown

SOURCE MATERIAL:
{request.source_text}
"""

    try:
        knowledge_points = await call_json_ai(prompt)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI knowledge extraction failed: {error}",
        )

    return {
        "knowledge_points": knowledge_points,
        "source": "anthropic",
        "source_length": len(request.source_text),
    }


@app.post("/api/questions")
async def generate_questions(request: QuestionRequest):
    if not request.knowledge_points:
        raise HTTPException(
            status_code=400,
            detail="No knowledge points available. Extract or add knowledge points first.",
        )

    compact_knowledge_points = [
        {
            "id": item.get("id", f"kp-{index}"),
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "importance": item.get("importance", "medium"),
        }
        for index, item in enumerate(request.knowledge_points, start=1)
    ]
    prompt = f"""
Generate exam questions from these knowledge points and exam goal.
Return JSON only with this shape:
{{
  "questions": [
    {{
      "id": "q-1",
      "knowledgePointId": "kp-id",
      "type": "multiple_choice",
      "prompt": "question text",
      "options": ["A", "B", "C", "D"],
      "correctAnswer": "one exact option",
      "rubric": "",
      "status": "draft"
    }}
  ]
}}

Rules:
- include at least two multiple_choice questions
- include at least one open_ended question
- type must be "multiple_choice" or "open_ended"
- status must be "draft"
- multiple_choice questions must have 4 options and one correctAnswer
- open_ended questions must include a scoring rubric
- if mode is practice, questions may include learning-friendly wording
- if mode is assessment, questions should be clear, formal, and balanced in difficulty
- do not include markdown

EXAM GOAL:
Target role: {request.target_role}
Topic focus: {request.topic_focus}
Difficulty: {request.difficulty}
Mode: {request.exam_mode}
Deadline: {request.deadline or "none"}

KNOWLEDGE POINTS:
{json.dumps(compact_knowledge_points, indent=2)}
"""

    try:
        questions = normalize_questions(await call_json_ai(prompt))
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI question generation failed: {error}",
        )

    return {
        "questions": questions,
        "source": "anthropic",
        "exam_goal": {
            "target_role": request.target_role,
            "topic_focus": request.topic_focus,
            "difficulty": request.difficulty,
        },
        "knowledge_point_count": len(request.knowledge_points),
    }


@app.post("/api/submit-exam")
async def submit_exam(request: SubmitExamRequest):
    exam_mode = request.exam_goal.get("exam_mode", "practice")
    deadline = request.exam_goal.get("deadline", "")
    exam_key = exam_key_from_goal(request.exam_goal)

    if exam_mode == "assessment":
        if not deadline:
            raise HTTPException(
                status_code=400,
                detail="Assessment mode requires a deadline before submission.",
            )
        if deadline:
            try:
                deadline_at = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                if deadline_at.tzinfo is None:
                    deadline_at = deadline_at.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > deadline_at.astimezone(timezone.utc):
                    raise HTTPException(
                        status_code=400,
                        detail="Assessment deadline has passed. Submission is closed.",
                    )
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid assessment deadline format.")

        if has_assessment_attempt(request.employee.get("id", ""), exam_key):
            raise HTTPException(
                status_code=400,
                detail="Assessment mode allows exactly one attempt for this employee.",
            )

    knowledge_by_id = {item.get("id"): item for item in request.knowledge_points}
    scored_answers = []

    for question in request.questions:
        question_id = question.get("id")
        response = request.answers.get(question_id, "")

        if question.get("type") == "multiple_choice":
            is_correct = response == question.get("correctAnswer")
            scored_answers.append(
                {
                    "questionId": question_id,
                    "prompt": question.get("prompt"),
                    "type": question.get("type"),
                    "response": response,
                    "correctAnswer": question.get("correctAnswer"),
                    "score": 1 if is_correct else 0,
                    "isCorrect": is_correct,
                    "aiRationale": "",
                }
            )
        else:
            knowledge_point = knowledge_by_id.get(question.get("knowledgePointId"))
            try:
                scoring = await score_open_ended_answer(question, response, knowledge_point)
            except Exception as error:
                raise HTTPException(status_code=502, detail=str(error))
            scored_answers.append(
                {
                    "questionId": question_id,
                    "prompt": question.get("prompt"),
                    "type": question.get("type"),
                    "response": response,
                    "correctAnswer": question.get("correctAnswer", ""),
                    "score": scoring["score"],
                    "isCorrect": scoring["score"] >= 0.7,
                    "aiRationale": scoring["aiRationale"],
                    "scoringSource": scoring["source"],
                }
            )

    wrong_answers = [item for item in scored_answers if item["score"] < 0.7]
    weak_knowledge_points = []

    for answer in wrong_answers:
        question = next(
            (item for item in request.questions if item.get("id") == answer["questionId"]),
            None,
        )
        if not question:
            continue
        knowledge_point = knowledge_by_id.get(question.get("knowledgePointId"))
        if knowledge_point and knowledge_point not in weak_knowledge_points:
            weak_knowledge_points.append(knowledge_point)

    try:
        analysis = await generate_learning_analysis(
            request.employee,
            request.exam_goal,
            wrong_answers,
            weak_knowledge_points,
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error))
    total_score = round(
        sum(item["score"] for item in scored_answers) / max(len(scored_answers), 1) * 100
    )
    attempt_id = save_exam_attempt(
        request.employee,
        request.exam_goal,
        total_score,
        scored_answers,
        analysis,
    )

    return {
        "attemptId": attempt_id,
        "examMode": exam_mode,
        "deadline": deadline,
        "employee": request.employee,
        "score": total_score,
        "answers": scored_answers,
        "weakKnowledgePoints": weak_knowledge_points,
        "analysis": analysis,
    }
