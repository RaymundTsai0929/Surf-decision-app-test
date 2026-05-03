# ability-deflation Specification

## Purpose

TBD - created by archiving change 'surf-decision-app'. Update Purpose after archive.

## Requirements

### Requirement: Fixed one-level deflation from quiz result

The system SHALL automatically reduce the user's assessed level by one step as a fixed safety margin before computing the effective level used for AI narrative. This deflation SHALL be hidden from the user.

#### Scenario: Proficient user deflated to understanding

- **WHEN** the user's quiz level is proficient
- **THEN** the base effective level before condition checks is understanding

#### Scenario: Understanding user deflated to cautious

- **WHEN** the user's quiz level is understanding
- **THEN** the base effective level before condition checks is cautious

#### Scenario: Cautious user remains at cautious

- **WHEN** the user's quiz level is cautious (already minimum)
- **THEN** the base effective level remains cautious

---
### Requirement: Condition-triggered additional deflation

The system SHALL apply additional deflation to the effective level when current CWA data or SAR results exceed defined thresholds. Multiple conditions MAY trigger simultaneously; each reduces the effective level by one additional step unless the minimum (cautious) is already reached.

#### Scenario: Wave height exceeds 2m

- **WHEN** the current wave height from CWA is greater than 2.0 m
- **THEN** the effective level is reduced by one additional step

#### Scenario: Wave period below 7s

- **WHEN** the current wave period from CWA is less than 7 seconds
- **THEN** the AI narrative input is flagged to include an irregular wave form note (does not change level numerically but modifies narrative context)

#### Scenario: Wind speed exceeds 25 kt

- **WHEN** the current wind speed from CWA exceeds 25 knots
- **THEN** the effective level is reduced by one additional step

#### Scenario: SAR drift speed exceeds threshold

- **WHEN** the computed SAR drift resultant speed exceeds 1.5 m/s
- **THEN** the effective level is reduced by one additional step

---
### Requirement: Dangerous drift endpoint locks to cautious

The system SHALL lock the effective level to cautious regardless of other calculations when the SAR drift simulation determines the trajectory endpoint is within a pre-defined danger zone of a surf spot (reef, breakwater, seawall).

#### Scenario: Drift trajectory terminates near dangerous object

- **WHEN** the SAR simulation endpoint coordinate is within 50 meters of a registered danger zone coordinate for the selected spot
- **THEN** the effective level is set to cautious and no further deflation or inflation is applied

#### Scenario: Effective level cannot drop below cautious

- **WHEN** multiple conditions trigger additional deflation simultaneously
- **THEN** the effective level SHALL NOT go below cautious regardless of how many conditions are triggered

##### Example: multi-condition deflation cap

- **GIVEN** quiz level = proficient, wave height = 2.5m, wind = 28kt, drift speed = 2.0 m/s
- **WHEN** deflation is computed
- **THEN** base = understanding (fixed -1), wave height → cautious (-1), wind → cautious already, drift speed → cautious already; final effective level = cautious
