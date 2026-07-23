import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Drawer from "./index";

describe("Drawer & Bottom Sheet", () => {
  it("renders desktop drawer dialog when open", () => {
    render(
      <Drawer isOpen={true} onClose={() => {}} ariaLabel="Test Drawer">
        <div>Drawer Content</div>
      </Drawer>
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText("Drawer Content")).toBeInTheDocument();
  });
});
