import clsx from "clsx";
import { ArrowRight, Clock, Hand, MessageCircleQuestion, OctagonX, SkipForward, type LucideIcon } from "lucide-react";

import { DECISION_META } from "@/lib/format";
import type { TimelineDecision } from "@/lib/types";

export const DECISION_ICON: Record<TimelineDecision, LucideIcon> = {
  CONTINUE: ArrowRight,
  DEFER: Clock,
  CLARIFY: MessageCircleQuestion,
  ASK_HUMAN: Hand,
  BLOCK: OctagonX,
  SKIPPED: SkipForward,
};

/** Decision chip: an icon in the decision hue + a text label in ink (never colour alone).
 * `plain` shows an everyday phrase ("Will ask later") instead of the decision name (DEFER). */
export function DecisionBadge({
  decision,
  size = "md",
  plain = false,
  className,
}: {
  decision: TimelineDecision;
  size?: "sm" | "md" | "lg";
  plain?: boolean;
  className?: string;
}) {
  const meta = DECISION_META[decision];
  const Icon = DECISION_ICON[decision];
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-md font-semibold whitespace-nowrap text-ink",
        meta.tint,
        size === "sm" && "px-1.5 py-0.5 text-[11px]",
        size === "md" && "px-2 py-1 text-xs",
        size === "lg" && "px-3 py-1.5 text-sm",
        className,
      )}
      title={meta.description}
    >
      <Icon className={size === "lg" ? "size-4" : "size-3.5"} style={{ color: meta.color }} aria-hidden />
      {plain ? meta.plain : meta.label.toUpperCase()}
    </span>
  );
}

export function DecisionDot({ decision }: { decision: TimelineDecision }) {
  return <span aria-hidden className="inline-block size-2.5 rounded-full" style={{ background: DECISION_META[decision].color }} />;
}
