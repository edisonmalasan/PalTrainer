# ui-states Delta

## Purpose

Defines how PalTrainer presents empty, loading, and guidance states on content pages (Pal Editor, Breeding, Map, Docs, Tools, table pages) and on the shell's status strip, so users always know what to do next instead of facing a blank canvas.

## ADDED Requirements

(none)

## MODIFIED Requirements

### Requirement: Status strip surfaces streamed operation messages

The system SHALL provide a visible bottom status strip that displays streamed load/save/log messages, replacing the hidden zero-height status bar, with the detachable console window behavior preserved. The strip SHALL present one short human-readable message at a time; raw technical payloads (exception text, HTTP status codes, decompression byte statistics) route to the application log/console instead of the strip, and update-check failures surface through the app-bar warning affordance states rather than persistent strip text.

#### Scenario: Save loads with visible feedback

- **WHEN** a save finishes loading
- **THEN** the status strip shows a short human result message (for example "Save loaded") without requiring the console to be detached, and no byte-count statistics render in the strip

#### Scenario: Console detach still available

- **WHEN** the user toggles the console utility from the app bar
- **THEN** streamed messages route to the detached console window and the status strip remains functional afterwards

#### Scenario: Technical payloads are demoted

- **WHEN** an operation emits exception text, an HTTP error, or decompression statistics
- **THEN** the full payload is visible in the log/console while the strip shows either a summarized human message or its neutral ready message
