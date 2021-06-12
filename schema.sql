CREATE TABLE IF NOT EXISTS guilds (
    id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS prefixes (
    id BIGINT PRIMARY KEY REFERENCES guilds (id) ON DELETE CASCADE,
    prefix VARCHAR(25)
);

CREATE TABLE IF NOT EXISTS games (
    game TEXT,
    snowflake BIGINT,
    id VARCHAR,
    PRIMARY KEY (game, snowflake)
);

CREATE TABLE IF NOT EXISTS interactions (
    method TEXT,
    initiator BIGINT,
    receiver BIGINT,
    count BIGINT DEFAULT 1,
    PRIMARY KEY (method, initiator, receiver)
);

CREATE TABLE IF NOT EXISTS totals (
    method TEXT,
    snowflake BIGINT,
    count BIGINT DEFAULT 1,
    PRIMARY KEY (method, snowflake)
);

CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,

    guild BIGINT REFERENCES guilds (id) ON DELETE CASCADE,
    author BIGINT,
    channel BIGINT,
    message BIGINT,

    expires TIMESTAMP,
    created TIMESTAMP,

    content TEXT
);

CREATE INDEX IF NOT EXISTS reminder_expire ON reminders (expires);

CREATE TABLE IF NOT EXISTS commands (
    id SERIAL PRIMARY KEY,

    guild BIGINT,
    channel BIGINT,
    author BIGINT,
    used TIMESTAMP,
    prefix TEXT,
    command TEXT,

    failed BOOLEAN
);

CREATE INDEX IF NOT EXISTS commands_guildx ON commands (guild);
CREATE INDEX IF NOT EXISTS commands_authorx ON commands (author);
CREATE INDEX IF NOT EXISTS commands_commandx ON commands (command);

