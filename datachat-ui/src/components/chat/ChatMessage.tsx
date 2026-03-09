"use client";

import { cn } from "@/lib/utils";
import type { ChatMessage as Msg } from "@/lib/types";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  message: Msg;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-2.5", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5",
          isUser
            ? "bg-gradient-to-br from-indigo-500 to-violet-600"
            : "bg-white/[0.05] border border-white/[0.08]"
        )}
      >
        {isUser ? (
          <User className="w-3.5 h-3.5 text-white" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-blue-400" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-gradient-to-br from-indigo-600 to-violet-700 text-white rounded-tr-sm shadow-lg shadow-indigo-900/20"
            : "bg-white/[0.04] border border-white/[0.07] text-slate-300 rounded-tl-sm"
        )}
      >
        {isUser ? (
          <p>{message.text}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-strong:text-white">
            <ReactMarkdown>{message.text}</ReactMarkdown>
          </div>
        )}
        <p
          className={cn(
            "text-[10px] mt-1 font-mono",
            isUser ? "text-indigo-200/60 text-right" : "text-white/25"
          )}
        >
          {message.time}
        </p>
      </div>
    </div>
  );
}
