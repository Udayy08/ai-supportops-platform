"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Bot, BarChart3, Database, ShieldCheck, UserCheck, Search, Activity, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-blue-100">
      
      {/* Navigation */}
      <nav className="sticky top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-blue-600">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold tracking-tight text-lg">AI SupportOps</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#product" className="hover:text-slate-900 transition-colors">Product</a>
            <a href="#features" className="hover:text-slate-900 transition-colors">Features</a>
            <a href="#security" className="hover:text-slate-900 transition-colors">Security</a>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors hidden sm:block">
              Log in
            </Link>
            <Button asChild className="rounded-full bg-slate-900 text-white hover:bg-slate-800 h-9 px-5 font-medium shadow-sm">
              <Link href="/dashboard">
                Go to Dashboard
              </Link>
            </Button>
          </div>
        </div>
      </nav>

      <main className="relative pt-24 pb-16 overflow-hidden">
        {/* Subtle Background Pattern */}
        <div className="absolute inset-0 z-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:16px_16px] [mask-image:linear-gradient(to_bottom,white,transparent_80%)] opacity-50" />

        <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-8">
            <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
            Platform v1.0 available now
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-slate-900 max-w-4xl mx-auto leading-[1.1]">
            The new standard for <br />
            <span className="text-blue-600">support operations.</span>
          </h1>
          
          <p className="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
            Automate triage, resolve tickets instantly with deterministic AI, and empower your human agents to focus on high-value conversations.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button asChild size="lg" className="rounded-full bg-blue-600 hover:bg-blue-700 text-white h-12 px-8 text-base shadow-sm">
              <Link href="/dashboard">
                Start building for free
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="rounded-full border-slate-300 text-slate-700 hover:bg-slate-50 h-12 px-8 text-base shadow-sm">
              <Link href="/tickets">
                Book a demo
              </Link>
            </Button>
          </div>
        </div>

        {/* High Fidelity Dashboard Mockup */}
        <div id="product" className="relative z-10 max-w-6xl mx-auto px-6 mt-20">
          <div className="rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-200/50 overflow-hidden flex flex-col">
            {/* Window Header */}
            <div className="h-12 bg-slate-50 border-b border-slate-200 flex items-center px-4 gap-4">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <div className="w-3 h-3 rounded-full bg-slate-300" />
                <div className="w-3 h-3 rounded-full bg-slate-300" />
              </div>
              <div className="flex-1 flex justify-center">
                <div className="w-1/2 h-6 bg-white border border-slate-200 rounded text-[10px] flex items-center justify-center text-slate-400 font-mono shadow-sm">
                  app.supportops.ai
                </div>
              </div>
              <div className="w-12" /> {/* Spacer */}
            </div>
            
            {/* Window Body - UI Mockup */}
            <div className="flex h-[500px]">
              {/* Sidebar */}
              <div className="w-64 border-r border-slate-200 bg-slate-50/50 p-4 flex flex-col gap-1.5 font-medium text-sm text-slate-600">
                <div className="flex items-center gap-2.5 px-3 py-2 bg-blue-100/50 text-blue-700 rounded-md mb-2">
                  <BarChart3 className="w-4 h-4" /> Dashboard
                </div>
                <div className="flex items-center gap-2.5 px-3 py-2 hover:bg-slate-100 rounded-md transition-colors">
                  <Bot className="w-4 h-4" /> AI Evaluation
                </div>
                <div className="flex items-center gap-2.5 px-3 py-2 hover:bg-slate-100 rounded-md transition-colors">
                  <Activity className="w-4 h-4" /> Workflow Traces
                </div>
                <div className="flex items-center gap-2.5 px-3 py-2 hover:bg-slate-100 rounded-md transition-colors">
                  <ShieldCheck className="w-4 h-4" /> Review Queue
                </div>
              </div>
              
              {/* Main Content */}
              <div className="flex-1 p-8 bg-white overflow-hidden relative">
                <div className="flex justify-between items-center mb-8">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">SupportOps Overview</h2>
                    <p className="text-sm text-slate-500 mt-1">Live LangGraph routing metrics</p>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-xs font-semibold border border-emerald-200 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    System Active
                  </div>
                </div>
                
                {/* Metrics */}
                <div className="grid grid-cols-3 gap-5 mb-8">
                  <div className="border border-slate-200 rounded-xl p-5 flex flex-col gap-1 shadow-sm">
                    <span className="text-sm text-slate-500 font-medium">Auto-Resolution Rate</span>
                    <span className="text-3xl font-bold text-slate-900 mt-2">72.5%</span>
                    <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 mt-1">
                       +5.2% vs last week
                    </span>
                  </div>
                  <div className="border border-slate-200 rounded-xl p-5 flex flex-col gap-1 shadow-sm relative overflow-hidden group">
                    <span className="text-sm text-slate-500 font-medium">Retrieval Confidence</span>
                    <span className="text-3xl font-bold text-slate-900 mt-2">94.2%</span>
                    <span className="text-xs text-blue-600 font-medium mt-1">Cross-Encoder Threshold: -6.0</span>
                    <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />
                  </div>
                  <div className="border border-slate-200 rounded-xl p-5 flex flex-col gap-1 shadow-sm">
                    <span className="text-sm text-slate-500 font-medium">Escalation Queue</span>
                    <span className="text-3xl font-bold text-slate-900 mt-2">12</span>
                    <span className="text-xs text-amber-600 font-medium mt-1 animate-pulse">Needs human review</span>
                  </div>
                </div>

                {/* Table */}
                <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <div className="h-10 bg-slate-50 border-b border-slate-200 grid grid-cols-12 items-center px-5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    <div className="col-span-6">User Query</div>
                    <div className="col-span-3">Confidence</div>
                    <div className="col-span-3 text-right">Status</div>
                  </div>
                  <div className="h-14 border-b border-slate-100 grid grid-cols-12 items-center px-5 text-sm hover:bg-slate-50 transition-colors">
                    <div className="col-span-6 font-medium text-slate-900 truncate pr-4">How do I reset my API key?</div>
                    <div className="col-span-3 font-mono text-slate-500">8.42</div>
                    <div className="col-span-3 flex justify-end">
                      <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-semibold border border-emerald-200">Auto-Resolved</span>
                    </div>
                  </div>
                  <div className="h-14 border-b border-slate-100 grid grid-cols-12 items-center px-5 text-sm hover:bg-slate-50 transition-colors">
                    <div className="col-span-6 font-medium text-slate-900 truncate pr-4">Billing plan upgrade failed</div>
                    <div className="col-span-3 font-mono text-slate-500">-7.15</div>
                    <div className="col-span-3 flex justify-end">
                      <span className="px-2.5 py-1 bg-amber-100 text-amber-700 rounded text-xs font-semibold border border-amber-200 animate-pulse">Escalated</span>
                    </div>
                  </div>
                  <div className="h-14 grid grid-cols-12 items-center px-5 text-sm hover:bg-slate-50 transition-colors">
                    <div className="col-span-6 font-medium text-slate-900 truncate pr-4">Can I invite multiple users?</div>
                    <div className="col-span-3 font-mono text-slate-500">9.12</div>
                    <div className="col-span-3 flex justify-end">
                      <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-semibold border border-emerald-200">Auto-Resolved</span>
                    </div>
                  </div>
                </div>

                {/* Fade Out Bottom */}
                <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent pointer-events-none" />
              </div>
            </div>
          </div>
        </div>
      </main>



      {/* Features Section */}
      <section id="features" className="py-32 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20 max-w-3xl mx-auto">
            <h2 className="text-4xl font-extrabold text-slate-900 mb-6 tracking-tight">Enterprise reliability, built in.</h2>
            <p className="text-lg text-slate-600 leading-relaxed">
              We don't just generate text. Our multi-agent system enforces strict mathematical quality gates before any response reaches your customers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={GitBranch}
              title="Agentic Orchestration"
              description="LangGraph-powered state machines direct semantic retrieval, synthesis, and safety checks with predictable routing."
            />
            <FeatureCard 
              icon={Database}
              title="Hybrid Retrieval"
              description="Combines BM25 sparse lexical search with ChromaDB dense vectors to ensure maximum document recall."
            />
            <FeatureCard 
              icon={ShieldCheck}
              title="Confidence Gating"
              description="Cross-Encoder reranking ensures only high-confidence documents are utilized, mathematically preventing hallucinations."
            />
            <FeatureCard 
              icon={UserCheck}
              title="Human-in-the-Loop"
              description="Low confidence inquiries or potential risks are automatically escalated to a dedicated human review queue."
            />
            <FeatureCard 
              icon={Search}
              title="Full Traceability"
              description="Every AI decision is logged with comprehensive source attribution and confidence scoring for full transparency."
            />
            <FeatureCard 
              icon={BarChart3}
              title="Evaluation Analytics"
              description="Built-in dashboards track RAGAS metrics, resolution rates, and retrieval latency in real-time."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-2.5 mb-6">
                <div className="flex h-6 w-6 items-center justify-center rounded bg-slate-900">
                  <Bot className="h-3 w-3 text-white" />
                </div>
                <span className="font-bold tracking-tight text-slate-900">AI SupportOps</span>
              </div>
              <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
                The enterprise-grade platform for automating customer support operations with agentic intelligence and deterministic quality gating.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 mb-4">Product</h4>
              <ul className="space-y-3 text-sm text-slate-500">
                <li><a href="#" className="hover:text-blue-600 transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Security</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 mb-4">Company</h4>
              <ul className="space-y-3 text-sm text-slate-500">
                <li><a href="#" className="hover:text-blue-600 transition-colors">About</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Contact</a></li>
              </ul>
            </div>
          </div>
          
          <div className="pt-8 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              © {new Date().getFullYear()} AI SupportOps. All rights reserved.
            </p>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-slate-500">Developed by</span>
              <span className="font-semibold text-slate-900">Uday Kumar</span>
              <a href="https://github.com/Udayy08" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-900 transition-colors">
                <span className="sr-only">GitHub</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.02c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A4.8 4.8 0 0 0 8 18v4"></path></svg>
              </a>
              <a href="https://linkedin.com/in/uday-kumar" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-900 transition-colors">
                <span className="sr-only">LinkedIn</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-8 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
      <div className="h-12 w-12 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center mb-6">
        <Icon className="h-6 w-6 text-blue-600" />
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-3 tracking-tight">{title}</h3>
      <p className="text-slate-600 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
