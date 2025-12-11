---
agent: 'agent'
description: 'Execute an implementation plan systematically, completing all phases and tasks, with validation after each phase, culminating in a pull request for review.'
tools: ['vscode', 'execute', 'read', 'edit', 'search', 'web', 'github/*', 'copilot-container-tools/*', 'agent', 'pylance-mcp-server/*', 'memory', 'github.vscode-pull-request-github/copilotCodingAgent', 'github.vscode-pull-request-github/issue_fetch', 'github.vscode-pull-request-github/suggest-fix', 'github.vscode-pull-request-github/searchSyntax', 'github.vscode-pull-request-github/doSearch', 'github.vscode-pull-request-github/renderIssues', 'github.vscode-pull-request-github/activePullRequest', 'github.vscode-pull-request-github/openPullRequest', 'ms-vscode.vscode-websearchforcopilot/websearch', 'todo']
---

# Execute Implementation Plan

## Primary Directive

Execute the implementation plan located at `${input:PlanPath:plan/*.md}` systematically and completely. Process each phase sequentially, complete all tasks within each phase, validate success criteria, and culminate in creating a pull request for review and merge into the main branch.

## Execution Context

This prompt is designed for autonomous AI agent execution. The agent must interpret and execute the implementation plan literally, tracking progress, handling errors gracefully, and documenting all changes. Human intervention should only be required for ambiguous requirements or blocking issues.

## Input Requirements

| Input | Description | Required |
|-------|-------------|----------|
| `PlanPath` | Relative path to the implementation plan markdown file | Yes |
| `TargetBranch` | Branch to create PR against (default: `main`) | No |
| `DryRun` | If "true", validate plan without executing changes | No |

## Pre-Execution Checklist

Before beginning execution, the agent MUST complete these validation steps:

1. **Read the Implementation Plan**: Parse the entire plan file and extract:
   - Total number of phases
   - Total number of tasks per phase
   - All file paths mentioned in FILE-* entries
   - All test requirements from TEST-* entries
   - All dependencies from DEP-* entries
   - Success criteria and constraints

2. **Validate Workspace State**:
   - Confirm all referenced files exist (or are marked for creation)
   - Verify no uncommitted changes that could conflict
   - Check current branch matches expected development branch
   - Verify all DEP-* dependencies are available

3. **Create Execution Manifest**: Generate a structured task list for tracking:

   ```markdown
   ## Execution Manifest
   - Plan: [Plan Title]
   - Total Phases: [N]
   - Total Tasks: [M]
   - Start Time: [ISO 8601 timestamp]
   - Current Phase: 1
   - Current Task: TASK-001
   ```

4. **Establish Baseline**:
   - Run existing tests to confirm green baseline (if tests exist)
   - Note any pre-existing errors or warnings
   - Document current codebase state

## Phase Execution Protocol

For EACH phase in the implementation plan, execute the following workflow:

### Phase Entry

1. **Announce Phase Start**:

   ```
   ═══════════════════════════════════════════════════════════
   PHASE [N]: [Phase Title]
   GOAL: [GOAL-XXX description]
   Tasks: [count] | Estimated Files: [count]
   ═══════════════════════════════════════════════════════════
   ```

2. **Read Phase Requirements**: Extract all tasks, their descriptions, and any inter-task dependencies within the phase.

3. **Plan Task Execution Order**: Identify tasks that can be executed in parallel vs. those with dependencies.

### Task Execution

For EACH task (TASK-XXX) within the phase:

1. **Task Announcement**:

   ```
   ───────────────────────────────────────────────────────────
   TASK-XXX: [Task Description]
   Files: [list affected files]
   ───────────────────────────────────────────────────────────
   ```

2. **Execute Task Actions**:
   - If task involves file deletion: Delete the file, verify deletion
   - If task involves file creation: Create file with specified content
   - If task involves file modification: Make the changes, preserve surrounding code
   - If task involves running commands: Execute and capture output
   - If task involves multiple files: Use batch operations when possible

3. **Task Validation**:
   - Verify the change was applied correctly
   - Check for syntax errors or linting issues
   - Confirm no unintended side effects
   - Run relevant unit tests if specified

