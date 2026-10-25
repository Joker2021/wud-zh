#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const args = process.argv.slice(2);
const command = args.shift();
const option = (name, fallback) => {
  const index = args.indexOf(name);
  return index < 0 ? fallback : args[index + 1];
};
const root = path.resolve(option("--upstream", "upstream"));
const ui = path.join(root, "ui");
const require = createRequire(path.join(ui, "package.json"));
const { parse: parseSfc } = require("@vue/compiler-sfc");
const { baseParse } = require("@vue/compiler-dom");
const allowedAttributes = new Set(["placeholder", "title", "aria-label", "alt", "label"]);

function translationId(file, context, text) {
  return crypto.createHash("sha256").update(`${file}\0${context}\0${text}`).digest("hex");
}

function staticStrings(source, file) {
  const { descriptor, errors } = parseSfc(source, { filename: file });
  if (errors.length) throw new Error(`${file}: invalid Vue SFC: ${errors[0].message}`);
  if (!descriptor.template) return [];
  const template = descriptor.template.content;
  const parseErrors = [];
  const ast = baseParse(template, { onError: (error) => parseErrors.push(error) });
  if (parseErrors.length) throw new Error(`${file}: invalid Vue template: ${parseErrors[0].message}`);
  const items = [];
  const visit = (node, parent = "template") => {
    if (node.type === 2 && /[A-Za-z]{2}/.test(node.content) && node.content.trim()) {
      const text = node.content.trim();
      const context = `${parent}:text`;
      const raw = template.slice(node.loc.start.offset, node.loc.end.offset);
      items.push({ id: translationId(file, context, text), text, context,
        start: node.loc.start.offset, end: node.loc.end.offset,
        prefix: raw.match(/^[\t\r\n\f ]*/)?.[0] ?? "",
        suffix: (raw.match(/(?:[\t\r\n\f ]|&nbsp;|\u00a0)*$/i)?.[0] ?? "").replaceAll("\u00a0", "&nbsp;") });
    }
    if (node.type === 1) {
      const tag = node.tag.toLowerCase();
      if (["v-icon", "code", "pre"].includes(tag)) return;
      for (const attr of node.props ?? []) {
        if (attr.type !== 6 || !allowedAttributes.has(attr.name) || !attr.value) continue;
        const text = attr.value.content.trim();
        if (!/[A-Za-z]{2}/.test(text)) continue;
        const context = `${tag}:@${attr.name}`;
        items.push({ id: translationId(file, context, text), text, context,
          start: attr.value.loc.start.offset, end: attr.value.loc.end.offset });
      }
      for (const child of node.children ?? []) visit(child, tag);
    } else if (node.type === 0) {
      for (const child of node.children ?? []) visit(child, parent);
    }
  };
  visit(ast);
  return items.map(({ id, text, context, ...location }) => ({ id, text, context, file, ...location }));
}

function files() {
  const found = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith(".vue")) found.push(full);
    }
  };
  walk(path.join(ui, "src"));
  return found.sort();
}

function extract() {
  const extracted = files().flatMap((full) => {
    const relative = path.relative(root, full).split(path.sep).join("/");
    return staticStrings(fs.readFileSync(full, "utf8"), relative);
  });
  const manifest = [...new Map(extracted.map((item) => [item.id, item])).values()];
  const output = option("--output", "translations/extracted.json");
  fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(JSON.stringify({ identified: manifest.length, output }));
}

function apply() {
  const translations = JSON.parse(fs.readFileSync(option("--translations", "translations/zh-CN.json"), "utf8"));
  const report = { identified: 0, translated: 0, untranslated: 0, files: 0 };
  for (const full of files()) {
    const relative = path.relative(root, full).split(path.sep).join("/");
    const source = fs.readFileSync(full, "utf8");
    const { descriptor, errors } = parseSfc(source, { filename: relative });
    if (errors.length) throw new Error(`${relative}: invalid Vue SFC`);
    if (!descriptor.template) continue;
    const template = descriptor.template.content;
    const entries = staticStrings(source, relative).sort((a, b) => b.start - a.start);
    let updated = template;
    for (const entry of entries) {
      report.identified += 1;
      const translation = translations[entry.id];
      if (typeof translation !== "string" || !translation.trim()) {
        report.untranslated += 1;
        continue;
      }
      const value = entry.context.endsWith(":text")
        ? `${entry.prefix}${translation.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")}${entry.suffix}`
        : translation.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
      updated = updated.slice(0, entry.start) + value + updated.slice(entry.end);
      report.translated += 1;
    }
    if (updated !== template) {
      const start = descriptor.template.loc.start.offset;
      const end = descriptor.template.loc.end.offset;
      fs.writeFileSync(full, source.slice(0, start) + updated + source.slice(end));
    }
    report.files += 1;
  }
  const reportPath = option("--report", "coverage.json");
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report));
  if (report.untranslated) process.exitCode = 1;
}

if (command === "extract") extract();
else if (command === "apply") apply();
else throw new Error("usage: i18n.mjs <extract|apply> --upstream <path> [--output|--translations|--report <path>]");
