# drift-animation Specification

## Purpose

TBD - created by archiving change 'surf-decision-app'. Update Purpose after archive.

## Requirements

### Requirement: Coastal boundary polygon per surf spot

The system SHALL store a hand-drawn coastal outline polygon for each configured surf spot as a list of geographic coordinate pairs in `frontend/src/data/spots.ts`. The coastline polygon SHALL be rendered as a vector overlay (line or semi-transparent fill) on the satellite map in Screen 1.

#### Scenario: Coastline rendered on spot entry

- **WHEN** the user selects a surf spot and Screen 1 loads
- **THEN** the coastal boundary polygon for that spot is drawn on the p5.js canvas as a visible outline over the satellite imagery

#### Scenario: Coastline polygon stored per spot

- **WHEN** the spots data is loaded
- **THEN** each spot entry in `frontend/src/data/spots.ts` contains a `coastline` field with an array of `{lat, lng}` coordinate pairs defining the boundary

---
### Requirement: Windy-style particle flow field with toggle

The system SHALL render a Windy-style particle flow field over the surf zone in Screen 1 using p5.js. The flow field SHALL be driven by the vector sum of CWA Swell1, Swell2, and wind direction forces. The particle flow field SHALL be hidden by default and toggled on or off by a visible button in Screen 1.

#### Scenario: Flow field hidden by default

- **WHEN** the user enters Screen 1 for a surf spot
- **THEN** no flow field particles are visible; a toggle button labeled to show particles is present

#### Scenario: User enables flow field

- **WHEN** the user taps the particle toggle button
- **THEN** flow field particles appear across the surf zone, moving in directions determined by the CWA vector field

#### Scenario: Particles across the surf zone

- **WHEN** the flow field is active
- **THEN** particles are distributed across the configured surf zone bounding box and each moves according to the local vector field derived from CWA data

---
### Requirement: Coastal boundary collision and reflection

When flow field particles contact the coastal boundary polygon, the system SHALL reflect their velocity vector according to the polygon edge normal at the contact point. This SHALL produce emergent current patterns including convergence zones and outward-rushing flows in concave coastal geometries that approximate rip current behavior without requiring bathymetry data.

#### Scenario: Particle reflects off straight coastline segment

- **WHEN** a flow field particle reaches a straight coastal boundary edge
- **THEN** the particle velocity component perpendicular to the edge is reversed, and the particle continues with the reflected vector

#### Scenario: Concave geometry produces convergence

- **WHEN** waves push particles into a concave coastal section (bay shape)
- **THEN** particles accumulate near the center of the concavity and accelerate outward through the opening, producing a rip-current-like pattern

##### Example: concave bay convergence

- **GIVEN** a bay-shaped coastline with opening facing the ocean, Swell direction = onshore
- **WHEN** particles enter the bay and reflect off both curved walls
- **THEN** particles converge toward the bay center and exit through the opening at higher apparent speed than surrounding particles

---
### Requirement: Draggable yellow dot with static arrow

The system SHALL render a draggable yellow dot on Screen 1 that the user can move to any position within the surf zone. When the dot is at a given position, the system SHALL immediately display a static directional arrow indicating the vector field direction and magnitude (speed in m/s) at that position.

#### Scenario: Yellow dot initialized at spot reference coordinate

- **WHEN** Screen 1 loads for a surf spot
- **THEN** the yellow dot appears at the configured reference coordinate for that spot

#### Scenario: User drags yellow dot to a new position

- **WHEN** the user drags the yellow dot to a different geographic position
- **THEN** the static arrow updates immediately to show the vector field direction and speed (m/s) at the new position

#### Scenario: Arrow shows direction and speed value

- **WHEN** the static arrow is displayed
- **THEN** the arrow head indicates drift direction and a numeric label shows speed in m/s rounded to one decimal place

---
### Requirement: SAR trajectory animation from yellow dot position

The system SHALL provide a play button that, when tapped, runs the SAR drift trajectory animation starting from the current yellow dot position. The trajectory SHALL be computed by the backend SAR engine using the yellow dot's geographic coordinates as the origin.

#### Scenario: User taps play to start trajectory

- **WHEN** the user taps the play button with the yellow dot at a chosen position
- **THEN** the system sends the yellow dot coordinates to GET /api/v1/drift and animates the drift path from that position

#### Scenario: Trajectory and arrow coexist

- **WHEN** the trajectory animation is running
- **THEN** the static arrow remains visible alongside the animated trajectory path

#### Scenario: Trajectory resets on new drag

- **WHEN** the user drags the yellow dot to a new position while a trajectory is displayed
- **THEN** the previous trajectory is cleared and the play button returns to its initial state

---
### Requirement: Zoom-proportional particle speed

All p5.js particle and yellow dot movements SHALL be computed in geographic coordinate space and translated to screen pixels using `map.latLngToLayerPoint()` each animation frame, ensuring particle visual speed scales naturally with map zoom level.

#### Scenario: Zoom in maintains real-world speed

- **WHEN** the user zooms into the map
- **THEN** particles appear to move faster in pixels-per-frame, correctly reflecting the larger scale, while their real-world speed in m/s remains constant

##### Example: zoom-proportional pixel velocity

| Zoom Level | Pixels per Degree Lat (approx) | Particle real speed | Pixel speed (approx) |
|------------|-------------------------------|--------------------|-----------------------|
| Z12 | 256 | 1.0 m/s | 0.003 px/frame |
| Z14 | 1024 | 1.0 m/s | 0.012 px/frame |
| Z16 | 4096 | 1.0 m/s | 0.048 px/frame |

---
### Requirement: Particle count limit

The system SHALL render no more than 50 simultaneous flow field particles to maintain animation performance on mobile devices.

#### Scenario: Performance cap enforced

- **WHEN** the flow field animation loop runs
- **THEN** the total number of active flow field particles on screen SHALL NOT exceed 50
