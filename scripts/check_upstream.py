#!/usr/bin/env python3
"""Report the latest published stable WUD release and its immutable source SHA."""

import argparse
import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/getwud/wud/releases/latest"
REF_API = "https://api.github.com/repos/getwud/wud/git/ref/tags/{}"
TAG_API = "https://api.github.com/repos/getwud/wud/git/tags/{}"
SEMVER = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def fetch_release(token=None):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as response:
            return json.load(response)

    release = get(API)
    tag = release.get("tag_name", "")
    if release.get("draft") or release.get("prerelease") or not SEMVER.fullmatch(tag):
        raise ValueError("GitHub latest release is not a published stable SemVer release")
    obj = get(REF_API.format(urllib.parse.quote(tag, safe="")))["object"]
    while obj["type"] == "tag":
        obj = get(TAG_API.format(obj["sha"]))["object"]
    if obj["type"] != "commit" or not re.fullmatch(r"[0-9a-f]{40}", obj["sha"]):
        raise ValueError("release tag did not resolve to a commit")
    release["commit"] = obj["sha"]
    return release


def version_tuple(version):
    match = SEMVER.fullmatch(version.removeprefix("v"))
    if not match:
        raise ValueError(f"invalid stable version: {version}")
    return tuple(map(int, match.groups()))


def needs_update(current, latest):
    return version_tuple(latest) > version_tuple(current)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, default=Path("upstream.lock.json"))
    args = parser.parse_args()
    try:
        current = json.loads(args.current.read_text(encoding="utf-8"))["version"]
        release = fetch_release(os.getenv("GITHUB_TOKEN"))
        latest = release["tag_name"].removeprefix("v")
    except (OSError, KeyError, json.JSONDecodeError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"current": current, "latest": latest, "commit": release["commit"], "update": needs_update(current, latest), "url": release["html_url"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
