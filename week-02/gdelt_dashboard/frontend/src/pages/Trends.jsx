import { useEffect, useState, useCallback } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import api from "../api.js";
import EntityCard from "../components/EntityCard.jsx";

const PERIODS = [
  { value: "24h", label: "24 часа" },
  { value: "7d", label: "7 дней" },
  { value: "30d", label: "30 дней" },
];

const REFRESH_MS = 15 * 60 * 1000;

export default function Trends() {
  const [period, setPeriod] = useState("24h");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .get("/trends", { params: { period } })
      .then((res) => {
        setData(res.data);
        setUpdatedAt(new Date());
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [period]);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => clearInterval(timer);
  }, [load]);

  return (
    <div>
      <h1 className="page-title">Топ трендов</h1>

      <div className="toolbar">
        {PERIODS.map((p) => (
          <button key={p.value} className={"ghost" + (period === p.value ? " active" : "")} onClick={() => setPeriod(p.value)}>
            {p.label}
          </button>
        ))}
        <button className="secondary" onClick={load}>
          Обновить
        </button>
        {updatedAt && <span className="muted">Обновлено: {updatedAt.toLocaleTimeString("ru-RU")}</span>}
      </div>

      {error && <div className="error-box">Ошибка: {error}</div>}
      {loading && !data && <div className="loading">Загрузка...</div>}

      {data && (
        <>
          <div className="panel">
            <div className="section-title">Топ-20 организаций</div>
            <div className="entity-grid">
              {data.top_organizations.map((o) => (
                <EntityCard key={o.name} type="org" name={o.name} count={o.count} />
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="section-title">Топ-20 персон</div>
            <div className="entity-grid">
              {data.top_persons.map((p) => (
                <EntityCard key={p.name} type="person" name={p.name} count={p.count} />
              ))}
            </div>
          </div>

          <div className="grid-2">
            <div className="panel">
              <div className="section-title">Топ-10 тем</div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.top_themes} layout="vertical" margin={{ left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name_ru" width={170} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Публикаций" fill="#2f5fdb" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <div className="section-title">Топ-10 стран</div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.top_countries} layout="vertical" margin={{ left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name_ru" width={140} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Публикаций" fill="#1f9d55" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
