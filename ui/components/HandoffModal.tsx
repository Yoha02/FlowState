"use client";

import { useEffect, useRef, useState } from "react";
import type { HandoffTrigger } from "@/hooks/useFlowState";

interface Props {
  data: HandoffTrigger;
  onApprove: () => void;
  onReject: () => void;
  timeoutSeconds?: number;
}

export function HandoffModal({
  data,
  onApprove,
  onReject,
  timeoutSeconds = 30,
}: Props) {
  const [remaining, setRemaining] = useState(timeoutSeconds);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(timerRef.current!);
          onReject();
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current!);
  }, [onReject]);

  const progress = remaining / timeoutSeconds;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
      className="animate-fade-in"
    >
      {/* Backdrop */}
      <div
        onClick={onReject}
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(8, 8, 16, 0.85)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
        }}
      />

      {/* Modal */}
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "480px",
          background: "var(--color-dusk-card)",
          border: "1px solid rgba(239,68,68,0.4)",
          borderRadius: "12px",
          padding: "32px",
          boxShadow: "0 0 48px rgba(239,68,68,0.15), 0 24px 64px rgba(0,0,0,0.6)",
        }}
        className="animate-slide-up"
      >
        {/* Progress bar (top) */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "2px",
            background: "var(--color-dusk-border)",
            borderRadius: "12px 12px 0 0",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${progress * 100}%`,
              background: "linear-gradient(90deg, #ef4444, #f97316)",
              transition: "width 1s linear",
            }}
          />
        </div>

        {/* Header */}
        <div style={{ marginBottom: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <div
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                background: "#ef4444",
                boxShadow: "0 0 12px rgba(239,68,68,0.6)",
                animation: "pulse-critical 1.2s infinite",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                letterSpacing: "0.14em",
                color: "#ef4444",
                fontWeight: 700,
              }}
            >
              CRITICAL THRESHOLD REACHED
            </span>
          </div>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "24px",
              fontWeight: 600,
              color: "var(--color-dusk-text)",
              lineHeight: 1.3,
            }}
          >
            FlowState wants to take over
          </h2>
        </div>

        {/* Evidence */}
        <div
          style={{
            background: "rgba(239,68,68,0.06)",
            border: "1px solid rgba(239,68,68,0.15)",
            borderRadius: "8px",
            padding: "14px 16px",
            marginBottom: "16px",
          }}
        >
          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "13px",
              color: "rgba(241,240,236,0.8)",
              lineHeight: 1.6,
            }}
          >
            {data.evidence}
          </p>
        </div>

        {/* Task summary */}
        {data.task_summary && (
          <div style={{ marginBottom: "28px" }}>
            <p
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "var(--color-dusk-muted)",
                letterSpacing: "0.08em",
                marginBottom: "6px",
              }}
            >
              I&apos;LL HANDLE
            </p>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "14px",
                color: "var(--color-dusk-text)",
                lineHeight: 1.5,
              }}
            >
              {data.task_summary}
            </p>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <button
            onClick={onApprove}
            style={{
              flex: 1,
              padding: "12px 24px",
              background: "var(--color-dusk-accent)",
              color: "#0c0c14",
              fontFamily: "var(--font-sans)",
              fontSize: "14px",
              fontWeight: 600,
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "opacity 0.2s var(--ease-drift), transform 0.2s var(--ease-spring)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = "0.9";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = "1";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            Take over — I need a break
          </button>
          <button
            onClick={onReject}
            style={{
              padding: "12px 20px",
              background: "transparent",
              color: "var(--color-dusk-muted)",
              fontFamily: "var(--font-sans)",
              fontSize: "14px",
              border: "1px solid var(--color-dusk-border)",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "color 0.2s var(--ease-drift), border-color 0.2s var(--ease-drift)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--color-dusk-text)";
              e.currentTarget.style.borderColor = "var(--color-dusk-subtle)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--color-dusk-muted)";
              e.currentTarget.style.borderColor = "var(--color-dusk-border)";
            }}
          >
            I&apos;m fine
          </button>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              color: "var(--color-dusk-muted)",
              minWidth: "28px",
              textAlign: "right",
            }}
          >
            {remaining}s
          </span>
        </div>
      </div>
    </div>
  );
}
