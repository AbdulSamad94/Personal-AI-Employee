# Improvement Patterns

Common fixes for common skill validation issues.

---

## Structure Issues

### Problem: SKILL.md Too Long (>500 lines)

**Fix**: Extract to references

```
Before:
SKILL.md (800 lines with everything)

After:
SKILL.md (200 lines - overview + quick ref)
references/
├── detailed-patterns.md (300 lines)
├── advanced-usage.md (200 lines)
└── troubleshooting.md (100 lines)
```

**Add reference table**:
```markdown
## Reference Files

| File | When to Read |
|------|--------------|
| `references/detailed-patterns.md` | Complex implementations |
| `references/advanced-usage.md` | Non-standard scenarios |
```

### Problem: README.md Exists

**Fix**: Delete it. SKILL.md IS the readme.

### Problem: No Progressive Disclosure

**Fix**: Create references/ directory with topical files:
1. Identify independent topics in SKILL.md
2. Extract each to `references/[topic].md`
3. Add "when to read" guidance in SKILL.md

---

## Content Issues

### Problem: Verbose Content

**Before**:
```markdown
In this section, we will walk through the process of creating a new widget.
First, you will want to understand what data your widget needs to display.
This is important because the data shape determines how you structure your component.
```

**After**:
```markdown
## Creating a Widget

1. Define data shape (what `toolOutput` contains)
2. Choose display mode (inline/fullscreen/pip)
3. Implement with theme support
```

### Problem: "You should" Instead of Imperatives

**Before**:
```markdown
- You should validate all inputs
- It would be good to handle errors
- Try to follow the patterns
```

**After**:
```markdown
- Validate all inputs with Zod
- Handle errors with try/catch
- Follow these patterns:
```

### Problem: No Scope Boundaries

**Fix**: Add explicit sections:

```markdown
## What This Skill Does
- Creates X
- Validates Y
- Generates Z

## What This Skill Does NOT Do
- Deploy to production
- Optimize performance
- Handle authentication
```

---

## User Interaction Issues

### Problem: No Clarification Questions

**Fix**: Add structured clarification section:

```markdown
## Required Clarifications

Before building, ask:

1. **Data shape**: "What will `toolOutput` contain?"
   ```json
   Example: { items: [...], total: 10 }
   ```

2. **Action type**: "Display only or interactive?"
   - Display → No callTool needed
   - Interactive → Need tool name and params

3. **Display mode**: "Inline, fullscreen, or pip?"

## Optional Clarifications

4. **Styling**: "Any design preferences?" (ask if complex UI)
```

### Problem: All Questions Treated Equally

**Fix**: Separate required from optional:

```markdown
## Required (Must Ask)
1. Core question A
2. Core question B

## Optional (Ask if Relevant)
3. Nice-to-know question
4. Edge case question
```

### Problem: No Context Awareness

**Fix**: Add context-checking guidance:

```markdown
## Before Asking

Check existing context:
- Review conversation history for prior answers
- Infer from file names when possible
- Check toolOutput structure if available

Only ask what cannot be determined.
```

---

## Documentation Issues

### Problem: No Official Source Links

**Fix**: Add documentation table:

```markdown
## Official Documentation

| Resource | URL | Use For |
|----------|-----|---------|
| Getting Started | https://... | Basic setup |
| API Reference | https://... | Method details |
| Best Practices | https://... | Pattern guidance |

For patterns not covered here, fetch from official docs.
```

### Problem: No Fetch Guidance

**Fix**: Add on-the-go learning section:

```markdown
## Unlisted Scenarios

For patterns not documented here:

1. Fetch from official docs: [URL]
2. Apply same validation criteria
3. Follow established patterns in this skill

Examples of when to fetch:
- Complex authentication flows
- Third-party integrations
- Platform-specific features
```

### Problem: No Examples

**Fix**: Add good/bad examples:

```markdown
### Good Example
```typescript
// Correct pattern with explanation
const data = window.openai?.toolOutput ?? defaultValue;
```

### Bad Example (Don't Do This)
```typescript
// Why this is wrong
const data = window.openai.toolOutput; // Crashes if undefined
```
```

---

## Domain Standards Issues

### Problem: Best Practices Mentioned But Not Enforced

**Before**:
```markdown
Follow accessibility best practices.
```

**After**:
```markdown
## Accessibility Requirements

### Must Follow
- [ ] WCAG AA contrast (4.5:1 for text)
- [ ] Keyboard navigation for all interactions
- [ ] Focus indicators visible
- [ ] Screen reader labels for icons

### Must Avoid
- Color as only indicator
- Mouse-only interactions
- Auto-playing media without controls
```

