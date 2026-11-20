import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";
import { SettingsView } from "./SettingsView";

describe("SettingsView accessibility", () => {
  it("has no axe violations and labels every form control", async () => {
    const { container } = render(<SettingsView />);

    expect(screen.getByRole("combobox")).toHaveAccessibleName();
    for (const input of screen.queryAllByRole("textbox")) {
      expect(input).toHaveAccessibleName();
    }
    expect(await axe(container)).toHaveNoViolations();
  });
});
