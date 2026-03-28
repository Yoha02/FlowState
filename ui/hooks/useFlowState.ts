"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type FlowStateLevel = "calm" | "elevated" | "stressed" | "critical";

export interface StatusUpdate {
  state: FlowStateLevel;
  consecutive: number;
  stress: number;
  fatigue: number;
}

export interface HandoffTrigger {
  evidence: string;
  task_summary: string;
}

export interface ActionItem {
  id: string;
  step: string;
  icon: "terminal" | "browser" | "search" | "check";
  timestamp: number;
}

export interface UseFlowStateReturn {
  status: StatusUpdate;
  handoffPending: boolean;
  handoffData: HandoffTrigger | null;
  actions: ActionItem[];
  isControlling: boolean;
  doneMessage: string | null;
  connected: boolean;
  approve: () => Promise<void>;
  reject: () => Promise<void>;
}

const DEFAULT_STATUS: StatusUpdate = {
  state: "calm",
  consecutive: 0,
  stress: 0,
  fatigue: 0,
};

export function useFlowState(): UseFlowStateReturn {
  const [status, setStatus] = useState<StatusUpdate>(DEFAULT_STATUS);
  const [handoffPending, setHandoffPending] = useState(false);
  const [handoffData, setHandoffData] = useState<HandoffTrigger | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [isControlling, setIsControlling] = useState(false);
  const [doneMessage, setDoneMessage] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const actionIdRef = useRef(0);

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/status/stream`);
    esRef.current = es;

    es.addEventListener("open", () => setConnected(true));
    es.addEventListener("error", () => setConnected(false));

    es.addEventListener("status_update", (e: MessageEvent) => {
      try {
        setStatus(JSON.parse(e.data));
      } catch {}
    });

    es.addEventListener("handoff_trigger", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as HandoffTrigger;
        setHandoffData(data);
        setHandoffPending(true);
      } catch {}
    });

    es.addEventListener("action", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as Omit<ActionItem, "id" | "timestamp">;
        setIsControlling(true);
        setActions((prev) => [
          ...prev,
          {
            ...data,
            id: String(++actionIdRef.current),
            timestamp: Date.now(),
          },
        ]);
      } catch {}
    });

    es.addEventListener("done", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as { message: string };
        setDoneMessage(data.message);
        setIsControlling(false);
        setHandoffPending(false);
        // Clear actions after a short delay so user can read
        setTimeout(() => setActions([]), 8000);
      } catch {}
    });

    // Heartbeat — just keeps connection alive
    es.addEventListener("heartbeat", () => {});

    return () => {
      es.close();
      esRef.current = null;
    };
  }, []);

  const approve = useCallback(async () => {
    setHandoffPending(false);
    await fetch(`${API_BASE}/handoff/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: true }),
    });
  }, []);

  const reject = useCallback(async () => {
    setHandoffPending(false);
    setHandoffData(null);
    await fetch(`${API_BASE}/handoff/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: false }),
    });
  }, []);

  return {
    status,
    handoffPending,
    handoffData,
    actions,
    isControlling,
    doneMessage,
    connected,
    approve,
    reject,
  };
}
