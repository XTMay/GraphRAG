// ============================================
// Smart Home Knowledge Graph - Seed Data
// ============================================
// This Cypher script creates a sample smart home topology
// for demonstrating GraphRAG retrieval patterns.
//
// Run this script in Neo4j Browser or via Python driver.
// ============================================

// -----------------------------------------
// STEP 1: Clear existing data (optional)
// -----------------------------------------
// Uncomment the following line to clear existing data:
// MATCH (n) DETACH DELETE n;

// -----------------------------------------
// STEP 2: Create Constraints (for performance)
// -----------------------------------------
CREATE CONSTRAINT room_name IF NOT EXISTS FOR (r:Room) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE;
CREATE CONSTRAINT capability_name IF NOT EXISTS FOR (c:Capability) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT scene_name IF NOT EXISTS FOR (s:Scene) REQUIRE s.name IS UNIQUE;

// -----------------------------------------
// STEP 3: Create Capabilities
// -----------------------------------------
// These are the actions devices can perform

CREATE (c1:Capability {
    name: "power",
    description: "Turn device on or off",
    parameters: ["state"],
    example: "power: on/off"
})

CREATE (c2:Capability {
    name: "dim",
    description: "Adjust brightness level",
    parameters: ["brightness_percent"],
    example: "dim: 0-100"
})

CREATE (c3:Capability {
    name: "color",
    description: "Change light color",
    parameters: ["color_hex", "color_name"],
    example: "color: #FF5500 or 'warm white'"
})

CREATE (c4:Capability {
    name: "volume",
    description: "Adjust audio volume",
    parameters: ["volume_percent"],
    example: "volume: 0-100"
})

CREATE (c5:Capability {
    name: "play_music",
    description: "Play music or audio content",
    parameters: ["source", "playlist"],
    example: "play_music: spotify, 'Relaxing Jazz'"
})

CREATE (c6:Capability {
    name: "temperature",
    description: "Set target temperature",
    parameters: ["target_celsius", "target_fahrenheit"],
    example: "temperature: 22°C"
})

CREATE (c7:Capability {
    name: "input_select",
    description: "Select input source for display",
    parameters: ["input_name"],
    example: "input_select: HDMI1, Netflix"
})

CREATE (c8:Capability {
    name: "announce",
    description: "Make voice announcement",
    parameters: ["message"],
    example: "announce: 'Dinner is ready'"
})

CREATE (c9:Capability {
    name: "lock",
    description: "Lock or unlock",
    parameters: ["state"],
    example: "lock: locked/unlocked"
})

CREATE (c10:Capability {
    name: "open_close",
    description: "Open or close (blinds, curtains)",
    parameters: ["position_percent"],
    example: "open_close: 0 (closed) to 100 (open)"
});

// -----------------------------------------
// STEP 4: Create Rooms
// -----------------------------------------

CREATE (living:Room {
    name: "Living Room",
    floor: "Ground Floor",
    type: "entertainment",
    description: "Main living area for relaxation and entertainment"
})

CREATE (kitchen:Room {
    name: "Kitchen",
    floor: "Ground Floor",
    type: "utility",
    description: "Cooking and dining area"
})

CREATE (bedroom:Room {
    name: "Master Bedroom",
    floor: "First Floor",
    type: "bedroom",
    description: "Primary sleeping area"
})

CREATE (office:Room {
    name: "Home Office",
    floor: "First Floor",
    type: "work",
    description: "Work from home space"
})

CREATE (bathroom:Room {
    name: "Bathroom",
    floor: "First Floor",
    type: "utility",
    description: "Main bathroom"
});

// -----------------------------------------
// STEP 5: Create Room Adjacency Relationships
// -----------------------------------------

MATCH (living:Room {name: "Living Room"}), (kitchen:Room {name: "Kitchen"})
CREATE (living)-[:ADJACENT_TO]->(kitchen)
CREATE (kitchen)-[:ADJACENT_TO]->(living);

MATCH (bedroom:Room {name: "Master Bedroom"}), (bathroom:Room {name: "Bathroom"})
CREATE (bedroom)-[:ADJACENT_TO]->(bathroom)
CREATE (bathroom)-[:ADJACENT_TO]->(bedroom);

