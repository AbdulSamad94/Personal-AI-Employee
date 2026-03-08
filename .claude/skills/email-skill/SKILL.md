---
name: email-skill
description: Draft professional email replies and create email approval requests. Use when an EMAIL_*.md file exists in Needs_Action/, when the user says "reply to this email", "draft an email", "respond to [person]", or when a task requires sending an email communication.
allowed-tools: Read, Write
version: 1.0.0
---

# Skill: Email Drafting and Sending

## Purpose

Draft professional emails on behalf of the business owner and prepare
them for sending via the Email MCP server after human approval.
NEVER send an email without a corresponding approval file in vault/Approved/.

## Step 1 — Read the Email Task

Read the EMAIL\_\*.md file from vault/Needs_Action/.
Extract:

- Sender name and email address
- Subject line
- Email content/summary
- Any specific requests or questions asked
- Tone of the original email (formal/informal/urgent)

## Step 2 — Read Communication Rules

Read vault/Company_Handbook.md and note:

- Required tone (professional, friendly, etc.)
- Any specific rules about this type of email
- Signature format to use
- Any topics that require escalation

## Step 3 — Draft the Reply

Follow these writing rules:

- Match the formality level of the incoming email
- Be concise — get to the point within 2 sentences
- Always acknowledge their message first
- Address every question or request they made
- End with a clear next step or call to action
- Keep total length under 200 words unless content requires more
- Never make promises about money, deadlines, or deliverables
  without checking Business_Goals.md first

## Reply Structure:

```
Subject: Re: [original subject]

Hi [First Name],

[Acknowledgment sentence — thank them or confirm you received their message]

[Main response — address their question/request directly]

[Any clarifications or caveats needed]

[Clear next step]

Best regards,
[Your Name]
[Title if applicable]
```

## Step 4 — Create Approval Request

Create file at vault/Pending_Approval/EMAIL_[sender_name]_[YYYYMMDD].md:
---
type: approval_request
action: email_send
to: [recipient email address]
subject: Re: [original subject]
task_source: [original EMAIL_*.md filename]
created: [ISO timestamp]
expires: [ISO timestamp + 24 hours]
status: pending

---

## Email to Send

**To:** [email address]
**Subject:** Re: [subject]

---

## [Full email body here exactly as it should be sent]

## Original Message Summary

[2-3 sentence summary of what they sent]

## Why This Response

[Brief explanation of why you drafted this specific reply]

## To Approve

Move this file to vault/Approved/ folder.

## To Reject or Edit

Move this file to vault/Rejected/ folder
OR edit the email body above and then move to vault/Approved/.

## To Approve and Send via MCP

Once in vault/Approved/, the Email MCP server will send this automatically.

## Step 5 — Update Task Status

Update the original EMAIL\_\*.md in Needs_Action/:

- Change status: pending → awaiting_approval
- Add note: "Draft created at [timestamp], approval requested"

## Step 6 — Log the Action

Append to vault/Logs/[YYYY-MM-DD].md:

```
[timestamp] | email_draft | [original file] | approval_requested | to: [recipient]
```

## Email Quality Checklist

Before creating the approval file, verify:

- [ ] Addressed every point in the original email
- [ ] No spelling errors
- [ ] Tone matches Company_Handbook.md rules
- [ ] No promises made about money or deadlines
- [ ] Clear next step included
- [ ] Correct recipient email address
- [ ] Subject line starts with "Re: "
