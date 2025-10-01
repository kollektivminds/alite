// A custom hook to persist sidebar position in localStorage (optional enhancement)
import { useState, useEffect } from "react";

export default function useSidebarPosition() {
  const [position, setPosition] = useState({ top: 100, left: 0 });

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("sidebarPosition"));
    if (saved) setPosition(saved);
  }, []);

  const updatePosition = (newPosition) => {
    setPosition(newPosition);
    localStorage.setItem("sidebarPosition", JSON.stringify(newPosition));
  };

  return [position, updatePosition];
}
