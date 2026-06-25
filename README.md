# Wizlynn AI Assessment Platform MVP

An AI-powered business knowledge assessment MVP built for the Wiz.AI on-site assessment.

The demo shows how internal business material can be converted into structured knowledge points, reviewed questions, employee exam attempts, AI scoring, and learning suggestions.

## What I Built

This MVP implements one complete assessment workflow:

1. Manager uploads or pastes business source material.
2. AI summarizes the source material and extracts structured knowledge points.
3. Manager defines an exam goal, including target role, topic focus, difficulty, exam mode, and deadline.
4. AI generates structured questions from approved knowledge points and the exam goal.
5. Manager reviews, approves, rejects, regenerates, or manually adds knowledge points/questions.
6. Manager sends only approved questions to the Employee View.
7. Employee enters identity information and takes the exam.
8. Multiple-choice answers are scored automatically.
9. Open-ended answers are scored by AI with visible rationale.
10. The system generates weakness analysis and learning suggestions.
11. The result is saved to local SQLite and linked to employee identity.

## Requirement Coverage

| Requirement | MVP Coverage |
| --- | --- |
| AI extracts knowledge points from business material | Source material upload/paste + AI knowledge extraction |
| AI generates structured questions from exam goal | Exam goal form + AI question generation |
| Includes at least one open-ended question | AI prompt requires at least one open-ended question |
| Human can review/edit/reject before exam | Manager View supports approve/reject, regenerate, and manual additions |
| Employee can take exam | Employee View shows only manager-approved questions |
| Automatic scoring | Multiple choice is scored deterministically |
| AI scoring for open-ended answer | Open-ended answer is scored by Claude with visible rationale |
| Error analysis and learning suggestions | AI generates weakness summary and next steps |
| Result associated with employee identity | Employee ID/name/role are stored with the exam attempt |

## Additional Requirement Change

The app supports two exam modes:

- Practice mode:
  - employees can take the exam multiple times,
  - results are recorded for learning,
  - result display is learning-oriented.

- Assessment mode:
  - employees only get one attempt for the same assessment,
  - deadline is required and enforced,
  - result is treated as formal capability evaluation.

## Tech Stack

- Backend: FastAPI
- AI provider: Anthropic-compatible API
- Frontend: single HTML page with vanilla JavaScript
- Storage: SQLite
- PDF parsing: pypdf

## Project Structure

```txt
app/
├─ main.py
├─ database.py
├─ index.html
├─ requirements.txt
├─ .env.example
└─ data/
   └─ assessment.db
```

## Environment Variables

Create `app/.env`:

```env
ANTHROPIC_BASE_URL=http://crs.cm233.top:50005/api
ANTHROPIC_AUTH_TOKEN=<candidate-specific-token>
ANTHROPIC_MODEL=claude-opus-4-6
```

Do not commit `.env`.

## How To Run

```bash
cd app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

```txt
http://127.0.0.1:8000
```

## Demo Flow

1. Upload the Wizlynn User Manual PDF or paste source material.
2. Review the AI-generated source summary.
3. Click `Extract Knowledge Points`.
4. Confirm the exam goal.
5. Approve or reject knowledge points.
6. Generate questions from approved knowledge points.
7. Approve all questions or regenerate if rejected.
8. Click `Send Approved Questions to Employee View`.
9. Fill employee identity.
10. Answer multiple-choice and open-ended questions.
11. Submit exam and review score, AI rationale, weak areas, and learning suggestions.

## Key Design Decisions

- I separated the UI into Manager / Trainer View and Employee View instead of building full authentication, because the MVP needs to prove role separation without spending time on login infrastructure.
- I kept human approval between AI generation and the employee exam, because AI output must be visible, editable, and confirmable.
- I linked questions to knowledge points so wrong answers can be mapped back to knowledge gaps.
- I used deterministic scoring for multiple-choice questions and AI scoring for open-ended answers.
- I used SQLite for MVP persistence because the data is relational but does not require production database setup.
- I used local PDF extraction plus AI summarization so the source material can come from the provided manual without building a full document indexing system.

## Deliberately Left Out

- Full authentication and role-based permission system.
- Production-grade database and deployment setup.
- Advanced analytics dashboard.
- Large-scale document search or vector database.
- Question randomization and anti-cheating controls.
- Long-term learning history dashboard.

## What I Would Build Next

- Replace the single-page UI with a structured React frontend.
- Add real authentication for Manager and Employee roles.
- Move from SQLite to PostgreSQL for production.
- Add a question bank with versioning and audit logs.
- Add better question editing UX for options, rubrics, and source references.
- Add analytics for knowledge gaps by role, team, and time period.
- Add stronger assessment-mode controls such as timed exams and randomized question sets.