MATCH (bedroom:Room {name: "Master Bedroom"}), (office:Room {name: "Home Office"})
CREATE (bedroom)-[:ADJACENT_TO]->(office)
CREATE (office)-[:ADJACENT_TO]->(bedroom);

// -----------------------------------------
// STEP 6: Create Devices
// -----------------------------------------

// Living Room Devices
CREATE (tv:Device {
    device_id: "living_tv_01",
    name: "Smart TV",
    device_type: "television",
    brand: "Samsung",
    model: "QN55Q80C",
    status: "online"
})

CREATE (ceiling_light:Device {
    device_id: "living_ceiling_01",
    name: "Ceiling Light",
    device_type: "light",
    brand: "Philips Hue",
    model: "White and Color Ambiance",
    status: "online"
})

CREATE (floor_lamp:Device {
    device_id: "living_lamp_01",
    name: "Floor Lamp",
    device_type: "light",
    brand: "IKEA Tradfri",
    model: "Dimmable",
    status: "online"
})

CREATE (speaker:Device {
    device_id: "living_speaker_01",
    name: "Smart Speaker",
    device_type: "speaker",
    brand: "Sonos",
    model: "One",
    status: "online"
})

CREATE (blinds:Device {
    device_id: "living_blinds_01",
    name: "Window Blinds",
    device_type: "blinds",
    brand: "Lutron",
    model: "Serena",
    status: "online"
})

CREATE (thermostat:Device {
    device_id: "living_thermo_01",
    name: "Thermostat",
    device_type: "thermostat",
    brand: "Nest",
    model: "Learning Thermostat",
    status: "online"
})

// Kitchen Devices
CREATE (kitchen_light:Device {
    device_id: "kitchen_light_01",
    name: "Kitchen Light",
    device_type: "light",
    brand: "Philips Hue",
    model: "White Ambiance",
    status: "online"
})

CREATE (display:Device {
    device_id: "kitchen_display_01",
    name: "Smart Display",
    device_type: "display",
    brand: "Google",
    model: "Nest Hub Max",
    status: "online"
})

// Bedroom Devices
CREATE (bed_light:Device {
    device_id: "bedroom_light_01",
    name: "Bedroom Light",
    device_type: "light",
    brand: "Philips Hue",
    model: "White and Color Ambiance",
    status: "online"
})

CREATE (bedside_lamp:Device {
    device_id: "bedroom_lamp_01",
    name: "Bedside Lamp",
    device_type: "light",
    brand: "Philips Hue",
    model: "Go",
    status: "online"
})

CREATE (bed_speaker:Device {
    device_id: "bedroom_speaker_01",
    name: "Bedroom Speaker",
    device_type: "speaker",
    brand: "Amazon",
    model: "Echo Dot",
    status: "online"
})

// Office Devices
CREATE (desk_light:Device {
    device_id: "office_light_01",
    name: "Desk Lamp",
    device_type: "light",
    brand: "BenQ",
    model: "ScreenBar",
    status: "online"
})

CREATE (office_speaker:Device {
    device_id: "office_speaker_01",
    name: "Office Speaker",
    device_type: "speaker",
    brand: "Bose",
    model: "Companion 2",
    status: "online"
});

// -----------------------------------------
// STEP 7: Connect Devices to Rooms
// -----------------------------------------

// Living Room
MATCH (r:Room {name: "Living Room"}), (d:Device {device_id: "living_tv_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Living Room"}), (d:Device {device_id: "living_ceiling_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Living Room"}), (d:Device {device_id: "living_lamp_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Living Room"}), (d:Device {device_id: "living_speaker_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Living Room"}), (d:Device {device_id: "living_blinds_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Living Room"}), (d:Device {device_id: "living_thermo_01"})
CREATE (r)-[:CONTAINS]->(d);

// Kitchen
MATCH (r:Room {name: "Kitchen"}), (d:Device {device_id: "kitchen_light_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Kitchen"}), (d:Device {device_id: "kitchen_display_01"})
CREATE (r)-[:CONTAINS]->(d);

