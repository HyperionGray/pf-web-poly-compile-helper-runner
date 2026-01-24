import pyjson5
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    step_type: str
    body: Optional[str] = None
    mode: Optional[str] = None
    implementation_details: Optional[str] = None
    original_data: Optional[Dict[str, Any]] = None

@dataclass
class Workflow:
    steps: List[WorkflowStep]

class WorkflowParser:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def parse(self) -> Workflow:
        """Parses the JSON5 workflow file."""
        with open(self.filepath, "r") as f:
            data = pyjson5.load(f)

        steps = []
        raw_steps = data.get("steps", [])

        # Support if the top level is just a list
        if isinstance(data, list):
            raw_steps = data

        for item in raw_steps:
            steps.append(WorkflowStep(
                step_type=item.get("step-type", "unknown"),
                body=item.get("body"),
                mode=item.get("mode"),
                implementation_details=item.get("implementation-details"),
                original_data=item
            ))

        return Workflow(steps=steps)
