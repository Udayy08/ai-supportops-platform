"use client";

import React, { useState, useRef } from "react";
import useSWR from "swr";
import Link from "next/link";
import { 
  BookOpen, Search, Upload, Trash2, RefreshCw, 
  FileText, Eye
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { TableSkeleton } from "@/components/shared/skeleton-loaders";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  listKnowledgeArticles, 
  uploadKnowledgeDocument,
  deleteKnowledgeDocument,
  reindexKnowledgeDocument
} from "@/lib/api/endpoints";
import { formatDate } from "@/lib/utils";
import type { KnowledgeArticle } from "@/lib/types";
import { toast } from "sonner";

export default function KnowledgePage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading, mutate } = useSWR(
    `knowledge?page=${page}&search=${search}`,
    () => listKnowledgeArticles({ page, page_size: 10, search: search || undefined })
  );

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input
    e.target.value = '';

    setIsUploading(true);
    toast.loading("Extracting and chunking document...", { id: "upload" });

    try {
      await uploadKnowledgeDocument(file);
      toast.success("Document successfully uploaded and indexed!", { id: "upload" });
      mutate();
    } catch (err: unknown) {
      const errorMsg = (err as {response?: {data?: {detail?: string}}})?.response?.data?.detail || "Failed to upload document";
      toast.error(errorMsg, { id: "upload" });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document? It will be removed from the AI's knowledge base.")) return;
    
    toast.loading("Deleting document...", { id: "delete" });
    try {
      await deleteKnowledgeDocument(id);
      toast.success("Document deleted", { id: "delete" });
      mutate();
    } catch (err: unknown) {
      const errorMsg = (err as {response?: {data?: {detail?: string}}})?.response?.data?.detail || "Failed to delete document";
      toast.error(errorMsg, { id: "delete" });
    }
  };

  const handleReindex = async (id: string) => {
    toast.loading("Reindexing document...", { id: "reindex" });
    try {
      await reindexKnowledgeDocument(id);
      toast.success("Document successfully reindexed!", { id: "reindex" });
      mutate();
    } catch (err: unknown) {
      const errorMsg = (err as {response?: {data?: {detail?: string}}})?.response?.data?.detail || "Failed to reindex document";
      toast.error(errorMsg, { id: "reindex" });
    }
  };

  const renderStatus = (status?: string) => {
    switch (status) {
      case "SUCCESS":
        return <Badge className="bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 border-emerald-200">Indexed</Badge>;
      case "PROCESSING":
      case "PENDING":
        return <Badge variant="secondary" className="bg-amber-500/10 text-amber-600 border-amber-200">Processing</Badge>;
      case "FAILED":
        return <Badge variant="destructive" className="bg-red-500/10 text-red-600 border-red-200">Failed</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <>
      <Header
        title="Knowledge Base"
        description="Manage company policies, FAQs, and support documents for the AI Retriever pipeline"
      />
      <main className="flex-1 p-6 space-y-6">
        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search documents by name..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-9 h-10"
            />
          </div>
          
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <input 
              type="file" 
              ref={fileInputRef} 
              id="test-file-input"
              className="mb-4"
              accept=".pdf,.txt,.md,.csv" 
              onChange={handleFileChange} 
            />
            <Button 
              onClick={handleUploadClick} 
              disabled={isUploading}
              className="w-full sm:w-auto gap-2"
            >
              <Upload className="h-4 w-4" />
              {isUploading ? "Uploading..." : "Upload Document"}
            </Button>
          </div>
        </div>

        {/* Table View */}
        <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="p-4">
              <TableSkeleton rows={8} />
            </div>
          ) : !data?.items.length ? (
            <EmptyState
              title="No documents uploaded yet"
              description={search ? "Try a different search term." : "Upload PDFs, Text, or Markdown files to power the AI support agent."}
              icon={<BookOpen className="h-10 w-10 text-muted-foreground" />}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
                  <tr>
                    <th className="px-6 py-4 font-medium">Document Name</th>
                    <th className="px-6 py-4 font-medium">Type</th>
                    <th className="px-6 py-4 font-medium">Upload Date</th>
                    <th className="px-6 py-4 font-medium">Chunks</th>
                    <th className="px-6 py-4 font-medium">Status</th>
                    <th className="px-6 py-4 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data.items.map((doc: KnowledgeArticle) => (
                    <tr key={doc.id} className="hover:bg-muted/30 transition-colors group">
                      <td className="px-6 py-4 font-medium text-foreground flex items-center gap-3">
                        <FileText className="h-4 w-4 text-blue-500" />
                        <Link href={`/knowledge/${doc.id}`} className="hover:underline decoration-blue-500 underline-offset-4">
                          {doc.metadata?.filename || doc.title}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <span className="uppercase text-xs font-mono bg-muted px-2 py-1 rounded">
                          {doc.metadata?.file_type || "TXT"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        {formatDate(doc.created_at)}
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        {doc.metadata?.chunk_count || 0}
                      </td>
                      <td className="px-6 py-4">
                        {renderStatus(doc.metadata?.indexed_status)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Link href={`/knowledge/${doc.id}`}>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-blue-500">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-muted-foreground hover:text-amber-500"
                            onClick={() => handleReindex(doc.id)}
                            title="Reindex document"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-muted-foreground hover:text-red-500"
                            onClick={() => handleDelete(doc.id)}
                            title="Delete document"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Footer */}
          {data && data.total > 10 && (
            <div className="px-6 py-4 border-t flex items-center justify-between bg-muted/20">
              <p className="text-xs text-muted-foreground">
                Showing {Math.min(data.total, page * 10)} of {data.total} documents
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="h-8 text-xs"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.has_next}
                  className="h-8 text-xs"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
