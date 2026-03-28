"use client";

import type { StatusUpdate } from "@/hooks/useFlowState";

interface Props {
  status: StatusUpdate;
}

const TASK_ICONS: Record<string, string> = {
  coding: "⌨",
  browsing: "⊕",
  terminal: "›_",
  writing: "✍",
  unknown: "◯",
};

const LEVEL_LABEL: Record<string, string> = {
  calm: "All clear — no stress detected",
  elevated: "Mild tension — keeping watch",
  stressed: "High stress — approaching threshold",
  critical: "Critical — handoff pipeline active",
};

export function TaskContextCard({ status }: Props) {
  const stressed = status.stress;
  const fatigued = status.fatigue;

  return (
    <div
      style={{
        background: "var(--color-dusk-surface)",
        border: "1px solid var(--color-dusk-border)",
        borderRadius: "10px",
        padding: "24px",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* Status headline */}
      <div>
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "0.12em",
            color: "var(--color-dusk-muted)",
            fontWeight: 700,
            marginBottom: "10px",
          }}
        >
          SENTINEL STATUS
        </p>
        <p
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "18px",
            color: "var(--color-dusk-text)",
            lineHeight: 1.4,
            fontStyle: "italic",
          }}
        >
          {LEVEL_LABEL[status.state]}
        </p>
      </div>

      {/* Metrics grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "12px",
        }}
      >
        <MetricCell label="Stress" value={stressed} color="#f97316" />
        <MetricCell label="Fatigue" value={fatigued} color="var(--color-dusk-blue)" />
        <MetricCell
          label="Consecutive"
          value={status.consecutive}
          rawValue={`${status.consecutive} / 3`}
          color="var(--color-dusk-accent)"
        />
        <MetricCell
          label="State"
          rawValue={status.state.toUpperCase()}
          color={
            status.state === "calm"
              ? "#22d3a3"
              : status.state === "elevated"
              ? "#fbbf24"
              : status.state === "stressed"
              ? "#f97316"
              : "#ef4444"
          }
        />
      </div>

      {/* How it works */}
      <div
        style={{
          marginTop: "auto",
          padding: "16px",
          background: "var(--color-dusk-card)",
          borderRadius: "8px",
          border: "1px solid var(--color-dusk-border)",
        }}
      >
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "0.1em",
            color: "var(--color-dusk-muted)",
            marginBottom: "8px",
          }}
        >
          HOW IT WORKS
        </p>
        <ol
          style={{
            paddingLeft: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          {[
            "Webcam monitors facial expressions every 5s",
            "Gemini Flash scores stress + fatigue",
            "3 consecutive high readings → consent modal",
            "You approve → Claude takes over GCP Cloud Shell",
          ].map((step, i) => (
            <li
              key={i}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "12px",
                color: "rgba(241,240,236,0.6)",
                lineHeight: 1.5,
              }}
            >
              {step}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

function MetricCell({
  label,
  value,
  rawValue,
  color,
}: {
  label: string;
  value?: number;
  rawValue?: string;
  color: string;
}) {
  return (
    <div
      style={{
        background: "var(--color-dusk-card)",
        borderRadius: "8px",
        padding: "14px 16px",
        border: "1px solid var(--color-dusk-border)",
      }}
    >
      <p
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "9px",
          letterSpacing: "0.12em",
          color: "var(--color-dusk-muted)",
          marginBottom: "8px",
        }}
      >
        {label.toUpperCase()}
      </p>
      {rawValue ? (
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "14px",
            color,
            fontWeight: 700,
          }}
        >
          {rawValue}
        </p>
      ) : (
        <>
          <div
            style={{
              height: "3px",
              background: "var(--color-dusk-border)",
              borderRadius: "2px",
              overflow: "hidden",
              marginBottom: "6px",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${(value ?? 0) * 100}%`,
                background: color,
                borderRadius: "2px",
                transition: "width 0.8s var(--ease-drift)",
              }}
            />
          </div>
          <p
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "14px",
              color,
              fontWeight: 700,
            }}
          >
            {Math.round((value ?? 0) * 100)}%
          </p>
        </>
      )}
    </div>
  );
}
