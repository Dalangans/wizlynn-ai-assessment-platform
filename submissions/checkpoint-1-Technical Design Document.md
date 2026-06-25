# Checkpoint 1 - Technical Design Document

## Project

AI-Powered Business Knowledge Assessment Platform

## MVP Goal

Build a small working demo that proves one complete AI assessment flow:

Source material -> knowledge extraction -> question generation -> human review -> employee exam -> scoring -> weakness analysis and learning suggestions.

The goal is not to build a full exam platform, but to show how AI can turn internal business knowledge into measurable employee capability assessment.

## Source Material

The Wizlynn User Manual will be used as the main source material for the MVP.

Its role is to provide:

- source content for AI knowledge extraction,
- reference material for generating exam questions,
- grounding for correct answers and open-ended scoring rubrics,
- context for weakness analysis and learning suggestions.

For the MVP, I may use extracted text or a selected smaller section from the PDF to keep the demo focused and fast.

## MVP Scope

### In Scope

- Load or paste business material from the Wizlynn User Manual.
- Define an exam goal with target role, topic, difficulty, and question count.
- Use AI to extract structured knowledge points.
- Use AI to generate questions from approved knowledge points.
- Include both multiple-choice and open-ended questions.
- Allow a human reviewer to edit, approve, or reject AI-generated questions.
- Let an employee enter simple identity information and take the exam.
- Score multiple-choice answers automatically.
- Score open-ended answers using AI with visible rationale.
- Generate error analysis and learning suggestions after exam submission.

### Out of Scope

- Full authentication and role-based access control.
- Large-scale document search or vector database.
- Advanced analytics dashboard.
- Multi-exam scheduling.
- Production-grade database and audit logs.

These are excluded so the demo can focus on the required AI workflow.

## Main Roles

- Trainer / Admin: provides source material, defines the exam goal, reviews AI outputs, and approves questions.
- Employee: enters identity, takes the exam, and receives score plus learning suggestions.

For the MVP, these roles can be represented as separate screens instead of real login accounts.

## Data Model Sketch

```ts
type SourceDocument = {
  id: string;
  title: string;
  rawText: string;
};

type ExamGoal = {
  id: string;
  targetRole: string;
  topicFocus: string;
  difficulty: "basic" | "intermediate" | "advanced";
  questionCount: number;
};

type KnowledgePoint = {
  id: string;
  sourceDocumentId: string;
  title: string;
  description: string;
  importance: "low" | "medium" | "high";
  status: "draft" | "approved" | "rejected";
};

type Question = {
  id: string;
  knowledgePointId: string;
  type: "multiple_choice" | "open_ended";
  prompt: string;
  options?: string[];
  correctAnswer?: string;
  rubric?: string;
  status: "draft" | "approved" | "rejected";
};

type Employee = {
  id: string;
  name: string;
  role: string;
};

type ExamAttempt = {
  id: string;
  employeeId: string;
  answers: Answer[];
  score: number;
  analysis: LearningAnalysis;
};

type Answer = {
  questionId: string;
  response: string;
  score: number;
  aiRationale?: string;
};

type LearningAnalysis = {
  weakKnowledgePointIds: string[];
  summary: string;
  suggestions: string[];
};
```

## AI Integration

AI will be used in four required steps:

1. Knowledge extraction
   - Input: source material text.
   - Output: structured knowledge points.
   - Human review: trainer can edit, approve, or reject.

2. Question generation
   - Input: approved knowledge points and exam goal.
   - Output: multiple-choice and open-ended questions with answers/rubrics.
   - Human review: trainer approves questions before they enter the exam.

3. Open-ended scoring
   - Input: question, rubric, employee answer, and related knowledge point.
   - Output: score and visible rationale.

4. Learning suggestions
   - Input: wrong answers and weak knowledge points.
   - Output: weakness summary and recommended next steps.

## Technical Stack

- Frontend: React or Next.js.
- Backend: Next.js API routes or a lightweight Node API.
- Storage: local JSON file or SQLite for fast MVP development.
- AI Provider: provided Anthropic-compatible API.
- PDF handling: use extracted or pasted text from the provided manual.

Environment variables:

```env
ANTHROPIC_BASE_URL=http://crs.cm233.top:50005/api
ANTHROPIC_AUTH_TOKEN=<candidate-specific-token>
```

The API token will be stored in environment variables and will not be hardcoded in the source code.

## Key Design Decisions

- Human approval is required between AI steps because AI output must be visible, editable, and confirmable.
- Each question is linked to a knowledge point so wrong answers can be mapped to specific knowledge gaps.
- Multiple-choice questions are scored deterministically for reliability.
- Open-ended questions are scored by AI because they need semantic judgment and rationale.
- Simple employee identity fields are enough for the MVP because the requirement is result association, not full HR integration.
- Local storage is chosen to keep the demo simple, fast, and easy to explain.

## Success Criteria

The demo is successful if it can show:

1. The Wizlynn material becomes approved knowledge points.
2. Approved knowledge points become reviewed exam questions.
3. An employee completes the exam.
4. The result shows score, AI scoring rationale, weak areas, learning suggestions, and employee identity.
