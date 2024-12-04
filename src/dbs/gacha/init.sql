CREATE TABLE gacha (
    uuid             VARCHAR PRIMARY KEY,
    name             VARCHAR NOT NULL,
    description      VARCHAR,
    image_path       VARCHAR,
    uuid_rarity      VARCHAR NOT NULL,
    active           BOOLEAN DEFAULT TRUE,

    UNIQUE(name)
);

CREATE TABLE rarity (
    uuid             VARCHAR PRIMARY KEY,
    name             VARCHAR NOT NULL,
    symbol           VARCHAR NOT NULL,
    percentage       INTEGER NOT NULL,

    UNIQUE(name),
    UNIQUE(symbol)
);

CREATE TABLE player_gacha (
    uuid_player      VARCHAR NOT NULL,
    uuid_gacha       VARCHAR NOT NULL,
    quantity         INTEGER DEFAULT 1,

    PRIMARY KEY (uuid_player, uuid_gacha)
);

INSERT INTO rarity (uuid, name, symbol, percentage) VALUES 
    ('ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6', 'Common',    'C', 50), 
    ('7c0bcf1f-dbf6-4e33-a6e6-e051a54fed4e', 'Uncommon',  'U', 30), 
    ('3fcc18ef-674c-4ec6-8692-899188a68146', 'Rare',      'R', 10), 
    ('5b0a7f3e-c0bf-454d-965f-40fd1f3b131e', 'Epic',      'E', 8), 
    ('895b882e-c5a1-4007-b95b-1ee58f283700', 'Legendary', 'S', 2);

