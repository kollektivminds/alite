import React from 'react';
import { create } from 'zustand';
import { shallow } from 'zustand/shallow';

// ====================================================================
// 1. A minimal, self-contained Zustand store. No persistence.
// ====================================================================
const useDebugStore = create((set) => ({
  language: 'en',
  theme: 'light',
  setLanguage: (lang) => {
    console.log(`STORE: Setting language to '${lang}'`);
    set({ language: lang });
  },
  setTheme: (theme) => {
    console.log(`STORE: Setting theme to '${theme}'`);
    set({ theme: theme });
  },
}));


// ====================================================================
// 2. A simple component that uses this store.
//    It does NOT use i18next or any other library.
// ====================================================================
function SettingsTest() {
  console.log('RENDER: SettingsTest is rendering...');
  
  const { language, setLanguage, theme, setTheme } = useDebugStore(
    (state) => ({
      language: state.language,
      setLanguage: state.setLanguage,
      theme: state.theme,
      setTheme: state.setTheme,
    }),
    shallow
  );

  return (
    <div style={{ padding: '2rem', border: '2px solid blue', fontFamily: 'sans-serif' }}>
      <h2>Debug Component</h2>
      <p>This is a test to isolate the state management loop.</p>
      
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="lang-test">Language: </label>
        <select
          id="lang-test"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="en">English</option>
          <option value="ru">Russian</option>
        </select>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="theme-test">Theme: </label>
        <select
          id="theme-test"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      
      <h3>Current State:</h3>
      <p>Language: {language}</p>
      <p>Theme: {theme}</p>
    </div>
  );
}

// ====================================================================
// 3. Export a single component to render for the test.
// ====================================================================
export default function DebugPage() {
  return <SettingsTest />;
}