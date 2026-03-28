"use client";

import type { FlowStateLevel, StatusUpdate } from "@/hooks/useFlowState";

interface Props {
  status: StatusUpdate;
  connected: boolean;
}

const STATE_CONFIG: Record<
  FlowStateLevel,
  { label: string; color: string; glow: string; barColor: string }
> = {
  calm: {
    label: "CALM",
    color: "#22d3a3",
    glow: "rgba(34,211,163,0.25)",
    barColor: "#22d3a3",
  },
  elevated: {
    label: "ELEVATED",
    color: "#fbbf24",
    glow: "rgba(251,191,36,0.25)",
    barColor: "#fbbf24",
  },
  stressed: {
    label: "STRESSED",
    color: "#f97316",
    glow: "rgba(249,115,22,0.3)",
    barColor: "#f97316",
  },
  critical: {
    label: "CRITICAL",
    color: "#ef4444",
    glow: "rgba(239,68,68,0.35)",
    barColor: "#ef4444",
  },
};

export function SentinelStatusBar({ status, connected }: Props) {
  const cfg = STATE_CONFIG[status.state];
  const isCritical = status.state === "critical";

  return (
    <header
      style={{
        background: "var(--color-dusk-surface)",
        borderBottom: `1px solid var(--color-dusk-border)`,
        transition: `border-color 0.6s var(--ease-drift), box-shadow 0.6s var(--ease-drift)`,
        boxShadow: isCritical
          ? `0 0 32px 0 ${cfg.glow}, inset 0 -1px 0 ${cfg.color}40`
          : `0 1px 0 0 var(--color-dusk-border)`,
      }}
    >
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          padding: "0 24px",
          height: "56px",
          display: "flex",
          alignItems: "center",
          gap: "24px",
        }}
      >
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: cfg.color,
              transition: "background 0.5s var(--ease-drift)",
              boxShadow: `0 0 8px 2px ${cfg.glow}`,
              animation: isCritical ? "pulse-critical 1.5s infinite" : undefined,
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "17px",
              fontWeight: 600,
              color: "var(--color-dusk-text)",
              letterSpacing: "0.01em",
            }}
          >
            FlowState
          </span>
        </div>

        {/* Divider */}
        <div
          style={{
            width: "1px",
            height: "20px",
            background: "var(--color-dusk-border)",
          }}
        />

        {/* State badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              fontWeight: 700,
              color: cfg.color,
              letterSpacing: "0.12em",
              transition: "color 0.5s var(--ease-drift)",
            }}
          >
            {cfg.label}
          </span>
          {status.consecutive > 0 && (
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                color: "var(--color-dusk-muted)",
              }}
            >
              ×{status.consecutive}
            </span>
          )}
        </div>

        {/* Stress bar */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, maxWidth: "240px" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--color-dusk-muted)",
              minWidth: "36px",
            }}
          >
            stress
          </span>
          <div
            style={{
              flex: 1,
              height: "3px",
              background: "var(--color-dusk-border)",
              borderRadius: "2px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${status.stress * 100}%`,
                background: cfg.barColor,
                borderRadius: "2px",
                transition: "width 0.8s var(--ease-drift), background 0.5s var(--ease-drift)",
              }}
            />
          </div>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--color-dusk-muted)",
              minWidth: "32px",
              textAlign: "right",
            }}
          >
            {Math.round(status.stress * 100)}%
          </span>
        </div>

        {/* Fatigue bar */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, maxWidth: "240px" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--color-dusk-muted)",
              minWidth: "36px",
            }}
          >
            fatigue
          </span>
          <div
            style={{
              flex: 1,
              height: "3px",
              background: "var(--color-dusk-border)",
              borderRadius: "2px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${status.fatigue * 100}%`,
                background: "var(--color-dusk-blue)",
                borderRadius: "2px",
                transition: "width 0.8s var(--ease-drift)",
              }}
            />
          </div>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--color-dusk-muted)",
              minWidth: "32px",
              textAlign: "right",
            }}
          >
            {Math.round(status.fatigue * 100)}%
          </span>
        </div>

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Connection dot */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: connected ? "#22d3a3" : "#6b6980",
              transition: "background 0.4s var(--ease-drift)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--color-dusk-muted)",
            }}
          >
            {connected ? "live" : "offline"}
          </span>
        </div>
      </div>
    </header>
  );
}
