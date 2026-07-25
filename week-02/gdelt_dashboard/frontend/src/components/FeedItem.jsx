import ToneBar from "./ToneBar.jsx";
import ThemeTag from "./ThemeTag.jsx";
import { formatGdeltDateTime } from "../utils.js";

export default function FeedItem({ doc }) {
  const themes = doc.themes || [];
  const themesRu = doc.themes_ru || [];
  return (
    <div className="feed-item">
      <div className="feed-item-header">
        <span className="feed-source">{doc.source_name}</span>
        <div className="feed-meta">
          <span>{formatGdeltDateTime(doc.date)}</span>
          {doc.country_ru && <span>{doc.country_ru}</span>}
          <ToneBar value={doc.tone?.tone} />
        </div>
      </div>
      <a className="feed-url" href={doc.url} target="_blank" rel="noreferrer">
        {doc.url}
      </a>
      <div className="theme-tags">
        {themesRu.map((name, i) => (
          <ThemeTag key={i} code={themes[i] || name} nameRu={name} />
        ))}
      </div>
    </div>
  );
}
