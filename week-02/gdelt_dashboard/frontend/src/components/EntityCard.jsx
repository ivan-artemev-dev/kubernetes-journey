import { Link } from "react-router-dom";

export default function EntityCard({ type, name, count }) {
  return (
    <Link className="entity-card" to={`/entity/${type}/${encodeURIComponent(name)}`}>
      <span className="entity-name">{name}</span>
      <span className="entity-count">{count}</span>
    </Link>
  );
}
