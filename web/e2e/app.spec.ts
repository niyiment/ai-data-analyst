import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Surface failing API calls in the test output; the UI only shows them as short-lived toasts.
test.beforeEach(({ page }) => {
  page.on("response", (response) => {
    // A fresh browser has no session yet, so the first GET /sessions/me is expected to be 401.
    const expected = response.url().endsWith("/api/v1/sessions/me") && response.status() === 401;
    if (response.url().includes("/api/") && response.status() >= 400 && !expected) {
      console.log(`API ${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });
});

function nav(page: Page, name: RegExp) {
  return page.getByRole("navigation", { name: /workspace/i }).getByRole("button", { name });
}

async function loadSample(page: Page) {
  await page.goto("/");
  await expect(page.getByText(/auto-deletes/i)).toBeVisible();
  await nav(page, /datasets/i).click();
  await page.getByRole("button", { name: /load retail sales sample/i }).click();
  // Generous: the first request after `next dev` starts compiles the /api proxy route.
  await expect(page.getByRole("textbox", { name: /column name for/i }).first()).toBeVisible({
    timeout: 30_000,
  });
}

async function ask(page: Page, question: string) {
  await nav(page, /ai analyst/i).click();
  await page.getByRole("textbox", { name: /question/i }).fill(question);
  await page.getByRole("button", { name: /^ask$/i }).click();
}

test.describe("analyst journey", () => {
  test("load sample, ask, see table + chart + SQL, get insights, pin and export a report", async ({
    page,
  }) => {
    await loadSample(page);
    await ask(page, "What is the revenue by region?");

    const log = page.getByRole("log", { name: /conversation/i });
    await expect(log.getByRole("cell", { name: "North" })).toBeVisible();
    await expect(log.getByRole("figure", { name: /revenue by region/i })).toBeVisible();
    await expect(log.getByText(/SUM\(revenue\)/i)).toBeVisible();

    await log.getByRole("button", { name: /generate insights/i }).click();
    await expect(log.getByRole("region", { name: /insights/i })).toContainText(
      "Revenue is concentrated",
    );

    await log.getByRole("button", { name: /pin to report/i }).click();
    const pdf = log.getByRole("link", { name: /pdf/i });
    await expect(pdf).toBeVisible();
    const exported = await page.request.get((await pdf.getAttribute("href")) ?? "");
    expect(exported.headers()["content-type"]).toContain("application/pdf");
    expect((await exported.body()).subarray(0, 4).toString()).toBe("%PDF");

    await nav(page, /reports/i).click();
    await expect(
      page.getByRole("heading", { name: /what is the revenue by region/i }),
    ).toBeVisible();
  });

  test("unsafe model SQL is blocked by the validator and explained", async ({ page }) => {
    await loadSample(page);
    await ask(page, "Please delete all the orders");

    const alert = page.getByRole("alert").filter({ hasText: /rejected/i });
    await expect(alert).toBeVisible();
    await expect(page.getByRole("cell", { name: "North" })).toHaveCount(0);
  });

  test("an ambiguous question asks for clarification, then answers", async ({ page }) => {
    await loadSample(page);
    await ask(page, "What are our best regions?");

    await expect(page.getByText(/best by revenue or by units sold\?/i)).toBeVisible();
    await page.getByRole("button", { name: "By total revenue" }).click();
    await expect(page.getByRole("cell", { name: "North" }).first()).toBeVisible();
  });

  test("delete my data clears datasets and starts a fresh session", async ({ page }) => {
    await loadSample(page);

    await page.getByRole("button", { name: /delete my data/i }).click();
    await nav(page, /datasets/i).click();

    await expect(page.getByRole("button", { name: /load retail sales sample/i })).toBeVisible();
    await expect(page.getByRole("textbox", { name: /column name for/i })).toHaveCount(0);
  });
});

test.describe("evaluation", () => {
  test("a background run shows progress and completes", async ({ page }) => {
    await page.goto("/");
    await nav(page, /evaluation/i).click();
    await page
      .getByRole("combobox", { name: /golden question set/i })
      .selectOption("retail_orders");
    await page.getByRole("button", { name: /run evaluation/i }).click();

    await expect(page.getByRole("status")).toContainText(/answered \d+ of 26/i);
    await expect(page.getByRole("status")).toBeHidden({ timeout: 90_000 });
    await expect(page.getByRole("cell", { name: "ro-26" })).toBeVisible();
    await expect(page.getByText(/of 26 passed/i)).toBeVisible();
    await expect(page.getByText(/model: ollama:e2e-stub/i)).toBeVisible();
  });
});

test.describe("accessibility in a real browser", () => {
  test("skip link moves keyboard focus to the main content", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/auto-deletes/i)).toBeVisible();

    await page.keyboard.press("Tab");
    const skip = page.getByRole("link", { name: /skip to main content/i });
    await expect(skip).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.locator("#main-content")).toBeFocused();
  });

  for (const pageName of [/overview/i, /datasets/i, /reports/i, /evaluation/i]) {
    test(`no WCAG A/AA violations, including contrast, on ${pageName.source}`, async ({ page }) => {
      await page.goto("/");
      await expect(page.getByText(/auto-deletes/i)).toBeVisible();
      await nav(page, pageName).click();

      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      expect(results.violations.map((v) => `${v.id}: ${v.nodes.length}`)).toEqual([]);
    });
  }
});
