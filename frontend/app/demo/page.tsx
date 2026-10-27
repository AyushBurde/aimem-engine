"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

const API = "http://127.0.0.1:8000/api";

type Memory = {
  id: number;
  content: string;
  memory_type: string;
  category: string;
  confidence: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ConsolidationCluster = {
  mergedContent: string;
  mergedFrom: { id: number; content: string }[];
  phase: "detecting" | "connecting" | "merging" | "done";
};

export default function DemoPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [memories, setMemories] = useState<Memory[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [consolidation, setConsolidation] = useState<ConsolidationCluster | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auth guard: redirect to login if not logged in
  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login?redirect=/demo");
    }
  }, [user, authLoading, router]);

  // Create or reuse conversation
  useEffect(() => {
    if (authLoading || !user) return;

    async function init() {
      try {
        const saved = localStorage.getItem("aimem_conversation_id");
        if (saved) {
          setConversationId(Number(saved));
          const res = await fetch(`${API}/memories?conversation_id=${saved}`);
          const data = await res.json();
          setMemories(data);
          return;
        }

        const res = await fetch(`${API}/conversations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_id: "demo", user_id: String(user.id) }),
        });
        const data = await res.json();
        setConversationId(data.id);
        localStorage.setItem("aimem_conversation_id", String(data.id));
      } catch (err) {
        console.error("Backend not reachable:", err);
      }
    }
    init();
  }, [user, authLoading]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function refreshMemories() {
    if (!conversationId) return;
    const res = await fetch(`${API}/memories?conversation_id=${conversationId}`);
    const data = await res.json();
    setMemories(data);
  }

  // Auto-consolidation after every message
  const autoConsolidate = useCallback(async () => {
    if (!conversationId) return;

    try {
      const res = await fetch(
        `${API}/memories/consolidate?conversation_id=${conversationId}`,
        { method: "POST" }
      );
      const result = await res.json();

      if (result.clusters_found > 0 && result.new_memories?.length > 0) {
        // For each cluster, animate the consolidation
        for (const cluster of result.new_memories) {
          const archived = result.archived_memories?.filter((a: any) =>
            cluster.merged_from.includes(a.id)
          ) || [];

          // Phase 1: Detecting
          setConsolidation({
            mergedContent: cluster.content,
            mergedFrom: archived,
            phase: "detecting",
          });
          await sleep(1200);

          // Phase 2: Connecting (show edges)
          setConsolidation((prev) =>
            prev ? { ...prev, phase: "connecting" } : null
          );
          await sleep(1500);

          // Phase 3: Merging (animate collapse)
          setConsolidation((prev) =>
            prev ? { ...prev, phase: "merging" } : null
          );
          await sleep(1800);

          // Phase 4: Done
          setConsolidation((prev) =>
            prev ? { ...prev, phase: "done" } : null
          );
          await sleep(2000);
        }

        // Clear visualization and refresh
        setConsolidation(null);
        await refreshMemories();
      }
    } catch (err) {
      console.error("Consolidation error:", err);
      setConsolidation(null);
    }
  }, [conversationId]);

  // Send message
  async function handleSend() {
    if (!input.trim() || !conversationId) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          conversation_id: conversationId,
        }),
      });
      const result = await res.json();

      let reply = "";

      if (result.answer) {
        reply += result.answer;
      }

      const extraction = result.extraction || {};
      const added = extraction.memories_added || [];
      const superseded = extraction.memories_superseded || [];
      const skipped = extraction.memories_skipped || [];

      if (added.length > 0 || superseded.length > 0) {
        reply += "\n\n───── Memory Update ─────\n";
        if (added.length > 0) {
          reply += `+ Extracted ${added.length} new memories:\n`;
          added.forEach((m: any) => {
            reply += `  • ${m.content} [${m.memory_type}]\n`;
          });
        }
        if (superseded.length > 0) {
          reply += `~ Superseded ${superseded.length} memories (temporal update):\n`;
          superseded.forEach((m: any) => {
            reply += `  • "${m.old_content}" → "${m.new_content}"\n`;
          });
        }
        if (skipped.length > 0) {
          reply += `- Skipped ${skipped.length} duplicates.\n`;
        }
      }

      const recalled = result.recalled_memories || [];
      if (recalled.length > 0) {
        reply += "\n───── Recalled Context ─────\n";
        recalled.forEach((m: any) => {
          reply += `  → ${m.content} (score: ${(m.score * 100).toFixed(0)}%)\n`;
        });
      }

      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
      await refreshMemories();

      // Auto-trigger consolidation after each message
      setTimeout(() => autoConsolidate(), 500);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Could not reach the backend." },
      ]);
    }

    setLoading(false);
  }

  // Group memories by type
  const permanent = memories.filter((m) => m.memory_type === "permanent");
  const temporal = memories.filter((m) => m.memory_type === "temporal");
  const episodic = memories.filter((m) => m.memory_type === "episodic");

  if (authLoading || !user) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-mono text-white/40">Checking authentication...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* ── LEFT: CHAT ── */}
      <div className="flex-1 flex flex-col border-r border-white/10">
        <div className="px-6 py-4 border-b border-white/10">
          <h1 className="text-lg font-semibold">Live Demo</h1>
          <p className="text-xs text-white/40 mt-1">
            Type anything — the engine extracts, recalls, and consolidates
            memories automatically
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-white/20 text-sm text-center mt-20">
              Try: &quot;My name is Parth, I live in Delhi and I love
              cricket&quot;
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${msg.role === "user"
                  ? "ml-auto bg-white/10 text-white"
                  : "mr-auto bg-white/5 text-white/70 border border-white/10"
                }`}
            >
              {msg.content}
            </div>
          ))}

          {loading && (
            <div className="mr-auto px-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-white/40 text-sm">
              Thinking...
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        <div className="px-6 py-4 border-t border-white/10">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type a message..."
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none focus:border-white/30 transition"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-5 py-3 bg-white text-black rounded-xl text-sm font-semibold hover:bg-white/90 disabled:opacity-30 transition"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* ── RIGHT: MEMORY PANEL ── */}
      <div className="w-full md:w-[420px] overflow-y-auto p-6">
        <h2 className="text-sm font-semibold text-white/50 uppercase tracking-widest mb-6">
          Memory Store
        </h2>

        {/* ── CONSOLIDATION GRAPH ── */}
        {consolidation && (
          <ConsolidationGraph cluster={consolidation} />
        )}

        <MemorySection
          title="Permanent"
          subtitle="Facts that don't change"
          memories={permanent}
          color="border-green-500/30"
        />

        <MemorySection
          title="Temporal"
          subtitle="Can change over time"
          memories={temporal}
          color="border-yellow-500/30"
        />

        <MemorySection
          title="Episodic"
          subtitle="Events & experiences"
          memories={episodic}
          color="border-blue-500/30"
        />

        {memories.length === 0 && !consolidation && (
          <p className="text-white/20 text-sm text-center mt-10">
            Memories will appear here as you chat
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Consolidation Graph Visualization ── */
function ConsolidationGraph({ cluster }: { cluster: ConsolidationCluster }) {
  const nodes = cluster.mergedFrom;
  const phase = cluster.phase;

  // Position nodes in a circle
  const cx = 170;
  const cy = 130;
  const radius = 80;
  const nodePositions = nodes.map((_, i) => {
    const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });

  const phaseLabel =
    phase === "detecting"
      ? "🔍 Detecting similar memories..."
      : phase === "connecting"
        ? "🔗 Found similarity cluster!"
        : phase === "merging"
          ? "⚡ Consolidating into one memory..."
          : "✅ Consolidated!";

  return (
    <div
      className="mb-6 rounded-2xl border border-purple-500/30 bg-purple-500/[0.04] overflow-hidden"
      style={{
        animation: "fadeIn 0.4s ease",
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-purple-500/20 bg-purple-500/[0.06]">
        <div className="text-xs font-semibold text-purple-300">{phaseLabel}</div>
      </div>

      {/* SVG Graph */}
      <div className="flex justify-center py-3">
        <svg width="340" height="260" viewBox="0 0 340 260">
          {/* Edges — only show after detecting */}
          {(phase === "connecting" || phase === "merging") &&
            nodePositions.map((from, i) =>
              nodePositions.slice(i + 1).map((to, j) => (
                <line
                  key={`edge-${i}-${j}`}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="rgba(168, 85, 247, 0.4)"
                  strokeWidth="2"
                  strokeDasharray={phase === "connecting" ? "6,4" : "none"}
                  style={{
                    animation:
                      phase === "connecting"
                        ? "dashMove 1s linear infinite"
                        : undefined,
                  }}
                />
              ))
            )}

          {/* Memory Nodes */}
          {nodePositions.map((pos, i) => {
            const isCollapsing = phase === "merging" || phase === "done";
            const targetX = isCollapsing ? cx : pos.x;
            const targetY = isCollapsing ? cy : pos.y;
            const opacity = phase === "done" ? 0 : 1;

            return (
              <g
                key={`node-${i}`}
                style={{
                  transition: "all 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)",
                  transform: `translate(${targetX - pos.x}px, ${targetY - pos.y}px)`,
                  opacity,
                }}
              >
                {/* Glow */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="32"
                  fill="none"
                  stroke="rgba(168, 85, 247, 0.15)"
                  strokeWidth="8"
                  style={{
                    animation:
                      phase === "detecting"
                        ? "pulse 2s ease-in-out infinite"
                        : undefined,
                  }}
                />
                {/* Node circle */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="24"
                  fill="rgba(168, 85, 247, 0.15)"
                  stroke="rgba(168, 85, 247, 0.6)"
                  strokeWidth="2"
                />
                {/* Node label */}
                <text
                  x={pos.x}
                  y={pos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="rgba(255,255,255,0.7)"
                  fontSize="8"
                  fontFamily="monospace"
                >
                  {truncate(nodes[i]?.content || "", 12)}
                </text>
              </g>
            );
          })}

          {/* Center merged node — appears in merging/done phase */}
          {(phase === "merging" || phase === "done") && (
            <g
              style={{
                animation: "scaleIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)",
                transformOrigin: `${cx}px ${cy}px`,
              }}
            >
              <circle
                cx={cx}
                cy={cy}
                r="36"
                fill="rgba(34, 197, 94, 0.15)"
                stroke="rgba(34, 197, 94, 0.7)"
                strokeWidth="2.5"
              />
              <circle
                cx={cx}
                cy={cy}
                r="44"
                fill="none"
                stroke="rgba(34, 197, 94, 0.1)"
                strokeWidth="10"
              />
              <text
                x={cx}
                y={cy - 6}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="rgba(34, 197, 94, 0.9)"
                fontSize="10"
                fontWeight="bold"
                fontFamily="monospace"
              >
                ✓ Merged
              </text>
              <text
                x={cx}
                y={cy + 10}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="rgba(255,255,255,0.5)"
                fontSize="7"
                fontFamily="monospace"
              >
                {truncate(cluster.mergedContent, 24)}
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Cluster details */}
      <div className="px-4 pb-3">
        <div className="space-y-1">
          {nodes.map((m, i) => (
            <div
              key={m.id}
              className={`text-xs px-3 py-1.5 rounded-lg transition-all duration-700 ${phase === "merging" || phase === "done"
                  ? "bg-white/[0.02] text-white/20 line-through"
                  : "bg-purple-500/[0.08] text-purple-200/80"
                }`}
            >
              #{m.id}: {truncate(m.content, 50)}
            </div>
          ))}
          {(phase === "merging" || phase === "done") && (
            <div className="text-xs px-3 py-2 rounded-lg bg-green-500/[0.1] text-green-300/90 border border-green-500/20 mt-2">
              → {cluster.mergedContent}
            </div>
          )}
        </div>
      </div>

      {/* CSS animations */}
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { r: 32; opacity: 0.15; }
          50% { r: 38; opacity: 0.3; }
        }
        @keyframes dashMove {
          to { stroke-dashoffset: -20; }
        }
        @keyframes scaleIn {
          from { transform: scale(0); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

/* ── Memory Section Component ── */
function MemorySection({
  title,
  subtitle,
  memories,
  color,
}: {
  title: string;
  subtitle: string;
  memories: Memory[];
  color: string;
}) {
  if (memories.length === 0) return null;

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold mb-1">{title}</h3>
      <p className="text-xs text-white/30 mb-3">{subtitle}</p>
      <div className="space-y-2">
        {memories.map((m) => (
          <div
            key={m.id}
            className={`px-4 py-3 rounded-xl bg-white/[0.03] border-l-2 ${color} text-sm text-white/80`}
          >
            <div>{m.content}</div>
            <div className="flex gap-3 mt-1 text-xs text-white/30">
              <span>{m.category}</span>
              <span>confidence: {(m.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Helpers ── */
function truncate(str: string, len: number): string {
  return str.length > len ? str.slice(0, len) + "…" : str;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
