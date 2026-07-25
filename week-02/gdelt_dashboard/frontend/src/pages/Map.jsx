import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip as LeafletTooltip } from "react-leaflet";
import api from "../api.js";
import FeedItem from "../components/FeedItem.jsx";
import { gdeltToInputDate, inputDateToGdelt } from "../utils.js";

function radiusForCount(count) {
  return Math.min(30, 4 + Math.sqrt(count) * 0.05);
}

export default function Map() {
  const [theme, setTheme] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [applied, setApplied] = useState({ theme: "", from: "", to: "" });

  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selected, setSelected] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [selectedLoading, setSelectedLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get("/map", {
        params: {
          theme: applied.theme || undefined,
          from: applied.from || undefined,
          to: applied.to || undefined,
        },
      })
      .then((res) => setPoints(res.data.points))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [applied]);

  function handleSubmit(e) {
    e.preventDefault();
    setApplied({ theme, from, to });
  }

  function handleMarkerClick(point) {
    setSelected(point);
    setSelectedLoading(true);
    api
      .get("/map/point", {
        params: {
          lat: point.lat,
          lon: point.lon,
          radius_km: 100,
          from: applied.from || undefined,
          to: applied.to || undefined,
        },
      })
      .then((res) => setSelectedItems(res.data.items))
      .finally(() => setSelectedLoading(false));
  }

  return (
    <div>
      <h1 className="page-title">Карта публикаций</h1>

      <form className="toolbar panel" onSubmit={handleSubmit}>
        <div className="field">
          <label>Тема (код)</label>
          <input value={theme} onChange={(e) => setTheme(e.target.value)} placeholder="например: PROTEST" />
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

      {error && <div className="error-box">Ошибка: {error}</div>}
      {loading && <div className="loading">Загрузка...</div>}

      <div className="map-wrap">
        <MapContainer center={[20, 10]} zoom={2} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {points.map((p, i) => (
            <CircleMarker
              key={i}
              center={[p.lat, p.lon]}
              radius={radiusForCount(p.count)}
              pathOptions={{ color: "#2f5fdb", fillColor: "#2f5fdb", fillOpacity: 0.5 }}
              eventHandlers={{ click: () => handleMarkerClick(p) }}
            >
              <LeafletTooltip>
                {p.name || "—"}: {p.count.toLocaleString("ru-RU")} публикаций
              </LeafletTooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {selected && (
        <div className="panel" style={{ marginTop: 16 }}>
          <div className="section-title">
            Публикации рядом с «{selected.name || "выбранная точка"}» ({selected.count.toLocaleString("ru-RU")} всего в
            этой точке на карте)
          </div>
          {selectedLoading && <div className="loading">Загрузка...</div>}
          {!selectedLoading && selectedItems.length === 0 && <div className="empty">Публикации не найдены</div>}
          {!selectedLoading && selectedItems.map((doc) => <FeedItem key={doc.record_id} doc={doc} />)}
        </div>
      )}
    </div>
  );
}
