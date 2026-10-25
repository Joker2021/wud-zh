#!/usr/bin/env python3
"""Translate extracted WUD UI strings with Youdao and atomically persist the cache."""

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

API = "https://openapi.youdao.com/api"
TOKENS = re.compile(r"\$\{[^}]+\}|\{\{?[^{}]+\}?\}|%[a-zA-Z]")


def input_signature(text):
    return text if len(text) <= 20 else text[:10] + str(len(text)) + text[-10:]


def validate_placeholders(source, translated):
    return sorted(TOKENS.findall(source)) == sorted(TOKENS.findall(translated))


def sign(app_key, secret, text, salt, curtime):
    raw = app_key + input_signature(text) + salt + curtime + secret
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def apply_glossary(text, glossary):
    protected = []
    for term, translation in sorted(glossary.items(), key=lambda item: len(item[0]), reverse=True):
        if not term or not translation:
            continue
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", re.IGNORECASE)
        def replace(_match):
            token = f"WUDTERM{len(protected)}TOKEN"
            protected.append((token, translation))
            return token
        text = pattern.sub(replace, text)
    return text, protected


def restore_glossary(text, protected):
    for token, translation in protected:
        if text.count(token) != 1:
            raise RuntimeError("translation changed a protected glossary term")
        text = text.replace(token, translation)
    return text


def youdao(text, app_key, secret, timeout=15, opener=urllib.request.urlopen, sleep=time.sleep):
    for attempt in range(4):
        salt, curtime = str(uuid.uuid4()), str(int(time.time()))
        data = urllib.parse.urlencode({
            "q": text, "from": "en", "to": "zh-CHS", "appKey": app_key,
            "salt": salt, "sign": sign(app_key, secret, text, salt, curtime),
            "signType": "v3", "curtime": curtime,
        }).encode("utf-8")
        request = urllib.request.Request(API, data=data, method="POST")
        try:
            with opener(request, timeout=timeout) as response:
                result = json.load(response)
            if result.get("errorCode") != "0" or not result.get("translation"):
                raise RuntimeError(f"Youdao returned error code {result.get('errorCode', 'missing')}")
            return "\n".join(result["translation"])
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            if attempt == 3:
                raise RuntimeError(f"Youdao request failed after retries: {type(exc).__name__}") from None
            sleep(min(2 ** attempt + random.random(), 15))
    raise RuntimeError("translation attempts exhausted")


def translate_file(manifest_path, memory_path, output_path, version, app_key=None, secret=None, dry_run=False, translate=youdao, glossary_path=Path("translations/glossary.json")):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    memory_file, output_file = Path(memory_path), Path(output_path)
    memory = json.loads(memory_file.read_text(encoding="utf-8")) if memory_file.exists() else {}
    output = json.loads(output_file.read_text(encoding="utf-8")) if output_file.exists() else {}
    glossary = json.loads(Path(glossary_path).read_text(encoding="utf-8")) if Path(glossary_path).exists() else {}
    todo = [item for item in manifest if item["id"] not in memory or memory[item["id"]].get("source") != item["text"]]
    needs_api = [item for item in todo if item["text"] not in glossary]
    if needs_api and (not app_key or not secret) and not dry_run:
        raise RuntimeError(f"{len(needs_api)} untranslated strings; configure YOUDAO_APP_KEY and YOUDAO_APP_SECRET")
    stats = {"identified": len(manifest), "translated": 0, "cached": 0, "new": 0, "failed": 0, "untranslated": 0,
             "apiRequests": 0, "apiCharacters": 0, "requestsNeeded": len(needs_api),
             "charactersNeeded": sum(len(apply_glossary(item["text"], glossary)[0]) for item in needs_api)}
    for item in manifest:
        entry = memory.get(item["id"])
        if entry and entry.get("source") == item["text"]:
            output[item["id"]] = entry["translation"]
            stats["cached"] += 1
            continue
        if dry_run:
            if item["text"] in glossary:
                stats["new"] += 1
            else:
                stats["untranslated"] += 1
            continue
        try:
            origin = "youdao"
            if item["text"] in glossary:
                result, origin = glossary[item["text"]], "glossary"
            else:
                if len(item["text"]) > 5000:
                    raise RuntimeError("string exceeds Youdao's 5000-character request limit")
                query, protected = apply_glossary(item["text"], glossary)
                result = restore_glossary(translate(query, app_key, secret), protected)
                stats["apiRequests"] += 1
                stats["apiCharacters"] += len(query)
                time.sleep(1)
            if not validate_placeholders(item["text"], result):
                raise RuntimeError("translation changed interpolation placeholders")
            memory[item["id"]] = {
                "source": item["text"], "translation": result,
                "context": item["context"], "sourceVersion": version,
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "origin": origin, "reviewed": origin == "glossary",
            }
            output[item["id"]] = result
            stats["new"] += 1
        except Exception as exc:
            stats["failed"] += 1
            print(f"translation failed for {item['id']}: {exc}", file=sys.stderr)
            raise
    stats["translated"] = stats["cached"] + stats["new"]
    stats["untranslated"] += stats["failed"]
    if not dry_run:
        for path, value in ((memory_file, memory), (output_file, output)):
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(path.suffix + ".tmp")
            temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temp.replace(path)
    print(json.dumps(stats, ensure_ascii=False))
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--memory", type=Path, default=Path("translations/memory.json"))
    parser.add_argument("--output", type=Path, default=Path("translations/zh-CN.json"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        translate_file(args.manifest, args.memory, args.output, args.version,
                       os.getenv("YOUDAO_APP_KEY"), os.getenv("YOUDAO_APP_SECRET"), args.dry_run)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
