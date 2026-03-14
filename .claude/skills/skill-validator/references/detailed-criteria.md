# Detailed Validation Criteria

Deep evaluation guidance for each criterion.

---

## 1. Structure & Anatomy

### 1.1 SKILL.md Exists
- **Score 3**: Present at root of skill directory
- **Score 0**: Missing = automatic fail

### 1.2 Line Count
- **Score 3**: <300 lines (lean and focused)
- **Score 2**: 300-500 lines (acceptable)
- **Score 1**: 500-800 lines (bloated, needs refactoring)
- **Score 0**: >800 lines (automatic fail - split into references)

**Why it matters**: Context window is a shared resource. Every line in SKILL.md competes with user's actual work.

### 1.3 Frontmatter Quality

**Score 3** - Complete, triggerable, proper format:
```yaml
---
name: skill-name  # lowercase, hyphens, ≤64 chars, matches directory
description: |    # ≤1024 chars, third-person style
  This skill creates X and validates Y.
  This skill should be used when users need to build widgets,
  generate reports, or process data.
---
```

**Score 2** - Present but format issues:
```yaml
---
name: skill-name
description: Creates X. Use when doing Y.  # Not third-person
---
```

**Score 1** - Minimal:
```yaml
---
name: skill-name
description: X skill
---
```

**Score 0**: Missing frontmatter

### 1.4 Name Constraints

**Score 3**: All constraints met
- Lowercase letters only
- Numbers allowed
- Hyphens for separation
- ≤64 characters
- Matches directory name exactly

**Score 2**: Minor violation (e.g., slightly over 64 chars)

**Score 1**: Multiple violations (e.g., uppercase, underscores)

**Score 0**: Name missing or completely invalid

### 1.5 Description Format

**Score 3** - [What] + [When] + Third-person:
```yaml
description: |
  Validates skills against production criteria.
  This skill should be used when reviewing, auditing, or
  improving skills to ensure quality standards.
```

**Score 2** - Has content but wrong style:
```yaml
description: |
  Validate skills against criteria.
  Use when reviewing skills.  # Not third-person
```

**Score 1** - Vague:
```yaml
description: Helps with skill stuff
```

**Score 0**: Missing or single word

### 1.6 No Extraneous Files

**Should NOT exist in skill directory**:
- README.md (SKILL.md IS the readme)
- CHANGELOG.md (version in frontmatter if needed)
- LICENSE (inherited from repo)
- package.json (unless skill runs scripts)
- .gitignore

**Exception**: `assets/`, `references/`, `scripts/` directories are expected.

### 1.7 Progressive Disclosure

**Score 3**:
- SKILL.md has overview + quick reference
- Complex patterns in `references/`
- Table of reference files with "when to read"

**Score 2**:
- Some content in references
- SKILL.md still has most detail

**Score 1**:
- References exist but poorly organized

**Score 0**:
- Everything in SKILL.md or no references

---

## 2. Content Quality

### 2.1 Conciseness

**Score 3** - Every sentence earns its place:
```markdown
## Quick Start
1. Define input schema
2. Implement handler
3. Register tool
```

**Score 1** - Verbose:
```markdown
## Quick Start
In this section, we will walk through the steps needed to get started with creating your tool. First, you will need to define an input schema. This schema specifies what parameters your tool accepts...
```

### 2.2 Imperative Form

**Score 3**:
```markdown
- Validate all inputs with Zod
- Return structured responses
- Handle errors gracefully
```

**Score 1**:
```markdown
- You should validate all inputs with Zod
- It would be good to return structured responses
- Try to handle errors gracefully
```

### 2.3 Appropriate Freedom

**Score 3** - Constraints where needed, flexibility elsewhere:
```markdown
## Required (No Exceptions)
- Use TypeScript strict mode
- Validate inputs at boundaries

## Flexible (Your Choice)
- Error message format
- Logging verbosity
```

**Score 1** - Either too rigid or too loose

### 2.4 Scope Clarity

**Score 3**:
```markdown
## What This Skill Does
- Creates X
- Validates Y
- Generates Z

## What This Skill Does NOT Do
- Production deployment
- Performance optimization
- Security auditing
```

**Score 1**: No explicit scope boundaries

### 2.5 Output Specification

**Score 3**:
```markdown
## Output Format
Every generated [artifact] includes:
- [ ] Component A with X property
- [ ] Component B following Y pattern
- [ ] Component C validated against Z
```

**Score 0**: No clear output definition

---

## 3. User Interaction

