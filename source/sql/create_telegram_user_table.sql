CREATE TABLE IF NOT EXISTS telegram_user
(
    user_id INTEGER NOT NULL
        CONSTRAINT user_pkey PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64),
    username VARCHAR(32)
);
ALTER TABLE telegram_user OWNER TO {};