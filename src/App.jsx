import { useState } from "react";
import reactLogo from "./assets/react.svg";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

function App() {
  const [tabs, setTabs] = useState([{ id: 1, title: "New Tab", url: "/home.html" }]);
  const [activeTabId, setActiveTabId] = useState(1);

  const handleAddTab = () => {
    const newId = Date.now();
    const newTab = { id: newId, title: "New Tab", url: "/home.html" };
    setTabs([...tabs, newTab]);
    setActiveTabId(newId);
  };

  const handleCloseTab = (e, id) => {
    e.stopPropagation(); // Prevent activating the tab when closing
    const newTabs = tabs.filter(t => t.id !== id);
    if (newTabs.length === 0) {
      // Logic for when last tab is closed: keep one or show empty state?
      // For browser-like feel, often closing last window closes app, but here we probably want at least one tab or a "News Tab" page. 
      // Let's just create a new fresh tab if all are closed for now, or prevent closing the last one.
      // OPTION: Create a new tab.
      const newId = Date.now();
      setTabs([{ id: newId, title: "New Tab", url: "/home.html" }]);
      setActiveTabId(newId);
    } else {
      setTabs(newTabs);
      if (activeTabId === id) {
        // If we closed the active tab, switch to the last one
        setActiveTabId(newTabs[newTabs.length - 1].id);
      }
    }
  };

  return (
    <main className="app-container">
      {/* Tab Bar */}
      <div className="tab-bar">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={`tab ${activeTabId === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTabId(tab.id)}
          >
            <span className="tab-title">{tab.title}</span>
            <button
              className="close-tab-btn"
              onClick={(e) => handleCloseTab(e, tab.id)}
              title="Close Tab"
            >
              &times;
            </button>
          </div>
        ))}
        <button className="add-tab-btn" onClick={handleAddTab} title="New Tab">
          +
        </button>
      </div>

      {/* Tab Content (Iframes) */}
      <div className="tab-content">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className="iframe-container"
            style={{ display: activeTabId === tab.id ? 'flex' : 'none' }}
          >
            <iframe
              src={tab.url}
              title={`Tab ${tab.id}`}
              onLoad={(e) => {
                try {
                  const title = e.target.contentDocument.title;
                  if (title) {
                    setTabs(prevTabs => prevTabs.map(t =>
                      t.id === tab.id ? { ...t, title: title } : t
                    ));
                  }
                } catch (err) {
                  console.warn("Could not read iframe title (likely cross-origin):", err);
                }
              }}
            />
          </div>
        ))}
      </div>
    </main>
  );
}

export default App;
