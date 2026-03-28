"use client";

import { useEffect, useRef } from "react";
import type { ActionItem } from "@/hooks/useFlowState";

interface Props {
  actions: ActionItem[];
  isControlling: boolean;
  doneMessage: string | null;
}

const ICON_MAP: Record<ActionItem["icon"], string> = {
  terminal: "›_",
  browser: "⊕",
  search: "◎",
  check: "✓",
};

const ICON_COLOR: Record<ActionItem["icon"], string> = {
  terminal: "var(--color-dusk-blue)",
  browser: "var(--color-dusk-accent)",
  search: "#fbbf24",
  check: "#22d3a3",
};

export function ActionFeed({ actions, isControlling, doneMessage }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [actions]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "var(--color-dusk-surface)",
        border: "1px solid var(--color-dusk-border)",
        borderRadius: "10px",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px 20px 14px",
          borderBottom: "1px solid var(--color-dusk-border)",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "0.12em",
            color: "var(--color-dusk-muted)",
            fontWeight: 700,
          }}
        >
          AGENT ACTIVITY
        </span>
        {isControlling && (
          <span
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              fontFamily: "var(--font-mono)",
              fontSize: "9px",
              color: "var(--color-dusk-accent)",
              letterSpacing: "0.1em",
            }}
          >
            <span
              style={{
                width: "5px",
                height: "5px",
                borderRadius: "50%",
                background: "var(--color-dusk-accent)",
                animation: "pulse-critical 1.2s infinite",
              }}
            />
            LIVE
          </span>
        )}
      </div>

      {/* Feed */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "12px 0",
        }}
      >
        {actions.length === 0 && !doneMessage ? (
          <div
            style={{
              padding: "32px 20px",
              textAlign: "center",
              fontFamily: "var(--font-mono)",
              fontSize: "12px",
              color: "var(--color-dusk-subtle)",
            }}
          >
            Waiting for agent activity...
          </div>
        ) : (
          <>
            {actions.map((action, i) => (
              <div
                key={action.id}
                className="animate-slide-up"
                style={{
                  padding: "10px 20px",
                  display: "flex",
                  gap: "12px",
                  alignItems: "flex-start",
                  animationDelay: `${i * 40}ms`,
                  borderBottom: "1px solid rgba(36,36,54,0.5)",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "11px",
                    color: ICON_COLOR[action.icon],
                    minWidth: "18px",
                    paddingTop: "1px",
                    fontWeight: 700,
                  }}
                >
                  {ICON_MAP[action.icon]}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "rgba(241,240,236,0.75)",
                    lineHeight: 1.5,
                    wordBreak: "break-all",
                  }}
                >
                  {action.step}
                </span>
              </div>
            ))}

            {doneMessage && (
              <div
                className="animate-slide-up"
                style={{
                  margin: "12px 20px 0",
                  padding: "12px 16px",
                  background: "rgba(34,211,163,0.08)",
                  border: "1px solid rgba(34,211,163,0.2)",
                  borderRadius: "8px",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "13px",
                    color: "#22d3a3",
                  }}
                >
                  ✓ {doneMessage}
                </span>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
