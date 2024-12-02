CREATE TABLE admin (
    uuid               VARCHAR NOT NULL PRIMARY KEY,
    username           VARCHAR NOT NULL,
    password_hash      VARCHAR NOT NULL,

    UNIQUE(username)
);

INSERT INTO admin (uuid, username, password_hash) VALUES
    ('1e785a5dd-7fdd-483f-93b3-b84ecaa62683', 'admin', '$2b$12$QnbxGRl6jVTzt.fbksJWVuITmX4832AnfF1uSx00hZSsDBgjXDxcO'); -- psw: admin
