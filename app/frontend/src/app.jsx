import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import Header from "./components/navigation/Header";
import Sidebar from "./components/navigation/SidebarMenu";
import SplashMenu from "./components/navigation/SplashMenu";
import { usePreferencesStore } from "./state/usePreferencesStore";

console.log("At app level:", usePreferencesStore.getState());

function App() {
  console.log("App is rendering");

  const { t, i18n } = useTranslation();

  useEffect(() => {
    document.title = t("siteTitle");
  }, [i18n.language, t]);

  return (
    <div className="App">
      <div className="relative w-full h-full">
        <Header />
        <Sidebar />
        <SplashMenu />
      </div>
    </div>
  );
}
export default App;
