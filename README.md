# ry-dist-archives

This repository contains built wheels for `ry` packages, many of which have been
removed from PyPI.

PyPI imposes a 10 GB limit on the total size of all files in a given project.
Once that limit is reached, you must either delete old files or request a size
increase. As of now (`2025-07-22T08:34:51.3412157-07:00[America/Los_Angeles]`),
the `ry` package is still very much in beta, and I (jesse) am not going to
request a size increase while the project remains pre-`0.1.0`.

`ry` builds are performed with github cicd, and published builds for versions
`0.44.0` are uploaded to github
[releases](https://github.com/jessekrubin/ry/releases), BUT publishing releases
was not previously a part of the cicd workflow.

The script for downloading wheels is
[`scripts/dl_versions.py`](scripts/dl_versions.py). It serves as a good example
of how to use `ry`'s HTTP client, JSON parsing and dumping, and async file I/O
tools.

## Versions

- [0.0.16](./dist/0.0.16)
- [0.0.17](./dist/0.0.17)
- [0.0.18](./dist/0.0.18)
- [0.0.19](./dist/0.0.19)
- [0.0.20](./dist/0.0.20)
- [0.0.21](./dist/0.0.21)
- [0.0.22](./dist/0.0.22)
- [0.0.23](./dist/0.0.23)
- [0.0.24](./dist/0.0.24)
- [0.0.25](./dist/0.0.25)
- [0.0.26](./dist/0.0.26)
- [0.0.27](./dist/0.0.27)
- [0.0.28](./dist/0.0.28)
- [0.0.29](./dist/0.0.29)
- [0.0.30](./dist/0.0.30)
- [0.0.31](./dist/0.0.31)
- [0.0.32](./dist/0.0.32)
- [0.0.33](./dist/0.0.33)
- [0.0.34](./dist/0.0.34)
- [0.0.35](./dist/0.0.35)
- [0.0.36](./dist/0.0.36)
- [0.0.37](./dist/0.0.37)
- [0.0.38](./dist/0.0.38)
- [0.0.39](./dist/0.0.39)
- [0.0.40](./dist/0.0.40)
- [0.0.41](./dist/0.0.41)
- [0.0.42](./dist/0.0.42)
- [0.0.43](./dist/0.0.43)
- [0.0.44](./dist/0.0.44)
