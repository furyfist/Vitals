import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const srcDir = path.join(__dirname, "../src");

let errorsCount = 0;

function walkDir(dir, callback) {
  fs.readdirSync(dir).forEach((f) => {
    const filePath = path.join(dir, f);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      walkDir(filePath, callback);
    } else {
      callback(filePath);
    }
  });
}

const HEX_REGEX = /#(?:[0-9a-fA-F]{3}){1,2}\b/g;

walkDir(srcDir, (filePath) => {
  if (!filePath.endsWith(".module.css")) return;
  if (filePath.endsWith("tokens.css")) return;

  const content = fs.readFileSync(filePath, "utf-8");
  const lines = content.split("\n");

  lines.forEach((line, idx) => {
    // Check hex colors
    const hexMatches = line.match(HEX_REGEX);
    if (hexMatches) {
      console.error(
        `[Token Error] ${path.relative(srcDir, filePath)}:${idx + 1} Hardcoded hex color ${hexMatches.join(", ")} found. Use design tokens.`
      );
      errorsCount++;
    }
  });
});

if (errorsCount > 0) {
  console.error(`\nToken Linter failed with ${errorsCount} violation(s).`);
  process.exit(1);
} else {
  console.log("Token Linter passed cleanly! All CSS modules use design tokens.");
  process.exit(0);
}
