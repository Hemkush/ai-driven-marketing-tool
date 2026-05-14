import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";

const COMMANDS = [
  { id: "projects",      label: "Business Profile",        path: "/projects",      group: "Navigate" },
  { id: "questionnaire", label: "Marketing Discovery",     path: "/questionnaire", group: "Navigate" },
  { id: "analysis",      label: "Competitive Benchmarking",path: "/analysis",      group: "Navigate" },
  { id: "positioning",   label: "Positioning",             path: "/positioning",   group: "Navigate" },
  { id: "personas",      label: "Personas",                path: "/personas",      group: "Navigate" },
  { id: "research",      label: "Research",                path: "/research",      group: "Navigate" },
  { id: "roadmap",       label: "Roadmap",                 path: "/roadmap",       group: "Navigate" },
  { id: "content",       label: "Content Studio",          path: "/content",       group: "Navigate" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const backdropRef = useRef(null);

  useEffect(() => {
    const handleKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        setQuery("");
        setSelected(0);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => inputRef.current?.focus(), 30);
      return () => clearTimeout(t);
    }
  }, [open]);

  const filtered = query.trim()
    ? COMMANDS.filter((c) =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.group.toLowerCase().includes(query.toLowerCase())
      )
    : COMMANDS;

  const handleSelect = (item) => {
    setOpen(false);
    navigate(item.path);
  };

  if (!open) return null;

  return (
    <div
      className="cp-backdrop"
      ref={backdropRef}
      onClick={(e) => { if (e.target === backdropRef.current) setOpen(false); }}
      role="dialog"
      aria-label="Command palette"
      aria-modal="true"
    >
      <div className="cp-panel">
        <div className="cp-search-row">
          <Search size={16} strokeWidth={2} className="cp-search-icon" />
          <input
            ref={inputRef}
            className="cp-input"
            placeholder="Go to page…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelected(0); }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setSelected((s) => Math.min(s + 1, filtered.length - 1));
              }
              if (e.key === "ArrowUp") {
                e.preventDefault();
                setSelected((s) => Math.max(s - 1, 0));
              }
              if (e.key === "Enter" && filtered[selected]) {
                handleSelect(filtered[selected]);
              }
            }}
          />
          <kbd className="cp-esc-key">ESC</kbd>
        </div>

        <div className="cp-divider" />

        <div className="cp-results" role="listbox">
          {filtered.length === 0 && (
            <div className="cp-empty">No results for &ldquo;{query}&rdquo;</div>
          )}
          {filtered.map((item, i) => (
            <button
              key={item.id}
              role="option"
              aria-selected={i === selected}
              className={`cp-result${i === selected ? " cp-result-selected" : ""}`}
              onMouseEnter={() => setSelected(i)}
              onClick={() => handleSelect(item)}
            >
              <span className="cp-result-group">{item.group}</span>
              <span className="cp-result-label">{item.label}</span>
            </button>
          ))}
        </div>

        <div className="cp-footer">
          <span className="cp-footer-hint"><kbd>↑↓</kbd> navigate</span>
          <span className="cp-footer-hint"><kbd>↵</kbd> open</span>
          <span className="cp-footer-hint"><kbd>⌘K</kbd> toggle</span>
        </div>
      </div>
    </div>
  );
}