// Bedroom
MATCH (r:Room {name: "Master Bedroom"}), (d:Device {device_id: "bedroom_light_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Master Bedroom"}), (d:Device {device_id: "bedroom_lamp_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Master Bedroom"}), (d:Device {device_id: "bedroom_speaker_01"})
CREATE (r)-[:CONTAINS]->(d);

// Office
MATCH (r:Room {name: "Home Office"}), (d:Device {device_id: "office_light_01"})
CREATE (r)-[:CONTAINS]->(d);

MATCH (r:Room {name: "Home Office"}), (d:Device {device_id: "office_speaker_01"})
CREATE (r)-[:CONTAINS]->(d);

// -----------------------------------------
// STEP 8: Connect Devices to Capabilities
// -----------------------------------------

// Smart TV capabilities
MATCH (d:Device {device_id: "living_tv_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_tv_01"}), (c:Capability {name: "volume"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_tv_01"}), (c:Capability {name: "input_select"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Ceiling Light capabilities (full-featured)
MATCH (d:Device {device_id: "living_ceiling_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_ceiling_01"}), (c:Capability {name: "dim"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_ceiling_01"}), (c:Capability {name: "color"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Floor Lamp capabilities (dimmable only)
MATCH (d:Device {device_id: "living_lamp_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_lamp_01"}), (c:Capability {name: "dim"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Smart Speaker capabilities
MATCH (d:Device {device_id: "living_speaker_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_speaker_01"}), (c:Capability {name: "volume"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_speaker_01"}), (c:Capability {name: "play_music"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "living_speaker_01"}), (c:Capability {name: "announce"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Window Blinds capabilities
MATCH (d:Device {device_id: "living_blinds_01"}), (c:Capability {name: "open_close"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Thermostat capabilities
MATCH (d:Device {device_id: "living_thermo_01"}), (c:Capability {name: "temperature"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Kitchen Light capabilities
MATCH (d:Device {device_id: "kitchen_light_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "kitchen_light_01"}), (c:Capability {name: "dim"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Smart Display capabilities
MATCH (d:Device {device_id: "kitchen_display_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "kitchen_display_01"}), (c:Capability {name: "volume"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Bedroom Light capabilities
MATCH (d:Device {device_id: "bedroom_light_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_light_01"}), (c:Capability {name: "dim"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_light_01"}), (c:Capability {name: "color"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Bedside Lamp capabilities
MATCH (d:Device {device_id: "bedroom_lamp_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_lamp_01"}), (c:Capability {name: "dim"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_lamp_01"}), (c:Capability {name: "color"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Bedroom Speaker capabilities
MATCH (d:Device {device_id: "bedroom_speaker_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_speaker_01"}), (c:Capability {name: "volume"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_speaker_01"}), (c:Capability {name: "play_music"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "bedroom_speaker_01"}), (c:Capability {name: "announce"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Desk Lamp capabilities
MATCH (d:Device {device_id: "office_light_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "office_light_01"}), (c:Capability {name: "dim"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// Office Speaker capabilities
MATCH (d:Device {device_id: "office_speaker_01"}), (c:Capability {name: "power"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "office_speaker_01"}), (c:Capability {name: "volume"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

MATCH (d:Device {device_id: "office_speaker_01"}), (c:Capability {name: "play_music"})
CREATE (d)-[:HAS_CAPABILITY]->(c);

// -----------------------------------------
// STEP 9: Create Scenes
// -----------------------------------------

CREATE (movie:Scene {
    name: "Movie Night",
    description: "Optimal settings for watching movies",
    mood: "relaxed",
    typical_actions: ["dim lights to 20%", "close blinds", "turn on TV", "set warm color"]
})

CREATE (morning:Scene {
    name: "Good Morning",
    description: "Energizing settings to start the day",
    mood: "energetic",
    typical_actions: ["open blinds", "bright lights", "play upbeat music"]
})

CREATE (sleep:Scene {
    name: "Bedtime",
    description: "Relaxing settings for sleep preparation",
    mood: "calm",
    typical_actions: ["dim all lights", "warm colors", "play soft music", "set cool temperature"]
})

CREATE (focus:Scene {
    name: "Focus Mode",
    description: "Distraction-free work environment",
    mood: "focused",
    typical_actions: ["bright desk light", "other lights off", "no music or soft ambient"]
})

CREATE (party:Scene {
    name: "Party Mode",
    description: "Fun atmosphere for gatherings",
    mood: "exciting",
    typical_actions: ["colorful lights", "upbeat music", "all speakers on"]
});

// -----------------------------------------
// STEP 10: Connect Scenes to Rooms and Devices
// -----------------------------------------

// Movie Night scene
MATCH (s:Scene {name: "Movie Night"}), (r:Room {name: "Living Room"})
CREATE (s)-[:APPLIES_TO]->(r);

MATCH (s:Scene {name: "Movie Night"}), (d:Device {device_id: "living_tv_01"})
CREATE (s)-[:USES_DEVICE {action: "power on"}]->(d);

MATCH (s:Scene {name: "Movie Night"}), (d:Device {device_id: "living_ceiling_01"})
CREATE (s)-[:USES_DEVICE {action: "dim to 20%, warm color"}]->(d);

MATCH (s:Scene {name: "Movie Night"}), (d:Device {device_id: "living_lamp_01"})
CREATE (s)-[:USES_DEVICE {action: "dim to 30%"}]->(d);

MATCH (s:Scene {name: "Movie Night"}), (d:Device {device_id: "living_blinds_01"})
CREATE (s)-[:USES_DEVICE {action: "close"}]->(d);

// Good Morning scene
MATCH (s:Scene {name: "Good Morning"}), (r:Room {name: "Master Bedroom"})
CREATE (s)-[:APPLIES_TO]->(r);

MATCH (s:Scene {name: "Good Morning"}), (d:Device {device_id: "bedroom_light_01"})
CREATE (s)-[:USES_DEVICE {action: "bright white light"}]->(d);

MATCH (s:Scene {name: "Good Morning"}), (d:Device {device_id: "bedroom_speaker_01"})
CREATE (s)-[:USES_DEVICE {action: "play morning playlist"}]->(d);

// Bedtime scene
MATCH (s:Scene {name: "Bedtime"}), (r:Room {name: "Master Bedroom"})
CREATE (s)-[:APPLIES_TO]->(r);

MATCH (s:Scene {name: "Bedtime"}), (d:Device {device_id: "bedroom_light_01"})
CREATE (s)-[:USES_DEVICE {action: "dim to 10%"}]->(d);

MATCH (s:Scene {name: "Bedtime"}), (d:Device {device_id: "bedroom_lamp_01"})
CREATE (s)-[:USES_DEVICE {action: "warm orange, dim"}]->(d);

// Focus Mode scene
MATCH (s:Scene {name: "Focus Mode"}), (r:Room {name: "Home Office"})
CREATE (s)-[:APPLIES_TO]->(r);

MATCH (s:Scene {name: "Focus Mode"}), (d:Device {device_id: "office_light_01"})
CREATE (s)-[:USES_DEVICE {action: "bright, cool white"}]->(d);

// Party Mode scene
MATCH (s:Scene {name: "Party Mode"}), (r:Room {name: "Living Room"})
CREATE (s)-[:APPLIES_TO]->(r);

MATCH (s:Scene {name: "Party Mode"}), (d:Device {device_id: "living_ceiling_01"})
CREATE (s)-[:USES_DEVICE {action: "colorful cycling"}]->(d);

MATCH (s:Scene {name: "Party Mode"}), (d:Device {device_id: "living_speaker_01"})
CREATE (s)-[:USES_DEVICE {action: "play party playlist, high volume"}]->(d);

// -----------------------------------------
// STEP 11: Verify the Graph
// -----------------------------------------
// Run these queries to verify data was loaded:

// Count nodes by label:
// MATCH (n) RETURN labels(n) AS label, count(n) AS count;

// View room topology:
// MATCH (r:Room)-[:CONTAINS]->(d:Device)
// RETURN r.name AS room, collect(d.name) AS devices;

// View device capabilities:
// MATCH (d:Device)-[:HAS_CAPABILITY]->(c:Capability)
// RETURN d.name AS device, collect(c.name) AS capabilities;
