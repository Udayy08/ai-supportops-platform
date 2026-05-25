"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Ticket,
  BarChart3,
  FlaskConical,
  GitBranch,
  BookOpen,
  Settings,
  UserCheck,
  Bot,
  Network
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tickets", label: "Tickets", icon: Ticket },
  { href: "/queue", label: "Review Queue", icon: UserCheck },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/evaluations", label: "Evaluations", icon: FlaskConical },
  { href: "/traces", label: "Workflow Traces", icon: GitBranch },
  { href: "/architecture", label: "Architecture", icon: Network },
  { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-64 shrink-0 border-r bg-sidebar min-h-screen">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2.5 px-5 py-4 border-b border-sidebar-border hover:bg-sidebar-accent/50 transition-colors cursor-pointer">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
          <Bot className="h-4 w-4 text-primary-foreground" />
        </div>
        <div>
          <p className="text-sm font-semibold text-sidebar-foreground leading-none">
            AI SupportOps
          </p>
          <p className="text-xs text-sidebar-foreground/50 mt-0.5">
            Demo Tenant
          </p>
        </div>
      </Link>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === "/"
              ? pathname === "/"
              : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground font-medium"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-sidebar-border">
        <p className="text-xs text-sidebar-foreground/40">
          Phase 8 — Frontend UI
        </p>
      </div>
    </aside>
  );
}
