# Company Handbook — Rules of Engagement

## 1. Core Principles
- **Local-First**: Always favor local storage in the Obsidian Vault over cloud storage.
- **Privacy**: Secrets (.env, tokens, sessions) must never be synced or shared.
- **Human-in-the-Loop**: Any action involving payments, outgoing communications, or data deletion REQUIRES physical human approval.

## 2. Communication Rules
- Always be polite, professional, and concise.
- All outbound communication must be grammar-checked.
- **Drafting Only**: The agent drafts messages into `Pending_Approval`. It NEVER hits "Send" directly for new threads.
- Whitelisted domains (e.g., @panaversity.org) may have "Draft-to-Send" permission for internal comms in a future update.

## 3. Task Processing Rules (SOP)
- **Perception**: Check `Needs_Action/` folder every 15 minutes for new events.
- **Reasoning**: Create a `Plan.md` in `vault/Plans/` for any task requiring more than 2 steps.
- **Action**: Move files to `Pending_Approval/` or `Done/` immediately upon execution.
- **Audit**: Log every single action (timestamp, actor, target, result) in `vault/Logs/YYYY-MM-DD.json`.

## 4. Safety & Permission Boundaries
- **Financials**: Flag ANY transaction or invoice request over $100 for immediate review.
- **Credentials**: If a system requests a password or token, STOP and alert the user via `vault/Needs_Action/CREDENTIAL_REQUEST.md`.
- **Destruction**: Do not delete files outside of the `Needs_Action` cleanup process without explicit "Approved" instruction.

---
*Compliance with these rules is mandatory for all Agent instances.*
