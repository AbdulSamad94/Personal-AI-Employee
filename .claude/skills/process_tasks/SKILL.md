---
name: Process Tasks
description: |
  Processes all pending Markdown files in /Needs_Action. For each file, Claude will determine the required action, create a plan entry in /Plans, safely execute the action if allowed, update Dashboard.md, move the file to /Done, and log the activity in a dated log file.
---

## Instructions

1. **Identify Pending Files**
   - List all `.md` files in `/Needs_Action`.

2. **Determine Required Action**
   - Read each file carefully.
   - Identify tasks or instructions in the file.
   - Ignore any tasks involving payments, sensitive data, or emails unless explicitly approved.

3. **Create Plan Entry**
   - For each task, generate a concise plan entry and save it in `/Plans` as a Markdown file named after the original file (e.g., `task1.md`).

4. **Execute Safe Actions**
   - Only perform actions that are safe and non-sensitive.
   - Skip or flag unsafe actions for human review.

5. **Update Dashboard**
   - After processing each file, append a summary line to `Dashboard.md`:
     ```
     YYYY-MM-DD: Processed <filename>, executed <safe actions count>, skipped <unsafe actions count>
     ```

6. **Move Processed File**
   - Move each successfully processed file from `/Needs_Action` to `/Done`.

7. **Log Activity**
   - For each processed file, append a detailed log entry to `/Logs/YYYY-MM-DD.log`:
     ```
     [TIME] Processed <filename>: safe actions executed: X, unsafe actions skipped: Y
     ```

---

## Rules

- Always follow `Company_Handbook.md`.
- Never send emails or make payments without explicit approval.
- Dashboard.md must reflect every processed task immediately.
- Logs must be detailed enough for audit purposes.

---

## Examples

**Input File (`/Needs_Action/fix-login.md`)**:
