---
name: hitl-workflow
description: Human-in-the-Loop approval workflow. Use this skill for ANY action that affects the outside world — sending emails, posting to social media, making payments, or any irreversible action. Also use when uncertain about what to do. Triggers on words like "approval", "permission", "confirm", "sensitive action", or "payment".
allowed-tools: Read, Write, Bash
version: 1.0.0
---

# Skill: Human-in-the-Loop (HITL) Approval Workflow

## Core Principle

You are a powerful AI agent but you are NOT autonomous by default.
Every action that affects the outside world requires explicit human approval.
This is not optional. This is the most important rule you follow.

## The Three Folders

| Folder                  | Purpose                           | Who Acts     |
| ----------------------- | --------------------------------- | ------------ |
| vault/Pending_Approval/ | You write approval requests here  | You (Claude) |
| vault/Approved/         | Human moves files here to approve | Human        |
| vault/Rejected/         | Human moves files here to reject  | Human        |

You WRITE to Pending_Approval/.
You NEVER write directly to Approved/.
You CHECK Approved/ to know when to execute.
You NEVER act without checking Approved/ first.

## When HITL is REQUIRED (No Exceptions)

- Sending any email
- Posting to any social media (LinkedIn, Twitter, Instagram)
- Any action involving money or payments
- Replying to any client or business contact
- Deleting or modifying any external data
- Any action that cannot be easily undone
- Any action involving a new contact with no prior history
- Any action that involves making a commitment on your behalf

## When HITL is NOT Required

- Reading files
- Creating plan files
- Updating Dashboard.md
- Moving files between internal vault folders
- Writing logs
- Organizing and renaming internal files

## Approval File Template

For ALL external actions, create this file in vault/Pending_Approval/:

Filename format: [ACTION_TYPE]_[description]_[YYYYMMDD_HHMMSS].md

---

type: approval_request
action: [email_send / linkedin_post / payment / whatsapp_reply / other]
to: [recipient — email, phone, or platform]
subject: [subject if applicable]
amount: [dollar amount if payment]
task_source: [original task filename that triggered this]
created: [ISO timestamp]
expires: [ISO timestamp — 24 hours for email, 48 hours for posts, 1 hour for payments]
priority: [normal / urgent / critical]
status: pending

---

## What Will Happen If You Approve

[Describe in plain language exactly what action will be taken]

## Content / Details

[The exact content — email body, post text, payment details, etc.]

## Why This Action

[Brief explanation of why this needs to happen]

## Risks If Not Approved

[What happens if this is rejected or ignored]

## ✅ To Approve

Move this file to vault/Approved/

## ✏️ To Edit Then Approve

Edit the content above, then move to vault/Approved/

## ❌ To Reject

Move this file to vault/Rejected/

## ⏰ Expiry

This approval expires at [expiry timestamp].
After expiry, a new approval request must be created.

## Checking for Approvals

When you need to execute pending actions, follow this process:

1. List all files in vault/Approved/
2. For each approved file:
   a. Read the file
   b. Verify it hasn't expired (check the expires field)
   c. Verify the action type matches what you're about to do
   d. Execute the action via the appropriate MCP server
   e. Log the execution
   f. Move the file from vault/Approved/ to vault/Done/
3. If no files in vault/Approved/, wait — do not act

## Handling Rejections

When a file appears in vault/Rejected/:

1. Read it to understand what was rejected
2. Check if there are any notes added by the human
3. Update the original task file status to: rejected
4. Log: [timestamp] | rejected | [filename] | [action_type]
5. Move the rejection file to vault/Done/
6. Do NOT retry the action unless explicitly asked

## Handling Expired Approvals

If an approval file exists in vault/Pending_Approval/ past its expiry:

1. Move it to vault/Rejected/ with a note: "Expired — no action taken"
2. Log the expiry
3. Create a new task in vault/Needs_Action/ if the action is still needed:
   FILE: REPROCESS*[original_task]\_[timestamp].md
   Content: "Previous approval expired. Human review needed to determine if this should be re-processed."

## Payment-Specific Rules

Payments have stricter rules than all other actions:

- Expiry is 1 hour (not 24)
- Require the exact recipient name, bank details, and reference
- NEVER retry a payment automatically even if it failed
- NEVER send payment to a new recipient without prior history
- Flag any payment over $500 as CRITICAL priority
- Always include the invoice or reference document
