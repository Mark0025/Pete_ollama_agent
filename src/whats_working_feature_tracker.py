import os
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "test.log")
WHATS_WORKING_MD = os.path.join("DEV_MAN", "whatsworking.md")

console = Console()

# Educational intro
INTRO = (
    "# 🚀 Twilio CLI Reporting Project: Feature Health & Learning Guide\n\n"
    "I'm a curious developer and I want to learn how to build, test, and grow a CLI reporting app for Twilio call logs so I can automate insights and teach others best practices.\n\n"
    "---\n\n"
    "## 📦 App Structure\n\n"
    "```mermaid\n"
    "flowchart TD\n"
    "    A[TwilioApp/] --> B[src/]\n"
    "    A --> C[applogs/]\n"
    "    A --> D[tests/]\n"
    "    D --> E[logs/]\n"
    "    D --> F[whatsWorking.py]\n"
    "    D --> G[test_cli_features.sh]\n"
    "    A --> H[Dev_Man/]\n"
    "    H --> I[whatsworking.md]\n"
    "    B --> J[cli.py]\n"
    "    B --> K[backend/]\n"
    "    K --> L[api/]\n"
    "    L --> M[twilio_api.py]\n"
    "```\n\n"
    "---\n\n"
    "## 📝 Feature Health Table\n"
)

FEATURES = [
    ("Analyze logs", "1️⃣", "Analyzes and displays call log data in a beautiful table."),
    ("Show summary", "2️⃣", "Shows summary statistics for your call logs."),
    ("Visualize call volume", "3️⃣", "(Stub) Will visualize call volume trends."),
    ("Exit", "4️⃣", "Exits the CLI tool.")
]

COLOR_MAP = {True: "green", False: "red"}


def parse_logs():
    if not os.path.exists(LOG_PATH):
        return set()
    features = set()
    with open(LOG_PATH, "r") as f:
        for line in f:
            if "INFO" in line and "Menu option selected" in line:
                if "1" in line:
                    features.add("Analyze logs")
                elif "2" in line:
                    features.add("Show summary")
                elif "3" in line:
                    features.add("Visualize call volume")
                elif "4" in line:
                    features.add("Exit")
    return features

def build_feature_table(working):
    table = Table(title="Feature Health", show_lines=True)
    table.add_column("Feature", style="bold")
    table.add_column("Emoji", style="bold")
    table.add_column("Status", style="bold")
    table.add_column("Description", style="")
    for name, emoji, desc in FEATURES:
        status = "✅ Working" if name in working else "❌ Not Used"
        color = COLOR_MAP[name in working]
        table.add_row(name, emoji, f"[{color}]{status}[/{color}]", desc)
    return table

def build_md_table(working):
    md = "| Feature | Emoji | Status | Description |\n|---|---|---|---|\n"
    for name, emoji, desc in FEATURES:
        status = "✅ Working" if name in working else "❌ Not Used"
        md += f"| {name} | {emoji} | {status} | {desc} |\n"
    return md

def build_growth_section():
    return (
        "---\n\n"
        "## 📚 How the App Grows\n\n"
        "- Each time you use a CLI feature, it is logged and tracked.\n"
        "- This report updates automatically, teaching you which features are working and which need attention.\n"
        "- As you add new features or wire in the API, they will appear here!\n\n"
        "### Real-World Use Case\n"
        "Imagine onboarding a new teammate: they can see at a glance what works, what’s next, and how to contribute.\n\n"
        "---\n\n"
        "## 🧑‍🏫 Next Steps\n\n"
        "- Try using more CLI features and rerun this report!\n"
        "- Add new reports or visualizations and see them show up here.\n"
        "- When the API is ready, uncomment the mapping utility and connect your endpoints.\n\n"
        "---\n\n"
        "_Was this report helpful? What would you like to learn or automate next?_ 😊\n"
    )

def main():
    working = parse_logs()
    # Build Markdown
    md = INTRO
    md += build_md_table(working)
    md += build_growth_section()
    with open(WHATS_WORKING_MD, "w") as f:
        f.write(md)
    # Print rich table for CLI output
    table = build_feature_table(working)
    console.print(table)
    console.print("\n[bold cyan]See Dev_Man/whatsworking.md for the full educational report![/bold cyan]")

if __name__ == "__main__":
    main() 