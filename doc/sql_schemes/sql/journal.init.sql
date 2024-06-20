-- Create table for technical grades and insert data

CREATE TABLE IF NOT EXISTS technical_grade (
	technical_grade_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	grade TEXT NOT NULL UNIQUE,
	position INTEGER NOT NULL UNIQUE CHECK (position >= 0)
);

CREATE INDEX index_technical_grade_id ON technical_grade (technical_grade_id);

INSERT INTO technical_grade (grade, position)
VALUES ("I", 0),
	("II", 1),
	("III", 2),
	("IV", 3),
	("V", 4),
	("VI", 5),
	("VIIa", 6),
	("VIIb", 7),
	("VIIc", 8),
	("VIIIa", 9),
	("VIIIb", 10),
	("VIIIc", 11),
	("IXa", 12),
	("IXb", 13),
	("IXc", 14),
	("Xa", 15),
	("Xb", 16),
	("Xc", 17),
	("XIa", 18),
	("XIb", 19),
	("XIc", 20),
	("XIIa", 21),
	("XIIb", 22),
	("XIIc", 23),
	("XIIIa", 24),
	("XIIIb", 25),
	("XIIIc", 26),
	("1", 27),
	("2", 28),
	("3", 29),
	("4", 30),
	("5", 31),
	("6", 32),
	("7", 33);

-- Create table for adjectival grades and insert data

CREATE TABLE IF NOT EXISTS adjectival_grade (
	adjectival_grade_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	grade TEXT NOT NULL UNIQUE,
	position INTEGER NOT NULL UNIQUE CHECK (position >= 0)
);

CREATE INDEX index_adjectival_grade_id ON adjectival_grade (adjectival_grade_id);

INSERT INTO adjectival_grade (grade, position)
VALUES ("E0", 0),
	("E1", 1),
	("E2", 2),
	("E3", 3),
	("E4", 4);

-- Create table for journal

CREATE TABLE IF NOT EXISTS journal (
	journal_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	date INTEGER NOT NULL,
	area TEXT NOT NULL,
	summit TEXT NOT NULL,
	route TEXT NOT NULL,
	technical_grade_id INTEGER NOT NULL,
	adjectival_grade_id INTEGER,
	note TEXT,
	FOREIGN KEY(technical_grade_id) REFERENCES technical_grade (technical_grade_id) ON DELETE CASCADE,
	FOREIGN KEY(adjectival_grade_id) REFERENCES adjectival_grade (adjectival_grade_id) ON DELETE CASCADE
);

CREATE INDEX index_journal_id ON journal (journal_id);

-- Create table for team

CREATE TABLE IF NOT EXISTS team (
	team_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	journal_id INTEGER NOT NULL,
	name TEXT NOT NULL,
	position INTEGER NOT NULL CHECK (position >= 0),
	UNIQUE(journal_id,position),
	FOREIGN KEY(journal_id) REFERENCES journal (journal_id) ON DELETE CASCADE
);

-- Create journal view

CREATE VIEW view_journal AS
SELECT journal_id,
	date,
	area,
	summit,
	route,
	technical_grade.grade AS 'technical_grade',
	adjectival_grade.grade AS 'adjectival_grade',
	note
FROM journal
	JOIN technical_grade ON journal.technical_grade_id = technical_grade.technical_grade_id
	LEFT JOIN adjectival_grade ON journal.adjectival_grade_id = adjectival_grade.adjectival_grade_id;

-- Create ordered technical grade view

CREATE VIEW view_ordered_technical_grade AS
SELECT technical_grade_id,
	grade
FROM technical_grade
ORDER BY position;

-- Create ordered adjectival grade view

CREATE VIEW view_ordered_adjectival_grade AS
SELECT adjectival_grade_id,
	grade
FROM adjectival_grade
ORDER BY position;

-- Perform analyze

ANALYZE;