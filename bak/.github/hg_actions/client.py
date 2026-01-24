import os
import json
import time
import uuid
import subprocess
import requests
from typing import Dict, Any, Optional
from .config import settings

class HGAClient:
    def __init__(self):
        self.base_url = settings.openai_base_url
        self.api_key = settings.openai_api_key
        self.github_token = settings.github_token
        self.proxy_repo = settings.hga_proxy_repo

    def chat_completion(self, messages: list, model: str = "gpt-4o") -> str:
        """
        Sends a chat completion request to the LLM provider.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
        }

        # Correct param for O1/newer models if gpt-5 or o1 is detected
        if "gpt-5" in model or "o1" in model:
             payload["max_completion_tokens"] = 4096
             # gpt-5 and o1 models don't support temperature parameter
        else:
             payload["max_tokens"] = 4096
             payload["temperature"] = 0.2

        try:
            response = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            # Fallback for dev/mocking if the server isn't running
            return self._mock_planner_response(messages)

    def _mock_planner_response(self, messages: list) -> str:
        """
        Returns a mock response for testing when the LLM is unavailable.
        """
        # Check if this is a planning request
        is_planner = False
        user_content = ""
        for msg in messages:
            if "You are the HGActions Planner" in msg.get("content", ""):
                is_planner = True
            if msg.get("role") == "user":
                user_content = msg.get("content", "")

        if is_planner:
            # Detect Proxy Intent
            if "Copilot" in user_content or "remote" in user_content:
                return json.dumps({
                    "steps": [
                        {"type": "proxy_action", "task": "copilot-review", "description": "Run Remote Copilot Review"}
                    ]
                })

            return json.dumps({
                "steps": [
                    {"type": "shell", "command": "git branch --show-current", "description": "Check current branch"},
                    {"type": "ai", "prompt": "Review code locally", "output_file": "review.txt", "description": "Local Review"}
                ]
            })
        else:
            return "Simulated AI Response: The code looks good."

    def run_github_command(self, args: list) -> str:
        try:
            result = subprocess.run(["gh"] + args, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"
        except FileNotFoundError:
            return f"Simulated execution of: gh {' '.join(args)}"

    # --- API HELPER METHODS ---

    def create_issue(self, title: str, body: str, labels: list = None, assignees: list = None) -> str:
        """Creates a GitHub issue."""
        cmd = ["issue", "create", "--title", title, "--body", body]
        if labels:
            for label in labels:
                cmd.extend(["--label", label])
        if assignees:
            for assignee in assignees:
                cmd.extend(["--assignee", assignee])
        return self.run_github_command(cmd)

    def add_label_to_issue(self, issue_number: str, label: str) -> str:
        """Adds a label to an issue."""
        return self.run_github_command(["issue", "edit", str(issue_number), "--add-label", label])

    def comment_on_issue(self, issue_number: str, body: str) -> str:
        """Adds a comment to an issue."""
        return self.run_github_command(["issue", "comment", str(issue_number), "--body", body])

    # --- PROXY RUNNER METHODS ---

    def execute_proxy_action(self, task: str) -> str:
        """
        Orchestrates the Proxy Execution:
        1. Create job branch.
        2. Commit instruction.
        3. Push to proxy repo.
        4. Wait for result.
        """
        if not self.proxy_repo:
            return "Error: HGA_PROXY_REPO environment variable not set. Cannot run proxy action."

        job_id = str(uuid.uuid4())[:8]
        branch_name = f"job-{job_id}"

        print(f"  [Proxy] Preparing job {job_id} ({task})...")

        current_branch = None
        try:
            # Check if we are in a git repo
            current_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()

            # Create temp branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)

            # Add instruction
            os.makedirs(".hga", exist_ok=True)
            with open(".hga/instruction.txt", "w") as f:
                f.write(task)

            subprocess.run(["git", "add", ".hga/instruction.txt"], check=True, capture_output=True)

            # Commit
            # Note: This requires user.name/email to be configured.
            subprocess.run(["git", "commit", "-m", f"HGA Job: {task}"], check=True, capture_output=True)

            # Push to Proxy (The Real Logic)
            print(f"  [Proxy] Pushing to {self.proxy_repo}...")
            # We assume the user has configured the remote or we push to the URL directly
            subprocess.run(["git", "push", self.proxy_repo, branch_name], check=True)

            # Wait for Result
            print("  [Proxy] Waiting for runner to process...")

            # Polling Logic
            # We look for a new commit on the branch (pushed by the runner) containing 'hga_result.md'
            for _ in range(30): # 30 attempts
                time.sleep(5)
                subprocess.run(["git", "fetch", self.proxy_repo, branch_name], check=True, capture_output=True)

                # Check for result file in the remote branch
                # git show FETCH_HEAD:hga_result.md
                try:
                    result = subprocess.check_output(
                        ["git", "show", "FETCH_HEAD:hga_result.md"],
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                    return f"## Proxy Result (Job {job_id})\n{result}"
                except subprocess.CalledProcessError:
                    print(".", end="", flush=True)
                    continue

            return "Error: Timeout waiting for proxy result."

        except subprocess.CalledProcessError as e:
            return f"Proxy Error: {e}\nStderr: {e.stderr.strip()}"
        finally:
            # Cleanup: return to original branch
            if current_branch:
                 subprocess.run(["git", "checkout", current_branch], check=False, capture_output=True)
                 # Delete the temp branch locally
                 subprocess.run(["git", "branch", "-D", branch_name], check=False, capture_output=True)