### Problem: No Output Checklist

**Fix**: Add quality gate:

```markdown
## Output Checklist

Before delivering, verify ALL items:

### Functional
- [ ] Core feature works
- [ ] Error states handled
- [ ] Loading states present

### Quality
- [ ] Follows naming conventions
- [ ] No hardcoded values
- [ ] Comments where non-obvious

### Standards
- [ ] Passes domain requirements (above)
- [ ] Tested against criteria
```

---

## Technical Issues

### Problem: No Error Handling Guidance

**Fix**: Add error handling section:

```markdown
## Error Handling

| Scenario | Action |
|----------|--------|
| Invalid input | Return validation error with specifics |
| Network failure | Retry 3x with backoff, then fallback |
| Unknown error | Log context, return safe default |

### Error Response Format
```typescript
return {
  isError: true,
  content: [{ type: 'text', text: 'User-friendly message' }],
  _meta: { errorCode: 'VALIDATION_FAILED', details: {...} }
};
```
```

### Problem: No Security Guidance

**Fix**: Add security section (when relevant):

```markdown
## Security Considerations

- **Never hardcode**: Secrets, API keys, tokens
- **Always validate**: User input, file paths, URLs
- **Escape output**: Prevent XSS in generated HTML
- **Use parameterized**: Queries to prevent injection
```

### Problem: Dependencies Not Listed

**Fix**: Add dependencies section:

```markdown
## Dependencies

### Required
- Node.js 18+
- TypeScript 5.0+

### Optional
- Redis (for caching)

### External APIs
- OpenAI Apps SDK (via window.openai)
- No rate limits apply to widget
```

---

## Maintainability Issues

### Problem: Monolithic SKILL.md

**Fix**: Modularize into references:

1. Identify 3-5 independent topics
2. Create `references/[topic].md` for each
3. Keep SKILL.md as entry point with "when to read" table

### Problem: No Update Guidance

**Fix**: Add versioning section:

```markdown
## Keeping Current

- Official docs: [URL]
- Changelog: [URL]
- Last verified: 2024-12

When official docs update:
1. Check for breaking changes
2. Update affected references
3. Test against validation criteria
```

### Problem: Hardcoded Values

**Before**:
```markdown
Set timeout to 5000ms.
Use port 3000.
```

**After**:
```markdown
Set timeout (default: 5000ms, adjust for your use case).
Use configured port (default: 3000).
```

---

## Zero-Shot Implementation Issues

### Problem: Runtime Discovery Instead of Embedded Expertise

**Before (Bad)**:
```markdown
## Implementation
1. Research the domain best practices
2. Fetch library documentation
3. Discover common patterns
4. Implement based on findings
```

**After (Good)**:
```markdown
## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing structure, patterns, conventions |
| **Conversation** | User's specific requirements |
| **Skill References** | Domain patterns from `references/` |
| **User Guidelines** | Project-specific conventions |

## Implementation
1. Apply patterns from `references/best-practices.md`
2. Follow examples in `references/examples.md`
3. Avoid anti-patterns in `references/anti-patterns.md`
```

### Problem: Asking User for Domain Knowledge

**Before (Bad)**:
```markdown
## Clarifications
1. What is Kafka and how does it work?
2. What are Kafka best practices?
3. What libraries are available?
```

**After (Good)**:
```markdown
## Required Clarifications

Ask about USER's context (domain expertise is in this skill):

1. **Use case**: "What's YOUR specific use case?"
2. **Tech stack**: "What's YOUR environment?"
3. **Constraints**: "Any specific requirements?"

Note: Domain best practices are embedded in `references/`.
```

### Problem: No Context Gathering Guidance

**Fix**: Add Before Implementation section:

```markdown
## Before Implementation

Gather context from available sources:
1. **Codebase** (if exists): Scan structure, patterns, conventions
2. **Conversation**: Review discussed requirements and decisions
3. **Skill References**: Apply embedded domain expertise
4. **User Guidelines**: Follow project-specific conventions

Adapt approach based on available context.
Only ask user for what cannot be discovered.
```

---

## Reusability Issues

### Problem: Hardcoded to Single Requirement

**Before (Bad)**:
```markdown
# Sales Dashboard Creator

Creates a bar chart showing monthly sales using Recharts.

## Output
- Bar chart component
- Uses blue color scheme
- Shows last 12 months
```

