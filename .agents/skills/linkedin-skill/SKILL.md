---
name: linkedin-skill
description: Draft and schedule LinkedIn posts to generate business leads and build professional presence. Use when the user says "write a LinkedIn post", "post on LinkedIn", "create content", "share on LinkedIn", or when a completed project or milestone should be announced. Also triggers on weekly scheduled post days.
allowed-tools: Read, Write
version: 1.0.0
---

# Skill: LinkedIn Content Creation

## Purpose

Create compelling, value-driven LinkedIn posts that build the business
owner's professional brand and generate inbound leads.
NEVER post directly — always create an approval file first.

## Step 1 — Gather Context

Before writing, read:

- vault/Business_Goals.md — what the business is about and current goals
- vault/Done/ — recent completed tasks (last 7 days) for post ideas
- vault/Briefings/ — latest CEO briefing for business highlights
- vault/Company_Handbook.md — brand voice and communication rules

## Step 2 — Determine Post Type

| Post Type         | When to Use                       | Engagement Style                         |
| ----------------- | --------------------------------- | ---------------------------------------- |
| Achievement       | Project completed, milestone hit  | "We just did X — here's how"             |
| Insight           | Lesson learned from recent work   | "After doing X, I learned Y"             |
| Value             | Tip or advice for target audience | "3 things I wish I knew about X"         |
| Question          | Start a conversation              | "What's your biggest challenge with X?"  |
| Behind the scenes | Show your process                 | "Here's what my typical week looks like" |

## Step 3 — Write the Post

### LinkedIn Post Formula (High Engagement):

```
[HOOK — first line that stops the scroll]

[BLANK LINE — always leave this]

[Context or story setup — 1-2 lines]

[Main value/insight/achievement — 3-5 lines]

[Specific detail or example — makes it credible]

[Takeaway or lesson — what readers can apply]

[Call to action or question — drives comments]

[BLANK LINE]

[3-5 relevant hashtags]
```

### Hook Examples (Use as inspiration, not copy):

- "I built an AI employee that manages my Gmail and LinkedIn. Here's what happened."
- "Most developers are building chatbots. I built something different."
- "We completed Project Alpha 2 weeks early. Here's the one thing that made the difference."

### Writing Rules:

- Maximum 1300 characters total
- First line must work as a standalone hook — no context needed
- Short sentences. Easy to scan.
- One main idea per post — don't try to say everything
- Use numbers when possible ("3 lessons", "saved 18 hours", "$2,450 revenue")
- Be specific — vague posts get ignored
- No corporate jargon
- Write like a human, not a press release
- Always add 3-5 hashtags at the end
- Emoji are optional — use max 3 if you use them

## Step 4 — Create Approval File

Create file at vault/Pending_Approval/LINKEDIN_[YYYYMMDD_HHMMSS].md:

---

type: approval_request
action: linkedin_post
created: [ISO timestamp]
expires: [ISO timestamp + 48 hours]
post_type: [achievement/insight/value/question/behind_the_scenes]
status: pending

---

## Post Content

[Full LinkedIn post text exactly as it should be published]

## Why This Post

[1-2 sentences explaining what business goal this serves]

## Best Time to Post

Weekdays 8-10am or 5-6pm for highest engagement.
Current time: [current time] — [recommend posting now or scheduling]

## To Approve

Move this file to vault/Approved/ folder.
The LinkedIn watcher will publish it automatically.

## To Edit

Edit the text under "## Post Content" above, then move to vault/Approved/.

## To Reject

Move this file to vault/Rejected/ folder.

## Step 5 — Log

Append to vault/Logs/[YYYY-MM-DD].md:

```
[timestamp] | linkedin_draft | [post_type] | approval_requested
```

## Content Ideas Bank

If no specific trigger exists, check these sources for post ideas:

- Recent completed tasks in vault/Done/ from past 7 days
- Any achievements mentioned in vault/Briefings/
- Business goals progress from vault/Business_Goals.md
- Problems solved recently that others in your industry face
- Tools or techniques discovered while building this AI Employee project
