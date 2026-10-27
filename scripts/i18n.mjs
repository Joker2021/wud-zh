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
const roleLabelTarget = {
  file: "ui/src/components/NavigationDrawer.vue",
  block: "script",
  anchor: "return props.user.role;",
  context: "script:userRole.display",
  values: ["admin", "rw", "ro"],
};
const dynamicTextTargets = {
  "ui/src/components/NavigationDrawer.vue": [
    ...["server", "registries", "watchers", "triggers", "auth", "users"].map((text) => ({
      block: "script", anchor: `name: "${text}"`, values: [text], context: "script:configurationItems.name",
    })),
    { block: "script", anchor: 'return "Settings";', values: ["Settings"], context: "script:userName.fallback" },
    { block: "script", anchor: 'return "Connected";', values: ["Connected"], context: "script:userSubtitle.connected" },
    { block: "script", anchor: 'return "Preferences";', values: ["Preferences"], context: "script:userSubtitle.preferences" },
    { block: "script", anchor: '`Error when trying to logout (${e.message})`', values: ["Error when trying to logout (", ")"], context: "script:logout.error" },
    { block: "script", anchor: '`Switched to demo user: ${newUser.username} (${newUser.role})`', values: ["Switched to demo user: ", " (", ")"], context: "script:demo.switch" },
    { block: "template", anchor: `:title="mini ? 'Expand sidebar' : 'Collapse sidebar'"`, values: ["Expand sidebar", "Collapse sidebar"], context: "button:@title" },
  ],
  "ui/src/components/ConfigurationDrawerContent.vue": [
    { block: "template", anchor: `{{ configurationItems.length }} {{ configurationItems.length === 1 ? 'entry' : 'entries' }}`, values: ["entry", "entries"], context: "configurationItems:count" },
    { block: "template", anchor: "{{ cfg.value ? 'true' : 'false' }}", values: ["true", "false"], context: "configuration:boolean" },
    { block: "script", anchor: '`${key} copied to clipboard`', values: [" copied to clipboard"], context: "script:configuration.copy.success" },
    { block: "script", anchor: '`Unable to copy ${key} to clipboard`', values: ["Unable to copy ", " to clipboard"], context: "script:configuration.copy.failure" },
  ],
};

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

function dynamicStrings(source, file, block) {
  const { descriptor, errors } = parseSfc(source, { filename: file });
  if (errors.length) throw new Error(`${file}: invalid Vue SFC: ${errors[0].message}`);
  const content = descriptor[block]?.content;
  if (content === undefined) return [];
  const items = [];
  for (const target of dynamicTextTargets[file] ?? []) {
    if (target.block !== block) continue;
    const anchorStart = content.indexOf(target.anchor);
    if (anchorStart < 0 || content.indexOf(target.anchor, anchorStart + target.anchor.length) >= 0) {
      throw new Error(`${file}: expected exactly one dynamic text anchor: ${target.anchor}`);
    }
    for (const text of target.values) {
      const textOffset = target.anchor.indexOf(text);
      if (textOffset < 0 || target.anchor.indexOf(text, textOffset + text.length) >= 0) {
        throw new Error(`${file}: invalid dynamic text target: ${text}`);
      }
      const context = `${target.context}:${text}`;
      items.push({
        id: translationId(file, context, text), text, context,
        start: anchorStart + textOffset, end: anchorStart + textOffset + text.length,
      });
    }
  }
  return items;
}

