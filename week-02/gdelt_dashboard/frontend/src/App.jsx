import { NavLink, Route, Routes } from "react-router-dom";
import Feed from "./pages/Feed.jsx";
import Search from "./pages/Search.jsx";
import Entity from "./pages/Entity.jsx";
import Trends from "./pages/Trends.jsx";
import Map from "./pages/Map.jsx";
import GCAM from "./pages/GCAM.jsx";
import Historical from "./pages/Historical.jsx";

const navLinkClass = ({ isActive }) => "nav-link" + (isActive ? " active" : "");

export default function App() {
  return (
    <div className="app-shell">
      <nav className="navbar">
        <span className="brand">GDELT Аналитика</span>
        <NavLink to="/" end className={navLinkClass}>
          Лента
        </NavLink>
        <NavLink to="/search" className={navLinkClass}>
          Поиск
        </NavLink>
        <NavLink to="/trends" className={navLinkClass}>
          Тренды
        </NavLink>
        <NavLink to="/gcam" className={navLinkClass}>
          GCAM
        </NavLink>
        <NavLink to="/map" className={navLinkClass}>
          Карта
        </NavLink>
        <NavLink to="/historical" className={navLinkClass}>
          История
        </NavLink>
      </nav>
      <div className="content">
        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/search" element={<Search />} />
          <Route path="/entity/:type/:name" element={<Entity />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/gcam" element={<GCAM />} />
          <Route path="/map" element={<Map />} />
          <Route path="/historical" element={<Historical />} />
        </Routes>
      </div>
    </div>
  );
}
