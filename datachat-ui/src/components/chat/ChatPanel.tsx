"use client";

import { useEffect, useRef } from "react";
import { useStore } from "@/lib/store";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { MessageSquarePlus, Sparkles } from "lucide-react";

export function ChatPanel() {
  const { messages, isLoading, sendMessage } = useStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full bg-[#0b0f1e]">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.05] shrink-0">
        <MessageSquarePlus className="w-4 h-4 text-indigo-400" />
        <h2 className="text-sm font-semibold text-white/80">Conversation</h2>
        <span className="ml-auto text-[10px] text-white/25 font-mono">
          {messages.length} msg{messages.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4 py-12">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600/20 to-violet-600/20 border border-indigo-500/20 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <p className="text-white/60 text-sm font-medium">
                Ask anything about your data
              </p>
              <p className="text-white/25 text-xs mt-1">
                Charts, metrics, summaries — powered by Gemini AI
              </p>
            </div>
            <div className="grid grid-cols-1 gap-1.5 w-full max-w-xs mt-2">
              {[
                "Show total sales by region",
                "What are the top 10 products?",
                "How many nulls in each column?",
              ].map((hint) => (
                <button
                  key={hint}
                  onClick={() => sendMessage(hint)}
                  className="text-left text-xs px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-white/40 hover:text-white/70 hover:bg-white/[0.06] transition-all"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-white/[0.05] border border-white/[0.08] flex items-center justify-center">
              <div className="w-3 h-3 rounded-full border-2 border-blue-400/50 border-t-blue-400 animate-spin" />
            </div>
            <div className="bg-white/[0.04] border border-white/[0.07] rounded-2xl rounded-tl-sm px-3.5 py-2.5">
              <div className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0">
        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="e.g. Total claims of 2023, Top 10 insurers…"
        />
      </div>
    </div>
  );
}
