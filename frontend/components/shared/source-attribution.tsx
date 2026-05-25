"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, FileText, Link as LinkIcon, BadgeInfo } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress, ProgressTrack, ProgressIndicator } from "@/components/ui/progress";
import type { SourceAttribution as SourceAttributionType } from "@/lib/types";

interface SourceAttributionProps {
  sources: SourceAttributionType[];
}

export function SourceAttribution({ sources }: SourceAttributionProps) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const toggleExpand = (idx: number) => {
    setExpanded((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-3 mt-4 pt-4 border-t border-border">
      <h4 className="text-sm font-semibold flex items-center gap-1.5 text-muted-foreground uppercase tracking-wide">
        <LinkIcon className="h-4 w-4" />
        Sources Used
      </h4>
      <div className="flex flex-col gap-3">
        {sources.map((source, idx) => {
          // Normalize scores for progress bars
          const cePct = source.cross_encoder_score !== undefined 
            ? Math.max(0, Math.min(100, ((source.cross_encoder_score + 10) / 10) * 100))
            : 0;
          const semPct = source.semantic_score !== undefined ? source.semantic_score * 100 : 0;
          const lexPct = source.lexical_score !== undefined ? Math.min(100, source.lexical_score * 10) : 0;

          return (
          <div key={idx} className="rounded-xl border bg-card p-4 shadow-sm transition-all hover:shadow-md">
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-md bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                    <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <span className="font-semibold text-sm text-foreground block">{source.filename}</span>
                    <span className="text-xs text-muted-foreground block">Chunk {source.chunk_index} • ID: {source.document_id.slice(0, 8)}...</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {source.used_for_generation && (
                    <Badge variant="soft-success" className="text-[10px] uppercase tracking-wider">
                      Used
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs bg-muted/50">
                    Rank: #{source.post_rerank_rank ?? source.retrieval_rank}
                  </Badge>
                </div>
              </div>

              {/* Visual Scores Row */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-muted/20 p-3 rounded-lg border border-border/50">
                {source.cross_encoder_score !== undefined && (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[10px] uppercase text-muted-foreground font-semibold">Cross-Encoder</span>
                      <span className="text-xs font-mono text-orange-600 dark:text-orange-400">{source.cross_encoder_score.toFixed(2)}</span>
                    </div>
                    <Progress value={cePct} className="h-1">
                      <ProgressTrack>
                        <ProgressIndicator className="bg-orange-500" />
                      </ProgressTrack>
                    </Progress>
                  </div>
                )}
                
                {source.semantic_score !== undefined ? (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[10px] uppercase text-muted-foreground font-semibold">Semantic</span>
                      <span className="text-xs font-mono text-blue-600 dark:text-blue-400">{source.semantic_score.toFixed(3)}</span>
                    </div>
                    <Progress value={semPct} className="h-1">
                      <ProgressTrack>
                        <ProgressIndicator className="bg-blue-500" />
                      </ProgressTrack>
                    </Progress>
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[10px] uppercase text-muted-foreground font-semibold">Similarity</span>
                      <span className="text-xs font-mono">{source.similarity_score.toFixed(3)}</span>
                    </div>
                    <Progress value={source.similarity_score * 100} className="h-1">
                      <ProgressTrack>
                        <ProgressIndicator />
                      </ProgressTrack>
                    </Progress>
                  </div>
                )}

                {source.lexical_score !== undefined && (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[10px] uppercase text-muted-foreground font-semibold">Lexical (BM25)</span>
                      <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400">{source.lexical_score.toFixed(3)}</span>
                    </div>
                    <Progress value={lexPct} className="h-1">
                      <ProgressTrack>
                        <ProgressIndicator className="bg-emerald-500" />
                      </ProgressTrack>
                    </Progress>
                  </div>
                )}
              </div>
            
            <div className="mt-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleExpand(idx)}
                className="h-6 text-xs px-2 -ml-2 text-muted-foreground hover:text-foreground hover:bg-muted/50"
              >
                {expanded[idx] ? (
                  <>
                    <ChevronUp className="h-3 w-3 mr-1" />
                    Hide Preview
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3 mr-1" />
                    Show Preview
                  </>
                )}
              </Button>

              {expanded[idx] && (
                <div className="mt-2 text-sm text-foreground bg-muted/30 rounded-lg border border-border/50 p-4 whitespace-pre-wrap leading-relaxed shadow-inner">
                  {source.chunk_preview}
                </div>
              )}
            </div>
            </div>
          </div>
          );
        })}
      </div>
    </div>
  );
}
