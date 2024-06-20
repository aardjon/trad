-- Insert into journal
INSERT INTO journal (date, area, summit, route, technical_grade_id)
VALUES (
        "2024-06-14",
        "Bielatal",
        "Glasergrundwand",
        "Südkante",
        (
            SELECT technical_grade_id
            FROM technical_grade
            WHERE grade = 'II'
        )
    );

-- Create a temporary table to store the last inserted ID
CREATE TEMP TABLE last_journal_id (journal_id INTEGER);

-- Insert the last inserted ID into the temporary table
INSERT INTO last_journal_id (journal_id)
VALUES (last_insert_rowid());

-- Insert multiple entries into team using the stored ID
INSERT INTO team (journal_id, name, position)
SELECT journal_id, "John Doe", 0 FROM last_journal_id;

INSERT INTO team (journal_id, name, position)
SELECT journal_id, "Jane Smith", 1 FROM last_journal_id;

INSERT INTO team (journal_id, name, position)
SELECT journal_id, "Alice Johnson", 2 FROM last_journal_id;

-- Drop the temporary table
DROP TABLE last_journal_id;