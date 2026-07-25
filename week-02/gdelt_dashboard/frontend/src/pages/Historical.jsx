import { useEffect, useState } from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import api from "../api.js";
import { formatGdeltDay } from "../utils.js";

const DAY_OPTIONS = [7, 30, 90];

export default function Historical() {
  const [days, setDays] = useState(30);
  const [country, setCountry] = useState("");
  const [theme, setTheme] = useState("");
  const [applied, setApplied] = useState({ country: "", theme: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get("/historical", {
        params: { days, country: applied.country || undefined, theme: applied.theme || undefined },
      })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [days, applied]);

  function handleSubmit(e) {
    e.preventDefault();
    setApplied({ country, theme });
  }

  return (
    <div>
      <h1 className="page-title">Исторические графики</h1>

      <div className="toolbar">
        {DAY_OPTIONS.map((d) => (
          <button key={d} className={"ghost" + (days === d ? " active" : "")} onClick={() => setDays(d)}>
            {d} дней
          </button>
        ))}
      </div>

      <form className="toolbar panel" onSubmit={handleSubmit}>
        <div className="field">
          <label>Страна (код FIPS)</label>
          <input value={country} onChange={(e) => setCountry(e.target.value)} placeholder="например: UK" />
        </div>
        <div className="field">
          <label>Тема (код)</label>
          <input value={theme} onChange={(e) => setTheme(e.target.value)} placeholder="например: PROTEST" />
        </div>
        <button type="submit">Применить фильтр</button>
      </form>

      {error && <div className="error-box">Ошибка: {error}</div>}
      {loading && <div className="loading">Загрузка...</div>}

      {!loading && data && (
        <div className="grid-2">
          <div className="panel">
            <div className="section-title">Количество публикаций по дням</div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatGdeltDay} />
                <YAxis />
                <Tooltip labelFormatter={formatGdeltDay} />
                <Line type="monotone" dataKey="count" name="Публикаций" stroke="#2f5fdb" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <div className="section-title">Средняя тональность по дням</div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatGdeltDay} />
                <YAxis />
                <Tooltip labelFormatter={formatGdeltDay} />
                <Line type="monotone" dataKey="avg_tone" name="Средняя тональность" stroke="#d1373f" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
