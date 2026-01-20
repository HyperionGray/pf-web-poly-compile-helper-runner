import subprocess
import os
from typing import List, Dict, Any
from .client import HGAClient

class Executor:
    def __init__(self):
        self.client = HGAClient()

    def execute_plan(self, plan: Dict[str, Any]):
        """
        Executes the list of steps in the plan.
        """
        steps = plan.get("steps", [])
        print(f"Executing {len(steps)} steps...")

        for i, step in enumerate(steps):
            print(f"\nStep {i+1}: {step.get('description', 'Unknown Step')}")

            step_type = step.get("type")
            if step_type == "shell":
                self._run_shell(step)
            elif step_type == "github":
                self._run_github(step)
            elif step_type == "ai":
                self._run_ai(step)
            elif step_type == "proxy_action":
                self._run_proxy(step)
            else:
                print(f"Unknown step type: {step_type}")

    def _run_shell(self, step: Dict[str, Any]):
        command = step.get("command")
        print(f"  > Running: {command}")
        try:
            # Using shell=True for flexibility
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"  Output: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"  Error: {e.stderr}")

    def _run_github(self, step: Dict[str, Any]):
        args = step.get("args", [])
        print(f"  > GitHub: gh {' '.join(args)}")
        output = self.client.run_github_command(args)
        print(f"  Output: {output}")

    def _run_ai(self, step: Dict[str, Any]):
        prompt = step.get("prompt")
        context_files = step.get("context_files", [])
        output_file = step.get("output_file")

        # Read context files
        context_content = ""
        for filepath in context_files:
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    context_content += f"\n--- File: {filepath} ---\n{f.read()}\n"
            else:
                print(f"  Warning: Context file {filepath} not found.")

        full_prompt = f"{prompt}\n\nContext:\n{context_content}"

        print(f"  > Asking AI...")
        response = self.client.chat_completion([{"role": "user", "content": full_prompt}])

        print(f"  AI Response (preview): {response[:100]}...")

        if output_file:
            with open(output_file, "w") as f:
                f.write(response)
            print(f"  Saved response to {output_file}")

    def _run_proxy(self, step: Dict[str, Any]):
        task = step.get("task")
        print(f"  > Triggering Proxy Action: {task}")
        result = self.client.execute_proxy_action(task)
        print(f"  Result:\n{result}")
