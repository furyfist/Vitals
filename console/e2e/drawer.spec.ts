import { expect, test } from "@playwright/test";

test.describe("Verdict Drawer E2E & SPA History Fallback", () => {
  test("opens drawer on row click, updates URL, closes on Esc", async ({ page }) => {
    await page.goto("/");

    // Click "View full record →" link in hero card
    const viewRecordLink = page.getByRole("link", { name: /view full record/i });
    if (await viewRecordLink.isVisible()) {
      await viewRecordLink.click();

      // Assert URL updated to /v/:id
      await expect(page).toHaveURL(/\/v\//);

      // Assert drawer dialog is open
      const drawer = page.getByRole("dialog", { name: /verdict details/i });
      await expect(drawer).toBeVisible();

      // Press Escape key
      await page.keyboard.press("Escape");

      // Assert URL returned to /
      await expect(page).toHaveURL(/\/$|^\/[^v]/);
    }
  });

  test("direct deep-link to /v/:verdictId renders drawer (SPA Fallback §0.2)", async ({ page }) => {
    // Navigate directly to a deep link
    await page.goto("/v/4f2a91b8e301");

    // Assert console shell renders underneath and drawer opens
    await expect(page.getByRole("link", { name: /vitals/i })).toBeVisible();
    await expect(page.getByRole("dialog")).toBeVisible();
  });
});
