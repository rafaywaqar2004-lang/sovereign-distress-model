-- Sovereign Distress Model -- database schema (SQLite)
--
-- A real relational layer over the panel, replacing the flat-CSV approach
-- MENASA and Gulf Tracker both use. Normalized into three tables rather than
-- one wide one, so the schema itself documents what's a country attribute,
-- what's a time-varying observation, and what's an event -- not just a
-- convenience for storage.

CREATE TABLE countries (
    country_code TEXT PRIMARY KEY,      -- ISO3, matches MENASA's own coding
    country_name TEXT NOT NULL
);

CREATE TABLE macro_observations (
    country_code TEXT NOT NULL REFERENCES countries(country_code),
    year INTEGER NOT NULL,
    debt_to_gdp REAL,
    current_account_pct_gdp REAL,
    reserves_months_imports REAL,
    gdp_growth REAL,
    inflation REAL,
    currency_depreciation_pct REAL,
    political_stability REAL,
    government_effectiveness REAL,
    rule_of_law REAL,
    regulatory_quality REAL,
    control_of_corruption REAL,
    PRIMARY KEY (country_code, year)
);

CREATE TABLE distress_events (
    country_code TEXT NOT NULL REFERENCES countries(country_code),
    year INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('sovereign_default', 'imf_program_entry')),
    detail TEXT,                        -- the sourced description (default date, program name/approval date)
    PRIMARY KEY (country_code, year, event_type)
);

-- The analysis view a model script actually queries -- joins the panel back
-- together with both outcome columns as 0/1 flags, same shape as panel.csv,
-- but derived from the normalized tables above rather than duplicating them.
CREATE VIEW analysis_panel AS
SELECT
    m.country_code,
    m.year,
    m.debt_to_gdp,
    m.current_account_pct_gdp,
    m.reserves_months_imports,
    m.gdp_growth,
    m.inflation,
    m.currency_depreciation_pct,
    m.political_stability,
    m.government_effectiveness,
    m.rule_of_law,
    m.regulatory_quality,
    m.control_of_corruption,
    MAX(CASE WHEN d.event_type = 'sovereign_default' THEN 1 ELSE 0 END) AS sovereign_default,
    MAX(CASE WHEN d.event_type = 'imf_program_entry' THEN 1 ELSE 0 END) AS imf_program_entry
FROM macro_observations m
LEFT JOIN distress_events d
    ON m.country_code = d.country_code AND m.year = d.year
GROUP BY m.country_code, m.year;
