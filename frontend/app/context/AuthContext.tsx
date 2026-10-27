"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

// ── Types ──
type User = {
    id: number;
    email: string;
    name: string | null;
};

type AuthContextType = {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name?: string) => Promise<void>;
    logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ── Provider ──
export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // On mount: check if a token exists in localStorage → fetch /me
    useEffect(() => {
        const savedToken = localStorage.getItem("aimem_token");
        if (savedToken) {
            setToken(savedToken);
            fetch(`${API_BASE}/api/auth/me`, {
                headers: { Authorization: `Bearer ${savedToken}` },
            })
                .then((res) => (res.ok ? res.json() : Promise.reject()))
                .then((data) => setUser(data))
                .catch(() => {
                    localStorage.removeItem("aimem_token");
                    setToken(null);
                })
                .finally(() => setIsLoading(false));
        } else {
            setIsLoading(false);
        }
    }, []);

    const login = async (email: string, password: string) => {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Login failed");
        }
        const data = await res.json();
        localStorage.setItem("aimem_token", data.access_token);
        setToken(data.access_token);
        setUser(data.user);
    };

    const register = async (email: string, password: string, name?: string) => {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, name }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Registration failed");
        }
        const data = await res.json();
        localStorage.setItem("aimem_token", data.access_token);
        setToken(data.access_token);
        setUser(data.user);
    };

    const logout = () => {
        localStorage.removeItem("aimem_token");
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

// ── Hook ──
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");
    return ctx;
}