### 3.1 Clarification Triggers

**Score 3** - Structured clarification section:
```markdown
## Required Clarifications
Before proceeding, ask:
1. **Data shape**: "What structure will the input have?"
2. **Action type**: "Read-only or write?"

## Optional Clarifications
3. **Styling**: "Any design preferences?" (if relevant)
```

**Score 2**: Questions mentioned but unstructured

**Score 1**: "Ask questions if needed" without specifics

**Score 0**: No clarification guidance

### 3.2 Required vs Optional

**Score 3**: Clearly labeled required vs optional questions
**Score 1**: All questions treated equally

### 3.3 Context Awareness

**Score 3**:
```markdown
Before asking:
- Check conversation history for prior answers
- Infer from file names/content when possible
- Only ask what cannot be determined
```

**Score 0**: No guidance on using existing context

---

## 4. Documentation & References

### 4.1 Source URLs

**Score 3** - Table with official sources:
```markdown
| Resource | URL | Use For |
|----------|-----|---------|
| Official Guide | https://... | Core patterns |
| API Reference | https://... | Method details |
```

**Score 2**: URLs mentioned but scattered

**Score 1**: One or two links buried in text

**Score 0**: No external references

### 4.2 Fetch Guidance

**Score 3**:
```markdown
For patterns not covered here, fetch from official docs:
- Complex widget: https://...
- Advanced auth: https://...
```

**Score 0**: No guidance for unlisted scenarios

### 4.3 Example Coverage

**Score 3**:
```markdown
### Good Example
[working code]

### Bad Example (Don't Do This)
[antipattern with explanation why]
```

**Score 1**: Only good examples, no antipatterns

---

## 5. Domain Standards

### 5.1 Best Practices Enforcement

**Score 3** - Mandatory checklist:
```markdown
### Must Follow
- [ ] WCAG AA contrast (4.5:1)
- [ ] Keyboard navigation
- [ ] Error states

### Must Avoid
- Nested scrolling
- Hardcoded strings
```

**Score 1**: Mentions best practices without enforcement

### 5.2 Quality Gates

**Score 3** - Output checklist before delivery:
```markdown
## Output Checklist
Before delivering, verify:
- [ ] All required components present
- [ ] Follows naming convention
- [ ] No hardcoded values
- [ ] Tested against criteria
```

**Score 0**: No quality gate

---

## 6. Technical Robustness

### 6.1 Error Handling

**Score 3**:
```markdown
## Error Handling
- Invalid input: Return validation error with specifics
- Network failure: Retry with backoff, then graceful fallback
- Unknown error: Log context, return safe default
```

**Score 0**: No error handling guidance

### 6.2 Security Considerations

**Score 3** (when relevant):
```markdown
## Security
- Never hardcode secrets
- Validate/sanitize all user input
- Use parameterized queries
```

**Score 2**: Mentions security generally
**Score 0**: No security guidance (when relevant)

### 6.3 Dependencies

**Score 3**:
```markdown
## Dependencies
- Requires: Node.js 18+, TypeScript 5+
- Optional: Redis for caching
- External APIs: None / List with rate limits
```

**Score 0**: Dependencies not documented

---

## 7. Maintainability

### 7.1 Modularity

**Score 3** - Self-contained reference files:
```
references/
├── core-patterns.md      # Can be read independently
├── advanced-usage.md     # Self-contained advanced topic
└── troubleshooting.md    # Standalone help
```

**Score 1**: References that require reading other files first

### 7.2 Update Path

**Score 3**:
```markdown
## Keeping Current
- Fetch latest from [URL] for new patterns
- Check [changelog URL] for breaking changes
- Last verified: 2024-12
```

**Score 0**: No update guidance

### 7.3 Clear Organization

**Score 3** - Logical flow:
1. What (overview)
2. When (triggers)
3. How (workflow)
4. Reference (details)
5. Examples

**Score 1**: Scattered organization, hard to navigate

---

## 8. Zero-Shot Implementation

Skills should enable single-interaction implementation with embedded expertise.

### 8.1 Before Implementation Section

**Score 3** - Complete context gathering:
```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing structure, patterns, conventions |
| **Conversation** | User's specific requirements |
| **Skill References** | Domain patterns from `references/` |
| **User Guidelines** | Project-specific conventions |

Ensure all required context is gathered before implementing.
```

**Score 2**: Mentions gathering context but incomplete sources

**Score 1**: Brief "check context first" note

**Score 0**: No context gathering guidance

### 8.2 Embedded Expertise

