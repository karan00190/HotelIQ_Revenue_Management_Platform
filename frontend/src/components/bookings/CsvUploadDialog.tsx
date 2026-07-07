"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ingestionApi } from "@/lib/api";

interface CsvUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CsvUploadDialog({ open, onOpenChange }: CsvUploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: (file: File) => ingestionApi.uploadCsv(file),
    onSuccess: (result) => {
      if (result.success) {
        queryClient.invalidateQueries({ queryKey: ["bookings"] });
      }
    },
  });

  const result = uploadMutation.data;

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setSelectedFile(null);
      uploadMutation.reset();
    }
    onOpenChange(nextOpen);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload bookings CSV</DialogTitle>
          <DialogDescription>
            Runs the full validation and feature-engineering pipeline before loading anything.
            Duplicate rows (same hotel/room/check-in) are skipped automatically.
          </DialogDescription>
        </DialogHeader>

        <input
          type="file"
          accept=".csv"
          onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
          className="text-sm text-foreground file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-1.5 file:text-sm file:text-secondary-foreground"
        />

        {uploadMutation.isError && (
          <p className="text-sm text-status-critical">
            {uploadMutation.error instanceof Error ? uploadMutation.error.message : "Upload failed."}
          </p>
        )}

        {result && (
          <div className="flex flex-col gap-2 rounded-lg bg-muted/40 p-3 text-sm">
            <p
              className="font-medium"
              style={{ color: result.success ? "var(--status-good)" : "var(--status-critical)" }}
            >
              {result.success ? "Upload succeeded" : "Upload rejected"}
            </p>
            <p className="text-muted-foreground">
              {result.records_extracted} record(s) extracted
              {result.load &&
                ` · ${result.load.loaded} loaded, ${result.load.skipped} skipped (duplicates), ${result.load.errors} error(s)`}
            </p>
            {result.validation.errors.length > 0 && (
              <ul className="list-disc pl-5" style={{ color: "var(--status-critical)" }}>
                {result.validation.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            )}
            {result.validation.warnings.length > 0 && (
              <ul className="list-disc pl-5 text-muted-foreground">
                {result.validation.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <DialogFooter>
          <Button
            onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
            disabled={!selectedFile || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? "Uploading..." : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
