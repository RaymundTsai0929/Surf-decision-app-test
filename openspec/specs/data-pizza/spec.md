# data-pizza Specification

## Purpose

TBD - created by archiving change 'surf-decision-app'. Update Purpose after archive.

## Requirements

### Requirement: SVG sector chart with raw data values

The system SHALL render an SVG-based sector (pizza) chart in the upper portion of the right 38.2% panel of Screen 2 (Landscape). The chart SHALL display five sectors, each containing a raw numeric value. No color SHALL be used to imply danger level; sector colors are used solely for visual differentiation between sectors.

#### Scenario: Five sectors rendered with current data

- **WHEN** Screen 2 is displayed and CWA + SAR data is available
- **THEN** five equal sectors are rendered, each labeled and containing a raw number

##### Example: sector content

| Sector | Label | Unit | Example Value |
|--------|-------|------|---------------|
| 1 | 浪高 | m | 1.5 |
| 2 | 週期 | s | 8 |
| 3 | 風速 | m/s | 12 |
| 4 | 流速 | m/s | 0.4 |
| 5 | 漂流速 | m/s | 1.2 |

#### Scenario: No scores or levels displayed

- **WHEN** the pizza chart renders
- **THEN** no numerical score, percentage, star rating, danger level label, or traffic-light color coding SHALL appear anywhere in the chart

#### Scenario: Missing data in a sector

- **WHEN** a value for a sector is unavailable
- **THEN** the sector displays `--` instead of a number and retains its sector shape
