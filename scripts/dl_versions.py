# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pydantic",
#     "rich",
#     "ry>=0.0.93",
# ]
# ///
import asyncio
import hashlib
from typing import Literal

from pydantic.dataclasses import dataclass
from rich.console import Console

import ry

_PACKAGE_NAME = "ry"  # Change to your desired package
console = Console()

console.log(f"ry: {ry.__version__}")


@dataclass(frozen=True)
class Digests:
    md5: str
    sha256: str
    blake2b_256: str


@dataclass(frozen=True)
class RyPackage:
    url: str
    filename: str
    version: str
    md5_digest: str
    size: int
    digests: Digests
    upload_time: ry.DateTime
    upload_time_iso_8601: ry.Timestamp


@dataclass(frozen=True)
class DownloadResult:
    ok: bool
    pkg: RyPackage
    status: Literal["ok", "skip", "err"]
    reason: str | None
    msg: str | None
    elapsed: float | None


def _rich_msg(result: DownloadResult) -> str:
    filename = result.pkg.url.split("/")[-1]
    if not result.ok:
        return f"[red]failed[/red]: {filename} ({result.reason}) - {result.msg}"
    if result.status == "ok":
        return f"[green]success[/green]: {filename} {result.elapsed:.2f}s"
    elif result.status == "skip":
        return f"[yellow]skipped[/yellow]: {filename} (already exists)"
    msg = "unreachable"
    raise RuntimeError(msg)


def md5_hash(s: ry.Bytes) -> str:
    return hashlib.md5(s).hexdigest()  # noqa: S324


def sha256_hash(s: ry.Bytes) -> str:
    return ry.sha256(s).hexdigest()


async def get_all_versions(package_name: str) -> list[str]:
    """Fetch all available versions of a package from PyPI."""
    response = await ry.fetch(f"https://pypi.org/pypi/{package_name}/json")
    if response.status_code != 200:
        err = Exception(f"Failed to fetch package data: {response.status_code}")
        raise err
    data = await response.json()
    console.print(data)
    return list(data["releases"].keys())


async def pypi_package_stats(package_name: str) -> tuple[int, int]:
    """Get the total size of all packages for a given package name."""
    response = await ry.fetch(f"https://pypi.org/pypi/{package_name}/json")
    if response.status_code != 200:
        err = Exception(f"Failed to fetch package data: {response.status_code}")
        raise err
    data = await response.json()
    total_size = sum(
        sum(pkg["size"] for pkg in data["releases"][version])
        for version in data["releases"]
    )
    total_number = sum(len(data["releases"][version]) for version in data["releases"])
    return total_size, total_number


async def get_wheel_urls(package_name: str, version: str) -> list[RyPackage]:
    """Fetch .whl file URLs for a specific version."""
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    response = await ry.fetch(url)
    if response.status_code != 200:
        msg = f"[red]error[/red] Failed to fetch version {version}: {response.status_code}"
        console.log(msg)
        return []

    data = await response.json()
    return [
        RyPackage(
            url=file["url"],
            filename=file["filename"],
            version=version,
            md5_digest=file["md5_digest"],
            size=file["size"],
            digests=Digests(
                md5=file["md5_digest"],
                sha256=file["digests"]["sha256"],
                blake2b_256=file["digests"]["blake2b_256"],
            ),
            upload_time=ry.DateTime.parse(file["upload_time"]),
            upload_time_iso_8601=ry.Timestamp.parse(file["upload_time_iso_8601"]),
        )
        for file in data["urls"]
        if (file["filename"].endswith(".whl") or file["filename"].endswith(".tar.gz"))
        and file["filename"]
    ]


async def scrape_all_wheels(package_name: str) -> dict[str, list[RyPackage]]:
    """Scrape all versions and their respective wheels."""
    versions = await get_all_versions(package_name)
    wheels = {}
    for version in versions:
        wheels[version] = await get_wheel_urls(package_name, version)
    return wheels


