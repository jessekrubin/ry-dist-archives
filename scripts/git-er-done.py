# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "rich",
# ]
# ///
from rich import print
from functools import lru_cache
from subprocess import run
from rich.console import Console

console = Console()
console._log_render.omit_repeated_times = False

terminal_width = console.width


@lru_cache(maxsize=1)
def _br_str(s: str = "_", cols: int | None = None) -> str:
    assert len(s) == 1, "String must be a single character"
    return s * (cols or terminal_width)


def br(s: str = "_") -> None:
    console.print(_br_str(s, terminal_width), style="cyan")


def add_file_and_git_push(filepath: str) -> None:
    """Add a file to git and push the changes."""
    console.log(f"Adding: [bold green]{filepath}[/bold green]")
    print()
    run(["git", "add", "--force", filepath], check=True)
    run(["git", "commit", "-m", f"Add {filepath}"], check=True)
    run(["git", "push"], check=True)


def get_untracked_wheels() -> list[str] | None:
    done = run(
        ["git", "ls-files", "--other", "--exclude-standard"],
        capture_output=True,
        text=True,
    )
    # first one
    if done.returncode != 0:
        console.log("Error getting untracked files", style="bold red")
        return None
    files = done.stdout.splitlines()
    return list(filter(lambda x: x.endswith(".whl") or x.endswith(".gz"), files))


def main() -> None:
    files = get_untracked_wheels()
    if not files:
        console.log("No untracked wheels found.")
        return
    for f in files:
        br()
        add_file_and_git_push(f)


if __name__ == "__main__":
    main()
