from rich.console import Console

import ry

console = Console()


def generate_versions_md(versions: list[str]) -> str:
    """Generate markdown list of versions."""
    return "\n".join(f"- [{ver}](./dist/{ver})" for ver in versions)


def main() -> None:
    s = ry.read_to_string("README.md")
    start_tag = "<!-- <GENERATED> -->"
    end_tag = "<!-- </GENERATED> -->"
    versions = ry.ls("dist", sort=True)
    start_idx = s.index(start_tag) + len(start_tag)
    end_idx = s.index(end_tag)
    new_s = (
        s[:start_idx] + "\n\n" + generate_versions_md(versions) + "\n\n" + s[end_idx:]
    )
    if new_s != s:
        ry.write_text("README.md", new_s)
        console.print("Updated README.md with new versions.")


if __name__ == "__main__":
    main()
