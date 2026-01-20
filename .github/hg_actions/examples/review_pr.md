# Action: Review Repository Code

## AI Planner command: `python -m hg_actions.cli --execute`

## Description
Please review the code in the current directory. Look for bugs and security issues.

## AI to use
Task: "Review the code"
  - Chain
     - OpenAI via API
     - Local QwenCoder 2.5
  TaskSteps:
     - Check current git branch.
     - List all Python files.
     - For the file `src/clusterfk_llm/memory/manager.py`, perform a code review.
     - Save the review to `review_output.txt`.
