"""
Справочники GDELT: темы, GCAM-метрики, коды стран.
Хранятся в SQLite (references.db), при отсутствии файла база строится
из встроенных словарей при первом импорте модуля.
"""
import os
import sqlite3
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "references.db")

# --- Темы GDELT GKG (наиболее частотные категории) -> русский перевод ---
THEMES = {
    "TAX_FNCACT": "Функциональная роль (общее)",
    "TAX_ETHNICITY": "Этническая принадлежность",
    "TAX_WORLDLANGUAGES": "Языки мира",
    "WB_832_ANTI_CORRUPTION": "Антикоррупция",
    "WB_678_CORRUPTION": "Коррупция",
    "ECON_STOCKMARKET": "Фондовый рынок",
    "ECON_INTERESTRATES": "Процентные ставки",
    "ECON_INFLATION": "Инфляция",
    "ECON_UNEMPLOYMENT": "Безработица",
    "ECON_BANKRUPTCY": "Банкротство",
    "ECON_SUBSIDIES": "Субсидии",
    "ECON_TRADE_DISPUTE": "Торговый спор",
    "ECON_FREETRADE": "Свободная торговля",
    "ECON_ENTREPRENEURSHIP": "Предпринимательство",
    "ECON_TAXATION": "Налогообложение",
    "ECON_COST_OF_LIVING": "Стоимость жизни",
    "BUS_MARKET_CLOSE": "Закрытие рынка",
    "BUS_MARKET_OPEN": "Открытие рынка",
    "BUS_STOCK_MARKET": "Фондовый рынок (бизнес)",
    "CRISISLEX_CRISISLEXREC": "Кризисная ситуация",
    "CRISISLEX_T03_DEAD": "Погибшие (кризис)",
    "CRISISLEX_T01_CERTAINTY": "Достоверность (кризис)",
    "TERROR": "Терроризм",
    "ARMEDCONFLICT": "Вооружённый конфликт",
    "MILITARY": "Военная тематика",
    "KILL": "Убийство",
    "ASSASSINATION": "Покушение",
    "KIDNAP": "Похищение",
    "TORTURE": "Пытки",
    "MASSACRE": "Массовое убийство",
    "GENOCIDE": "Геноцид",
    "PROTEST": "Протест",
    "RIOT": "Массовые беспорядки",
    "STRIKE": "Забастовка",
    "COUP": "Государственный переворот",
    "CEASEFIRE": "Прекращение огня",
    "PEACEKEEPING": "Миротворчество",
    "SANCTIONS": "Санкции",
    "REFUGEES": "Беженцы",
    "IMMIGRATION": "Иммиграция",
    "HUMAN_RIGHTS": "Права человека",
    "HUMAN_RIGHTS_ABUSES": "Нарушения прав человека",
    "FREESPEECH": "Свобода слова",
    "CENSORSHIP": "Цензура",
    "ELECTION": "Выборы",
    "ELECTION_FRAUD": "Фальсификация выборов",
    "GOVERNMENT": "Правительство",
    "CORRUPTION": "Коррупция",
    "LEGISLATION": "Законодательство",
    "CONSTITUTIONAL": "Конституционные вопросы",
    "JUDICIAL": "Судебная система",
    "TRIAL": "Судебный процесс",
    "ARREST": "Арест",
    "SECURITY_SERVICES": "Спецслужбы",
    "CYBER_ATTACK": "Кибератака",
    "TAX_DISEASE": "Заболевание",
    "MEDICAL": "Медицина",
    "PANDEMIC": "Пандемия",
    "EPIDEMIC": "Эпидемия",
    "VACCINATION": "Вакцинация",
    "HEALTH_PANDEMIC": "Пандемия (здравоохранение)",
    "ENV_CLIMATECHANGE": "Изменение климата",
    "ENV_DISASTER": "Экологическая катастрофа",
    "ENV_MINING": "Добыча полезных ископаемых",
    "ENV_OIL": "Нефтяная отрасль",
    "ENV_SOLAR": "Солнечная энергетика",
    "ENV_WIND": "Ветровая энергетика",
    "NATURAL_DISASTER": "Стихийное бедствие",
    "EARTHQUAKE": "Землетрясение",
    "FLOOD": "Наводнение",
    "WILDFIRE": "Лесной пожар",
    "DROUGHT": "Засуха",
    "HURRICANE": "Ураган",
    "SCIENCE": "Наука",
    "TECHNOLOGY": "Технологии",
    "SPACE": "Космос",
    "ARTIFICIAL_INTELLIGENCE": "Искусственный интеллект",
    "SOCIALMEDIA": "Социальные сети",
    "GENERAL_HEALTH": "Здравоохранение (общее)",
    "EDUCATION": "Образование",
    "RELIGION": "Религия",
    "SPORTS": "Спорт",
    "ENTERTAINMENT": "Развлечения",
    "DIPLOMACY": "Дипломатия",
    "TRADE": "Торговля",
    "AID": "Гуманитарная помощь",
    "DELAY": "Задержка",
    "LEADER": "Лидер",
    "WOMEN": "Женщины",
    "CHILDREN": "Дети",
    "LGBT": "ЛГБТ",
    "DISCRIMINATION": "Дискриминация",
    "POVERTY": "Бедность",
    "WATER_SECURITY": "Водная безопасность",
    "FOOD_SECURITY": "Продовольственная безопасность",
    "ENERGY": "Энергетика",
    "NUCLEAR": "Ядерная тематика",
    "WEAPONS": "Оружие",
    "ALLIANCE": "Альянс",
    "TREATY": "Договор",
    "UNGP_FORESTS_RIVERS_OCEANS": "Леса, реки и океаны",
    "SELF_IDENTIFIED_ENVIRON_DISASTER": "Экологическая катастрофа (самоидентиф.)",
    "SOC_POINTSOFINTEREST": "Достопримечательности",
    "MEDIA_MSM": "Традиционные СМИ",
    "MEDIA_SOCIAL": "Социальные СМИ",
    "USPEC_POLITICS_GENERAL1": "Политика (общее)",
    "USPEC_ETHNIC_MINORITIES": "Этнические меньшинства",
}

