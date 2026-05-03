# ai-narrative Specification

## Purpose

TBD - created by archiving change 'surf-decision-app'. Update Purpose after archive.

## Requirements

### Requirement: Claude API narrative generation

The system SHALL call the Claude API (model: claude-sonnet-4-6) when the user enters Screen 2 (Landscape) to generate a 2–3 paragraph Traditional Chinese narrative describing current surf conditions for the selected spot. The narrative SHALL NOT contain scores, numeric ratings, danger levels, or traffic-light language.

#### Scenario: Narrative triggered on Screen 2 entry

- **WHEN** the user swipes into Screen 2 for the first time for a given spot in the current session
- **THEN** the system sends a request to the Claude API and displays a loading skeleton in the narrative panel

#### Scenario: Narrative displayed after response

- **WHEN** the Claude API response is received
- **THEN** the loading skeleton is replaced with the 2–3 paragraph Traditional Chinese text

#### Scenario: Narrative contains no rating language

- **WHEN** the narrative is rendered
- **THEN** no words such as 危險等級, 幾顆星, 評分, 紅燈, 黃燈, 綠燈, 不建議 expressed as a directive SHALL appear in the output

---
### Requirement: Prompt caching for system prompt

The system prompt sent to the Claude API SHALL be marked with cache_control to enable prompt caching, reducing latency and cost for repeated calls with the same base context.

#### Scenario: System prompt uses cache_control

- **WHEN** the Claude API request is constructed
- **THEN** the system prompt block includes `"cache_control": {"type": "ephemeral"}` in the Anthropic API message format

---
### Requirement: Narrative input includes effective level and data snapshot

The user message sent to Claude SHALL include: effective level (cautious / understanding / proficient), spot name, current CWA data snapshot (wave height, period, wind speed, wind direction, gust, tide, sea temperature), SAR drift resultant speed, and drift endpoint danger flag.

#### Scenario: All inputs present in user message

- **WHEN** the API request is assembled
- **THEN** the user message payload contains all seven data fields plus the effective level and danger flag

---
### Requirement: Result cached per spot per hour

The system SHALL cache the Claude narrative response in memory (not localStorage) and reuse it for the same spot within the same clock hour, avoiding duplicate API calls.

#### Scenario: User re-enters Screen 2 within the same hour

- **WHEN** the user navigates away from Screen 2 and returns within the same clock hour for the same spot
- **THEN** the cached narrative is displayed immediately without a new API call

#### Scenario: Cache expires on the hour boundary

- **WHEN** the user enters Screen 2 after the clock hour has changed since the last fetch
- **THEN** a new Claude API call is made and the cache is updated

---
### Requirement: API parameters

The Claude API call SHALL use max_tokens: 400 and temperature: 0.3.

#### Scenario: API call parameters enforced

- **WHEN** the Claude API request is sent
- **THEN** the request body includes `max_tokens: 400` and `temperature: 0.3`
