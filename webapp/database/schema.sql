-- Shows Attended Database Schema

-- Venues table
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT,
    closed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bands table
CREATE TABLE IF NOT EXISTS bands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shows table
CREATE TABLE IF NOT EXISTS shows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    venue_id INTEGER NOT NULL,
    event_id INTEGER,
    confirmed BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venue_id) REFERENCES venues(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- ShowBands junction table (many-to-many with order)
CREATE TABLE IF NOT EXISTS show_bands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    band_id INTEGER NOT NULL,
    band_order INTEGER NOT NULL,
    FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
    FOREIGN KEY (band_id) REFERENCES bands(id),
    UNIQUE(show_id, band_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_shows_date ON shows(date);
CREATE INDEX IF NOT EXISTS idx_shows_venue ON shows(venue_id);
CREATE INDEX IF NOT EXISTS idx_shows_event ON shows(event_id);
CREATE INDEX IF NOT EXISTS idx_show_bands_show ON show_bands(show_id);
CREATE INDEX IF NOT EXISTS idx_show_bands_band ON show_bands(band_id);
CREATE INDEX IF NOT EXISTS idx_bands_name ON bands(name);
CREATE INDEX IF NOT EXISTS idx_venues_name ON venues(name);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
