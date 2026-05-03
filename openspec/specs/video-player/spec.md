# video-player Specification

## Purpose

TBD - created by archiving change 'surf-decision-app'. Update Purpose after archive.

## Requirements

### Requirement: Pre-recorded video playback in landscape screen

The system SHALL play a locally stored pre-recorded video file in the left 61.8% (golden ratio) section of Screen 2 (Landscape). The video SHALL autoplay, loop, and be muted by default to satisfy iOS Safari autoplay policy.

#### Scenario: User swipes to landscape screen

- **WHEN** the user swipes to enter Screen 2 (Landscape)
- **THEN** the video begins playing automatically without requiring user interaction

#### Scenario: Video loops continuously

- **WHEN** the video reaches its end
- **THEN** the video restarts from the beginning without user interaction

#### Scenario: iOS Safari autoplay compliance

- **WHEN** the VideoPlayer component mounts on any browser
- **THEN** the video element SHALL have the attributes `muted`, `playsInline`, and `autoPlay` set to satisfy mobile browser autoplay restrictions

---
### Requirement: Video fills its container proportionally

The video SHALL fill the left 61.8% panel of Screen 2 using `object-fit: cover` so the aspect ratio is maintained without letterboxing.

#### Scenario: Video container rendered

- **WHEN** Screen 2 is displayed
- **THEN** the video fills the left panel without horizontal or vertical black bars on standard mobile aspect ratios
