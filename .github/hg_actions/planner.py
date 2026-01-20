import json
import re
from typing import List, Dict, Any
from .client import HGAClient

PLANNER_SYSTEM_PROMPT = """
You are the HGActions Planner. Your job is to convert a semi-structured "Action Doc" into a precise JSON execution plan.

The user will provide a description of tasks.
You must output a JSON object with a single key "steps", which is a list of steps.

Supported Step Types:
1. "shell": Run local bash command.
   - fields: "command"
2. "github": Run GitHub CLI command.
   - fields: "args" (list of strings)
3. "ai": Run local AI inference (using configured clusterfk-llm/OpenAI).
   - fields: "prompt", "context_files" (list), "output_file" (optional)
4. "proxy_action": Offload task to Remote Proxy Runner (e.g. for GitHub-hosted features like Copilot, CodeQL, or heavy compute).
   - fields: "task" (string, e.g. "copilot-review", "security-scan")

Guidelines:
- If the user asks for "Copilot", "CodeQL", or "Remote Scan", use "proxy_action".
- If the user asks for "Review" without specifying "Copilot", default to local "ai" step.
- Ensure shell commands are safe.

Example Output:
{
  "steps": [
    { "type": "shell", "command": "git pull", "description": "Update repo" },
    { "type": "proxy_action", "task": "copilot-review", "description": "Remote Copilot Review" }
  ]
}
"""

class Planner:
    def __init__(self):
        self.client = HGAClient()

    def create_plan(self, action_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates an execution plan from the parsed action data.
        """
        user_prompt = f"""
        Action Title: {action_data.get('title')}
        Description: {action_data.get('description')}

        AI Config / Tasks:
        {action_data.get('ai_config_text')}

        Please generate the JSON execution plan.
        """

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response_text = self.client.chat_completion(messages)
        return self._extract_json(response_text)

    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts JSON from the LLM response (handling markdown blocks).
        """
        try:
            # Try to find JSON block
            match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))

            # Try parsing raw text
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Error parsing JSON plan: {text}")
            return {"steps": []}
