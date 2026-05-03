## ADDED Requirements

### Requirement: Taiwan region map entry

The app SHALL display a full Taiwan island map as the entry screen, divided into four clickable regions (North, East, South, West).

#### Scenario: User opens app for the first time

- **WHEN** the user opens the app after completing or skipping onboarding
- **THEN** the full Taiwan island map is displayed with four region zones visible

#### Scenario: User taps a region

- **WHEN** the user taps the East region
- **THEN** the map zooms into the east coast and displays surf spot pins for that region

### Requirement: Surf spot pins with condition color

The system SHALL display a pin marker for each configured surf spot within the zoomed region. Each pin SHALL show the spot name and a color representing the aggregated current conditions for that spot (green = mild conditions, red = severe conditions). This color is a navigation-layer indicator only and does not constitute a safety rating.

#### Scenario: Spot pins appear after region zoom

- **WHEN** the map has zoomed into a region
- **THEN** pins appear at the configured coordinates for each spot in that region, each labeled with the spot name

#### Scenario: Pin color reflects aggregated conditions

- **WHEN** CWA data is available for a spot
- **THEN** the pin color is computed from the aggregated conditions snapshot and rendered on a green-to-red scale

##### Example: pin color thresholds

| Wave Height | Wind Speed | Pin Color |
|-------------|------------|-----------|
| ≤ 1.0m | ≤ 10 m/s | green |
| 1.0–1.5m | 10–15 m/s | yellow |
| 1.5–2.0m | 15–20 m/s | orange |
| > 2.0m | > 20 m/s | red |

#### Scenario: No CWA data available for a spot

- **WHEN** CWA data cannot be fetched for a spot
- **THEN** the pin is displayed in grey and no color classification is applied

### Requirement: Navigate to spot detail

The system SHALL navigate the user to the spot detail view (Screen 1 Portrait) when a spot pin is tapped.

#### Scenario: User taps a spot pin

- **WHEN** the user taps a spot pin
- **THEN** the app transitions to Screen 1 (Portrait) showing the satellite map and data table for that spot
