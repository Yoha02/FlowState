"use client";

import { SentinelStatusBar } from "@/components/SentinelStatusBar";
import { HandoffModal } from "@/components/HandoffModal";
import { ActionFeed } from "@/components/ActionFeed";
import { TaskContextCard } from "@/components/TaskContextCard";
import { useFlowState } from "@/hooks/useFlowState";

export default function Home() {
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

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--color-dusk-bg)",
      }}
    >
      {/* Top bar */}
      <SentinelStatusBar status={status} connected={connected} />

      {/* Main content */}
      <main
        style={{
          flex: 1,
          maxWidth: "1280px",
          width: "100%",
          margin: "0 auto",
          padding: "32px 24px",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "20px",
          alignItems: "start",
        }}
      >
        {/* Left — context + metrics */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <TaskContextCard status={status} />

          {/* Demo trigger */}
          {status.state === "calm" && !isControlling && (
            <button
              onClick={startDemo}
              style={{
                padding: "14px 24px",
                background: "var(--color-dusk-card)",
                color: "var(--color-dusk-muted)",
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                letterSpacing: "0.06em",
                border: "1px solid var(--color-dusk-border)",
                borderRadius: "8px",
                cursor: "pointer",
                transition: "color 0.2s var(--ease-drift), border-color 0.2s var(--ease-drift)",
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
          )}
        </div>

        {/* Right — activity feed */}
        <div style={{ height: "520px" }}>
          <ActionFeed
            actions={actions}
            isControlling={isControlling}
            doneMessage={doneMessage}
          />
        </div>
      </main>

      {/* Footer */}
      <footer
        style={{
          padding: "16px 24px",
          borderTop: "1px solid var(--color-dusk-border)",
          display: "flex",
          justifyContent: "center",
          gap: "24px",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            color: "var(--color-dusk-subtle)",
            letterSpacing: "0.08em",
          }}
        >
          Gemini 2.0 Flash · Claude Computer Use · Augment Context Engine
        </span>
      </footer>

      {/* Handoff modal */}
      {handoffPending && handoffData && (
        <HandoffModal
          data={handoffData}
          onApprove={approve}
          onReject={reject}
        />
      )}
    </div>
  );
}
