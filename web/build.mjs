/**
 * Build the self-contained interactive demo at ../index.html from the TypeScript
 * port. Bundles the checker with esbuild, then inlines it and the embedded
 * fonts into the UI template. Run from the web/ directory: `node build.mjs`.
 */
import { execSync } from "node:child_process";
import fs from "node:fs";

// Browser bundle (IIFE global `HZ`) for the demo, and an ESM bundle for parity.
execSync(
  "npx --yes esbuild src/checker.ts --bundle --format=iife --global-name=HZ --outfile=dist/checker.iife.js --minify",
  { stdio: "inherit" },
);
execSync(
  "npx --yes esbuild src/checker.ts --bundle --format=esm --outfile=dist/checker.mjs",
  { stdio: "inherit" },
);

const template = fs.readFileSync("ui-template.html", "utf8");
const fonts = fs.readFileSync("fonts-embed.css", "utf8");
const checker = fs.readFileSync("dist/checker.iife.js", "utf8");

const html = template
  .replace("/*__FONTS__*/", () => fonts)
  .replace("/*__CHECKER__*/", () => checker);

if (html.includes("__FONTS__") || html.includes("__CHECKER__")) {
  throw new Error("template placeholder was not replaced");
}
fs.writeFileSync("../index.html", html);
console.log(`wrote ../index.html (${html.length} bytes)`);
