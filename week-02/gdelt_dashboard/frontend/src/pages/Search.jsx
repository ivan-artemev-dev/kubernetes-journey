import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../api.js";
import FeedItem from "../components/FeedItem.jsx";
import { gdeltToInputDate, inputDateToGdelt } from "../utils.js";

const SIZE = 50;

const TYPE_LABELS = {
  person: "Персона",
  org: "Организация",
  theme: "Тема",
  country: "Страна (код)",
  source: "Источник",
  url: "URL (ключевое слово)",
};

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const type = searchParams.get("type") || "person";
  const q = searchParams.get("q") || "";
  const from = searchParams.get("from") || "";
  const to = searchParams.get("to") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);

  const [typeDraft, setTypeDraft] = useState(type);
  const [qDraft, setQDraft] = useState(q);
  const [fromDraft, setFromDraft] = useState(from);
  const [toDraft, setToDraft] = useState(to);

  useEffect(() => {
    setTypeDraft(type);
    setQDraft(q);
    setFromDraft(from);
    setToDraft(to);
  }, [type, q, from, to]);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!q) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    api
      .get("/search", { params: { q, type, from: from || undefined, to: to || undefined, page, size: SIZE } })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [q, type, from, to, page]);

  function buildParams(overrides) {
    const params = { type, q, page: "1" };
    if (from) params.from = from;
    if (to) params.to = to;
    return { ...params, ...overrides };
  }

  function handleSubmit(e) {
    e.preventDefault();
    const params = { type: typeDraft, q: qDraft, page: "1" };
    if (fromDraft) params.from = fromDraft;
    if (toDraft) params.to = toDraft;
    setSearchParams(params);
  }

  function goPage(p) {
    setSearchParams(buildParams({ page: String(p) }));
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / SIZE)) : 1;

  return (
    <div>
      <h1 className="page-title">Поиск</h1>
      <form className="toolbar panel" onSubmit={handleSubmit}>
        <div className="field">
          <label>Тип</label>
          <select value={typeDraft} onChange={(e) => setTypeDraft(e.target.value)}>
            {Object.entries(TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Запрос</label>
          <input value={qDraft} onChange={(e) => setQDraft(e.target.value)} placeholder="например: biden" required />
        </div>
        <div className="field">
          <label>С даты</label>
          <input
            type="date"
            value={gdeltToInputDate(fromDraft)}
            onChange={(e) => setFromDraft(inputDateToGdelt(e.target.value))}
          />
        </div>
        <div className="field">
          <label>По дату</label>
          <input
            type="date"
            value={gdeltToInputDate(toDraft)}
            onChange={(e) => setToDraft(inputDateToGdelt(e.target.value, true))}
          />
        </div>
        <button type="submit">Искать</button>
      </form>

      {type === "url" && !from && !to && q && (
        <div className="muted" style={{ marginBottom: 12 }}>
          Поиск по URL без указания периода ограничивается последними 24 часами (поле URL не индексируется в
          Elasticsearch).
        </div>
      )}

      {error && <div className="error-box">Ошибка: {error}</div>}

      <div className="panel">
        {!q && <div className="empty">Введите запрос для поиска</div>}
        {loading && <div className="loading">Загрузка...</div>}
        {!loading && data && data.items.length === 0 && <div className="empty">Ничего не найдено</div>}
        {!loading && data && data.items.map((doc) => <FeedItem key={doc.record_id} doc={doc} />)}
      </div>

      {data && data.items.length > 0 && (
        <div className="pagination">
          <button className="secondary" disabled={page <= 1} onClick={() => goPage(page - 1)}>
            Назад
          </button>
          <span className="muted">
            Страница {page} из {totalPages} (найдено {data.total.toLocaleString("ru-RU")})
          </span>
          <button className="secondary" disabled={page >= totalPages} onClick={() => goPage(page + 1)}>
            Вперёд
          </button>
        </div>
      )}

      {(type === "person" || type === "org") && q && (
        <div className="panel">
          <Link to={`/entity/${type}/${encodeURIComponent(q)}`}>Открыть аналитику по «{q}» →</Link>
        </div>
      )}
    </div>
  );
}