# --- Коды GCAM -> (русское название, категория) ---
GCAM = {
    "wc": ("Количество слов", "Общее"),
    "v10.1": ("Тональность документа", "Тональность"),
    "c1.1": ("Позитивная лексика (общая)", "Тональность"),
    "c1.2": ("Негативная лексика (общая)", "Тональность"),
    "c2.21": ("Позитивные эмоции (общие)", "Эмоции"),
    "c2.22": ("Негативные эмоции (общие)", "Эмоции"),
    "c2.76": ("Тревожность (Anxiety)", "Эмоции"),
    "c2.82": ("Гнев (Anger)", "Эмоции"),
    "c2.83": ("Грусть (Sadness)", "Эмоции"),
    "c2.100": ("Радость (Joy)", "Эмоции"),
    "c2.148": ("Позитивные эмоции", "Эмоции"),
    "c2.39": ("Негативные эмоции", "Эмоции"),
    "c2.126": ("Доверие (Trust)", "Эмоции"),
    "c2.135": ("Отвращение (Disgust)", "Эмоции"),
    "c2.141": ("Удивление (Surprise)", "Эмоции"),
    "c2.143": ("Страх (Fear)", "Эмоции"),
    "c9.767": ("Доминантность", "Психолингвистика"),
    "c9.10": ("Уверенность", "Психолингвистика"),
    "c16.57": ("Неопределённость", "Психолингвистика"),
    "c15.15": ("Экономическая тематика", "Тематика"),
    "c17.36": ("Военная тематика", "Тематика"),
    "c18.117": ("Политическая тематика", "Тематика"),
}

# --- Коды стран GDELT (FIPS 10-4) -> русское название ---
COUNTRIES = {
    "US": "США", "UK": "Великобритания", "GM": "Германия", "FR": "Франция",
    "IT": "Италия", "SP": "Испания", "PO": "Португалия", "NL": "Нидерланды",
    "BE": "Бельгия", "SW": "Швеция", "NO": "Норвегия", "DA": "Дания",
    "FI": "Финляндия", "PL": "Польша", "EZ": "Чехия", "LO": "Словакия",
    "HU": "Венгрия", "RO": "Румыния", "BU": "Болгария", "GR": "Греция",
    "TU": "Турция", "RS": "Россия", "UP": "Украина", "BO": "Беларусь",
    "LG": "Латвия", "LH": "Литва", "EN": "Эстония", "MD": "Молдова",
    "GG": "Грузия", "AM": "Армения", "AJ": "Азербайджан", "KZ": "Казахстан",
    "UZ": "Узбекистан", "TX": "Туркменистан", "TI": "Таджикистан", "KG": "Киргизия",
    "CH": "Китай", "JA": "Япония", "KS": "Южная Корея", "KN": "Северная Корея",
    "IN": "Индия", "PK": "Пакистан", "BG": "Бангладеш", "CE": "Шри-Ланка",
    "AF": "Афганистан", "IR": "Иран", "IZ": "Ирак", "SA": "Саудовская Аравия",
    "IS": "Израиль", "JO": "Иордания", "LE": "Ливан", "SY": "Сирия",
    "YM": "Йемен", "TC": "ОАЭ", "QA": "Катар", "KU": "Кувейт",
    "BA": "Бахрейн", "MU": "Оман", "EG": "Египет", "LY": "Ливия",
    "TS": "Тунис", "AG": "Алжир", "MO": "Марокко", "SU": "Судан",
    "ET": "Эфиопия", "SO": "Сомали", "KE": "Кения", "TZ": "Танзания",
    "UG": "Уганда", "NI": "Нигерия", "GH": "Гана", "IV": "Кот-д'Ивуар",
    "SG": "Сенегал", "ML": "Мали", "NG": "Нигер", "CD": "ДР Конго",
    "CG": "Республика Конго", "AO": "Ангола", "SF": "ЮАР", "ZI": "Зимбабве",
    "ZA": "Замбия", "MZ": "Мозамбик", "MA": "Мадагаскар", "CM": "Камерун",
    "CA": "Канада", "MX": "Мексика", "BR": "Бразилия", "AR": "Аргентина",
    "CI": "Чили", "CO": "Колумбия", "PE": "Перу", "VE": "Венесуэла",
    "EC": "Эквадор", "BL": "Боливия", "PA": "Парагвай", "UY": "Уругвай",
    "CU": "Куба", "HA": "Гаити", "DR": "Доминиканская Республика", "JM": "Ямайка",
    "AS": "Австралия", "NZ": "Новая Зеландия", "ID": "Индонезия", "MY": "Малайзия",
    "TH": "Таиланд", "VM": "Вьетнам", "RP": "Филиппины", "CB": "Камбоджа",
    "LA": "Лаос", "BM": "Мьянма", "SN": "Сингапур", "TW": "Тайвань",
    "MN": "Монголия", "NP": "Непал", "CY": "Кипр", "IC": "Исландия",
    "IE": "Ирландия", "AU": "Австрия", "SZ": "Швейцария", "AL": "Албания",
    "SR": "Сербия", "HR": "Хорватия", "BK": "Босния и Герцеговина", "SI": "Словения",
    "MK": "Северная Македония", "MJ": "Черногория",
}

