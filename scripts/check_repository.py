"""Check the public repository boundary and local documentation links."""

from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLANNING_NAMES = {
    "requirements_review.md",
    "errata_review.md",
    "ci_plan.md",
    "roadmap.md",
    "backlog.md",
    "items.json",
    "verification.md",
}
PLANNING_DIRS = {"planning", "governance", "backlog"}


def main():
    """Check tracked public paths and maintained documentation links."""
    paths = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    for name in filter(None, paths):
        path = Path(name)
        parts = {part.lower() for part in path.parts[:-1]}
        if (
            path.name.lower() in PLANNING_NAMES
            or parts & PLANNING_DIRS
            or name.lower().startswith("docs/source/")
            or re.match(r"DGR-(SRS|ERR|PROMPT)-", path.name, re.I)
        ):
            raise ValueError(f"Planning material must remain private: {name}")
    for name in ("README.md", "CONTRIBUTING.md"):
        page = ROOT / name
        for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", page.read_text()):
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (page.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                raise ValueError(f"Broken local link in {name}: {link}")
    print("PASS: public repository boundary and documentation links")


if __name__ == "__main__":
    main()
