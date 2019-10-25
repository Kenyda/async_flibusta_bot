INSERT INTO posted_book (book_id, file_type, file_id) VALUES ($1, cast($2 AS VARCHAR), cast($3 AS VARCHAR))
ON CONFLICT (book_id, file_type) DO UPDATE SET file_id = EXCLUDED.file_id;