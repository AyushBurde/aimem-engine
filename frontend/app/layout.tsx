import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./context/AuthContext";
import NavAuth from "./components/NavAuth";


export const metadata: Metadata = {
  title: "aimem — AI Memory Engine",
  description: "A memory layer for AI agents that actually remembers what matters.",
  icons: {
    icon: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {/* ── NAVBAR ── */}
          <header className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
            <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
              {/* Logo / Name */}
              <a href="/" className="flex items-center gap-2.5 text-xl font-bold tracking-tight">
                <img src="/logo.png" alt="aimem logo" className="w-7 h-7 rounded-md object-contain" />
                <span>aimem</span>
              </a>

              {/* Nav Links */}
              <nav className="flex items-center gap-8">
                <a href="/" className="text-sm text-white/70 hover:text-white">Home</a>

                <a href="/docs" className="text-sm text-white/70 hover:text-white">Docs</a>
                <a href="/" className="text-sm text-white/70 hover:text-white">Products</a>
                <NavAuth />
              </nav>
            </div>
          </header>

          {/* ── PAGE CONTENT ── */}
          <main>{children}</main>

          {/* ── FOOTER ── */}
          <footer className="border-t border-white/10 py-8">
            <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <img src="/logo.png" alt="aimem logo" className="w-5 h-5 rounded object-contain opacity-70" />
                <span className="text-sm text-white/40">aimem</span>
              </div>
              <span className="text-sm text-white/40">AI Memory Engine</span>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
