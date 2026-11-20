import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { SessionBanner } from "./SessionBanner";

describe("SessionBanner accessibility", () => {
  it("has no axe violations and a named delete action", async () => {
    const { container } = render(
      <SessionBanner
        session={{
          session_id: "00000000-0000-4000-8000-000000000001",
          created_at: "2026-11-20T00:00:00Z",
          expires_at: "2026-11-21T00:00:00Z",
          status: "active",
        }}
        deleting={false}
        onDeleteSession={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /delete/i })).toBeEnabled();
    expect(await axe(container)).toHaveNoViolations();
  });
});
