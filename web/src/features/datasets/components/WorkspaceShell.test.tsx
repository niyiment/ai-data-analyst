import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { WorkspaceShell } from "./WorkspaceShell";

function renderShell(queryCount = 6) {
  return render(
    <WorkspaceShell
      activePage="analyst"
      onNavigate={vi.fn()}
      session={null}
      deleting={false}
      onDeleteSession={vi.fn()}
      queryCount={queryCount}
    >
      <h1>Page body</h1>
    </WorkspaceShell>,
  );
}

describe("WorkspaceShell accessibility", () => {
  it("has no axe violations", async () => {
    const { container } = renderShell();

    expect(await axe(container)).toHaveNoViolations();
  });

  it("offers a skip link that targets the main landmark", () => {
    renderShell();

    const skip = screen.getByRole("link", { name: /skip to main content/i });
    expect(skip).toHaveAttribute("href", "#main-content");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
  });

  it("marks only the active page in the navigation", () => {
    renderShell();

    const nav = screen.getByRole("navigation", { name: /workspace/i });
    const current = nav.querySelectorAll('[aria-current="page"]');
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("AI Analyst");
  });

  it("reports whether the mobile menu is expanded", async () => {
    renderShell();
    const toggle = screen.getByRole("button", { name: /toggle menu/i });

    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveAttribute("aria-controls");
    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });

  it("exposes session quota usage as a labelled progress bar", () => {
    renderShell(6);

    const bar = screen.getByRole("progressbar", { name: /session quota/i });
    expect(bar).toHaveAttribute("aria-valuenow", "20");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });
});
