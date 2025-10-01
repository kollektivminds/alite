import React from "react";
import { useTranslation } from "react-i18next";
import { useEffect } from "react";
import SplashMenu from "./components/navigation/SplashMenu";
import { preferencesStore } from "./state/usePreferencesStore";
import Sidebar from "./components/navigation/SidebarMenu";
import Header from "./components/navigation/Header";

console.log("At app level:", preferencesStore.getState());

function App() {
  console.log("App is rendering");

  const { t, i18n } = useTranslation();

  useEffect(() => {
    // Update the document title on language change
    document.title = t("site_title");
  }, [i18n.language, t]);

  return (
    <div className="App">
      <div className="relative w-full h-screen">
        <Header />
        <Sidebar />
        <SplashMenu />
      </div>
    </div>
  );
}
// console.log("Is this logging?");
export default App;
