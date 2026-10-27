"use client";

import { useState } from "react";

const TERMINAL_CODE = "pip install aimem-engine";

const GEMINI_CODE = `from aimem import configure, create_tables, Memory, SessionLocal

# Configure with Google Gemini (Free Tier)
configure(
    gemini_api_key="AIzaSy...",
    database_url="postgresql://...",  # Optional, defaults to SQLite
)

create_tables()
db = SessionLocal()
memory = Memory(db)`;

const OPENAI_CODE = `from aimem import configure, create_tables, Memory, SessionLocal

# Configure with OpenAI (Direct)
configure(
    openai_api_key="sk-...",
    database_url="postgresql://...",  # Optional, defaults to SQLite
)

create_tables()
db = SessionLocal()
memory = Memory(db)`;

const OPENROUTER_CODE = `from aimem import configure, create_tables, Memory, SessionLocal

# Configure with OpenRouter (Claude, DeepSeek, etc.)
configure(
    openrouter_api_key="sk-or-v1-...",
    llm_provider="openrouter",
    llm_model="anthropic/claude-3.5-sonnet",  # Or any OpenRouter model
    embedding_model="openai/text-embedding-3-small",
    database_url="postgresql://...",  # Optional, defaults to SQLite
)

create_tables()
db = SessionLocal()
memory = Memory(db)`;

const MEMORY_OPERATIONS_CODE = `# 1. ADD: Extract & store memories from conversation
memory.add(
    messages=[
        {"role": "user", "content": "I love Python programming and live in Delhi"}
    ],
    conversation_id=1
)

# 2. SEARCH: Hybrid retrieval (BM25 + Semantic Vector)
results = memory.search(
    query="What does the user like?",
    conversation_id=1
)

# 3. UPDATE: Modify an existing memory
memory.update(
    memory_id=1,
    text="User loves Python and Rust programming"
)

# 4. DELETE: Remove from Database and FAISS
memory.delete(memory_id=1)`;

const ENV_CODE = `# For Google Gemini
export GEMINI_API_KEY="AIzaSy..."

# For OpenAI
export OPENAI_API_KEY="sk-..."

# For OpenRouter
export OPENROUTER_API_KEY="sk-or-v1-..."

# Optional: Storage Backend (defaults to SQLite)
export DATABASE_URL="postgresql://..."`;

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    return (
        <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white text-xs transition border border-white/5 group"
            title="Copy code to clipboard"
            type="button"
        >
            {copied ? (
                <>
                    <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-emerald-400 font-mono text-[11px]">Copied!</span>
                </>
            ) : (
                <>
                    <svg className="w-3.5 h-3.5 text-white/40 group-hover:text-white transition" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span className="font-mono text-[11px]">Copy</span>
                </>
            )}
        </button>
    );
}

