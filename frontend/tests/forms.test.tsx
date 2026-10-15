import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChartFrame } from "@/components/charts/charts";
import { Questionnaire } from "@/components/study/questionnaire";
import type { Instrument } from "@/lib/types";

const instrument = {
  id: "pilot",
  name: "Pilot items",
  validated: false,
  ready: true,
  scale: { type: "likert", min: 1, max: 5, min_label: "Disagree", max_label: "Agree" },
  items: [
    { id: "q1", text: "I understood why the agent stopped." },
    { id: "q2", text: "I felt in control." },
  ],
} as unknown as Instrument;

describe("Questionnaire", () => {
  it("requires every item before submitting", async () => {
    const onSubmit = vi.fn();
    render(<Questionnaire instrument={instrument} onSubmit={onSubmit} />);
    expect(screen.getByText("Pilot items (not a validated scale)")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Please answer every question.");
    expect(onSubmit).not.toHaveBeenCalled();

    const groups = screen.getAllByRole("group");
    await userEvent.click(groups[0]!.querySelector('input[value="4"]')!);
    await userEvent.click(groups[1]!.querySelector('input[value="2"]')!);
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(onSubmit).toHaveBeenCalledWith({ q1: 4, q2: 2 });
  });
});

describe("ChartFrame", () => {
  it("offers a table view of the plotted data", async () => {
    render(
      <ChartFrame title="Interruptions" table={{ columns: ["Policy", "Rate"], rows: [["Adaptive", 0.4]] }} legend={[{ label: "A", color: "#000" }, { label: "B", color: "#111" }]}>
        <div>chart</div>
      </ChartFrame>,
    );
    expect(screen.getByText("chart")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Legend" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Show table" }));
    expect(screen.getByRole("columnheader", { name: "Rate" })).toBeInTheDocument();
    expect(screen.getByText("Adaptive")).toBeInTheDocument();
  });
});
