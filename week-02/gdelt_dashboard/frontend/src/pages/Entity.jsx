import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import api from "../api.js";
import FeedItem from "../components/FeedItem.jsx";
import { formatGdeltDayShort } from "../utils.js";

const DAY_OPTIONS = [7, 30, 90];

export default function Entity() {
  const { type, name } = useParams();
  const decodedName = decodeURIComponent(name);
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get(`/entity/${type}/${encodeURIComponent(decodedName)}`, { params: { days } })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [type, decodedName, days]);

  const typeLabel = type === "person" ? "Персона" : "Организация";

  return (
    <div>
      <h1 className="page-title">
        {typeLabel}: {decodedName}
      </h1>

      <div className="toolbar">
        {DAY_OPTIONS.map((d) => (
          <button key={d} className={"ghost" + (days === d ? " active" : "")} onClick={() => setDays(d)}>
            {d} дней
          </button>
        ))}
      </div>

      {error && <div className="error-box">Ошибка: {error}</div>}
      {loading && <div className="loading">Загрузка...</div>}

      {!loading && data && (
        <>
          <div className="stat-row">
            <div className="stat-tile">
              <div className="label">Упоминаний за период</div>
              <div className="value">{data.total.toLocaleString("ru-RU")}</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="panel">
              <div className="section-title">Тональность по дням</div>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={data.by_day}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatGdeltDayShort} />
                  <YAxis />
                  <Tooltip labelFormatter={formatGdeltDayShort} />
                  <Line type="monotone" dataKey="avg_tone" name="Средняя тональность" stroke="#2f5fdb" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <div className="section-title">Количество упоминаний по дням</div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={data.by_day}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatGdeltDayShort} />
                  <YAxis />
                  <Tooltip labelFormatter={formatGdeltDayShort} />
                  <Bar dataKey="count" name="Упоминания" fill="#2f5fdb" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid-2">
            <div className="panel">
              <div className="section-title">Топ тем</div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.top_themes} layout="vertical" margin={{ left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name_ru" width={160} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Публикаций" fill="#2f5fdb" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <div className="section-title">Топ источников</div>
              {data.top_sources.map((s) => (
                <div className="list-row" key={s.source}>
                  <span>{s.source}</span>
                  <span className="muted">{s.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="section-title">Топ стран</div>
            {data.top_countries.map((c) => (
              <div className="list-row" key={c.code}>
                <span>{c.name_ru}</span>
                <span className="muted">{c.count}</span>
              </div>
            ))}
          </div>

          <div className="panel">
            <div className="section-title">Последние публикации</div>
            {data.recent.map((doc) => (
              <FeedItem key={doc.record_id} doc={doc} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