**Score 3** - Domain knowledge IN the skill:
- Best practices documented in `references/`
- Code examples included
- Anti-patterns listed
- Library/API documentation embedded

**Score 2**: Some expertise embedded, some requires runtime discovery

**Score 1**: Mostly relies on runtime discovery ("search for..." instructions)

**Score 0**: No embedded domain expertise

**Red flags**:
- "Research the domain..."
- "Fetch documentation for..."
- "Discover best practices..."

These indicate runtime discovery instead of embedded expertise.

### 8.3 User-Only Questions

**Score 3** - Only asks about USER's context:
```markdown
| Ask | Don't Ask |
|-----|-----------|
| "What's YOUR use case?" | "What is [technology]?" |
| "What's YOUR tech stack?" | "What options exist?" |
| "Specific constraints?" | "What are best practices?" |
```

**Score 2**: Mostly user questions, some domain questions

**Score 1**: Mixes user and domain questions

**Score 0**: Asks user for domain knowledge skill should contain

---

## 9. Reusability

Skills should handle variations, not single requirements.

### 9.1 Handles Variations

**Score 3** - Explicitly adaptable:
```markdown
This skill adapts to:
- Different data shapes
- Multiple output formats
- Various libraries/frameworks
```

**Score 2**: Some variability but limited

**Score 1**: Works for narrow range of cases

**Score 0**: Hardcoded to single requirement

### 9.2 Variable vs Constant Analysis

**Score 3** - Clear separation:
```markdown
## What VARIES (ask user)
- Data shape/structure
- Tool/library preference
- Output format

## What's CONSTANT (encoded in skill)
- Best practices
- Error handling patterns
- Security requirements
```

**Score 2**: Implicit separation

**Score 1**: Mixed without clear distinction

**Score 0**: No consideration of variability

### 9.3 Not Requirement-Specific

**Score 3** - Generic within domain:
```markdown
# Good: "Create visualizations"
Adapts to chart type, library, data shape

# Good: "Deploy applications"
Adapts to platform, orchestration, environment
```

**Score 0** - Too specific:
```markdown
# Bad: "Create bar chart with sales data using Recharts"
# Bad: "Deploy to AWS EKS with Helm"
```

### 9.4 Abstraction Level

| Level | Description | Score |
|-------|-------------|-------|
| Domain-agnostic | Works across domains | 3 |
| Domain-specific, tool-agnostic | Within domain, any tool | 3 |
| Tool-specific, workflow-agnostic | Specific tool, flexible workflow | 2 |
| Requirement-specific | Single use case | 0 |

---

## 10. Type-Specific Criteria

### 10.1 Builder Skills

Must have ALL of:
- [ ] Required Clarifications section
- [ ] Output Specification
- [ ] Domain Standards (Must Follow / Must Avoid)
- [ ] Output Checklist

**Score 3**: All present and detailed
**Score 2**: All present, some minimal
**Score 1**: Missing 1-2 elements
**Score 0**: Missing 3+ elements

### 10.2 Guide Skills

Must have ALL of:
- [ ] Workflow Steps (numbered, sequential)
- [ ] Good/Bad Examples
- [ ] Official Documentation links

**Score 3**: All present with clear examples
**Score 2**: All present, examples minimal
**Score 1**: Missing 1 element
**Score 0**: Missing 2+ elements

### 10.3 Automation Skills

Must have ALL of:
- [ ] Scripts in `scripts/` directory
- [ ] Dependencies documented
- [ ] Error Handling guidance
- [ ] Input/Output Specification

**Score 3**: All present, scripts tested
**Score 2**: All present, minimal documentation
**Score 1**: Missing 1-2 elements
**Score 0**: Missing 3+ elements or no scripts

### 10.4 Analyzer Skills

Must have ALL of:
- [ ] Analysis Scope (what to analyze, what to ignore)
- [ ] Evaluation Criteria
- [ ] Output Format specification
- [ ] Synthesis guidance

**Score 3**: All present with clear criteria
**Score 2**: All present, criteria vague
**Score 1**: Missing 1-2 elements
**Score 0**: Missing 3+ elements

### 10.5 Validator Skills

Must have ALL of:
- [ ] Quality Criteria with weights
- [ ] Scoring Rubric (0-3 or similar)
- [ ] Pass/Fail Thresholds
- [ ] Remediation guidance

**Score 3**: All present with clear thresholds
**Score 2**: All present, thresholds vague
**Score 1**: Missing 1-2 elements
**Score 0**: Missing 3+ elements
