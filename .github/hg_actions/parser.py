import re
from typing import Dict, Any

def parse_markdown_action(content: str) -> Dict[str, Any]:
    """
    Parses a semi-structured Markdown action file.
    """
    lines = content.splitlines()
    action_data = {
        "title": "Untitled Action",
        "description": "",
        "ai_planner_command": "",
        "ai_config": {},
        "raw_content": content
    }

    current_section = None
    buffer = []

    def flush_section():
        nonlocal current_section, buffer
        if current_section:
            text = "\n".join(buffer).strip()

            # Check for colon in section name (e.g., "AI Planner command: `...`")
            section_name = current_section
            inline_value = None
            if ":" in current_section:
                parts = current_section.split(":", 1)
                section_name = parts[0].strip()
                inline_value = parts[1].strip()

            if section_name == "AI Planner command":
                val = inline_value if inline_value else text
                # Extract code from inline code block if present
                match = re.search(r"`(.*?)`", val)
                if match:
                    action_data["ai_planner_command"] = match.group(1)
                else:
                    action_data["ai_planner_command"] = val
            elif section_name == "Description":
                action_data["description"] = text
            elif section_name == "AI to use":
                action_data["ai_config_text"] = text
            elif section_name.startswith("Action"):
                 # Usually the title
                 pass
        buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            flush_section()
            action_data["title"] = stripped[2:].strip()
            current_section = "Title"
        elif stripped.startswith("## "):
            flush_section()
            current_section = stripped[3:].strip()
        else:
            buffer.append(line)

    flush_section()

    return action_data

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "r") as f:
        data = parse_markdown_action(f.read())
        import json
        print(json.dumps(data, indent=2))
