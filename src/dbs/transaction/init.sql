CREATE TABLE transaction (
    uuid             VARCHAR PRIMARY KEY NOT NULL,
    price            INTEGER NOT NULL,
    created_at       BIGINT NOT NULL,
    uuid_player      VARCHAR NOT NULL,
    uuid_auction     VARCHAR NOT NULL,

    UNIQUE(uuid),
    UNIQUE(uuid_auction)
);

CREATE FUNCTION check_negative_price() RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.price < 0 THEN
            RAISE EXCEPTION 'Error: negative price';
        END IF;

        RETURN NEW;
    END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER negative_price
    BEFORE INSERT OR UPDATE OF price ON transaction
    FOR EACH ROW
    EXECUTE FUNCTION check_negative_price();

INSERT INTO transaction (uuid, price, created_at, uuid_player, uuid_auction) VALUES 
    ('d8e6010d-077d-4474-ad9d-6e324eeef7f1', 700, 11112011, '71520f05-80c5-4cb1-b05a-a9642f9ae222', '71520f05-80c5-4cb1-b05a-a9642f9bbbbb');
