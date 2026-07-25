import { useEffect, useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import api from "../api.js";
import { gdeltToInputDate, inputDateToGdelt } from "../utils.js";

export default function GCAM() {
  const [country, setCountry] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [applied, setApplied] = useState({ country: "", from: "", to: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get("/gcam/summary", {
        params: {
          country: applied.country || undefined,
          from: applied.from || undefined,
          to: applied.to || undefined,
        },
      })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [applied]);

  function handleSubmit(e) {
    e.preventDefault();
    setApplied({ country, from, to });
  }

  const grouped = {};
  if (data) {
    for (const m of data.metrics) {
      grouped[m.category] = grouped[m.category] || [];
      grouped[m.category].push(m);
    }
  }

  return (
    <div>
      <h1 className="page-title">GCAM: расшифровка эмоциональных метрик</h1>

      <form className="toolbar panel" onSubmit={handleSubmit}>
        <div className="field">
          <label>Код страны (FIPS)</label>
          <input value={country} onChange={(e) => setCountry(e.target.value)} placeholder="например: UK" />
        </div>
        <div className="field">
          <label>С даты</label>
          <input type="date" value={gdeltToInputDate(from)} onChange={(e) => setFrom(inputDateToGdelt(e.target.value))} />
        </div>
        <div className="field">
          <label>По дату</label>
          <input type="date" value={gdeltToInputDate(to)} onChange={(e) => setTo(inputDateToGdelt(e.target.value, true))} />
        </div>
        <button type="submit">Показать</button>
      </form>

      {!applied.from && !applied.to && (
        <div className="muted" style={{ marginBottom: 12 }}>
          Без указания периода анализируются публикации за последние 24 часа (GCAM-поля не индексируются, полный скан
          был бы слишком медленным).
        </div>
      )}

      {error && <div className="error-box">Ошибка: {error}</div>}
      {loading && <div className="loading">Загрузка...</div>}

      {!loading && data && (
        <>
          <div className="stat-row">
            <div className="stat-tile">
              <div className="label">Документов в выборке</div>
              <div className="value">{data.total_docs.toLocaleString("ru-RU")}</div>
            </div>
          </div>

          {Object.keys(grouped).length === 0 && <div className="empty">Нет данных за выбранный период</div>}

          <div className="grid-2">
            {Object.entries(grouped).map(([category, items]) => (
              <div className="panel" key={category}>
                <div className="section-title">{category}</div>
                <ResponsiveContainer width="100%" height={Math.max(120, items.length * 40)}>
                  <BarChart data={items} layout="vertical" margin={{ left: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name_ru" width={170} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="avg_value" name="Среднее значение" fill="#2f5fdb" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
