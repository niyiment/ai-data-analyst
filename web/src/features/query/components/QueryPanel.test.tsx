import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import type { QueryResult } from "../types/query";
import { QueryPanel } from "./QueryPanel";

const { askQuestion } = vi.hoisted(() => ({ askQuestion: vi.fn() }));
vi.mock("../api/query-api", () => ({ askQuestion }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

describe("QueryPanel accessibility", () => {
  beforeEach(() => {
    askQuestion.mockReset();
  });

  it("has no axe violations", async () => {
    const { container } = render(<QueryPanel datasetId="ds-1" />);

    expect(await axe(container)).toHaveNoViolations();
  });

  it("announces new answers through a labelled conversation log", () => {
    render(<QueryPanel datasetId="ds-1" />);

    expect(screen.getByRole("log", { name: /conversation/i })).toBeInTheDocument();
  });

  it("marks the conversation busy and names the running state on the submit button", async () => {
    const pending = deferred<QueryResult>();
    askQuestion.mockReturnValue(pending.promise);
    render(<QueryPanel datasetId="ds-1" />);

    await userEvent.type(screen.getByRole("textbox", { name: /question/i }), "How many rows?");
    await userEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(screen.getByRole("log", { name: /conversation/i })).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("button", { name: /running/i })).toBeDisabled();

    pending.resolve({} as QueryResult);
    await waitFor(() =>
      expect(screen.getByRole("log", { name: /conversation/i })).toHaveAttribute(
        "aria-busy",
        "false",
      ),
    );
  });
});
