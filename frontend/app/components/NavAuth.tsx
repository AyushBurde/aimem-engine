"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { useAuth } from "../context/AuthContext";

export default function NavAuth() {
    const { user, isLoading, login, register, logout } = useAuth();
    const [showModal, setShowModal] = useState(false);
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    if (isLoading) return null;

    // ── Logged in state ──
    if (user) {
        return (
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-400 font-bold">
                    {(user.name?.[0] || user.email[0]).toUpperCase()}
                </div>
                <span className="text-sm text-white/70">{user.name || user.email}</span>
                <button
                    onClick={logout}
                    className="text-xs text-white/40 hover:text-white/70 transition ml-2"
                >
                    Sign Out
                </button>
            </div>
        );
    }

    // ── Submit handler ──
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSubmitting(true);
        try {
            if (isLoginMode) {
                await login(email, password);
            } else {
                await register(email, password, name || undefined);
            }
            setShowModal(false);
            setEmail("");
            setPassword("");
            setName("");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <>
            {/* Navbar buttons */}
            <div className="flex items-center gap-3">
                <button
                    onClick={() => { setIsLoginMode(true); setShowModal(true); setError(""); }}
                    className="text-sm text-white/70 hover:text-white transition"
                >
                    Log In
                </button>
                <button
                    onClick={() => { setIsLoginMode(false); setShowModal(true); setError(""); }}
                    className="px-4 py-1.5 bg-emerald-500 text-black text-sm font-semibold rounded-full hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20"
                >
                    Sign Up
                </button>
            </div>

            {/* Modal overlay */}
            {showModal && createPortal(
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
                    onClick={() => setShowModal(false)}
                >
                    <div
                        className="w-full max-w-sm mx-4 bg-[#111] border border-white/10 rounded-2xl p-8 shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Title */}
                        <h2 className="text-xl font-bold text-white mb-1">
                            {isLoginMode ? "Welcome back" : "Create account"}
                        </h2>
                        <p className="text-sm text-white/40 mb-6">
                            {isLoginMode
                                ? "Log in to your aimem account"
                                : "Sign up to get started with aimem"}
                        </p>

                        {/* Error banner */}
                        {error && (
                            <div className="mb-4 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                                {error}
                            </div>
                        )}

                        {/* Form */}
                        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                            {!isLoginMode && (
                                <input
                                    type="text"
                                    placeholder="Name (optional)"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-emerald-500/50 transition"
                                />
                            )}
                            <input
                                type="email"
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-emerald-500/50 transition"
                            />
                            <input
                                type="password"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-emerald-500/50 transition"
                            />

                            <button
                                type="submit"
                                disabled={submitting}
                                className="w-full py-3 bg-emerald-500 text-black font-semibold rounded-xl hover:bg-emerald-400 transition disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                            >
                                {submitting
                                    ? "..."
                                    : isLoginMode
                                        ? "Log In"
                                        : "Create Account"}
                            </button>
                        </form>

                        {/* Toggle mode */}
                        <p className="mt-6 text-center text-sm text-white/40">
                            {isLoginMode ? "Don't have an account? " : "Already have an account? "}
                            <button
                                onClick={() => { setIsLoginMode(!isLoginMode); setError(""); }}
                                className="text-emerald-400 hover:text-emerald-300 transition"
                            >
                                {isLoginMode ? "Sign Up" : "Log In"}
                            </button>
                        </p>
                    </div>
                </div>
            , document.body)}
        </>
    );
}
