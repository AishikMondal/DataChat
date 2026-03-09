"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send, Mic, MicOff, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
type AnyRecognition = any;

declare global {
  interface Window {
    SpeechRecognition: new () => AnyRecognition;
    webkitSpeechRecognition: new () => AnyRecognition;
  }
}

export function ChatInput({ onSend, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");
  const [listening, setListening] = useState(false);
  const recRef = useRef<AnyRecognition | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMic = useCallback(() => {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }

    const SpeechRec =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const rec = new SpeechRec();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.continuous = false;

    rec.onstart = () => setListening(true);
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setValue((prev) => (prev ? `${prev} ${transcript}` : transcript));
      setListening(false);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    rec.start();
    recRef.current = rec;
  }, [listening]);

  return (
    <div className="relative flex items-end gap-2 px-3 py-3 bg-[#0b0f1e] border-t border-white/[0.05]">
      {/* Voice button */}
      <button
        onClick={toggleMic}
        disabled={disabled}
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all focus:outline-none",
          listening
            ? "bg-red-500/20 border border-red-500/40 text-red-400 animate-pulse"
            : "bg-white/[0.04] border border-white/[0.07] text-white/40 hover:text-violet-400 hover:border-violet-500/30 hover:bg-violet-500/10"
        )}
        title={listening ? "Stop listening" : "Voice input"}
      >
        {listening ? (
          <MicOff className="w-4 h-4" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </button>

      {/* Text area */}
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          disabled={disabled}
          placeholder={placeholder || "Ask anything about your data…"}
          rows={1}
          className={cn(
            "w-full resize-none bg-white/[0.04] border border-white/[0.08] rounded-xl",
            "px-3.5 py-2 pr-10 text-sm text-slate-200 placeholder:text-white/25",
            "focus:outline-none focus:border-indigo-500/50 focus:bg-white/[0.05]",
            "transition-all scrollbar-none",
            "disabled:opacity-40 disabled:cursor-not-allowed"
          )}
          style={{ maxHeight: 140, lineHeight: "1.5" }}
        />
      </div>

      {/* Send button */}
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all",
          "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-900/30",
          "disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none disabled:hover:bg-indigo-600"
        )}
        title="Send"
      >
        {disabled ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