**After (Good)**:
```markdown
# Data Visualization Creator

Creates visualizations adaptable to data shape, chart type, and library.

## Required Clarifications
1. **Data shape**: "What structure will input have?"
2. **Chart type**: "Bar, line, pie, or other?"
3. **Library**: "Recharts, D3, Chart.js, or no preference?"

## Output
Adapts based on clarifications.
```

### Problem: No Variability Analysis

**Fix**: Add Varies vs Constant section:

```markdown
## Variability Analysis

| What VARIES (ask user) | What's CONSTANT (encoded) |
|------------------------|---------------------------|
| Data shape/structure | Accessibility requirements |
| Chart type preference | Responsive patterns |
| Library choice | Error handling |
| Color scheme | Loading states |
```

### Problem: Too Specific Abstraction Level

**Before (Bad)**:
```markdown
# AWS EKS Helm Deployment

Deploys to AWS EKS using Helm charts.
```

**After (Good)**:
```markdown
# Application Deployment

Deploys applications with adaptable platform, orchestration, and configuration.

## Required Clarifications
1. **Platform**: "AWS, GCP, Azure, or other?"
2. **Orchestration**: "Kubernetes, ECS, serverless?"
3. **Configuration**: "Helm, Terraform, CDK?"
```

---

## Frontmatter Issues

### Problem: Wrong Description Style

**Before (Bad)**:
```yaml
description: |
  Create widgets for apps.
  Use when building UI components.
```

**After (Good)**:
```yaml
description: |
  Creates production widgets for applications.
  This skill should be used when users want to build
  UI components, visual interfaces, or interactive elements.
```

### Problem: Name Constraint Violations

**Before (Bad)**:
```yaml
name: Widget_Creator    # Uppercase, underscores
name: my-super-long-skill-name-that-exceeds-the-sixty-four-character-limit  # Too long
```

**After (Good)**:
```yaml
name: widget-creator    # Lowercase, hyphens, ≤64 chars
```

### Problem: Description Too Long or Missing Format

**Fix**: Use [What] + [When] format, ≤1024 chars:

```yaml
description: |
  [What] Creates X, validates Y, generates Z.
  [When] This skill should be used when users need to
  build widgets, review code, or process data.
```

---

## Type-Specific Issues

### Problem: Builder Skill Missing Required Sections

**Fix**: Add all required sections:

```markdown
## Required Clarifications
1. Question about input
2. Question about output

## Output Specification
[Define what artifact looks like]

## Domain Standards
### Must Follow
- [ ] Requirement 1
### Must Avoid
- Anti-pattern 1

## Output Checklist
- [ ] Meets requirements
- [ ] Follows standards
```

### Problem: Analyzer Skill Missing Scope

**Fix**: Add analysis scope:

```markdown
## Analysis Scope

### What to Analyze
- Code structure
- Naming conventions
- Error handling

### What to Ignore
- Comments and formatting
- Third-party libraries
- Generated code

## Evaluation Criteria
| Criterion | Weight | How to Assess |
|-----------|--------|---------------|
| Readability | 30% | Naming, structure |
| Robustness | 40% | Error handling |
| Performance | 30% | Complexity |
```

### Problem: Validator Skill Missing Thresholds

**Fix**: Add clear thresholds:

```markdown
## Scoring Rubric
- **3**: Excellent
- **2**: Adequate
- **1**: Needs improvement
- **0**: Missing/Fail

## Thresholds
| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Pass | Ready for use |
| 70-89 | Conditional | Minor fixes needed |
| <70 | Fail | Major rework required |

## Remediation
| Issue | Fix |
|-------|-----|
| Missing X | Add X section |
| Weak Y | Strengthen with examples |
```

---

## Quick Improvement Checklist

When improving a skill, address in this order:

1. **Critical** (blocks usage):
   - [ ] SKILL.md exists and <500 lines
   - [ ] Frontmatter: name (≤64, lowercase) + description (≤1024, third-person)
   - [ ] Core workflow documented

2. **High Priority** (major quality):
   - [ ] Before Implementation section (context gathering)
   - [ ] Domain expertise embedded in `references/`
   - [ ] Clarification questions (for builder skills)
   - [ ] Output specification

3. **Medium Priority** (polish):
   - [ ] Handles variations (not requirement-specific)
   - [ ] Progressive disclosure to references
   - [ ] Error handling guidance
   - [ ] Good/bad examples

4. **Low Priority** (excellence):
   - [ ] Type-specific sections complete
   - [ ] Update path documented
   - [ ] All edge cases covered
   - [ ] Templates in assets/
