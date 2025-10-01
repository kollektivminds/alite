import useSidebarPosition from "@/hooks/useSidebarPosition";
import { Button } from "@/components/ui/button";
import { DashboardModal, InfoModal, FeedbackModal } from "@/components/modals";
import { MoveLeft, MoveRight, MoveDown, LayoutDashboard, Info, MessageSquare } from "lucide-react";
import { useState } from "react";

export default function Sidebar() {
  const [position, setPosition] = useSidebarPosition();
  const [activeModal, setActiveModal] = useState(null);

  const positions = {
    left: "left-0 top-0 h-full flex-col",
    right: "right-0 top-0 h-full flex-col",
    bottom: "bottom-0 left-0 w-full flex-row",
  };

  return (
    <div className={`fixed ${positions[position]} bg-gray-800 p-4 flex items-center justify-center z-50`}>
      {/* Move buttons */}
      <div className="absolute top-2 flex space-x-2">
        <Button onClick={() => setPosition("left")} size="icon" variant="ghost"><MoveLeft /></Button>
        <Button onClick={() => setPosition("right")} size="icon" variant="ghost"><MoveRight /></Button>
        <Button onClick={() => setPosition("bottom")} size="icon" variant="ghost"><MoveDown /></Button>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col space-y-4">
        <Button onClick={() => setActiveModal("dashboard")} size="icon"><LayoutDashboard /></Button>
        <Button onClick={() => setActiveModal("info")} size="icon"><Info /></Button>
        <Button onClick={() => setActiveModal("about")} size="icon"><Info /></Button>
        <Button onClick={() => setActiveModal("feedback")} size="icon"><MessageSquare /></Button>
      </div>

      {/* Modals */}
      <DashboardModal open={activeModal === "dashboard"} onClose={() => setActiveModal(null)} />
      <InfoModal open={activeModal === "info"} onClose={() => setActiveModal(null)} />
      <AboutModal open={activeModal === "about"} onClose={() => setActiveModal(null)} />
      <FeedbackModal open={activeModal === "feedback"} onClose={() => setActiveModal(null)} />
    </div>
  );
}
