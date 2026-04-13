/// <reference types="vite/client" />
import { type ReactNode, type ComponentType, useState, useEffect } from "react";
import {
  Outlet,
  Link,
  createRootRoute,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ErrorBoundary } from "@/components/error-boundary";
import { ToastProvider } from "@/components/toast-provider";
import { CommandPalette } from "@/components/command-palette";
import {
  LayoutDashboard, Receipt, TrendingUp, Landmark, CreditCard, Target,
  LineChart, FileText, Shield, DollarSign, Bot,
  FolderOpen, Database, Settings, BookOpen,
  Menu, X, Sun, Moon, Monitor, Search,
} from "lucide-react";
import "../styles.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

interface NavItem { path: string; label: string; icon: ComponentType<{ size?: number }> }
interface NavGroup { label: string; items: NavItem[] }

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [{ path: "/", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Finances",
    items: [
      { path: "/expenses", label: "Expenses", icon: Receipt },
      { path: "/investments", label: "Investments", icon: TrendingUp },
      { path: "/muni-bonds", label: "Muni Bonds", icon: Landmark },
      { path: "/debts", label: "Debts", icon: CreditCard },
      { path: "/goals", label: "Goals", icon: Target },
    ],
  },
  {
    label: "Planning",
    items: [
      { path: "/projections", label: "Projections", icon: LineChart },
      { path: "/tax", label: "Tax Center", icon: FileText },
      { path: "/social-security", label: "Social Security", icon: Shield },
      { path: "/paycheck", label: "Paycheck", icon: DollarSign },
      { path: "/advisor", label: "AI Advisor", icon: Bot },
    ],
  },
  {
    label: "Data",
    items: [
      { path: "/artifacts", label: "Files", icon: FolderOpen },
      { path: "/db", label: "Database", icon: Database },
    ],
  },
  {
    label: "System",
    items: [
      { path: "/settings", label: "Settings", icon: Settings },
      { path: "/guide", label: "User Guide", icon: BookOpen },
    ],
  },
];

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "FinBot" },
    ],
  }),
  component: RootComponent,
});

function NavContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="space-y-4">
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {group.label}
          </p>
          <div className="space-y-0.5">
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={onNavigate}
                  className="flex items-center gap-2.5 px-3 py-1.5 rounded-md text-sm hover:bg-accent hover:text-accent-foreground transition-colors [&.active]:bg-primary [&.active]:text-primary-foreground"
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

type ThemeMode = "light" | "dark" | "system";

function useTheme() {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window === "undefined") return "system";
    return (localStorage.getItem("finbot-theme") as ThemeMode) || "system";
  });

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");

    if (mode === "dark") {
      root.classList.add("dark");
    } else if (mode === "light") {
      root.classList.add("light");
    }
    // "system" = no class, CSS media query handles it

    localStorage.setItem("finbot-theme", mode);
  }, [mode]);

  const cycle = () => {
    setModeState((prev) => {
      if (prev === "system") return "dark";
      if (prev === "dark") return "light";
      return "system";
    });
  };

  return { mode, cycle };
}

function ThemeToggle({ mode, onCycle }: { mode: ThemeMode; onCycle: () => void }) {
  const labels: Record<ThemeMode, string> = { light: "Light", dark: "Dark", system: "System" };
  return (
    <button onClick={onCycle} title={`Theme: ${labels[mode]} (click to cycle)`}
      className="p-1.5 hover:bg-accent active:bg-accent rounded-md text-sm flex items-center gap-1.5 text-muted-foreground">
      {mode === "light" && <Sun size={15} />}
      {mode === "dark" && <Moon size={15} />}
      {mode === "system" && <Monitor size={15} />}
      <span className="hidden lg:inline text-xs">{labels[mode]}</span>
    </button>
  );
}

function RootComponent() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false);
  const { mode, cycle } = useTheme();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); setCmdPaletteOpen(true); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <RootDocument>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ErrorBoundary>
            <div className="flex min-h-screen bg-background text-foreground">
              {/* Desktop sidebar */}
              <aside className="w-56 border-r border-border bg-card p-4 hidden md:block overflow-y-auto shrink-0">
                <div className="flex items-center justify-between mb-5">
                  <h1 className="text-xl font-bold text-primary">FinBot</h1>
                  <ThemeToggle mode={mode} onCycle={cycle} />
                </div>
                <NavContent />
              </aside>

              {/* Mobile overlay */}
              {mobileMenuOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                  <div className="absolute inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
                  <aside className="absolute left-0 top-0 bottom-0 w-64 bg-card p-4 overflow-y-auto shadow-xl z-50">
                    <div className="flex justify-between items-center mb-5">
                      <h1 className="text-xl font-bold text-primary">FinBot</h1>
                      <button onClick={() => setMobileMenuOpen(false)} className="p-1 hover:bg-accent active:bg-accent rounded">
                        <X size={20} />
                      </button>
                    </div>
                    <NavContent onNavigate={() => setMobileMenuOpen(false)} />
                  </aside>
                </div>
              )}

              <div className="flex-1 flex flex-col overflow-hidden">
                {/* Mobile header */}
                <header className="md:hidden flex items-center gap-3 p-3 border-b border-border bg-card">
                  <button onClick={() => setMobileMenuOpen(true)} className="p-1.5 hover:bg-accent active:bg-accent rounded-md">
                    <Menu size={22} />
                  </button>
                  <span className="font-bold text-primary flex-1">FinBot</span>
                  <button onClick={() => setCmdPaletteOpen(true)} className="p-1.5 hover:bg-accent active:bg-accent rounded-md text-muted-foreground">
                    <Search size={18} />
                  </button>
                  <ThemeToggle mode={mode} onCycle={cycle} />
                </header>

                <main className="flex-1 p-6 overflow-auto">
                  <Outlet />
                </main>
                <CommandPalette open={cmdPaletteOpen} onClose={() => setCmdPaletteOpen(false)} />
              </div>
            </div>
          </ErrorBoundary>
        </ToastProvider>
      </QueryClientProvider>
    </RootDocument>
  );
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}
