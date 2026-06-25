# Mock Reference Only

This file is only a note for manual fallback during presentation preparation.
The running application does not depend on these mock examples for knowledge extraction or question generation.

## Example Knowledge Points

```json
[
  {
    "id": "kp-1",
    "sourceDocumentId": "doc-1",
    "title": "Wizlynn product value",
    "description": "Employees need to understand how Wizlynn creates business value for customers.",
    "importance": "high",
    "status": "draft"
  },
  {
    "id": "kp-2",
    "sourceDocumentId": "doc-1",
    "title": "Customer scenario application",
    "description": "Employees should connect product capabilities to real customer problems.",
    "importance": "high",
    "status": "draft"
  }
]
```

## Example Questions

```json
[
  {
    "id": "q-1",
    "knowledgePointId": "kp-1",
    "type": "multiple_choice",
    "prompt": "What is the main purpose of Wizlynn enablement material?",
    "options": [
      "To replace customer support teams",
      "To help employees understand product value and customer-facing workflows",
      "To manage payroll records",
      "To schedule office facilities"
    ],
    "correctAnswer": "To help employees understand product value and customer-facing workflows",
    "rubric": "",
    "status": "draft"
  },
  {
    "id": "q-2",
    "knowledgePointId": "kp-2",
    "type": "open_ended",
    "prompt": "Explain how a pre-sales employee should use Wizlynn product knowledge in a customer scenario.",
    "options": [],
    "correctAnswer": "",
    "rubric": "A strong answer connects a customer problem to relevant Wizlynn product value and explains the business impact clearly.",
    "status": "draft"
  }
]
```
