import { runChecks, pyRound } from "./dist/checker.mjs";
import fs from "fs";

const golden = JSON.parse(fs.readFileSync(new URL("./golden.json", import.meta.url), "utf8"));

// --- pyRound parity against Python round(x, 1) ---
const roundCases = JSON.parse(fs.readFileSync(new URL("./round_cases.json", import.meta.url), "utf8"));
let roundFails = 0;
for (const { x, py } of roundCases) {
  const got = pyRound(x, 1);
  if (got !== py && Math.abs(got - py) > 1e-12) {
    roundFails++;
    if (roundFails <= 20) console.log(`  pyRound(${x}) js ${got} != py ${py}`);
  }
}
console.log(`pyRound: ${roundCases.length - roundFails}/${roundCases.length} match Python round()`);

// a = golden (Python truth), b = js output
function eq(a, b, path, diffs) {
  if (typeof a === "number" && typeof b === "number") {
    if (Math.abs(a - b) > 1e-9) diffs.push(`${path}: js ${b} != py ${a}`);
    return;
  }
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b)) { diffs.push(`${path}: array/type mismatch`); return; }
    if (a.length !== b.length) diffs.push(`${path}: length js ${b.length} != py ${a.length}`);
    const n = Math.min(a.length, b.length);
    for (let i = 0; i < n; i++) eq(a[i], b[i], `${path}[${i}]`, diffs);
    return;
  }
  if (a && typeof a === "object" && b && typeof b === "object") {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const k of keys) {
      if (!(k in a)) diffs.push(`${path}.${k}: present in js, absent in py`);
      else if (!(k in b)) diffs.push(`${path}.${k}: present in py, absent in js`);
      else eq(a[k], b[k], `${path}.${k}`, diffs);
    }
    return;
  }
  if (a !== b) diffs.push(`${path}: js ${JSON.stringify(b)} != py ${JSON.stringify(a)}`);
}

let fails = 0;
const failed = [];
for (const t of golden) {
  const got = runChecks(t.text, t.content_type);
  const diffs = [];
  eq(t.report, got, t.name, diffs);
  if (diffs.length) {
    fails++;
    failed.push(t.name);
    console.log(`\n✗ ${t.name}`);
    diffs.slice(0, 15).forEach((d) => console.log("   " + d));
    if (diffs.length > 15) console.log(`   … +${diffs.length - 15} more`);
  }
}
console.log(`\n${golden.length - fails}/${golden.length} texts match Python exactly`);
if (fails) console.log("failed:", failed.join(", "));
process.exit(fails || roundFails ? 1 : 0);