function roleLabelStrings(source, file, block) {
  if (file !== roleLabelTarget.file || block !== roleLabelTarget.block) return [];
  const { descriptor, errors } = parseSfc(source, { filename: file });
  if (errors.length) throw new Error(`${file}: invalid Vue SFC: ${errors[0].message}`);
  const content = descriptor[block]?.content;
  const start = content?.indexOf(roleLabelTarget.anchor) ?? -1;
  if (start < 0 || content.indexOf(roleLabelTarget.anchor, start + roleLabelTarget.anchor.length) >= 0) {
    throw new Error(`${file}: expected exactly one role display anchor: ${roleLabelTarget.anchor}`);
  }
  return roleLabelTarget.values.map((text) => {
    const context = `${roleLabelTarget.context}:${text}`;
    return { id: translationId(file, context, text), text, context, file, block, roleLabel: true };
  });
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
    const source = fs.readFileSync(full, "utf8");
    return [
      ...staticStrings(source, relative),
      ...dynamicStrings(source, relative, "template"),
      ...dynamicStrings(source, relative, "script"),
      ...roleLabelStrings(source, relative, "script"),
    ];
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
    let updatedSource = source;
    for (const block of ["template", "script"]) {
      const { descriptor, errors } = parseSfc(updatedSource, { filename: relative });
      if (errors.length) throw new Error(`${relative}: invalid Vue SFC`);
      const section = descriptor[block];
      if (!section) continue;
      const sectionContent = section.content;
      const entries = [
        ...(block === "template" ? staticStrings(updatedSource, relative) : []),
        ...dynamicStrings(updatedSource, relative, block),
      ].sort((a, b) => b.start - a.start);
      let updatedSection = sectionContent;
      for (const entry of entries) {
        report.identified += 1;
        const translation = translations[entry.id];
        if (typeof translation !== "string" || !translation.trim()) {
          report.untranslated += 1;
          continue;
        }
        let value;
        if (entry.context.endsWith(":text")) {
          value = `${entry.prefix}${translation.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")}${entry.suffix}`;
        } else if (entry.context.startsWith("script:") || entry.context.startsWith("configurationItems:count") || entry.context.startsWith("configuration:boolean:") || entry.context.startsWith("button:@title:")) {
          value = translation;
        } else {
          value = `"${translation.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;")}"`;
        }
        updatedSection = updatedSection.slice(0, entry.start) + value + updatedSection.slice(entry.end);
        report.translated += 1;
      }
      const roleLabels = roleLabelStrings(source, relative, block);
      if (roleLabels.length) {
        const translationsByRole = {};
        for (const entry of roleLabels) {
          report.identified += 1;
          const translation = translations[entry.id];
          if (typeof translation !== "string" || !translation.trim()) {
            report.untranslated += 1;
          } else {
            translationsByRole[entry.text] = translation;
            report.translated += 1;
          }
        }
        if (Object.keys(translationsByRole).length === roleLabelTarget.values.length) {
          const roleAnchor = roleLabelTarget.anchor;
          const roleStart = updatedSection.indexOf(roleAnchor);
          if (roleStart < 0 || updatedSection.indexOf(roleAnchor, roleStart + roleAnchor.length) >= 0) {
            throw new Error(`${relative}: expected exactly one role display anchor: ${roleAnchor}`);
          }
          const roleMap = JSON.stringify(translationsByRole);
          const roleExpression = `return ((role: string, labels: Record<string, string>) => labels[role] ?? role)(props.user.role, ${roleMap});`;
          updatedSection = updatedSection.slice(0, roleStart) + roleExpression + updatedSection.slice(roleStart + roleAnchor.length);
          for (const role of ["admin", "rw"]) {
            const colorAnchor = `if (userRole.value === "${role}")`;
            const colorStart = updatedSection.indexOf(colorAnchor);
            if (colorStart < 0 || updatedSection.indexOf(colorAnchor, colorStart + colorAnchor.length) >= 0) {
              throw new Error(`${relative}: expected exactly one role color anchor: ${colorAnchor}`);
            }
            const localizedAnchor = `if (userRole.value === ${JSON.stringify(translationsByRole[role])})`;
            updatedSection = updatedSection.slice(0, colorStart) + localizedAnchor + updatedSection.slice(colorStart + colorAnchor.length);
          }
        }
      }
      if (updatedSection !== sectionContent) {
        updatedSource = updatedSource.slice(0, section.loc.start.offset) + updatedSection + updatedSource.slice(section.loc.end.offset);
      }
    }
    if (updatedSource !== source) fs.writeFileSync(full, updatedSource);
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
