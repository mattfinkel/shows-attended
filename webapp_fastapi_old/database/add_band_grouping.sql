-- Migration: Add band grouping support
-- Date: 2026-02-02
-- Description: Adds primary_band_id column to enable grouping band name variations

-- Add primary_band_id column (self-referencing foreign key)
ALTER TABLE bands ADD COLUMN primary_band_id INTEGER REFERENCES bands(id);

-- Create index for performance
CREATE INDEX idx_bands_primary ON bands(primary_band_id);

-- Usage:
-- - If primary_band_id IS NULL: This is a primary/standalone band
-- - If primary_band_id IS NOT NULL: This band is an alias of the primary band
--
-- Example:
-- UPDATE bands SET primary_band_id = (SELECT id FROM bands WHERE name = 'Lenny Lashley')
-- WHERE name IN ('Lenny Lashley & Friends', 'Lenny Lashley''s Gang of One');
