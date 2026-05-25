"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { Header } from "@/components/layout/header";
import { getKnowledgeDocument, reindexKnowledgeDocument, deleteKnowledgeDocument } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { RefreshCw, Trash2, FileText, Database, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export default function DocumentDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const { data: document, isLoading, mutate } = useSWR(
    id ? `knowledge/${id}` : null,
    () => getKnowledgeDocument(id)
  );

  const handleReindex = async () => {
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

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    
    toast.loading("Deleting document...", { id: "delete" });
    try {
      await deleteKnowledgeDocument(id);
      toast.success("Document deleted", { id: "delete" });
      router.push("/knowledge");
    } catch (err: unknown) {
      const errorMsg = (err as {response?: {data?: {detail?: string}}})?.response?.data?.detail || "Failed to delete document";
      toast.error(errorMsg, { id: "delete" });
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading document details...</div>;
  }

  if (!document) {
    return <div className="p-8 text-center text-muted-foreground">Document not found</div>;
  }

  const renderStatus = (status?: string) => {
    switch (status) {
      case "SUCCESS":
        return <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-200">Indexed</Badge>;
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
        title={document.metadata?.filename || document.title}
        description={`Document ID: ${document.id}`}
      />

      <main className="flex-1 p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => router.push("/knowledge")} className="gap-2 text-muted-foreground">
            <ArrowLeft className="h-4 w-4" /> Back to Knowledge Base
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleReindex} className="gap-2">
              <RefreshCw className="h-4 w-4" /> Reindex
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDelete} className="gap-2">
              <Trash2 className="h-4 w-4" /> Delete
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Metadata Sidebar */}
          <div className="md:col-span-1 space-y-6">
            <div className="rounded-lg border bg-card p-5 shadow-sm space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                <Database className="h-4 w-4 text-blue-500" /> Indexing Status
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1 border-b">
                  <span className="text-muted-foreground">Status</span>
                  <span>{renderStatus(document.metadata?.indexed_status)}</span>
                </div>
                <div className="flex justify-between py-1 border-b">
                  <span className="text-muted-foreground">Total Chunks</span>
                  <span className="font-medium">{document.metadata?.chunk_count || 0}</span>
                </div>
                <div className="flex justify-between py-1 border-b">
                  <span className="text-muted-foreground">File Type</span>
                  <span className="uppercase">{document.metadata?.file_type || "TXT"}</span>
                </div>
                <div className="flex justify-between py-1 border-b">
                  <span className="text-muted-foreground">Uploaded At</span>
                  <span>{formatDate(document.created_at)}</span>
                </div>
                <div className="flex justify-between py-1 border-b">
                  <span className="text-muted-foreground">Last Indexed</span>
                  <span>{document.metadata?.last_indexed_at ? formatDate(document.metadata.last_indexed_at) : "Never"}</span>
                </div>
                {document.metadata?.error && (
                  <div className="pt-2 text-red-500 text-xs">
                    <strong>Error:</strong> {String(document.metadata.error)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Content Preview */}
          <div className="md:col-span-2">
            <div className="rounded-lg border bg-card shadow-sm h-full flex flex-col">
              <div className="p-4 border-b bg-muted/20 flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <h3 className="font-semibold text-sm">Extracted Text Preview</h3>
              </div>
              <div className="p-5 flex-1 overflow-auto bg-muted/5 max-h-[600px]">
                <pre className="text-sm font-mono whitespace-pre-wrap text-foreground/80">
                  {document.content}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
