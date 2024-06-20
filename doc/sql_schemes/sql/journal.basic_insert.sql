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

INSERT INTO journal (date, area, summit, route, technical_grade_id, adjectival_grade_id)
VALUES (
        "2024-06-15",
        "Bielatal",
        "Glasergrundwand",
        "Rechter Schartenriß",
        (
            SELECT technical_grade_id
            FROM technical_grade
            WHERE grade = 'III'
        ),
        (
            SELECT adjectival_grade_id
            FROM adjectival_grade
            WHERE grade = 'E2'
        )
    );

INSERT INTO journal (date, area, summit, route, technical_grade_id, adjectival_grade_id, note)
VALUES (
        "2024-06-16",
        "Bielatal",
        "Glasergrundwand",
        "Südostkamin",
        (
            SELECT technical_grade_id
            FROM technical_grade
            WHERE grade = 'I'
        ),
        (
            SELECT adjectival_grade_id
            FROM adjectival_grade
            WHERE grade = 'E3'
        ),
        "Man kann nicht wirklich rausfallen"
    );