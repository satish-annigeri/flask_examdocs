DROP TABLE IF EXISTS messages;

CREATE TABLE messages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	subject TEXT,
	sender TEXT,
	sender_email TEXT,
	date TEXT,
	time TEXT,
	usn TEXT,
	payment_id TEXT,
	amount NUMERIC,
	phone TEXT,
	documents TEXT,
	raw_msg BLOB
);

DROP TABLE IF EXISTS attachments;

CREATE TABLE attachments (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename TEXT,
	message_id INTEGER,
	FOREIGN KEY (message_id) REFERENCES messages(id)
);

