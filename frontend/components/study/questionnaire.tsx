"use client";

import clsx from "clsx";
import { useId, useState } from "react";

import { Badge, Button } from "@/components/ui/primitives";
import type { Instrument, InstrumentItem } from "@/lib/types";

/** Renders one instrument and returns all answers (every item is required). */
export function Questionnaire({ instrument, onSubmit, busy }: { instrument: Instrument; onSubmit: (responses: Record<string, number | string>) => void; busy?: boolean }) {
  const [responses, setResponses] = useState<Record<string, number | string>>({});
  const [touched, setTouched] = useState(false);
  const complete = instrument.items.every((i) => responses[i.id] !== undefined);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setTouched(true);
        if (complete) onSubmit(responses);
      }}
      className="flex flex-col gap-5"
      aria-labelledby={`inst-${instrument.id}`}
    >
      <div>
        <h3 id={`inst-${instrument.id}`} className="text-lg font-semibold text-ink">
          {instrument.name}
        </h3>
        {!instrument.validated ? (
          <Badge tone="warning" className="mt-1">
            Pilot items (not a validated scale)
          </Badge>
        ) : null}
      </div>
      {instrument.items.map((item, index) => (
        <ItemInput
          key={item.id}
          index={index}
          item={item}
          scale={instrument.scale}
          value={responses[item.id]}
          invalid={touched && responses[item.id] === undefined}
          onChange={(v) => setResponses((r) => ({ ...r, [item.id]: v }))}
        />
      ))}
      {touched && !complete ? (
        <p role="alert" className="text-sm text-critical">
          Please answer every question.
        </p>
      ) : null}
      <div>
        <Button type="submit" loading={busy}>
          Continue
        </Button>
      </div>
    </form>
  );
}

function ItemInput({
  item,
  scale,
  value,
  onChange,
  invalid,
  index,
}: {
  item: InstrumentItem;
  scale: Instrument["scale"];
  value: number | string | undefined;
  onChange: (v: number | string) => void;
  invalid: boolean;
  index: number;
}) {
  const id = useId();
  const minLabel = item.min_label ?? scale.min_label;
  const maxLabel = item.max_label ?? scale.max_label;
  if (scale.type === "choice") {
    return (
      <fieldset className={clsx("rounded-lg border p-3", invalid ? "border-critical" : "border-line")}>
        <legend className="px-1 text-sm font-medium text-ink">
          {index + 1}. {item.text}
        </legend>
        <div className="mt-1 flex flex-col gap-1.5">
          {(item.options ?? []).map((option) => (
            <label key={option} className="flex cursor-pointer items-start gap-2 text-sm text-ink">
              <input type="radio" name={id} value={option} checked={value === option} onChange={() => onChange(option)} className="mt-1 accent-[var(--accent)]" />
              {option}
            </label>
          ))}
        </div>
      </fieldset>
    );
  }
  if (scale.type === "slider") {
    const v = typeof value === "number" ? value : undefined;
    return (
      <div className={clsx("rounded-lg border p-3", invalid ? "border-critical" : "border-line")}>
        <label htmlFor={id} className="text-sm font-medium text-ink">
          {index + 1}. {item.text}
        </label>
        <input
          id={id}
          type="range"
          min={scale.min ?? 0}
          max={scale.max ?? 100}
          step={scale.step ?? 5}
          value={v ?? 50}
          onChange={(e) => onChange(Number(e.target.value))}
          aria-valuetext={v === undefined ? "not answered" : String(v)}
          className={clsx("mt-3 w-full accent-[var(--accent)]", v === undefined && "opacity-50")}
        />
        <div className="mt-1 flex justify-between text-xs text-ink-3">
          <span>{minLabel}</span>
          <span className="tabular font-medium text-ink">{v === undefined ? "move the slider" : v}</span>
          <span>{maxLabel}</span>
        </div>
      </div>
    );
  }
  const points = Array.from({ length: (scale.max ?? 7) - (scale.min ?? 1) + 1 }, (_, i) => (scale.min ?? 1) + i);
  return (
    <fieldset className={clsx("rounded-lg border p-3", invalid ? "border-critical" : "border-line")}>
      <legend className="px-1 text-sm font-medium text-ink">
        {index + 1}. {item.text}
      </legend>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="w-24 text-xs text-ink-3">{minLabel}</span>
        {points.map((p) => (
          <label key={p} className={clsx("flex size-9 cursor-pointer items-center justify-center rounded-lg border text-sm", value === p ? "border-accent bg-accent text-accent-ink" : "border-line-strong text-ink hover:bg-surface-2")}>
            <input type="radio" name={id} value={p} checked={value === p} onChange={() => onChange(p)} className="sr-only" />
            {p}
          </label>
        ))}
        <span className="w-24 text-right text-xs text-ink-3">{maxLabel}</span>
      </div>
    </fieldset>
  );
}
