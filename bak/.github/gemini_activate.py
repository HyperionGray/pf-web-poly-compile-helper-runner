import os
import requests
import base64
import sys

# --- CONFIGURATION ---
REPO_OWNER_AND_NAME = input("Enter repo (e.g., yourusername/my-repo): ").strip()
BRANCH_NAME = "main" # Change if your default branch is master
GEMINI_MODEL = "gemini-1.5-pro" # Implementation for "Gemini 3" intent

# --- FILE CONTENTS ---

# 1. The Workflow YAML
WORKFLOW_CONTENT = f"""name: Gemini Code Review
on:
  issue_comment:
    types: [created]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  gemini_review:
    if: contains(github.event.comment.body, '@gemini') && github.event.issue.pull_request
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Dependencies
        run: pip install google-generativeai PyGithub
      - name: Run Gemini Review
        env:
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
          GEMINI_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
          REPO_NAME: ${{{{ github.repository }}}}
          PR_NUMBER: ${{{{ github.event.issue.number }}}}
        run: python .github/scripts/review_bot.py
"""

# 2. The Python Bot Logic
BOT_SCRIPT_CONTENT = f"""import os
import google.generativeai as genai
from github import Github

def review_code():
    gh_token = os.getenv('GITHUB_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    repo_name = os.getenv('REPO_NAME')
    pr_number = int(os.getenv('PR_NUMBER'))
    
    genai.configure(api_key=gemini_key)
    # Using specific model version
    model = genai.GenerativeModel('{GEMINI_MODEL}')

    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)

    files = pull_request.get_files()
    diff_content = ""
    
    for file in files:
        if file.status == "removed" or not file.patch:
            continue
        diff_content += f"\\n\\n--- File: {{file.filename}} ---\\n"
        diff_content += file.patch

    if not diff_content:
        pull_request.create_issue_comment("Found no code changes to review.")
        return

    prompt = f\"\"\"
    Act as a Senior Code Reviewer. Review these git diffs.
    Focus on: Logic bugs, Security, and Code Style.
    Output: GitHub Markdown.
    
    DIFFS:
    {{diff_content}}
    \"\"\"

    try:
        response = model.generate_content(prompt)
        pull_request.create_issue_comment("## 🤖 Gemini Review\\n\\n" + response.text)
    except Exception as e:
        pull_request.create_issue_comment(f"Error: {{str(e)}}")

if __name__ == "__main__":
    review_code()
"""

# --- API LOGIC ---

def push_file(path, content, message):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN env var is missing.")
        sys.exit(1)

    url = f"https://api.github.com/repos/{REPO_OWNER_AND_NAME}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if file exists to get SHA (for update)
    sha = None
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json().get("sha")

    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": BRANCH_NAME
    }
    if sha:
        data["sha"] = sha

    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        print(f"✅ Successfully pushed: {path}")
    else:
        print(f"❌ Failed to push {path}: {resp.text}")

def main():
    print(f"🚀 Bootstrapping Gemini Bot into {REPO_OWNER_AND_NAME}...")
    
    # 1. Push Workflow
    push_file(
        ".github/workflows/gemini_review.yml", 
        WORKFLOW_CONTENT, 
        "ci: Add Gemini Review Workflow"
    )

    # 2. Push Script
    push_file(
        ".github/scripts/review_bot.py", 
        BOT_SCRIPT_CONTENT, 
        "feat: Add Gemini Review Logic"
    )

    print("\n--- NEXT STEPS ---")
    print("Files are created. Now, set your Gemini API Key using GitHub CLI:")
    print(f"\n  gh secret set GEMINI_API_KEY -R {REPO_OWNER_AND_NAME}")
    print("\n(Or go to Repo Settings -> Secrets -> Actions -> New Repository Secret)")

if __name__ == "__main__":
    main()
