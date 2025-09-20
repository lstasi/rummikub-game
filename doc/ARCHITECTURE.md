# Architecture

This document will be updated as tasks progress. It describes the high-level system design for the Rummikub game application.

- Components: Models, Engine, Service (Redis), API (FastAPI), UI, Docker/Compose
- Data flow: Client -> API -> Service -> Redis; Service -> Engine -> Models
- Non-functional goals: reliability, testability, containerized deployment

Updates to this file must precede code changes in related tasks.
