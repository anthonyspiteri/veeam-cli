import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
skills_path = root / "skills" / "skills.json"
docs_path = root / "docs" / "skills.md"

skills = json.loads(skills_path.read_text())

lines = ["# bakufu-cli Skills", "", "Auto-generated index of skills.", ""]

for section, title in [
    ("services", "Services"),
    ("helpers", "Helpers"),
    ("personas", "Personas"),
    ("recipes", "Recipes"),
]:
    lines.append(f"## {title}")
    lines.append("")
    for item in skills.get(section, []):
        name = item["name"]
        desc = item["description"]
        lines.append(f"- `{name}`: {desc} (skills/{name}/SKILL.md)")
    lines.append("")

docs_path.write_text("\n".join(lines))
print("skills index generated")
