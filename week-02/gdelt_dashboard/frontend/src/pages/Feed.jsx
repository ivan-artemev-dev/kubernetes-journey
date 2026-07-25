import { useEffect, useState } from "react";
import api from "../api.js";
import FeedItem from "../components/FeedItem.jsx";

const SIZE = 50;

export default function Feed() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get("/feed", { params: { page, size: SIZE } })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / SIZE)) : 1;

  return (
    <div>
      <h1 className="page-title">Лента публикаций</h1>
      {error && <div className="error-box">Ошибка загрузки: {error}</div>}
      <div className="panel">
        {loading && <div className="loading">Загрузка...</div>}
        {!loading && data && data.items.length === 0 && <div className="empty">Публикаций не найдено</div>}
        {!loading && data && data.items.map((doc) => <FeedItem key={doc.record_id} doc={doc} />)}
      </div>
      {data && (
        <div className="pagination">
          <button className="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Назад
          </button>
          <span className="muted">
            Страница {page} из {totalPages} (всего {data.total.toLocaleString("ru-RU")})
          </span>
          <button className="secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Вперёд
          </button>
        </div>
      )}
    </div>
  );
}
