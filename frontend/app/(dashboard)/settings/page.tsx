"use client";

import React from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor, User, Building2, FlaskConical, Shield } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-4">
      <div>
        <p className="text-sm font-medium">{label}</p>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function SectionHeader({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-1">
      <Icon className="h-4 w-4 text-muted-foreground" />
      <h2 className="text-sm font-semibold">{title}</h2>
    </div>
  );
}

export default function SettingsPage() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const themes = [
    { value: "light", label: "Light", Icon: Sun },
    { value: "dark", label: "Dark", Icon: Moon },
    { value: "system", label: "System", Icon: Monitor },
  ];

  return (
    <>
      <Header title="Settings" description="Configure platform preferences" />
      <main className="flex-1 p-6">
        <div className="max-w-2xl mx-auto space-y-8">

          {/* Appearance */}
          <div className="rounded-lg border bg-card shadow-sm p-5">
            <SectionHeader icon={Sun} title="Appearance" />
            <Separator className="my-3" />

            <SettingRow
              label="Theme"
              description="Select your preferred color scheme. System follows your OS preference."
            >
              <div className="flex gap-2">
                {themes.map(({ value, label, Icon }) => (
                  <Button
                    key={value}
                    variant={theme === value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTheme(value)}
                    className="h-8 text-xs gap-1.5"
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                  </Button>
                ))}
              </div>
            </SettingRow>

            <Separator />
            <SettingRow label="Active Theme" description="Currently resolved theme.">
              <Badge variant="secondary" className="text-xs capitalize">
                {resolvedTheme ?? "—"}
              </Badge>
            </SettingRow>
          </div>

          {/* User Profile */}
          <div className="rounded-lg border bg-card shadow-sm p-5">
            <SectionHeader icon={User} title="User Profile" />
            <Separator className="my-3" />

            <SettingRow label="Name" description="Display name for this session.">
              <span className="text-sm font-medium">Test User</span>
            </SettingRow>
            <Separator />
            <SettingRow label="Email">
              <span className="text-sm font-mono text-muted-foreground">test@example.com</span>
            </SettingRow>
            <Separator />
            <SettingRow label="Role">
              <Badge className="text-xs bg-primary/10 text-primary border-primary/20">
                ADMIN
              </Badge>
            </SettingRow>
            <Separator />
            <SettingRow label="Auth Mode" description="Phase 8 uses a mock authentication session.">
              <Badge variant="outline" className="text-xs text-amber-600 border-amber-400">
                Mock Session
              </Badge>
            </SettingRow>
          </div>

          {/* Tenant */}
          <div className="rounded-lg border bg-card shadow-sm p-5">
            <SectionHeader icon={Building2} title="Tenant Information" />
            <Separator className="my-3" />

            <SettingRow label="Tenant Name">
              <span className="text-sm font-medium">Demo Corp</span>
            </SettingRow>
            <Separator />
            <SettingRow label="Slug">
              <span className="text-sm font-mono text-muted-foreground">demo-tenant</span>
            </SettingRow>
            <Separator />
            <SettingRow label="Plan">
              <Badge variant="secondary" className="text-xs">Enterprise</Badge>
            </SettingRow>
            <Separator />
            <SettingRow label="Data Isolation" description="Row-level multi-tenant security.">
              <div className="flex items-center gap-1.5">
                <Shield className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Enabled</span>
              </div>
            </SettingRow>
          </div>

          {/* Evaluation Settings */}
          <div className="rounded-lg border bg-card shadow-sm p-5">
            <SectionHeader icon={FlaskConical} title="Evaluation Settings" />
            <Separator className="my-3" />

            <SettingRow
              label="RAGAS Evaluations"
              description="Configured via ENABLE_RAGAS in backend .env"
            >
              <Badge className="text-xs bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border-0">
                Enabled
              </Badge>
            </SettingRow>
            <Separator />
            <SettingRow
              label="Sample Percentage"
              description="Percentage of workflow runs that trigger RAGAS scoring."
            >
              <span className="text-sm font-semibold">10%</span>
            </SettingRow>
            <Separator />
            <SettingRow
              label="LangSmith Tracing"
              description="Configured via LANGCHAIN_TRACING_V2 in backend .env"
            >
              <Badge variant="outline" className="text-xs text-muted-foreground">
                Disabled
              </Badge>
            </SettingRow>
            <Separator />
            <SettingRow label="Evaluation Model" description="Groq model used for RAGAS scoring.">
              <span className="text-xs font-mono text-muted-foreground">
                llama-3.1-8b-instant
              </span>
            </SettingRow>
          </div>

          {/* Backend info */}
          <div className="rounded-lg border bg-muted/40 p-4 text-xs text-muted-foreground space-y-1">
            <p className="font-medium text-foreground">API Configuration</p>
            <p>Backend URL: <code className="font-mono">http://localhost:8000</code></p>
            <p>API Version: <code className="font-mono">v1</code></p>
            <p>Platform Version: <code className="font-mono">0.1.0 — Phase 8</code></p>
          </div>
        </div>
      </main>
    </>
  );
}
