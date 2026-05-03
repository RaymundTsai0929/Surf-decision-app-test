## ADDED Requirements

### Requirement: Hourly CWA data table display

The system SHALL display a scrollable hourly data table in Screen 1 (Portrait, lower 61.8% golden ratio section) populated from the CWA coastal weather API. The current time column SHALL be highlighted with a distinct background.

#### Scenario: Table renders with CWA data

- **WHEN** CWA hourly data is fetched successfully
- **THEN** the table displays columns for each hour and rows for: wave height (m), wave period (s), wave direction, wind speed (m/s), wind direction, gust (m/s), weather icon, air temperature (°C), sea temperature (°C), tide (m)

#### Scenario: Current time column highlighted

- **WHEN** the table is rendered
- **THEN** the column corresponding to the current hour is displayed with a highlighted background distinct from other columns

#### Scenario: Missing data displayed as placeholder

- **WHEN** a CWA data field is null or absent
- **THEN** the cell displays `--` instead of a number

### Requirement: Per-column color coding with fixed thresholds

Each data column SHALL apply a background color to numeric cells based on fixed global thresholds. Color is applied per-column independently and SHALL NOT be interpreted as a danger rating.

#### Scenario: Wave height color applied

- **WHEN** a wave height cell value is rendered
- **THEN** the cell background color follows the blue-scale threshold

##### Example: wave height color thresholds

| Wave Height (m) | Background Color |
|-----------------|-----------------|
| < 0.5 | very light blue |
| 0.5 – 1.0 | light blue |
| 1.0 – 1.5 | medium blue |
| 1.5 – 2.0 | blue |
| > 2.0 | deep blue |

#### Scenario: Wind speed color applied

- **WHEN** a wind speed cell value is rendered
- **THEN** the cell background color follows the green-to-orange threshold

##### Example: wind speed color thresholds

| Wind Speed (m/s) | Background Color |
|------------------|-----------------|
| < 5 | green |
| 5 – 10 | yellow-green |
| 10 – 15 | yellow |
| 15 – 20 | orange |
| > 20 | deep orange |

#### Scenario: Gust color applied

- **WHEN** a gust cell value is rendered
- **THEN** the cell background color follows the shifted green-to-orange threshold

##### Example: gust color thresholds

| Gust (m/s) | Background Color |
|------------|-----------------|
| < 8 | green |
| 8 – 13 | yellow |
| 13 – 20 | orange |
| > 20 | deep orange |

#### Scenario: Tide color applied using relative scale

- **WHEN** tide cells are rendered
- **THEN** the minimum tide value in the dataset is green and the maximum tide value is pink, with interpolation between

#### Scenario: Wave period has no color

- **WHEN** a wave period cell is rendered
- **THEN** no background color is applied; the raw number is displayed on a neutral background
