# add-strategy Skill Implementation

## Overview

This directory contains the complete implementation of the `/add-strategy` skill for the ai-trader backtesting framework.

## Files

### 1. SKILL.md (472 lines)
**Main skill definition and workflow**

Contains:
- YAML frontmatter with skill metadata
- Overview and use cases
- Interactive workflow with 7 steps
- Usage examples (classic and portfolio strategies)
- File templates (classic and portfolio)
- Registration logic documentation
- Validation procedures
- Next steps after creation
- Error messages and troubleshooting
- Best practices and tips

### 2. PATTERNS.md (502 lines)
**Complete reference examples from the codebase**

Contains:
- DoubleTopStrategy (classic with custom indicator)
  - Shows: custom indicator usage, time-based exit, signal-based logic
- BBandsStrategy (classic with standard indicator)
  - Shows: simple mean reversion, clean next() logic, parameter usage
- ROCRotationStrategy (portfolio with multi-asset rotation)
  - Shows: self.datas iteration, position management, ranking, allocation
- Summary of core patterns for classic and portfolio strategies
- Docstring pattern documentation

Each example is annotated with inline comments explaining why specific patterns are used.

### 3. CONVENTIONS.md (684 lines)
**Naming rules and coding standards**

Contains:
- File naming (lowercase_with_underscores)
- Class naming (PascalCase + Strategy suffix)
- Parameter naming (lowercase_with_underscores)
- Import ordering (stdlib → backtrader → project → indicators)
- BaseStrategy inheritance requirements
  - Why super().__init__() is required
  - Using self.log() for date-formatted logging
  - Order methods and notification methods
- Docstring format with Entry/Exit/Parameters/Notes sections
- Code structure templates (classic and portfolio)
- Indicator usage (standard backtrader vs custom)
- Quick checklist for verification

### 4. VALIDATION.md (597 lines)
**Pre-flight and post-creation validation**

Contains:
- Pre-creation validation checks:
  - Strategy name validation (PascalCase, conflicts)
  - Filename validation (snake_case availability)
  - Strategy type validation (classic/portfolio)
  - Parameter validation (defaults, identifiers, keywords)
  - Custom indicator validation
- Post-creation verification:
  - File creation verification
  - Registration verification (imports, __all__)
  - Import verification (syntax, inheritance)
  - Git status verification
- Error handling with detailed solutions for:
  - File already exists
  - Name conflicts
  - Invalid parameter names
  - Missing defaults
  - Custom indicator not found
  - Import/syntax errors
  - Git tracking issues
- Pre-flight and post-creation checklists

## Skill Metadata

```yaml
name: add-strategy
description: Create a new trading strategy for the ai-trader backtesting framework
disable-model-invocation: true
argument-hint: "[strategy-type: classic|portfolio]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
```

## Key Design Decisions

1. **Modular Documentation:**
   - SKILL.md: Interactive workflow and user-facing guidance
   - PATTERNS.md: Reference examples from actual code
   - CONVENTIONS.md: Style guide and naming rules
   - VALIDATION.md: Implementation details and error handling

2. **Template-First Approach:**
   - Complete code templates provided
   - Users implement trading logic in provided structure
   - Reduces errors and ensures pattern compliance

3. **Comprehensive Validation:**
   - Pre-creation checks prevent name conflicts
   - Post-creation verification ensures correctness
   - Clear error messages with solutions

4. **Real-World Examples:**
   - All code examples from actual codebase
   - Inline annotations explain patterns
   - Shows both simple and complex strategies

## Implementation Notes

The skill orchestrates the following when invoked:

1. **Input Gathering:**
   - Strategy type (classic/portfolio)
   - Strategy name (PascalCase)
   - Description (1-2 sentences)
   - Parameters (name=value pairs)
   - Entry/exit conditions (narrative descriptions)
   - Custom indicators (if any)

2. **Validation:**
   - Runs all pre-creation checks
   - Reports any conflicts or issues
   - Prevents creation if validation fails

3. **File Generation:**
   - Creates strategy file with proper template
   - Generates comprehensive docstrings
   - Includes __main__ backtest block

4. **Registration:**
   - Adds import to {classic|portfolio}/__init__.py
   - Adds class name to __all__ list
   - Maintains alphabetical order

5. **Verification:**
   - Imports the new strategy to verify syntax
   - Checks git status
   - Shows next steps to user

## Usage

From the ai-trader project root:

```bash
# Create a classic strategy
/add-strategy classic

# Create a portfolio strategy
/add-strategy portfolio
```

The skill guides you through an interactive workflow to create a fully-functional trading strategy.

## Files Referenced (Read-Only)

During execution, the skill reads these files for validation and context:

- `ai_trader/backtesting/strategies/base.py` (BaseStrategy class)
- `ai_trader/backtesting/strategies/indicators.py` (available indicators)
- `ai_trader/backtesting/strategies/classic/__init__.py` (registration)
- `ai_trader/backtesting/strategies/portfolio/__init__.py` (registration)
- Example strategies in classic/ and portfolio/ directories

## Files Modified (During Skill Execution)

When creating a strategy, these files are modified:

- `ai_trader/backtesting/strategies/{classic|portfolio}/__init__.py` (add import and __all__ entry)
- `ai_trader/backtesting/strategies/{classic|portfolio}/{new_strategy}.py` (created)

## Success Criteria Met

✓ Complete documentation of patterns and conventions
✓ Pre-flight validation for name conflicts and custom indicators
✓ Post-creation verification ensuring correctness
✓ Real-world code examples with annotations
✓ Clear error messages and troubleshooting
✓ Template-driven strategy generation
✓ Automatic registration in __init__.py
✓ Syntax validation through import testing
✓ Git integration and status reporting

---

Generated with Claude Code
Implementation follows the plan: Create `/add-strategy` Skill for AI-Trader Project
