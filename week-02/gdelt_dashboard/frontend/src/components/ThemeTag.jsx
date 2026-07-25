import { Link } from "react-router-dom";

export default function ThemeTag({ code, nameRu }) {
  return (
    <Link className="theme-tag" to={`/search?type=theme&q=${encodeURIComponent(code)}`} title={code}>
      {nameRu || code}
    </Link>
  );
}