export default function DocsPage() {
    return (
        <div className="max-w-7xl mx-auto flex min-h-screen px-6">
            {/* ── SIDE PANEL ── */}
            <aside className="w-64 shrink-0 border-r border-white/10 py-8 pr-6 sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto">
                <div className="space-y-6">
                    {/* Section Group */}
                    <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">
                            Overview
                        </h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a href="#introduction" className="text-white hover:text-white/80 transition">
                                    Introduction
                                </a>
                            </li>
                            <li>
                                <a href="#quickstart" className="text-white/60 hover:text-white transition">
                                    Quickstart
                                </a>
                            </li>
                            <li>
                                <a href="#quickstart-gemini" className="text-white/40 hover:text-white pl-3 text-xs block transition">
                                    • Gemini
                                </a>
                            </li>
                            <li>
                                <a href="#quickstart-openai" className="text-white/40 hover:text-white pl-3 text-xs block transition">
                                    • OpenAI
                                </a>
                            </li>
                            <li>
                                <a href="#quickstart-openrouter" className="text-white/40 hover:text-white pl-3 text-xs block transition">
                                    • OpenRouter
                                </a>
                            </li>
                            <li>
                                <a href="#memory-operations" className="text-white/60 hover:text-white transition">
                                    Memory Operations
                                </a>
                            </li>
                            <li>
                                <a href="#environment-variables" className="text-white/60 hover:text-white transition">
                                    Environment Variables
                                </a>
                            </li>
                        </ul>
                    </div>

                    {/* Section Group */}
                    <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">
                            Core Concepts
                        </h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a href="#temporal-reasoning" className="text-white/60 hover:text-white transition">
                                    Temporal Reasoning
                                </a>
                            </li>
                            <li>
                                <a href="#memory-consolidation" className="text-white/60 hover:text-white transition">
                                    Memory Consolidation
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </aside>

            {/* ── MAIN CONTENT AREA ── */}
            <main className="flex-1 min-w-0 py-8 pl-10 max-w-3xl">
                <section id="introduction" className="mb-12">
                    <h1 className="text-3xl font-bold mb-4">Who we are </h1>
                    <p className="text-white/70 leading-relaxed">
                        Welcome to the Ai era, where Ai Agents are going to rule the world but one problem they often face is &apos;Memory&apos;. We Aimem are trying to solve
                        that with multiple strategies to retrieve faster and efficient and by providing better memory management.
                    </p>
                </section>

                {/* ── 1. INSTALLATION ── */}
                <section id="quickstart" className="mb-12">
                    <h2 className="text-2xl font-semibold mb-3">Quickstart</h2>
                    <p className="text-white/60 text-sm mb-4">Install Aimem via pip to get started in seconds.</p>
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
                        {/* Terminal dots + filename + Copy */}
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                                <span className="ml-3 text-xs text-white/30 font-mono">Terminal</span>
                            </div>
                            <CopyButton text={TERMINAL_CODE} />
                        </div>
                        <p className="font-mono text-sm text-emerald-400">$ pip install aimem-engine</p>
                    </div>
                </section>

                {/* ── 2. GEMINI QUICKSTART ── */}
                <section id="quickstart-gemini" className="mb-12">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xl font-semibold">Google Gemini</h3>
                        <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Free Tier
                        </span>
                    </div>
                    <p className="text-white/60 text-sm mb-4">
                        Use Google Gemini Flash for both LLM extraction and vector embeddings without credit card fees.
                    </p>
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
                        {/* Terminal dots + filename + Copy */}
                        <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                                <span className="ml-3 text-xs text-white/30 font-mono">quickstart_gemini.py</span>
                            </div>
                            <CopyButton text={GEMINI_CODE} />
                        </div>
                        <pre className="text-xs leading-relaxed font-mono overflow-x-auto">
                            <code>
                                <span style={{ color: '#C586C0' }}>from</span>
                                <span style={{ color: '#D4D4D4' }}> aimem </span>
                                <span style={{ color: '#C586C0' }}>import</span>
                                <span style={{ color: '#D4D4D4' }}> configure, </span>
                                <span style={{ color: '#4EC9B0' }}>Memory</span>
                                <span style={{ color: '#D4D4D4' }}>, create_tables, SessionLocal{'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Configure with Google Gemini (Free Tier)'}{'\n'}</span>
                                <span style={{ color: '#DCDCAA' }}>configure</span>
                                <span style={{ color: '#D4D4D4' }}>({'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>gemini_api_key</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;AIzaSy...&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>database_url</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;postgresql://...&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,  </span>
                                <span style={{ color: '#6A9955' }}>{'# Optional, defaults to SQLite'}{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Create tables & initialize'}{'\n'}</span>
                                <span style={{ color: '#DCDCAA' }}>create_tables</span>
                                <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>db</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#DCDCAA' }}>SessionLocal</span>
                                <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>memory</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#4EC9B0' }}>Memory</span>
                                <span style={{ color: '#D4D4D4' }}>(</span>
                                <span style={{ color: '#9CDCFE' }}>db</span>
                                <span style={{ color: '#D4D4D4' }}>)</span>
                            </code>
                        </pre>
                    </div>
                </section>

                {/* ── 3. OPENAI QUICKSTART ── */}
                <section id="quickstart-openai" className="mb-12">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xl font-semibold">OpenAI (Direct)</h3>
                        <span className="text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            gpt-4o-mini
                        </span>
                    </div>
                    <p className="text-white/60 text-sm mb-4">
                        Plug in your OpenAI API key for plug-and-play gpt-4o-mini intelligence and high-dimensional embeddings.
                    </p>
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
                        {/* Terminal dots + filename + Copy */}
                        <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                                <span className="ml-3 text-xs text-white/30 font-mono">quickstart_openai.py</span>
                            </div>
                            <CopyButton text={OPENAI_CODE} />
                        </div>
                        <pre className="text-xs leading-relaxed font-mono overflow-x-auto">
                            <code>
                                <span style={{ color: '#C586C0' }}>from</span>
                                <span style={{ color: '#D4D4D4' }}> aimem </span>
                                <span style={{ color: '#C586C0' }}>import</span>
                                <span style={{ color: '#D4D4D4' }}> configure, </span>
                                <span style={{ color: '#4EC9B0' }}>Memory</span>
                                <span style={{ color: '#D4D4D4' }}>, create_tables, SessionLocal{'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Configure with OpenAI (Direct)'}{'\n'}</span>
                                <span style={{ color: '#DCDCAA' }}>configure</span>
                                <span style={{ color: '#D4D4D4' }}>({'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>openai_api_key</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;sk-...&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>database_url</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;postgresql://...&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,  </span>
                                <span style={{ color: '#6A9955' }}>{'# Optional, defaults to SQLite'}{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Create tables & initialize'}{'\n'}</span>
                                <span style={{ color: '#DCDCAA' }}>create_tables</span>
                                <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>db</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#DCDCAA' }}>SessionLocal</span>
                                <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>memory</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#4EC9B0' }}>Memory</span>
                                <span style={{ color: '#D4D4D4' }}>(</span>
                                <span style={{ color: '#9CDCFE' }}>db</span>
                                <span style={{ color: '#D4D4D4' }}>)</span>
                            </code>
                        </pre>
                    </div>
                </section>

                {/* ── 4. OPENROUTER QUICKSTART ── */}
                <section id="quickstart-openrouter" className="mb-12">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xl font-semibold">OpenRouter (Claude, etc.)</h3>
                        <span className="text-xs px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                            Claude and other models
                        </span>
                    </div>
                    <p className="text-white/60 text-sm mb-4">
                        Connect to Anthropic Claude 3.5 Sonnet, DeepSeek, or any open-source model through OpenRouter.
                    </p>
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
                        {/* Terminal dots + filename + Copy */}
                        <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                                <span className="ml-3 text-xs text-white/30 font-mono">quickstart_openrouter.py</span>
                            </div>
                            <CopyButton text={OPENROUTER_CODE} />
                        </div>
                        <pre className="text-xs leading-relaxed font-mono overflow-x-auto">
                            <code>
                                <span style={{ color: '#C586C0' }}>from</span>
                                <span style={{ color: '#D4D4D4' }}> aimem </span>
                                <span style={{ color: '#C586C0' }}>import</span>
                                <span style={{ color: '#D4D4D4' }}> configure, </span>
                                <span style={{ color: '#4EC9B0' }}>Memory</span>
                                <span style={{ color: '#D4D4D4' }}>, create_tables, SessionLocal{'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Configure with OpenRouter (Claude, DeepSeek, etc.)'}{'\n'}</span>
                                <span style={{ color: '#DCDCAA' }}>configure</span>
                                <span style={{ color: '#D4D4D4' }}>({'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>openrouter_api_key</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;sk-or-v1-...&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>llm_provider</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;openrouter&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>llm_model</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;anthropic/claude-3.5-sonnet&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,  </span>
                                <span style={{ color: '#6A9955' }}>{'# Or any OpenRouter model'}{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>embedding_model</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;openai/text-embedding-3-small&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>{'    '}</span>
                                <span style={{ color: '#9CDCFE' }}>database_url</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;postgresql://...&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>,  </span>
                                <span style={{ color: '#6A9955' }}>{'# Optional, defaults to SQLite'}{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Create tables & initialize'}{'\n'}</span>
                                <span style={{ color: '#DCDCAA' }}>create_tables</span>
                                <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>db</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#DCDCAA' }}>SessionLocal</span>
                                <span style={{ color: '#D4D4D4' }}>(){'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>memory</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#4EC9B0' }}>Memory</span>
                                <span style={{ color: '#D4D4D4' }}>(</span>
                                <span style={{ color: '#9CDCFE' }}>db</span>
                                <span style={{ color: '#D4D4D4' }}>)</span>
                            </code>
                        </pre>
                    </div>
                </section>
                {/* ── 5. ENVIRONMENT VARIABLES (ALTERNATIVE) ── */}
                <section id="environment-variables" className="mb-12">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-2xl font-semibold">Environment Variables</h2>
                        <span className="text-xs px-2.5 py-1 rounded-full bg-white/10 text-white/80 border border-white/20 font-mono">
                            .env
                        </span>
                    </div>
                    <p className="text-white/60 text-sm mb-4">
                        As an alternative to passing keys in <code className="text-white font-mono bg-white/10 px-1.5 py-0.5 rounded text-xs">configure(...)</code>, you can define them in your environment or <code className="text-white font-mono bg-white/10 px-1.5 py-0.5 rounded text-xs">.env</code> file. Aimem will load them automatically.
                    </p>
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
                        {/* Terminal dots + filename + Copy */}
                        <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                                <span className="ml-3 text-xs text-white/30 font-mono">.env</span>
                            </div>
                            <CopyButton text={ENV_CODE} />
                        </div>
                        <pre className="text-xs leading-relaxed font-mono overflow-x-auto">
                            <code>
                                <span style={{ color: '#6A9955' }}>{'# For Google Gemini'}{'\n'}</span>
                                <span style={{ color: '#C586C0' }}>export </span>
                                <span style={{ color: '#9CDCFE' }}>GEMINI_API_KEY</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;AIzaSy...&quot;{'\n\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# For OpenAI'}{'\n'}</span>
                                <span style={{ color: '#C586C0' }}>export </span>
                                <span style={{ color: '#9CDCFE' }}>OPENAI_API_KEY</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;sk-...&quot;{'\n\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# For OpenRouter'}{'\n'}</span>
                                <span style={{ color: '#C586C0' }}>export </span>
                                <span style={{ color: '#9CDCFE' }}>OPENROUTER_API_KEY</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;sk-or-v1-...&quot;{'\n\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# Optional: Storage Backend (defaults to SQLite)'}{'\n'}</span>
                                <span style={{ color: '#C586C0' }}>export </span>
                                <span style={{ color: '#9CDCFE' }}>DATABASE_URL</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;postgresql://...&quot;</span>
                            </code>
                        </pre>
                    </div>
                </section>

                {/* ── 6. MEMORY OPERATIONS (ADD, SEARCH, UPDATE, DELETE) ── */}
                <section id="memory-operations" className="mb-12">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-2xl font-semibold">Memory Operations</h2>
                        <span className="text-xs px-2.5 py-1 rounded-full bg-white/10 text-white/80 border border-white/20">
                            Add • Search • Update • Delete
                        </span>
                    </div>
                    <p className="text-white/60 text-sm mb-4">
                        Once initialized, use the <code className="text-white font-mono bg-white/10 px-1.5 py-0.5 rounded text-xs">Memory</code> instance across all providers to extract, retrieve, update, and manage facts.
                    </p>
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl shadow-black/30">
                        {/* Terminal dots + filename + Copy */}
                        <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                                <span className="ml-3 text-xs text-white/30 font-mono">memory_operations.py</span>
                            </div>
                            <CopyButton text={MEMORY_OPERATIONS_CODE} />
                        </div>
                        <pre className="text-xs leading-relaxed font-mono overflow-x-auto">
                            <code>
                                <span style={{ color: '#6A9955' }}>{'# 1. ADD: Extract & store memories from conversation'}{'\n'}</span>
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
                                <span style={{ color: '#CE9178' }}>&quot;I love Python programming and live in Delhi&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>{'}'}{'\n'}</span>
                                <span style={{ color: '#D4D4D4' }}>], </span>
                                <span style={{ color: '#9CDCFE' }}>conversation_id</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#B5CEA8' }}>1</span>
                                <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# 2. SEARCH: Hybrid retrieval (BM25 + Semantic Vector)'}{'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>results</span>
                                <span style={{ color: '#D4D4D4' }}> = </span>
                                <span style={{ color: '#9CDCFE' }}>memory</span>
                                <span style={{ color: '#D4D4D4' }}>.</span>
                                <span style={{ color: '#DCDCAA' }}>search</span>
                                <span style={{ color: '#D4D4D4' }}>(</span>
                                <span style={{ color: '#9CDCFE' }}>query</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;What does the user like?&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>, </span>
                                <span style={{ color: '#9CDCFE' }}>conversation_id</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#B5CEA8' }}>1</span>
                                <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# 3. UPDATE: Modify an existing memory'}{'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>memory</span>
                                <span style={{ color: '#D4D4D4' }}>.</span>
                                <span style={{ color: '#DCDCAA' }}>update</span>
                                <span style={{ color: '#D4D4D4' }}>(</span>
                                <span style={{ color: '#9CDCFE' }}>memory_id</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#B5CEA8' }}>1</span>
                                <span style={{ color: '#D4D4D4' }}>, </span>
                                <span style={{ color: '#9CDCFE' }}>text</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#CE9178' }}>&quot;User loves Python and Rust programming&quot;</span>
                                <span style={{ color: '#D4D4D4' }}>){'\n'}</span>

                                <span style={{ color: '#D4D4D4' }}>{'\n'}</span>

                                <span style={{ color: '#6A9955' }}>{'# 4. DELETE: Remove from Database and FAISS'}{'\n'}</span>
                                <span style={{ color: '#9CDCFE' }}>memory</span>
                                <span style={{ color: '#D4D4D4' }}>.</span>
                                <span style={{ color: '#DCDCAA' }}>delete</span>
                                <span style={{ color: '#D4D4D4' }}>(</span>
                                <span style={{ color: '#9CDCFE' }}>memory_id</span>
                                <span style={{ color: '#D4D4D4' }}>=</span>
                                <span style={{ color: '#B5CEA8' }}>1</span>
                                <span style={{ color: '#D4D4D4' }}>)</span>
                            </code>
                        </pre>
                    </div>
                </section>


                {/* ── 7. TEMPORAL REASONING ── */}
                <section id="temporal-reasoning" className="mb-14">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-2xl font-semibold">Temporal Reasoning</h2>
                        <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-white/60 border border-white/10 font-mono">
                            Time-Aware Memory
                        </span>
                    </div>
                    <p className="text-white/70 text-sm leading-relaxed mb-6">
                        Human state evolves over time. When a user changes their location, employer, or preferences, traditional vector search returns conflicting facts because old and new statements have high semantic similarity. Aimem uses <strong className="text-white">validity intervals</strong> to record chronological history while guaranteeing active queries only retrieve current facts.
                    </p>

                    {/* Single Minimal Demonstration Box */}
                    <div className="bg-[#1C1C1C] border border-white/10 rounded-2xl p-6 md:p-8 shadow-2xl shadow-black/30 space-y-8">
                        {/* Header */}
                        <div className="flex items-center justify-between border-b border-white/10 pb-4">
                            <h3 className="text-xs font-mono uppercase tracking-wider text-white/60 font-semibold">
                                State Transition Example
                            </h3>
                            <span className="text-[11px] font-mono text-white/50 bg-white/5 px-2.5 py-1 rounded-full border border-white/10">
                                Validity Windows
                            </span>
                        </div>

                        {/* Part 1: Timeline State Transition */}
                        <div className="space-y-4">

                            {/* Step 1 */}
                            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-2">
                                <div className="flex items-center justify-between text-xs font-mono text-white/40">
                                    <span>Event 1 • 01/01/2025</span>
                                    <span>Status: Active</span>
                                </div>
                                <div className="text-sm text-white/90 font-mono">
                                    User: <span className="text-white">&quot;I live in San Francisco&quot;</span>
                                </div>
                                <div className="text-xs font-mono text-white/50 flex justify-between border-t border-white/5 pt-2">
                                    <span>Recorded Validity:</span>
                                    <span className="text-white/80">01/01/2025 — Present</span>
                                </div>
                            </div>

                            {/* Transition Marker */}
                            <div className="px-4 py-1 text-xs font-mono text-white/40 border-l border-white/10 ml-4">
                                One year later (01/01/2026): User says &quot;I moved to London&quot;
                            </div>

                            {/* Step 2: Resulting State */}
                            <div className="space-y-2.5">
                                <div className="text-xs font-mono text-white/40">
                                    Aimem automatically updates validity intervals:
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {/* Superseded Record */}
                                    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-2">
                                        <div className="flex items-center justify-between text-xs font-mono">
                                            <span className="text-white/60">Previous Memory</span>
                                            <span className="text-white/40 text-[11px] border border-white/10 px-1.5 py-0.5 rounded">Superseded</span>
                                        </div>
                                        <p className="text-sm font-mono text-white/70">&quot;Lives in San Francisco&quot;</p>
                                        <div className="text-xs font-mono text-white/40 flex justify-between border-t border-white/5 pt-2">
                                            <span>Interval:</span>
                                            <span className="text-white/60">01/01/2025 — 01/01/2026</span>
                                        </div>
                                    </div>

                                    {/* Active Record */}
                                    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-2">
                                        <div className="flex items-center justify-between text-xs font-mono">
                                            <span className="text-white/90">Current Memory</span>
                                            <span className="text-white/80 text-[11px] border border-white/20 px-1.5 py-0.5 rounded">Active</span>
                                        </div>
                                        <p className="text-sm font-mono text-white">&quot;Lives in London&quot;</p>
                                        <div className="text-xs font-mono text-white/40 flex justify-between border-t border-white/5 pt-2">
                                            <span>Interval:</span>
                                            <span className="text-white/90">01/01/2026 — Present</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Part 2: Visual Illustration of the Retrieval Mechanism */}
                        <div className="border-t border-white/10 pt-6 space-y-4">
                            <div className="text-xs font-mono uppercase tracking-wider text-white/40">
                                Retrieval Comparison: Naive Search vs Temporal Filtering
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Left: Naive Search */}
                                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-3">
                                    <div className="text-xs font-mono text-white/60 font-medium">
                                        Naive Vector Search
                                    </div>
                                    <p className="text-xs text-white/50 font-mono">
                                        Query: &quot;Where does user live?&quot;
                                    </p>
                                    <div className="p-3 rounded-lg bg-black/40 border border-white/5 font-mono text-xs text-white/60 space-y-1.5">
                                        <div>Match 1: SF (similarity 0.93)</div>
                                        <div>Match 2: London (similarity 0.91)</div>
                                        <div className="text-[11px] text-white/40 border-t border-white/5 pt-1.5">
                                            Outcome: Injects contradictory facts into prompt. LLM fails to discern current location.
                                        </div>
                                    </div>
                                </div>

                                {/* Right: Temporal Retrieval */}
                                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-3">
                                    <div className="text-xs font-mono text-white font-medium">
                                        Aimem Temporal Retrieval
                                    </div>
                                    <p className="text-xs text-white/50 font-mono">
                                        Query: &quot;Where does user live?&quot;
                                    </p>
                                    <div className="p-3 rounded-lg bg-black/40 border border-white/5 font-mono text-xs text-white/80 space-y-1.5">
                                        <div>Filter: valid_to is null (Active)</div>
                                        <div>Selected: London (01/01/2026 — Present)</div>
                                        <div className="text-[11px] text-white/40 border-t border-white/5 pt-1.5">
                                            Outcome: Returns single verified active state. Past locations are stored for historical queries.
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Minimal Query Example */}
                            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col md:flex-row md:items-center md:justify-between text-xs font-mono text-white/60 gap-2">
                                <div>
                                    <span className="text-white/40">Historical Query:</span>{" "}
                                    <span className="text-white/80">memory.search(&quot;Where did user live in 2025?&quot;)</span>
                                </div>
                                <span className="text-white/50">Resolves 2025 interval &rarr; San Francisco</span>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
