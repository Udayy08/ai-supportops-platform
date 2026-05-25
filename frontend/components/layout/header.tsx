"use client";

import { Menu, Plus, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ThemeSwitcher } from "@/components/shared/theme-switcher";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Sidebar } from "./sidebar";

interface HeaderProps {
  title: string;
  description?: string;
  backLink?: string;
}

export function Header({ title, description, backLink }: HeaderProps) {
  return (
    <header className="flex items-center justify-between border-b bg-background px-6 py-3.5 h-14 shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobile menu */}
        <Sheet>
          <SheetTrigger 
            render={
              <Button variant="ghost" size="icon" className="h-8 w-8 md:hidden">
                <Menu className="h-4 w-4" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            } 
          />
          <SheetContent side="left" className="p-0 w-64">
            <Sidebar />
          </SheetContent>
        </Sheet>

        {backLink && (
          <Button variant="ghost" size="icon" asChild className="h-8 w-8 mr-1 -ml-2 text-muted-foreground hover:text-foreground">
            <Link href={backLink}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
        )}

        <div>
          <h1 className="text-sm font-semibold text-foreground leading-none">
            {title}
          </h1>
          {description && (
            <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <ThemeSwitcher />
        <Button asChild size="sm" className="h-8 text-xs">
          <Link href="/tickets/new">
            <Plus className="h-3.5 w-3.5 mr-1.5" />
            New Ticket
          </Link>
        </Button>
      </div>
    </header>
  );
}
