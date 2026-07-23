import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const staticAssetsDir = path.resolve(import.meta.dirname, "../../vitals/console/static/assets");

if (!fs.existsSync(staticAssetsDir)) {
  console.error("Static assets directory does not exist. Run build first.");
  process.exit(1);
}

const files = fs.readdirSync(staticAssetsDir);

let totalJsGz = 0;
let totalCssGz = 0;

for (const file of files) {
  const filePath = path.join(staticAssetsDir, file);
  const stat = fs.statSync(filePath);
  if (!stat.isFile()) continue;

  const content = fs.readFileSync(filePath);
  const gzSize = zlib.gzipSync(content).length;

  if (file.endsWith(".js")) {
    totalJsGz += gzSize;
  } else if (file.endsWith(".css")) {
    totalCssGz += gzSize;
  }
}

const jsBudget = 250 * 1024; // 250 KB
const cssBudget = 30 * 1024; // 30 KB

console.log(`JS Gzipped size: ${(totalJsGz / 1024).toFixed(2)} KB / 250 KB budget`);
console.log(`CSS Gzipped size: ${(totalCssGz / 1024).toFixed(2)} KB / 30 KB budget`);

let failed = false;
if (totalJsGz > jsBudget) {
  console.error(`❌ JS bundle budget exceeded! (${(totalJsGz / 1024).toFixed(2)} KB > 250 KB)`);
  failed = true;
}
if (totalCssGz > cssBudget) {
  console.error(`❌ CSS bundle budget exceeded! (${(totalCssGz / 1024).toFixed(2)} KB > 30 KB)`);
  failed = true;
}

if (failed) {
  process.exit(1);
} else {
  console.log("✅ Bundle budget check passed!");
}
