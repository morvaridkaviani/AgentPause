import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DecisionBadge } from "@/components/decision/decision-badge";
import { InterventionCardView } from "@/components/demo/intervention-card";
import { Timeline } from "@/components/demo/timeline";

import { makeCard, makeDecision, makeTimelineItem } from "./fixtures";

describe("DecisionBadge", () => {
  it("shows a text label, not colour alone", () => {
    render(<DecisionBadge decision="ASK_HUMAN" />);
    expect(screen.getByText("ASK HUMAN")).toBeInTheDocument();
  });
});

describe("InterventionCardView", () => {
  it("explains what, why, consequences, reversibility, and alternatives", () => {
    render(<InterventionCardView card={makeCard()} onRespond={() => undefined} />);
    expect(screen.getByRole("heading", { name: /needs your confirmation/i })).toBeInTheDocument();
    expect(screen.getByText("Book the 08:10 flight to Lisbon for €412")).toBeInTheDocument();
    expect(screen.getByText("Cannot be undone")).toBeInTheDocument();
    expect(screen.getByText(/charged to the saved card/)).toBeInTheDocument();
    expect(screen.getByText(/Wrong dates or a fare/)).toBeInTheDocument();
    expect(screen.getByText("Hold the fare for 24 hours")).toBeInTheDocument();
    expect(screen.getByText(/last moment before the booking/)).toBeInTheDocument();
    expect(screen.getByText("Simulated action")).toBeInTheDocument();
  });

  it("offers only the allowed responses and reports clicks", async () => {
    const onRespond = vi.fn();
    render(<InterventionCardView card={makeCard()} onRespond={onRespond} />);
    expect(screen.queryByRole("button", { name: /I'll do this step/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Approve/ }));
    expect(onRespond).toHaveBeenCalledWith("approve", {});
  });

  it("supports keyboard shortcuts and shows the timing explanation on Ask why", async () => {
    const onRespond = vi.fn();
    render(<InterventionCardView card={makeCard()} onRespond={onRespond} />);
    await userEvent.keyboard("r");
    expect(onRespond).toHaveBeenLastCalledWith("reject", {});
    await userEvent.keyboard("w");
    expect(onRespond).toHaveBeenLastCalledWith("ask_why", {});
    expect(screen.getByText(/the flight had not been chosen yet/)).toBeInTheDocument();
  });

  it("ignores shortcuts while busy", async () => {
    const onRespond = vi.fn();
    render(<InterventionCardView card={makeCard()} onRespond={onRespond} busy />);
    await userEvent.keyboard("a");
    expect(onRespond).not.toHaveBeenCalled();
  });

  it("collects answers to clarification questions", async () => {
    const onRespond = vi.fn();
    const card = makeCard({
      decision: makeDecision({ decision: "CLARIFY" }),
      allowed_responses: ["answer", "cancel_task"],
      assumptions: [
        { id: "dates", description: "you want to fly on 12 May", kind: "input", agent_value: "12 May", options: ["12 May", "13 May"], confidence: 0.6, if_wrong: "Wrong flight" },
      ],
    });
    render(<InterventionCardView card={card} onRespond={onRespond} />);
    await userEvent.click(screen.getByLabelText("13 May"));
    await userEvent.click(screen.getByRole("button", { name: /Confirm answer/ }));
    expect(onRespond).toHaveBeenCalledWith("answer", { dates: "13 May" });
  });
});

describe("Timeline", () => {
  it("renders steps with decisions and lets the user select one", async () => {
    const onSelect = vi.fn();
    const items = [makeTimelineItem(), makeTimelineItem({ seq: 2, step_index: 1, label: "Book flight", decision: "ASK_HUMAN", response: "approve" })];
    render(<Timeline items={items} selectedSeq={2} onSelect={onSelect} />);
    expect(screen.getByRole("list", { name: "Agent timeline" }).children).toHaveLength(2);
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Book flight/ })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: /Search flights/ }));
    expect(onSelect).toHaveBeenCalledWith(items[0]);
  });

  it("hides ground-truth harm in study mode", () => {
    const item = makeTimelineItem({ harm: ["wrong_dates"] });
    const { rerender } = render(<Timeline items={[item]} selectedSeq={null} onSelect={() => undefined} />);
    expect(screen.getByText(/an error was executed here/)).toBeInTheDocument();
    rerender(<Timeline items={[item]} selectedSeq={null} onSelect={() => undefined} showGroundTruth={false} />);
    expect(screen.queryByText(/an error was executed here/)).not.toBeInTheDocument();
  });
});

describe("simple view", () => {
  it("uses everyday decision labels", () => {
    render(<DecisionBadge decision="DEFER" plain />);
    expect(screen.getByText("Will ask later")).toBeInTheDocument();
  });

  it("shows a plain card title and a single explanation", async () => {
    render(<InterventionCardView card={makeCard()} onRespond={() => undefined} simple />);
    expect(screen.getByRole("heading", { name: "The assistant needs your OK" })).toBeInTheDocument();
    expect(screen.getByText("Asked for approval")).toBeInTheDocument();
    expect(screen.queryByText(/last moment before the booking/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Ask why/ }));
    expect(screen.getByText(/last moment before the booking/)).toBeInTheDocument();
  });

  it("hides signal chips and scores in the simple timeline", () => {
    render(<Timeline items={[makeTimelineItem({ response: "approve" })]} selectedSeq={null} onSelect={() => undefined} simple />);
    expect(screen.getByRole("list", { name: "What the assistant did" })).toBeInTheDocument();
    expect(screen.getByText("Went ahead")).toBeInTheDocument();
    expect(screen.getByText("You: approved")).toBeInTheDocument();
    expect(screen.queryByText("Intent clarity")).not.toBeInTheDocument();
    expect(screen.queryByText(/Score/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
