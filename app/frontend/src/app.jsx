// app/frontend/src/App.jsx
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import AnalyticsPage from "./components/dashboard/AnalyticsPage";
import Header from "./components/navigation/Header";
import Sidebar from "./components/navigation/SidebarMenu";
import SplashMenu from "./components/navigation/SplashMenu";

export default function App() {
  const { t, i18n } = useTranslation();

  // Top-level workspace mode: "study" renders SplashMenu; "dashboard" renders full-screen analytics[cite: 31, 32].
  const [workspaceView, setWorkspaceView] = useState("study");

  useEffect(() => {
    document.title = t("siteTitle");
  }, [i18n.language, t]);

  const handleOpenDashboard = () => {
    setWorkspaceView("dashboard");
  };

  const handleReturnToStudy = () => {
    setWorkspaceView("study");
  };

  return (
    <div className="App min-h-screen">
      <div className="relative w-full min-h-full">
        <Header />

        {/* Sidebar triggers full-screen dashboard mode instead of opening a cramped modal tab[cite: 27, 30]. */}
        <Sidebar
          onSelectDashboard={handleOpenDashboard}
          isDashboardActive={workspaceView === "dashboard"}
        />

        {workspaceView === "dashboard" ? (
          <AnalyticsPage onBackToWorkspace={handleReturnToStudy} />
        ) : (
          <SplashMenu />
        )}
      </div>
    </div>
  );
}
