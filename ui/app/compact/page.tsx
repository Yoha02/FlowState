"use client";

import { useFlowState } from "@/hooks/useFlowState";
import { HandoffModal } from "@/components/HandoffModal";
import { ActionFeed } from "@/components/ActionFeed";

export default function CompactPage() {
  const {
    status,
    handoffPending,
    handoffData,
    actions,
    isControlling,
    doneMessage,
    connected,
    approve,
    reject,
    startDemo,
  } = useFlowState();

  const stateColor: Record<string, string> = {
    calm: "#22d3a3",
    elevated: "#fbbf24",
    stressed: "#f97316",
    critical: "#ef4444",
  };
  const color = stateColor[status.state] ?? "#22d3a3";
  const isCritical = status.state === "critical";

  return (
    <div
      style={{
        width: "100%",
        height: "100vh",
        background: "var(--color-dusk-bg)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        borderLeft: `2px solid ${color}40`,
        transition: "border-color 0.5s var(--ease-drift)",
      }}
    >
      {/* Compact header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--color-dusk-border)",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          flexShrink: 0,
          boxShadow: isCritical ? `0 0 20px ${color}30` : undefined,
          transition: "box-shadow 0.5s var(--ease-drift)",
        }}
      >
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: color,
            boxShadow: `0 0 8px ${color}60`,
            animation: isCritical ? "pulse-critical 1.2s infinite" : undefined,
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "14px",
            fontWeight: 600,
            color: "var(--color-dusk-text)",
          }}
        >
          FlowState
        </span>
        <div style={{ flex: 1 }} />
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            fontWeight: 700,
            color,
            letterSpacing: "0.1em",
          }}
        >
          {status.state.toUpperCase()}
        </span>
        <div
          style={{
            width: "5px",
            height: "5px",
            borderRadius: "50%",
            background: connected ? "#22d3a3" : "#6b6980",
          }}
        />
      </div>

      {/* Stress / fatigue bars */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--color-dusk-border)",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          flexShrink: 0,
        }}
      >
        <BarRow label="stress" value={status.stress} color={color} />
        <BarRow label="fatigue" value={status.fatigue} color="var(--color-dusk-blue)" />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: "var(--font-mono)",
            fontSize: "9px",
            color: "var(--color-dusk-muted)",
            letterSpacing: "0.1em",
            marginTop: "2px",
          }}
        >
          <span>consecutive: {status.consecutive}/3</span>
          <span>{Math.round(status.stress * 100)}% / {Math.round(status.fatigue * 100)}%</span>
        </div>
      </div>

      {/* Action feed — takes remaining space */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ActionFeed
          actions={actions}
          isControlling={isControlling}
          doneMessage={doneMessage}
        />
      </div>

      {/* Demo trigger (only when calm) */}
      {status.state === "calm" && !isControlling && (
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--color-dusk-border)", flexShrink: 0 }}>
          <button
            onClick={startDemo}
            style={{
              width: "100%",
              padding: "10px",
              background: "var(--color-dusk-card)",
              color: "var(--color-dusk-muted)",
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              letterSpacing: "0.06em",
              border: "1px solid var(--color-dusk-border)",
              borderRadius: "6px",
              cursor: "pointer",
              transition: "color 0.2s, border-color 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--color-dusk-accent)";
              e.currentTarget.style.borderColor = "var(--color-dusk-accent)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--color-dusk-muted)";
              e.currentTarget.style.borderColor = "var(--color-dusk-border)";
            }}
          >
            Simulate stress escalation
          </button>
        </div>
      )}

      {/* Handoff modal — full overlay */}
      {handoffPending && handoffData && (
        <HandoffModal data={handoffData} onApprove={approve} onReject={reject} />
      )}
    </div>
  );
}

function BarRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "9px",
          color: "var(--color-dusk-muted)",
          minWidth: "42px",
          letterSpacing: "0.08em",
        }}
      >
        {label}
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
            width: `${value * 100}%`,
            background: color,
            borderRadius: "2px",
            transition: "width 0.8s var(--ease-drift)",
          }}
        />
      </div>
    </div>
  );
}
