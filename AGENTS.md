# AGENTS.md — 0Skills Workspace Guide

Welcome to the **0Skills** workspace. This document establishes the operational rules, development standards, architectural conventions, and workflow guidelines for all AI agents collaborating in this repository.

---

## 1. Project Overview & Mission

- **Workspace**: `0Skills`
- **Purpose**: A structured, modular repository dedicated to building, testing, and managing AI agent skills, workflows, automation scripts, and foundational components from the ground up.
- **Core Philosophy**:
  - **Zero Assumptions**: Always verify facts and inspect files directly; never guess repository state.
  - **Modular Architecture**: Keep skills, utilities, and components strictly decoupled, self-contained, and reusable.
  - **High Reliability**: Every feature, tool, or skill must have clear verification steps, robust error handling, and documentation.

---

## 2. Agent Principles & Operating Agreement

All agents operating in this workspace must adhere to the following principles:

1. **Context-First Execution**:
   - Inspect existing workspace files, configurations, and dependencies before proposing or implementing changes.
   - Respect project conventions, file structures, and existing patterns.
2. **Minimal & Non-Destructive Edits**:
   - Apply targeted, precise modifications instead of large unneeded file rewrites.
   - Preserve comments, type signatures, and docstrings unless explicitly asked to modify them.
3. **Execution Safety**:
   - Never execute destructive commands (`rm -rf`, hard resets, external uploads of sensitive data).
   - Ensure long-running commands (servers, watchers) are properly tracked and managed.
4. **Verifiable Completion**:
   - Do not claim a task is complete until it has been verified (syntax checks, linters, unit tests, or runtime verification).
5. **Concise, Transparent Communication**:
   - Keep responses concise, structured, and actionable.
   - Provide clickable file links using markdown format: `[filename](file:///path/to/file)`.

---

## 3. Directory Layout & Architecture

The workspace follows this organizational pattern:

```text
0Skills/
├── AGENTS.md               # Repository rules & agent operating guidelines (this file)
├── .agents/                # Project-scoped agent customizations
│   ├── skills/             # Modular agent skills (e.g., .agents/skills/<name>/SKILL.md)
│   ├── rules/              # Granular, directory-specific rule files
│   └── workflows/          # Automation recipes and multi-step runbooks
├── src/                    # Source code (tools, libraries, runtimes)
├── tests/                  # Test suites, fixtures, and verification scripts
└── docs/                   # Technical specs, architecture guides, and references
```

---

## 4. Development Workflow

Follow this 5-stage lifecycle for every non-trivial task:

```mermaid
flowchart LR
    A[1. Discover & Analyze] --> B[2. Plan & Align]
    B --> C[3. Implement with Precision]
    C --> D[4. Verify & Test]
    D --> E[5. Document & Review]
```

1. **Discover & Analyze**:
   - Read relevant files and assess dependencies.
   - Identify edge cases, potential failure points, and scope limitations.
2. **Plan & Align**:
   - Formulate a clear implementation plan before taking complex action.
   - Clarify design ambiguities when needed.
3. **Implement with Precision**:
   - Write clean, idiomatic, well-commented code.
   - Adhere to separation of concerns and avoid unnecessary dependencies.
4. **Verify & Test**:
   - Run tests, check syntax, and validate behavior against edge cases.
5. **Document & Review**:
   - Update relevant documentation and provide clear summaries of changes.

---

## 5. Coding & Quality Standards

- **Language & Idioms**: Write modern, readable code following standard linting and formatting conventions.
- **Type Safety**: Favor strong typing (e.g., TypeScript, Python type annotations) across all interfaces.
- **Error Handling**: Handle errors explicitly at service boundaries; avoid silent exception suppression.
- **Security & Hygiene**: Never commit secrets, credentials, or API keys. Use `.env` or configuration stores.

---

## 6. Skills Management (`.agents/skills/`)

When defining new skills for this workspace:

- **Structure**: Place each skill in `.agents/skills/<skill-name>/` containing a `SKILL.md`.
- **Frontmatter**: Include valid YAML frontmatter with `name` and `description`:
  ```yaml
  ---
  name: example-skill
  description: Clear, concise summary of what this skill does and when to activate it.
  ---
  ```
- **Instructions**: Detail prerequisites, step-by-step procedures, tool invocations, and validation checks.
- **Progressive Loading**: Keep skills self-contained so they load on-demand without context bloat.

---

## 7. Common Commands & Runbooks

> *Update this section as project tooling and scripts are added.*

| Task | Command | Description |
| :--- | :--- | :--- |
| **Lint / Format** | *(To be configured)* | Run static code analysis and format checks |
| **Test** | *(To be configured)* | Run automated test suite |
| **Build** | *(To be configured)* | Compile or bundle project assets |

---

*Last Updated: 2026-09-10*
