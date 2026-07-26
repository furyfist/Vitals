import { expect, test } from "@playwright/test";

test.describe("Console Screen E2E", () => {
  test("loads console, displays hero card, and filters feed", async ({ page }) => {
    await page.goto("/");

    // Assert main header brand
    await expect(page.getByRole("link", { name: /vitals/i })).toBeVisible();

    // Assert Hero verdict card or empty state
    const heroCard = page.locator('[aria-label^="Latest verdict card"]');
    await expect(heroCard).toBeVisible();

    // Filter to CHANGED state
    const changedChip = page.getByRole("button", { name: /changed/i });
    if (await changedChip.isVisible()) {
      await changedChip.click();
      // Assert URL updated with ?state=changed
      await expect(page).toHaveURL(/state=changed/);
    }
  });
});
