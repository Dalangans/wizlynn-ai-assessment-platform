# Hiring Assignment: AI-Powered Business Knowledge Assessment Platform

**Date**: 2026-06-24  
**Duration**: ~7 hours (09:30–16:30)  
**Tools**: You may use any AI tools, including Claude Code. You are encouraged to use AI extensively.

---

## Background

Our company has accumulated a large body of internal business knowledge: product documentation, delivery playbooks, customer scenario guides, training materials, and FAQ content. This knowledge is scattered and hard to operationalize.

The current situation:
- Training content exists, but there is no structured question bank.
- Generating exam questions is manual, slow, and inconsistent in quality.
- After an exam, managers can see scores but cannot identify *which specific knowledge gaps* an employee has.
- There is no unified mechanism to verify business knowledge across roles — onboarding staff, pre-sales, delivery, and support all need different things.

## What We Want to Build

An AI-driven internal business knowledge assessment platform.

The core value is not building another online exam system. The goal is to use AI to close the loop between **raw internal knowledge** and **actionable, trackable employee capability verification**.

The pipeline should look roughly like this:

```
Internal documents + Exam goal definition
  → AI extracts knowledge points
  → AI generates structured questions
  → Human reviews and controls question quality
  → Exam is conducted
  → Auto-scoring / AI scoring for open-ended answers
  → Error analysis and learning suggestions generated
  → Results linked to employee identity
```

---

## What You Need to Deliver

By 16:30, you need to submit a **working demo** and a brief **written explanation**.

**The demo must prove these results are true:**

1. Given a piece of business material (you may use the provided Wizlynn User Manual as source material, or write your own), AI can extract knowledge points from it.
2. Given an exam goal (something that defines "what this exam should test"), AI can generate structured questions from the material — including at least one open-ended (subjective) question.
3. A human can review, edit, or reject AI-generated questions before they go into an exam.
4. An employee can take the exam, and their answers are scored automatically. The open-ended question must be scored by AI with a visible rationale.
5. After completion, the system produces an error analysis and learning suggestions based on the employee's wrong answers.
6. The exam result is associated with an employee identity in some form.

**The written explanation must cover:**
- What you built and what you deliberately left out (MVP scoping decisions)
- The key design choices you made and why
- What you would build next if you had more time

---

## Open Design Space

The following are intentionally **not specified**. You decide:

- What user roles exist and what each one can do.
- What an "exam goal" looks like — its format, fields, and how it constrains AI generation.
- What "employee identity" means and how it is implemented.
- Data structures, APIs, storage, and tech stack.
- How AI failures, bad-quality questions, and edge cases are handled.
- What to build vs. what to skip within the 7-hour window.
- UI, or whether there even needs to be one.

Evaluation will focus on whether you can make clear, well-reasoned decisions in these open areas — and whether you can explain *why* you made them.

---

## AI Requirements

AI must be embedded in the business flow, not just used for speed. At minimum, AI must cover these 4 steps:

1. **Knowledge extraction**: From raw documents to structured knowledge points.
2. **Question generation**: From knowledge points + exam goal to structured questions with correct answers and distractors.
3. **Subjective scoring**: At least one open-ended answer must be scored by AI, with visible scoring rationale.
4. **Learning suggestions**: After exam completion, AI generates a weakness analysis and recommended next steps based on the employee's wrong answers.

AI output at each step must be **visible, editable, and confirmable** before moving to the next step. You are responsible for designing the AI input/output contracts, failure handling, and human fallback mechanisms. No fixed prompts are provided.

---

## Reference Material

The following document is provided as sample source material for AI knowledge extraction and question generation:

**Wizlynn User Manual** (see `Wizlynn User Manual.pdf` in the same folder)

You may use this document, or create your own minimal business content to demonstrate the flow.

---

## Checkpoint Schedule

| Time  | Checkpoint       | What to Submit                                                                        |
| ----- | ---------------- | ------------------------------------------------------------------------------------- |
| 10:00 | Design Review    | Brief written technical design: MVP scope, data model sketch, AI integration approach |
| 13:00 | Progress Update  | 3–5 sentences on current status; you will also receive a change notice at this time   |
| 16:30 | Final Submission | Git link or code directory + written explanation                                      |


## What We Are Looking For

This is not primarily a test of how fast you can code. We are evaluating:

- Do you understand the business problem before you start building?
- Can you make and explain architecture decisions?
- How do you use AI — as a thinking partner or just a code generator?
- When requirements change, can you assess the impact systematically?
- Do you know what to build and what to skip within a tight time window?

There is no single correct solution. A well-scoped, clearly designed 60% implementation is better than a rushed, unexplained 100% implementation.
