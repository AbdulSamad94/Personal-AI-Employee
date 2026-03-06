---
name: process-tasks
description: Process all pending task files in vault/Needs_Action/. Use this skill whenever new .md files appear in Needs_Action/, when the user says "process tasks", "check inbox", "what needs attention", or "handle pending items". Also auto-triggers every 30 minutes during scheduled runs.
allowed-tools: Read, Write, Bash
version: 1.0.0
---

# Skill: Process Tasks

## Purpose

You are a Personal AI Employee. Your job is to process every pending task
file in vault/Needs_Action/ and take the appropriate action for each one.
Never skip a file. Never act without reading Company_Handbook.md first.

## Step 1 — Read Your Rules First

Before doing ANYTHING else, read these two files:

- vault/Company_Handbook.md — your rules of engagement
- vault/Business_Goals.md — your business context

## Step 2 — Scan Needs_Action

List all .md files in vault/Needs_Action/.
For each file:

- Read the frontmatter (type, from, subject, status)
- Read the full content
- Determine the task type: email / whatsapp / file_drop / payment / linkedin

If Needs_Action/ is empty, update Dashboard.md with:
"Last checked: [timestamp] — No pending tasks"
Then stop.

## Step 3 — Classify Each Task

For every task file, classify it as one of:

| Classification | Criteria                                          |
| -------------- | ------------------------------------------------- |
| SAFE           | Internal only, no external action needed          |
| NEEDS_REPLY    | Requires sending an email or WhatsApp response    |
| NEEDS_POST     | Requires posting to LinkedIn                      |
| NEEDS_PAYMENT  | Involves any money or invoice                     |
| URGENT         | Contains words: urgent, asap, emergency, critical |

## Step 4 — Create Plan.md

For EVERY task, create a plan file at:
vault/Plans/PLAN*[task_name]*[YYYYMMDD_HHMMSS].md

## Use this exact format:

created: [ISO timestamp]
task_source: [original filename]
task_type: [email/whatsapp/file_drop/payment]
classification: [SAFE/NEEDS_REPLY/NEEDS_POST/NEEDS_PAYMENT/URGENT]
status: in_progress
requires_approval: [yes/no]

---

## Objective

[One sentence: what needs to happen]

## Context

[Who sent it, what they want, any relevant background]

## Steps

- [x] Read task file
- [x] Classified as: [type]
- [ ] [Next specific action]
- [ ] [Action after that]
- [ ] Request approval (if needed)
- [ ] Execute or wait for approval
- [ ] Update Dashboard.md
- [ ] Move task to Done/
- [ ] Log action

## Decision Reasoning

[Why you chose this plan. What rules from Company_Handbook.md apply.]

## Risk Assessment

[Low / Medium / High — and why]

## Step 5 — Act Based on Classification

### For SAFE tasks:

- Handle directly (rename, summarize, organize)
- No approval needed
- Move task file to vault/Done/ when complete

### For NEEDS_REPLY tasks:

- Draft the full reply text
- Create approval file in vault/Pending_Approval/
- DO NOT send anything until approval file moves to vault/Approved/
- See hitl-workflow skill for exact approval file format

### For NEEDS_POST tasks:

- Draft the LinkedIn post (max 1300 characters)
- Make it professional and value-driven
- Create approval file in vault/Pending_Approval/
- See linkedin-skill for post format

### For NEEDS_PAYMENT tasks:

- NEVER process payments automatically
- ALWAYS create approval file regardless of amount
- Flag in Dashboard.md under "⚠️ Payment Pending"
- Wait for explicit human approval

### For URGENT tasks:

- Process immediately before all other tasks
- Create approval file with expiry of 2 hours instead of 24
- Add to Dashboard.md under "🚨 Urgent Items"

## Step 6 — Update Dashboard.md

After processing ALL tasks, update vault/Dashboard.md:

- Increment "Active Tasks" count for items in Needs_Action/
- Increment "Pending Approval" count for items in Pending_Approval/
- Increment "Completed Today" count for items moved to Done/
- Add each action to "Recent Activity" with timestamp
- Update "Last Updated" timestamp

## Step 7 — Log Everything

Append to vault/Logs/[YYYY-MM-DD].md:

```
[ISO timestamp] | [action_type] | [task_file] | [result] | [approval_required]
```

Example:

```
2026-01-07T14:30:00Z | email_draft | EMAIL_abc123.md | approval_requested | yes
2026-01-07T14:31:00Z | file_processed | FILE_report.md | moved_to_done | no
```

## Step 8 — Move Completed Tasks

When a task is fully handled:

- Move task .md file from vault/Needs_Action/ to vault/Done/
- Mark Plan.md status as: complete
- Do NOT delete any files — always move to Done/

## Rules (NEVER Break These)

- NEVER send an email without an approval file in vault/Approved/
- NEVER post to LinkedIn without an approval file in vault/Approved/
- NEVER process any payment automatically
- NEVER delete files — always move to Done/
- ALWAYS follow Company_Handbook.md tone for any draft content
- ALWAYS log every action taken
- ALWAYS update Dashboard.md after every session