# Резервные категории для расшифровки GCAM (по префиксу словаря)
GCAM_CATEGORY_PREFIXES = {
    "c1.": "Тональность",
    "c2.": "Эмоции",
    "c9.": "Психолингвистика",
    "c15.": "Тематика",
    "c16.": "Психолингвистика",
    "c17.": "Тематика",
    "c18.": "Тематика",
    "v10.": "Тональность",
}


def _build_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS themes (code TEXT PRIMARY KEY, name_ru TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS gcam (code TEXT PRIMARY KEY, name_ru TEXT, category TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS countries (code TEXT PRIMARY KEY, name_ru TEXT)")

    cur.executemany(
        "INSERT OR REPLACE INTO themes (code, name_ru) VALUES (?, ?)",
        list(THEMES.items()),
    )
    cur.executemany(
        "INSERT OR REPLACE INTO gcam (code, name_ru, category) VALUES (?, ?, ?)",
        [(code, name, cat) for code, (name, cat) in GCAM.items()],
    )
    cur.executemany(
        "INSERT OR REPLACE INTO countries (code, name_ru) VALUES (?, ?)",
        list(COUNTRIES.items()),
    )
    conn.commit()
    conn.close()


def _ensure_db():
    if not os.path.exists(DB_PATH):
        _build_db()
    else:
        # если справочники в коде пополнились - досеем недостающие записи
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='themes'")
        if cur.fetchone()[0] == 0:
            conn.close()
            _build_db()
        else:
            conn.close()


_ensure_db()


def _humanize_theme(code: str) -> str:
    """Запасной вариант для тем, которых нет в справочнике."""
    text = re.sub(r"^(TAX_|WB_\d+_|CRISISLEX_|USPEC_)", "", code)
    text = text.replace("_", " ").strip().lower()
    return text.capitalize() if text else code


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def decode_theme(code: str) -> str:
    conn = get_connection()
    row = conn.execute("SELECT name_ru FROM themes WHERE code = ?", (code,)).fetchone()
    conn.close()
    if row:
        return row["name_ru"]
    return _humanize_theme(code)


def decode_themes(codes):
    conn = get_connection()
    rows = {r["code"]: r["name_ru"] for r in conn.execute("SELECT code, name_ru FROM themes")}
    conn.close()
    return [rows.get(c, _humanize_theme(c)) for c in codes]


def decode_gcam(code: str):
    conn = get_connection()
    row = conn.execute("SELECT name_ru, category FROM gcam WHERE code = ?", (code,)).fetchone()
    conn.close()
    if row:
        return {"code": code, "name_ru": row["name_ru"], "category": row["category"]}
    category = next((v for k, v in GCAM_CATEGORY_PREFIXES.items() if code.startswith(k)), "Прочее")
    return {"code": code, "name_ru": code, "category": category}


def decode_country(code: str) -> str:
    if not code:
        return ""
    conn = get_connection()
    row = conn.execute("SELECT name_ru FROM countries WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row["name_ru"] if row else code


def list_gcam_catalog():
    conn = get_connection()
    rows = conn.execute("SELECT code, name_ru, category FROM gcam ORDER BY category, name_ru").fetchall()
    conn.close()
    return [dict(r) for r in rows]