async def download_file(
    pkg: RyPackage,
    outdir: str,
) -> DownloadResult:
    """Download a file from a URL to a specified directory."""
    filename = pkg.url.split("/")[-1]
    outpath = f"{outdir}/{filename}"
    if ry.FsPath(outpath).exists():
        return DownloadResult(
            ok=True,
            pkg=pkg,
            status="skip",
            reason="already exists",
            msg=f"{filename} already exists",
            elapsed=None,
        )
    start_time = ry.instant()
    response = await ry.fetch(pkg.url)
    body = await response.bytes()
    elapsed = start_time.elapsed()
    file_md5 = md5_hash(body)
    if file_md5 != pkg.md5_digest:
        msg = f"MD5 mismatch for {filename}: expected {pkg.md5_digest}, got {file_md5}"
        return DownloadResult(
            ok=False,
            pkg=pkg,
            status="err",
            reason="md5 mismatch",
            msg=msg,
            elapsed=elapsed.as_secs_f64(),
        )

    file_sha256 = sha256_hash(body)
    if file_sha256 != pkg.digests.sha256:
        msg = f"SHA256 mismatch for {filename}: expected {pkg.digests.sha256}, got {file_sha256}"
        return DownloadResult(
            ok=False,
            pkg=pkg,
            status="err",
            reason="sha256 mismatch",
            msg=msg,
            elapsed=elapsed.as_secs_f64(),
        )
    await ry.write_async(outpath, body)
    return DownloadResult(
        ok=True,
        pkg=pkg,
        status="ok",
        reason=None,
        msg=None,
        elapsed=elapsed.as_secs_f64(),
    )


async def download_file_task(
    pkg: RyPackage, outdir: str, *, log: bool = False
) -> DownloadResult:
    """Download a file from a URL to a specified directory as a task."""
    r = await download_file(pkg, outdir)
    if log and r.status != "skip":
        console.log(_rich_msg(r))
    return r


async def download_batch(pkgs: list[RyPackage], outdir: str) -> list[DownloadResult]:
    """Download a batch of packages."""
    tasks: list[asyncio.Task[DownloadResult]] = []
    start = ry.instant()
    async with asyncio.TaskGroup() as tg:
        for pkg in pkgs:
            task = tg.create_task(
                download_file_task(pkg, outdir, log=True), name=pkg.url
            )
            tasks.append(task)
    elapsed = start.elapsed()
    total_size_downloaded = sum(
        task.result().pkg.size
        for task in tasks
        if task.result().ok and task.result().status == "ok"
    )

    mb_per_sec = total_size_downloaded / elapsed.as_secs_f64() / (1024 * 1024)
    stats = {
        "elapsed": elapsed.as_secs_f64(),
        "total": len(tasks),
        "successful": sum(
            1 for task in tasks if task.result().ok and task.result().status == "ok"
        ),
        "skipped": sum(
            1 for task in tasks if task.result().ok and task.result().status == "skip"
        ),
        "failed": sum(1 for task in tasks if not task.result().ok),
        "downloaded": {
            "nbytes": total_size_downloaded,
            "nbytes_str": ry.fmt_size(total_size_downloaded),
            "mb/s": ry.Size.from_mib(mb_per_sec).format() + "/s",
        },
    }
    stats_json = ry.stringify(stats, fmt=True).decode()
    console.log(f"batch finished; stats: {stats_json}")
    return [task.result() for task in tasks]


async def write_index(data: dict[str, list[RyPackage]], path: str) -> None:
    json_data = ry.stringify(data, fmt=True, append_newline=True)
    await ry.write_async(path, json_data)
    console.log(f"wrote index: {path}")


async def download_dists(wheels: dict[str, list[RyPackage]]) -> None:
    """Download the wheel files."""

    ry.create_dir_all("dist")
    for version, urls in wheels.items():
        msg = f"downloading version: {version}"
        console.log("-" * len(msg))
        console.log(msg)
        outdir = f"dist/{version}"
        ry.create_dir_all(outdir)
        await download_batch(urls, outdir)
        await write_index({version: urls}, f"{outdir}/index.json")


async def main() -> None:
    wheels_data = await scrape_all_wheels(_PACKAGE_NAME)
    total_size_of_all_wheels = sum(
        sum(pkg.size for pkg in pkgs) for pkgs in wheels_data.values()
    )
    # Save to a JSON file
    json_data = ry.stringify(wheels_data, fmt=True, append_newline=True)
    await ry.write_async(
        f"{_PACKAGE_NAME}-wheels.json",
        json_data,
    )
    console.log(
        f"scraped {_PACKAGE_NAME}, saved wheel URLs to {_PACKAGE_NAME}_wheels.json"
    )
    await download_dists(wheels_data)
    await write_index(wheels_data, "dist/index.json")

    console.log(f"Total size of all wheels: {ry.fmt_size(total_size_of_all_wheels)}")


if __name__ == "__main__":
    from asyncio import run

    run(main())
