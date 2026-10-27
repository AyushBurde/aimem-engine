"use client";

import { useAuth } from "./context/AuthContext";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  const handleTryDemo = (e: React.MouseEvent) => {
    e.preventDefault();
    if (user) {
      router.push("/demo");
    } else {
      router.push("/login?redirect=/demo");
    }
  };

  return (
    <div className="min-h-screen">

      {/* ── HERO SECTION ── */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-16">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-10">

          {/* Left Column */}
          <div className="max-w-2xl flex-1">
            {/* Badge */}
            <span className="text-xs text-white/50 uppercase tracking-widest font-mono">
              AI AGENT MEMORY ENGINE
            </span>

            {/* Main Heading */}
            <h1
              className="mt-4 text-4xl lg:text-[42px] font-bold leading-tight"
              style={{
                fontFamily: "var(--mono)",
                color: "var(--text)",
              }}
            >
              <span className="whitespace-nowrap">Ai Agents deserve better</span>
              <br />
              <span style={{ color: "#10B981" }}>Memory</span>
            </h1>

            {/* Subheading */}
            <p className="mt-6 text-lg text-white/60 max-w-md leading-relaxed">
              A memory layer for AI agents that actually remembers what matters.
            </p>

            {/* CTA Buttons */}
            <div className="mt-8 flex gap-4">
              <button
                type="button"
                onClick={handleTryDemo}
                className="px-6 py-3 bg-white text-black rounded-full text-sm font-semibold hover:bg-white/90 transition shadow-lg shadow-white/10 cursor-pointer"
              >
                Try Demo →
              </button>
              <Link
                href="/docs"
                className="px-6 py-3 border border-white/20 rounded-full text-sm hover:border-white/40 transition"
              >
                Read Docs
              </Link>
            </div>
          </div>

          {/* Right Column */}
          <div className="w-full lg:w-[520px] flex-shrink-0" />

        </div>
      </section>

      {/* ── CODE SNIPPET SECTION ── */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <div className="text-center mb-6">
          <span className="text-xs font-mono text-white/50 uppercase tracking-widest">Get started with Aimem</span>
        </div>
        <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
          {/* Terminal dots + filename */}
          <div className="flex items-center gap-2 mb-5">
            <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
            <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
            <span className="w-3 h-3 rounded-full bg-[#28C840]" />
            <span className="ml-3 text-xs text-white/30 font-mono">quickstart.py</span>
          </div>
          <pre className="text-xs leading-relaxed font-mono overflow-x-auto">
            <code>
              <span style={{ color: '#C586C0' }}>from</span>
              <span style={{ color: '#D4D4D4' }}> aimem </span>
              <span style={{ color: '#C586C0' }}>import</span>
              <span style={{ color: '#D4D4D4' }}> </span>
              <span style={{ color: '#4EC9B0' }}>Memory</span>
              <span style={{ color: '#D4D4D4' }}>, create_tables, SessionLocal{'\n'}</span>

              <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

              <span style={{ color: '#6A9955' }}>{'# Setup database & tables'}{'\n'}</span>
              <span style={{ color: '#DCDCAA' }}>create_tables</span>
              <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
              <span style={{ color: '#9CDCFE' }}>memory</span>
              <span style={{ color: '#D4D4D4' }}> = </span>
              <span style={{ color: '#4EC9B0' }}>Memory</span>
              <span style={{ color: '#D4D4D4' }}>(</span>
              <span style={{ color: '#DCDCAA' }}>SessionLocal</span>
              <span style={{ color: '#D4D4D4' }}>())  {'\n'}</span>

              <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

              <span style={{ color: '#6A9955' }}>{'# Add memories from a conversation'}{'\n'}</span>
              <span style={{ color: '#9CDCFE' }}>memory</span>
              <span style={{ color: '#D4D4D4' }}>.</span>
              <span style={{ color: '#DCDCAA' }}>add</span>
              <span style={{ color: '#D4D4D4' }}>(</span>
              <span style={{ color: '#9CDCFE' }}>messages</span>
              <span style={{ color: '#D4D4D4' }}>=[{'\n'}</span>
              <span style={{ color: '#D4D4D4' }}>{'    '}{'{'}</span>
              <span style={{ color: '#CE9178' }}>&quot;role&quot;</span>
              <span style={{ color: '#D4D4D4' }}>: </span>
              <span style={{ color: '#CE9178' }}>&quot;user&quot;</span>
              <span style={{ color: '#D4D4D4' }}>, </span>
              <span style={{ color: '#CE9178' }}>&quot;content&quot;</span>
              <span style={{ color: '#D4D4D4' }}>: </span>
              <span style={{ color: '#CE9178' }}>&quot;I moved to London and love Python&quot;</span>
              <span style={{ color: '#D4D4D4' }}>{'}'}{'\n'}</span>
              <span style={{ color: '#D4D4D4' }}>], </span>
              <span style={{ color: '#9CDCFE' }}>conversation_id</span>
              <span style={{ color: '#D4D4D4' }}>=</span>
              <span style={{ color: '#B5CEA8' }}>1</span>
              <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

              <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

              <span style={{ color: '#6A9955' }}>{'# Search memories (Only currently active facts are returned)'}{'\n'}</span>
              <span style={{ color: '#9CDCFE' }}>results</span>
              <span style={{ color: '#D4D4D4' }}> = </span>
              <span style={{ color: '#9CDCFE' }}>memory</span>
              <span style={{ color: '#D4D4D4' }}>.</span>
              <span style={{ color: '#DCDCAA' }}>search</span>
              <span style={{ color: '#D4D4D4' }}>(</span>
              <span style={{ color: '#CE9178' }}>&quot;Where does the user live?&quot;</span>
              <span style={{ color: '#D4D4D4' }}>, </span>
              <span style={{ color: '#9CDCFE' }}>conversation_id</span>
              <span style={{ color: '#D4D4D4' }}>=</span>
              <span style={{ color: '#B5CEA8' }}>1</span>
              <span style={{ color: '#D4D4D4' }}>)</span>
            </code>
          </pre>
        </div>
      </section>

      {/* ── FEATURES SECTION ── */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="text-center mb-12">
          <span className="text-xs font-mono text-white/50 uppercase tracking-widest">Core Capabilities</span>
          <h2 className="text-3xl font-bold mt-2">
            Smart context for Agents
          </h2>
          <p className="text-sm text-white/50 mt-2 max-w-lg mx-auto">
            Retrieve user memories in an efficient way
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02] hover:border-white/20 transition flex flex-col justify-start">
            <span className="text-xs font-mono text-white/30 mb-3">01</span>
            <h3 className="font-semibold text-white text-base">Temporal Superseding</h3>
            <p className="text-sm text-white/50 leading-relaxed mt-2">
              Archives outdated facts when context changes instead of overwriting. Agents always act on active ground truth — zero temporal hallucination.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02] hover:border-white/20 transition flex flex-col justify-start">
            <span className="text-xs font-mono text-white/30 mb-3">02</span>
            <h3 className="font-semibold text-white text-base">Hybrid Retrieval</h3>
            <p className="text-sm text-white/50 leading-relaxed mt-2">
              Fuses BM25 keywords, dense embeddings, and exact-match anchoring into a unified ranker. Precision recall for both fuzzy concepts and exact IDs.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02] hover:border-white/20 transition flex flex-col justify-start">
            <span className="text-xs font-mono text-white/30 mb-3">03</span>
            <h3 className="font-semibold text-white text-base">Contradiction Resolution</h3>
            <p className="text-sm text-white/50 leading-relaxed mt-2">
              Pre-commit reasoning pass detects and resolves conflicting beliefs automatically. Old assertions expire cleanly with zero manual pruning.
            </p>
          </div>
        </div>
      </section>

    </div>
  );
}
