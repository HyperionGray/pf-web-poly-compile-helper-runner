import os
import asyncio
import logging
from .workflow import WorkflowParser, WorkflowStep
from .client import HGAClient
from .executor import Executor
from .memory import HGAMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hga_daemon")

class AutonomousLoop:
    def __init__(self, workflow_path: str, repo_path: str):
        self.workflow_path = workflow_path
        self.repo_path = repo_path
        self.client = HGAClient()
        self.executor = Executor()
        self.memory = HGAMemory(data_dir=os.path.join(repo_path, ".hga/memory"))
        self.parser = WorkflowParser(workflow_path)
        self.running = True

    async def start(self):
        """Starts the autonomous loop."""
        logger.info(f"Starting HGA Autonomous Daemon for {self.repo_path}")

        # Ensure we are in the right directory
        os.chdir(self.repo_path)

        # Initialize memory
        await self.memory.initialize()

        while self.running:
            try:
                # Reload workflow on each iteration to allow dynamic updates
                workflow = self.parser.parse()
                logger.info(f"Loaded workflow with {len(workflow.steps)} steps.")

                for step in workflow.steps:
                    await self.execute_step(step)

                # Basic loop delay or exit strategy?
                # User said "Go for YEARS", implying a continuous loop.
                # But if the workflow is linear, we should probably pause between full runs.
                logger.info("Workflow cycle complete. Sleeping for 60 seconds...")
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in autonomous loop: {e}")
                await asyncio.sleep(30) # Backoff on error

    async def execute_step(self, step: WorkflowStep):
        logger.info(f"Executing step: {step.step_type}")

        if step.step_type == "planning":
            await self._handle_planning(step)
        elif step.step_type == "code":
            await self._handle_code(step)
        elif step.step_type == "wait":
            await self._handle_wait(step)
        elif step.step_type == "api_action":
            await self._handle_api_action(step)
        else:
            logger.warning(f"Unknown step type: {step.step_type}")

    async def _handle_planning(self, step: WorkflowStep):
        """
        Consults the LLM to generate a plan based on the body and memory context.
        """
        context = await self.memory.get_context(step.body or "General planning")
        prompt = f"""
        You are an autonomous agent planning work for this repository.
        Goal: {step.body}

        Memory Context:
        {context}

        Implementation Details:
        {step.implementation_details}

        Please provide a concise plan of action.
        """

        response = self.client.chat_completion([{"role": "user", "content": prompt}])
        logger.info(f"Plan generated: {response[:100]}...")

        # Store the plan in memory
        await self.memory.store_work_log(f"Generated Plan: {response}", {"step": "planning"})

    async def _handle_code(self, step: WorkflowStep):
        """
        Executes code generation or modification.
        """
        # If specific implementation details are provided, try to execute them as commands
        # otherwise, ask the LLM.

        if step.implementation_details and "Command:" in step.implementation_details:
             cmd = step.implementation_details.replace("Command:", "").strip()
             logger.info(f"Executing command from implementation details: {cmd}")
             # We use the existing executor for consistency
             self.executor._run_shell({"command": cmd})
             await self.memory.store_work_log(f"Executed command: {cmd}", {"step": "code"})
        else:
             prompt = f"""
             Execute the coding task: {step.body}
             Details: {step.implementation_details}
             """

             response = self.client.chat_completion([{"role": "user", "content": prompt}])
             logger.info(f"Code action result: {response[:100]}...")

             await self.memory.store_work_log(f"Code Execution Result: {response}", {"step": "code"})

    async def _handle_wait(self, step: WorkflowStep):
        """
        Pauses execution.
        Simple implementation: Wait for a specific file to be deleted or just sleep.
        """
        logger.info("Waiting for user input (simulated pause)...")
        # For v1, we'll just sleep a bit or check for a 'continue' signal file
        # logic: if .hga/pause exists, wait.

        pause_file = ".hga/pause"
        if step.implementation_details and "file" in step.implementation_details:
             # simplistic parsing
             pass

        # Create a pause file to indicate we are waiting
        with open(pause_file, "w") as f:
            f.write("Delete this file to continue.")

        while os.path.exists(pause_file):
            logger.info("Paused. Waiting for user to remove .hga/pause...")
            await asyncio.sleep(5)

        logger.info("Resuming...")

    async def _handle_api_action(self, step: WorkflowStep):
        """
        Executes GitHub API actions.
        """
        action = step.implementation_details or ""

        # Guard against None body
        step_body = step.body or ""

        try:
            if "create_issue" in action:
                # Parse simplistic format: create_issue:Title:Body
                parts = step_body.split("|")
                title = parts[0] if parts else "Automated Issue"
                body = parts[1] if len(parts) > 1 else "Automated Issue Description"

                logger.info(f"Creating issue: {title}")
                result = self.client.create_issue(title, body)
                logger.info(f"Result: {result}")

            elif "label" in action:
                # label:123:bug
                parts = step_body.split("|")
                if len(parts) >= 2:
                    issue_num = parts[0]
                    label = parts[1]
                    self.client.add_label_to_issue(issue_num, label)
                else:
                    logger.warning(f"Invalid label format in body: {step_body}")
        except Exception as e:
            logger.error(f"Error executing API action: {e}")

def run_daemon(workflow_path: str, repo_path: str):
    loop = AutonomousLoop(workflow_path, repo_path)
    asyncio.run(loop.start())
