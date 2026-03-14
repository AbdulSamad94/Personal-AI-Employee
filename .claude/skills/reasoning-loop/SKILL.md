---
name: reasoning-loop
description: Deep reasoning loop for complex multi-step tasks. Use when a task requires planning across multiple files, cross-referencing business goals, making decisions with multiple options, or when the user says "think through this", "make a plan", "figure out what to do", or "analyze my tasks".
allowed-tools: Read, Write, Bash
version: 1.0.0
---

# Skill: Reasoning Loop

## Purpose

This skill gives you a structured thinking process for complex tasks
that require more than simple file processing. Use this when you need
to reason carefully before acting.

## The OODA Loop (Observe → Orient → Decide → Act)

### Phase 1 — OBSERVE

Gather all relevant information before forming any opinion:

Read in this exact order:

1. vault/Company_Handbook.md
2. vault/Business_Goals.md
3. vault/Dashboard.md (current state)
4. All files in vault/Needs_Action/
5. Most recent 3 files in vault/Done/ (for context on recent work)
6. Most recent briefing in vault/Briefings/ (if exists)

Write a one-paragraph summary of what you observed.
Do not form conclusions yet.

### Phase 2 — ORIENT

Analyze what you observed against your goals:

Ask yourself these questions and write answers:

- What is the most urgent thing that needs attention right now?
- What aligns with the goals in Business_Goals.md?
- What would be risky to do without human approval?
- What can I handle completely on my own?
- Are there any patterns? (e.g., same client contacting multiple times)
- Are there any deadlines I should know about?

### Phase 3 — DECIDE

For each task in Needs_Action/, decide ONE of:

| Decision          | When to Use                                       |
| ----------------- | ------------------------------------------------- |
| ACT_NOW           | Safe, internal, no external action                |
| DRAFT_AND_APPROVE | Needs external action (email/post/payment)        |
| ESCALATE          | Too complex, risky, or ambiguous — flag for human |
| DEFER             | Low priority, can wait for next cycle             |

Document your decision and reasoning for each task.

### Phase 4 — ACT

Execute decisions in this priority order:

1. URGENT items first
2. ESCALATE items (create flags immediately)
3. ACT_NOW items (handle directly)
4. DRAFT_AND_APPROVE items (create drafts + approval files)
5. DEFER items (add note to Dashboard.md)

## Creating Thorough Plan.md Files

For complex tasks, your Plan.md should include:

---

created: [timestamp]
task_source: [filename]
reasoning_depth: deep
status: in_progress

---

## Situation Analysis

[2-3 sentences describing the full situation]

## Stakeholders

- Who sent this?
- Who else is affected?
- Who needs to approve?

## Options Considered

### Option A: [name]

- Pros: ...
- Cons: ...
- Risk: Low/Medium/High

### Option B: [name]

- Pros: ...
- Cons: ...
- Risk: Low/Medium/High

## Chosen Approach

[Which option and why]

## Execution Steps

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Success Criteria

[How will you know this task is complete?]

## Fallback Plan

[What to do if the primary approach fails]

## Cross-References

- Related tasks: [list any related files in Needs_Action/ or Done/]
- Relevant handbook rules: [which rules apply]
- Business goal alignment: [which goal this serves]

## Completion Summary

[Fill this in when done: what actually happened]

## When to Stop and Escalate

Create an ESCALATE file in vault/Pending_Approval/ immediately if:

- You are uncertain about the right action
- The task involves legal, medical, or financial edge cases
- The task involves a new client you have no history with
- The task involves credentials or sensitive personal data
- Conflicting instructions exist between handbook and the request
- Any irreversible action with significant consequences

## Escalation file format:

type: escalation
reason: [why you are escalating]
task_source: [original file]
your_analysis: [what you figured out so far]
question_for_human: [the specific question you need answered]

---
