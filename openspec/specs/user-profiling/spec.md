# user-profiling Specification

## Purpose

TBD - created by archiving change 'surf-decision-app'. Update Purpose after archive.

## Requirements

### Requirement: Mandatory onboarding quiz

The system SHALL present a mandatory quiz to first-time users before allowing access to the main app. The quiz SHALL consist of 5 to 10 questions drawn randomly from a question bank. Question types SHALL vary (multiple-choice, scenario-based, true/false) and SHALL NOT follow a fixed sequence.

#### Scenario: First launch triggers quiz

- **WHEN** the app is launched and no quiz completion record exists in localStorage
- **THEN** the quiz screen is displayed before the Taiwan map entry screen

#### Scenario: User skips the quiz

- **WHEN** the user exits the quiz without completing it
- **THEN** the system assigns the most conservative internal level (cautious) and stores the skip record in localStorage

#### Scenario: Quiz questions are randomized

- **WHEN** the quiz is presented
- **THEN** each quiz session draws questions in random order from the question bank with random question types

---
### Requirement: Internal three-level classification

The system SHALL classify the user into one of three internal levels based on quiz responses: cautious, understanding, or proficient. The level SHALL be stored in localStorage and SHALL NOT be displayed to the user in any form.

#### Scenario: Level assigned after quiz completion

- **WHEN** the user completes all quiz questions
- **THEN** the system computes an internal level and stores it in localStorage without presenting the result to the user

##### Example: level assignment thresholds

| Correct Thinking Responses | Assigned Level |
|----------------------------|----------------|
| 0 – 40% | cautious |
| 41 – 70% | understanding |
| 71 – 100% | proficient |

#### Scenario: Level not visible to user

- **WHEN** the user navigates any screen of the app
- **THEN** no label, badge, icon, or text indicating the user's internal level SHALL be shown

---
### Requirement: Weekly quiz cooldown

The system SHALL enforce a minimum 7-day cooldown between quiz retakes. The cooldown is calculated from the timestamp of the last completed or skipped quiz stored in localStorage.

#### Scenario: User attempts retake within 7 days

- **WHEN** the user navigates to retake the quiz and fewer than 7 days have elapsed since the last attempt
- **THEN** the retake is blocked and the remaining cooldown duration is displayed

#### Scenario: User retakes quiz after cooldown expires

- **WHEN** 7 or more days have elapsed since the last quiz attempt
- **THEN** a new quiz session is presented and the result updates the stored level in localStorage
