"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createTicket } from "@/lib/api/endpoints";

const schema = z.object({
  subject: z.string().min(1, "Subject is required").max(500, "Subject too long"),
  description: z.string().min(1, "Description is required"),
  priority: z.enum(["low", "medium", "high", "critical"]),
  category: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function NewTicketPage() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { priority: "medium" },
  });

  // eslint-disable-next-line react-hooks/incompatible-library
  const priority = watch("priority");

  const onSubmit = async (data: FormData) => {
    try {
      const ticket = await createTicket(data);
      toast.success("Ticket created", {
        description: `#${ticket.id.slice(0, 8)} has been submitted.`,
      });
      router.push(`/tickets/${ticket.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create ticket";
      toast.error("Error creating ticket", { description: message });
    }
  };

  return (
    <>
      <Header title="New Ticket" description="Submit a new support request" />
      <main className="flex-1 p-6">
        <div className="max-w-xl mx-auto">
          <Button variant="ghost" size="sm" asChild className="mb-4 -ml-1 text-xs">
            <Link href="/tickets">
              <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
              Back to Tickets
            </Link>
          </Button>

          <div className="rounded-lg border bg-card shadow-sm p-6">
            <h2 className="text-base font-semibold mb-5">Ticket Details</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div className="space-y-1.5">
                <Label htmlFor="subject" className="text-sm">
                  Subject <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="subject"
                  {...register("subject")}
                  placeholder="e.g. Missing refund for order #123"
                  className="h-9"
                />
                {errors.subject && (
                  <p className="text-xs text-destructive">{errors.subject.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="description" className="text-sm">
                  Description <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="description"
                  {...register("description")}
                  placeholder="Describe the issue in detail..."
                  rows={5}
                  className="resize-none text-sm"
                />
                {errors.description && (
                  <p className="text-xs text-destructive">{errors.description.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-sm">Priority</Label>
                  <Select
                    value={priority}
                    onValueChange={(v) => setValue("priority", v as FormData["priority"])}
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="category" className="text-sm">
                    Category
                  </Label>
                  <Input
                    id="category"
                    {...register("category")}
                    placeholder="e.g. Billing"
                    className="h-9"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  Submit Ticket
                </Button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </>
  );
}
