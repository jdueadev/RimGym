---
name: completePhaseWithTesting
description: Complete implementation phase with unit tests, benchmarks, and documentation updates
argument-hint: phase name, performance targets, completion criteria
---

Complete the specified implementation phase to 100% by implementing comprehensive testing and updating all project documentation.

## Testing Requirements

1. **Unit Tests**
   - Create comprehensive unit tests covering all new functionality
   - Test happy paths, edge cases, and error conditions
   - Verify null handling and data transformation correctness
   - Ensure all tests pass with 100% success rate

2. **Performance Benchmarks**
   - Create benchmarks validating performance targets
   - Test with various scales (small, medium, large datasets)
   - Measure execution time, memory allocation, and GC pressure
   - Add warmup runs to eliminate JIT compilation variance
   - Verify all benchmarks meet or exceed specified targets

3. **Fix Test Failures**
   - Identify root causes of any test failures
   - Fix compatibility issues (e.g., framework versions, native dependencies)
   - Adjust thresholds where appropriate for sub-millisecond operations
   - Re-run tests until 100% passing

## Documentation Updates

After all tests pass, update the following documentation:

1. **Task File** (`memory-bank/tasks/[TASKID]-[name].md`)
   - Change status to "Completed"
   - Add completion date
   - Update progress tracking table to show all subtasks complete
   - Add final progress log entry with test results and performance metrics

2. **Active Context** (`memory-bank/activeContext.md`)
   - Update current focus to reflect phase completion
   - Move completed items from "Current Work" to "Recent Changes"
   - Update next steps to point to subsequent phases

3. **Progress Tracker** (`memory-bank/progress.md`)
   - Mark phase as complete with checkmark
   - Add final status section with test results
   - Update technical debt list (mark completed items)
   - Record final metrics and achievements

4. **Tasks Index** (`memory-bank/tasks/_index.md`)
   - Move task from "In Progress" to "Completed"
   - Add completion date and key achievements

## Success Criteria

- ✅ All unit tests passing (100% success rate)
- ✅ All performance benchmarks passing and meeting/exceeding targets
- ✅ Zero blocking issues or test failures
- ✅ All documentation updated to reflect completion
- ✅ Task tracking shows 100% completion status

## Output Summary

Provide a concise summary including:
- Total test count and pass rate
- Performance results vs. targets (with improvement factor)
- Key achievements and metrics
- Links to updated documentation files
