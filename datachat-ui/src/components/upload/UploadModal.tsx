"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, X, FileText, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export function UploadModal() {
  const { uploadFile, setUploadOpen } = useStore();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File) => {
    if (!f.name.toLowerCase().endsWith(".csv")) {
      setError("Only CSV files are supported.");
      return;
    }
    setFile(f);
    setError(null);
    setStatus("idle");
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setStatus("loading");
    setError(null);
    try {
      await uploadFile(file);
      setStatus("success");
      setTimeout(() => setUploadOpen(false), 800);
    } catch (e: unknown) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Upload failed.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setUploadOpen(false)}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 bg-[#0e1325] border border-white/[0.08] rounded-2xl shadow-2xl shadow-black/60 p-6">
        {/* Close */}
        <button
          onClick={() => setUploadOpen(false)}
          className="absolute top-4 right-4 p-1 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.05] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Title */}
        <div className="mb-5">
          <h2 className="text-base font-semibold text-white/90">Upload Dataset</h2>
          <p className="text-xs text-white/35 mt-0.5">
            Drag & drop or click to select a CSV file
          </p>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={cn(
            "relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed cursor-pointer transition-all py-10",
            dragging
              ? "border-indigo-500/60 bg-indigo-500/5"
              : file
              ? "border-emerald-500/30 bg-emerald-500/5"
              : "border-white/[0.1] bg-white/[0.02] hover:border-indigo-500/30 hover:bg-indigo-500/5"
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
          />

          {file ? (
            <>
              <FileText className="w-10 h-10 text-emerald-400/70" />
              <div className="text-center">
                <p className="text-sm font-medium text-white/70">{file.name}</p>
                <p className="text-xs text-white/30 mt-0.5">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="w-12 h-12 rounded-xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center">
                <Upload className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="text-center">
                <p className="text-sm text-white/50">
                  Drop CSV here or <span className="text-indigo-400">browse</span>
                </p>
              </div>
            </>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-3 flex items-center gap-2 text-xs text-red-400 bg-red-500/5 border border-red-500/15 rounded-lg px-3 py-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={() => setUploadOpen(false)}
            className="px-4 py-2 rounded-lg text-xs font-medium text-white/40 hover:text-white/60 hover:bg-white/[0.04] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || status === "loading" || status === "success"}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all",
              status === "success"
                ? "bg-emerald-600 text-white"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-900/30",
              (!file || status === "loading" || status === "success") && "opacity-50 cursor-not-allowed"
            )}
          >
            {status === "loading" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {status === "success" && <CheckCircle2 className="w-3.5 h-3.5" />}
            {status === "success" ? "Loaded!" : status === "loading" ? "Uploading…" : "Load CSV"}
          </button>
        </div>
      </div>
    </div>
  );
}