4. **Task Completion Recording**:
   - Update the implementation plan file: Mark task as ✅ with current date
   - Log completion in execution manifest

5. **Error Handling** (if task fails):
   - Document the error with full context
   - Attempt automated fix if pattern is recognizable
   - If fix fails, log as blocked and continue to next task
   - At phase end, report all blocked tasks

### Phase Exit

1. **Phase Validation**: Execute all TEST-* items associated with this phase:
   - Run unit tests: `uv run pytest` (Python) or `dotnet test` (C#)
   - Run linting: `uv run ruff check` (Python) or build warnings (C#)
   - Verify no new errors introduced

2. **Phase Summary**:

   ```
   ═══════════════════════════════════════════════════════════
   PHASE [N] COMPLETE
   ✅ Completed: [X] tasks
   ⚠️ Blocked: [Y] tasks (if any)
   ❌ Failed: [Z] tasks (if any)
   Tests: [PASS/FAIL] | Lint: [PASS/FAIL]
   ═══════════════════════════════════════════════════════════
   ```

3. **Commit Phase Changes**:
   - Stage all modified files: `git add .`
   - Create atomic commit with message:

     ```
     refactor(phase-N): [Phase Title]

     Completed tasks:
     - TASK-XXX: [description]
     - TASK-YYY: [description]
     ...

     Part of: [Plan Title]
     ```

4. **Proceed to Next Phase** (if current phase passed validation)

## Post-Execution Protocol

After ALL phases are complete:

### Final Validation

1. **Run Full Test Suite**:

   ```bash
   # Python tests
   uv run pytest --tb=short

   # C# tests (if applicable)
   dotnet test
   ```

2. **Run Full Lint Check**:

   ```bash
   # Python
   uv run ruff check .
   uv run ruff format --check .

   # C# (build with warnings as errors)
   dotnet build -warnaserror
   ```

3. **Verify Build Success**:

   ```bash
   # Python package
   uv build

   # C# / .NET
   dotnet build -c Release
   ```

4. **Documentation Validation**:
   - Verify all updated markdown files have no broken links
   - Confirm README reflects current state
   - Check that version numbers are consistent across files

### Update Project Tracking

1. **Update Implementation Plan Status**:
   - Change front matter `status` from `'Planned'` or `'In progress'` to `'Completed'`
   - Ensure all TASK-* rows have ✅ and dates

2. **Update Memory Bank** (if present):
   - Update `activeContext.md` with completion status
   - Update `progress.md` with achievements
   - Update `tasks/_index.md` to move task to Completed

3. **Generate CHANGELOG Entry** (if CHANGELOG.md exists):

   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD

   ### Changed
   - [List of changes from this plan]

   ### Removed
   - [List of deletions from this plan]

   ### Fixed
   - [List of fixes from this plan]
   ```

### Create Pull Request

1. **Push Branch**:

   ```bash
   git push origin [current-branch]
   ```

2. **Create Pull Request** with the following structure:

   **Title**: `[Plan Type]: [Plan Goal]`

   **Body**:

   ```markdown
   ## Summary

   This PR implements the changes specified in `[PlanPath]`.

   ## Implementation Plan

   [Link to plan file or embed summary]

   ## Changes Made

   ### Phase 1: [Title]
   - ✅ TASK-001: [description]
   - ✅ TASK-002: [description]
   ...

   ### Phase N: [Title]
   - ✅ TASK-XXX: [description]
   ...

   ## Validation

   - [x] All unit tests passing
   - [x] All linting checks passing
   - [x] Build succeeds
   - [x] Documentation updated
   - [x] No breaking changes (or documented if any)

   ## Test Results

   ```
   [Paste test output summary]
   ```

   ## Reviewer Notes

   [Any special considerations for reviewers]
   ```

3. **Request Review** (if configured):
   - Add appropriate reviewers based on CODEOWNERS
   - Add relevant labels (e.g., `refactor`, `documentation`, `enhancement`)

## Error Recovery Procedures

### Blocking Error Types

| Error Type | Recovery Action |
|------------|-----------------|
| File not found | Check if file was renamed; search for similar files; mark task blocked |
| Syntax error after edit | Revert change; re-analyze task; attempt alternative approach |
| Test failure | Analyze failure; fix if related to current task; else mark blocked |
| Merge conflict | Attempt auto-resolve; if complex, mark PR as needs-attention |
| Build failure | Check error output; fix if related to changes; else escalate |
| Dependency missing | Attempt install via package manager; mark blocked if unavailable |

### Escalation Protocol

If the agent encounters an unrecoverable error:

1. Document the error with full context and stack trace
2. List attempted recovery actions
3. Create an issue or comment describing the blockage
4. Commit partial progress with WIP marker
5. Push branch and create draft PR with blocking issue documented

## Success Criteria

The implementation plan execution is considered **SUCCESSFUL** when:

- ✅ All phases completed (or blocked tasks documented)
- ✅ All tests passing (existing + new)
- ✅ All linting checks passing
- ✅ Build succeeds for all targets
- ✅ Implementation plan status updated to `'Completed'`
- ✅ Pull request created with full documentation
- ✅ No untracked changes remaining in workspace

## Output Summary Template

Upon completion, provide this summary:

```markdown
# Execution Complete

## Plan: [Plan Title]
**Status**: ✅ COMPLETED | ⚠️ PARTIAL | ❌ FAILED

## Metrics
| Metric | Value |
|--------|-------|
| Total Phases | [N] |
| Total Tasks | [M] |
| Completed | [X] |
| Blocked | [Y] |
| Failed | [Z] |
| Execution Time | [duration] |

## Commits
- `[hash]` - Phase 1: [title]
- `[hash]` - Phase 2: [title]
...

## Pull Request
**URL**: [PR URL]
**Status**: Ready for Review | Draft

## Blocked Tasks (if any)
| Task | Reason | Suggested Action |
|------|--------|------------------|
| TASK-XXX | [reason] | [action] |

## Next Steps
1. [Reviewer action needed]
2. [Any follow-up tasks]
```

## Execution Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Parse and validate plan without making changes |
| `--continue` | Resume from last completed task (reads plan ✅ markers) |
| `--phase=N` | Execute only phase N |
| `--skip-tests` | Skip test validation (not recommended) |
| `--no-commit` | Make changes but don't commit (for review) |

## Best Practices

1. **Atomic Commits**: Commit at phase boundaries, not after every task
2. **Incremental Validation**: Run tests after each phase, not just at the end
3. **Document As You Go**: Update plan markers immediately after task completion
4. **Preserve Context**: Include enough detail in commits for future debugging
5. **Fail Fast**: If a critical task fails, stop and report rather than continue
6. **Idempotency**: Tasks should be safe to re-run if execution is interrupted

## Example Execution

```
$ Execute plan/refactor-codebase-cleanup-1.md

[Pre-Execution] Reading implementation plan...
[Pre-Execution] Found 9 phases, 60 tasks
[Pre-Execution] Validating workspace state... ✅
[Pre-Execution] Running baseline tests... 116 passed ✅

═══════════════════════════════════════════════════════════
PHASE 1: Code Cleanup - Legacy Removal
GOAL: Remove deprecated and unused code artifacts
Tasks: 3 | Estimated Files: 3
═══════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────
TASK-001: Delete RimworldMLBridge/GrpcService.cs
Files: RimworldMLBridge/GrpcService.cs
───────────────────────────────────────────────────────────
[Executing] Deleting file... ✅
[Validating] File removed... ✅
[Recording] Updated plan with ✅ 2025-12-11

... [continues for all tasks and phases] ...

═══════════════════════════════════════════════════════════
EXECUTION COMPLETE
═══════════════════════════════════════════════════════════

Pull Request Created: https://github.com/owner/repo/pull/42
Status: Ready for Review
```

## Related Prompts

- [create-implementation-plan.prompt.md](create-implementation-plan.prompt.md) - Create new implementation plans
- [update-implementation-plan.prompt.md](update-implementation-plan.prompt.md) - Update existing plans
- [completePhaseWithTesting.prompt.md](completePhaseWithTesting.prompt.md) - Complete individual phases with testing
