import { expect, test } from "@playwright/test";
import axe from "axe-core";

test.describe("Automated Accessibility Audits (axe-core)", () => {
  const routes = ["/", "/scopes", "/about"];

  for (const route of routes) {
    test(`should have zero axe-core violations on ${route}`, async ({ page }) => {
      await page.goto(route);
      await page.evaluate(axe.source);
      const results = await page.evaluate(async () => {
        return await (window as any).axe.run();
      });

      // Filter out non-critical issues if necessary or assert clean zero violations
      const violations = results.violations || [];
      expect(violations, `Found ${violations.length} accessibility violations on ${route}`).toEqual([]);
    });
  }
});