INSERT INTO gacha (uuid, name, description, image_path, uuid_rarity) VALUES
    ('4e120c8c-d5c0-43f6-8587-0a8b94473593', 'Orc',            'Orcs are brutal, aggressive humanoids known for their strength and savagery. They have green skin, muscular bodies, and prominent lower canines. Often found in tribes, orcs are fearsome warriors who value combat and conquest. They are typically chaotic and destructive, striking fear into their enemies with their ferocity and relentless attacks.',                                    '/assets/images/gachas/Orc (common).jpg',           'ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6'),
    ('09907f76-9b0f-4270-84a3-e9780b164ac4', 'Goblin',         'Goblins are small, malicious humanoids known for their cunning and mischief. They have green or gray skin, pointed ears, and sharp teeth. Often living in dark, underground lairs, goblins are clever and sneaky, using traps and ambushes to overcome foes. They are driven by greed and a love for causing chaos, making them dangerous and unpredictable adversaries.',                      '/assets/images/gachas/Goblin (common).jpg',        'ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6'),
    ('8930305e-262f-4ae9-92a0-f6d5dccc4d1f', 'Skeleton Mage',  'Skeleton mages are undead spellcasters with glowing eyes and tattered robes. They wield dark magic, casting spells with bony fingers. Often found in ancient ruins or crypts, these intelligent undead guard secrets and treasures. Their magical prowess and eerie presence make them formidable and chilling foes.',                                                                          '/assets/images/gachas/Skeleton mage (common).jpg', 'ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6'),
    ('dde21dde-5513-46d2-8d03-686fc620394c', 'Undead',         'Undead are reanimated corpses or spirits that refuse to rest. Often found in graveyards, ruins, or haunted places, undead are driven by a dark will, seeking to spread decay and fear. They range from mindless, shambling creatures to intelligent, malevolent beings, posing a constant threat to the living.',                                                                               '/assets/images/gachas/Undead (non-common).jpg',    '7c0bcf1f-dbf6-4e33-a6e6-e051a54fed4e'),
    ('0b75b774-9783-4bdc-b54a-4b8e9806399e', 'Cyclops',        'Cyclopes are giant, one-eyed humanoids known for their immense strength and brutality. Living in remote, mountainous regions, cyclopes are fearsome warriors who use their size and power to overwhelm enemies. Their unpredictable nature and raw force make them dangerous and terrifying foes.',                                                                                             '/assets/images/gachas/Cyclops (non-common).jpg',   '7c0bcf1f-dbf6-4e33-a6e6-e051a54fed4e'),
    ('cd6d4ae7-27a3-43cc-a2e5-b067f77c0744', 'Harpy',          'Harpies are vicious, bird-like humanoids with the body of a woman and the wings, legs, and claws of a predatory bird. Known for their screeching voices and malicious nature, harpies are often found in mountainous or coastal regions. They use their flight and sharp talons to attack from above, snatching victims and causing chaos.',                                                    '/assets/images/gachas/Harpy (non-common).jpg',     '7c0bcf1f-dbf6-4e33-a6e6-e051a54fed4e'),
    ('c6cc4f1f-f5f8-4e76-a446-b01b48b10575', 'Demon',          'Demons are malevolent supernatural beings from the depths of hell. They come in various shapes and sizes, often grotesque and terrifying. Known for their evil intentions and dark powers, demons seek to corrupt and destroy. They can possess humans, spread chaos, and are extremely difficult to vanquish.',                                                                                '/assets/images/gachas/Demon (rare).jpg',           '3fcc18ef-674c-4ec6-8692-899188a68146'),
    ('d00d0e34-0250-4c21-b4f8-12109f3925b0', 'Cerberus',       'Cerberus is a monstrous three-headed dog guarding the gates of the underworld. Each head is fierce and vigilant, ensuring no soul escapes and no living being enters uninvited. With a massive, muscular body and sharp teeth, Cerberus strikes fear into all who approach. Its loyalty to Hades is unwavering, making it a formidable and eternal sentinel.',                                  '/assets/images/gachas/Cerberus (rare).jpg',        '3fcc18ef-674c-4ec6-8692-899188a68146'),
    ('6150d92e-3592-46e2-8184-b3b5f2a8b684', 'Black Skeleton', 'Black skeletons are powerful, intelligent undead guardians. Unlike mindless skeletons, they possess clear minds and can defy orders if it benefits them. Formed from remains of creatures slain in evil-soaked grounds, they rise days after death, retaining memories of their former lives. They wear of their past life clothes of their life and armor, often carrying dual short swords.', '/assets/images/gachas/Skeleton (rare).jpg',        '3fcc18ef-674c-4ec6-8692-899188a68146'),
    ('a3bc71a1-44e9-4ac5-8215-c30666720ec5', 'Dragon',         'Dragons are legendary, powerful creatures known for their immense strength, scaled bodies, and ability to fly. They come in various colors, each with unique breath weapons like fire, ice, or acid. Often guarding vast treasures in their lairs, dragons are intelligent and fearsome, striking awe and terror into those who encounter them.',                                               '/assets/images/gachas/Dragon (epic).jpg',          '5b0a7f3e-c0bf-454d-965f-40fd1f3b131e'),
    ('6cc1d008-d047-4147-ba6f-25cba2bdf061', 'Minotaur',       'Minotaurs have a muscular human body and the head of a bull with sharp horns. Found in labyrinths or caverns, they charge with relentless fury, using horns and fists to overwhelm foes. Their aggressive nature makes them dangerous and unpredictable.',                                                                                                                                      '/assets/images/gachas/Minotaur (epic).jpg',        '5b0a7f3e-c0bf-454d-965f-40fd1f3b131e'),
    ('a954690a-5be4-443b-9137-92c73bee5480', 'Vampire',        'Vampires are undead creatures that feed on the blood of the living. They possess enhanced strength, speed, and hypnotic powers. Often found in dark, secluded places, vampires are cunning and manipulative, using their charm to lure victims. They are highly sensitive to sunlight and can be repelled by garlic and religious symbols.',                                                    '/assets/images/gachas/Vampire (epic).jpg',         '5b0a7f3e-c0bf-454d-965f-40fd1f3b131e'),
    ('7d1fec59-6a89-4b78-a9e5-aa4d0d10478e', 'Phoenix',        'The phoenix is a mythical bird known for its ability to be reborn from its own ashes. It possesses vibrant, fiery plumage and is often associated with the sun and immortality. When it senses its end is near, the phoenix builds a nest, sets it ablaze, and is consumed by the flames. From the ashes, a new phoenix emerges, symbolizing renewal and rebirth.',                             '/assets/images/gachas/Phoenix (legendary).jpg',    '895b882e-c5a1-4007-b95b-1ee58f283700'),
    ('3b8009f2-31c8-484b-aa74-32defbb02985', 'Kraken',         'The kraken is a legendary sea monster of enormous size and strength. It has numerous long tentacles and a massive body, capable of crushing ships and devouring sailors. Living in the deepest parts of the ocean, the kraken is a terrifying force of nature, striking fear into the hearts of mariners. Its appearance is often heralded by violent storms and whirlpools.',                  '/assets/images/gachas/Kraken (legendary).jpg',     '895b882e-c5a1-4007-b95b-1ee58f283700'),
    ('23255124-b509-41fd-b607-5f5da9f60447', 'Griffin',        'The griffin is a majestic creature with the body, tail, and back legs of a lion, and the head and wings of an eagle. Known for its strength and nobility, the griffin is often associated with guarding treasures and sacred places. It is a powerful and agile flyer, using its sharp beak and talons to defend its territory. Griffins are symbols of courage and divine power.',             '/assets/images/gachas/Griffin (legendary).jpg',    '895b882e-c5a1-4007-b95b-1ee58f283700');

INSERT INTO player_gacha (uuid_player, uuid_gacha, quantity) VALUES 
    ('71520f05-80c5-4cb1-b05a-a9642f9ae44d', '09907f76-9b0f-4270-84a3-e9780b164ac4', 5),
    ('71520f05-80c5-4cb1-b05a-a9642f9ae44d', '23255124-b509-41fd-b607-5f5da9f60447', 1),
    ('71520f05-80c5-4cb1-b05a-a9642f9ae44d', 'c6cc4f1f-f5f8-4e76-a446-b01b48b10575', 2),
    ('71520f05-80c5-4cb1-b05a-a9642f9ae44d', '0b75b774-9783-4bdc-b54a-4b8e9806399e', 1);