"use client";

import { useEffect } from "react";
import { useStore } from "@/lib/store";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { DashboardPanel } from "@/components/dashboard/DashboardPanel";
import { UploadModal } from "@/components/upload/UploadModal";
import { Topbar } from "@/components/layout/Topbar";

export default function Home() {
  const { init, uploadOpen } = useStore();

  useEffect(() => {
    init();
  }, [init]);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#080c18]">
      <Topbar />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <div className="flex flex-1 min-w-0 divide-x divide-white/[0.05]">
          <div className="w-[360px] shrink-0 flex flex-col min-h-0">
            <ChatPanel />
          </div>
          <div className="flex-1 min-w-0 flex flex-col">
            <DashboardPanel />
          </div>
        </div>
      </div>
      {uploadOpen && <UploadModal />}
    </div>
  );
}

