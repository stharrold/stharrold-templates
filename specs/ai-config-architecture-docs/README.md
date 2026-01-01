# AI Config Architecture Documentation

**Issue:** [#89](https://github.com/stharrold/stharrold-templates/issues/89)
**Type:** Feature (documentation-only)
**Status:** In Progress

## Overview

Document the AI configuration architecture to clarify the relationship between Gemini-first development and cross-tool compatibility.

## Problem

- Contributors don't know to edit `.gemini/` instead of `.agents/`
- Other AI tools need to find instructions in `.agents/` and `AGENTS.md`
- The sync mechanism is unclear

## Solution

Update documentation across 5 files:

1. **GEMINI.md** - Add "AI Configuration Architecture" section
2. **.gemini/GEMINI.md** - Add PRIMARY source statement
3. **.agents/GEMINI.md** - Add OpenAI spec reference and compatible tools
4. **CONTRIBUTING.md** - Add AI configuration guidelines
5. **README.md** - Add cross-tool compatibility mention

## Files

- [spec.md](spec.md) - Detailed technical specification
- [plan.md](plan.md) - Implementation plan with task breakdown
