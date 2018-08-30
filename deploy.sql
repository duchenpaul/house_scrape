--
-- File generated with SQLiteStudio v3.1.1 on Wed Aug 29 22:50:24 2018
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: rent_info_nanjing
DROP TABLE IF EXISTS rent_info_nanjing;

CREATE TABLE rent_info_nanjing (
    house_id   TEXT,
    district   TEXT,
    complex    TEXT,
    house_type TEXT,
    area       INTEGER,
    direction  TEXT,
    max_floor  INTEGER,
    floor_area TEXT,
    rent       INTEGER,
    year       INTEGER,
    url        TEXT
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
