# Changelog

All notable changes to PE-Nexus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- FAIR compliance metadata files (LICENSE, CITATION.cff, codemeta.json)

## [0.1.0] - 2024-01-21

### Added
- Deal pipeline management with state machine transitions
- Document upload and processing infrastructure
- ForensicAnalyst agent for financial extraction with full traceability
- IntelligenceScout agent for deal sourcing
- RelationshipNavigator agent for network path finding
- FastAPI-based REST API with OpenAPI documentation
- SQLAlchemy database models for deals, documents, and financials
- ChromaDB integration for vector search
- Event-driven architecture with async event bus
- Comprehensive Pydantic schemas for data validation
- Full source traceability for all extracted values

### Infrastructure
- SQLite database for development
- ChromaDB for vector storage
- Pytest test suite with async support

[Unreleased]: https://github.com/jordi/pe-nexus/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jordi/pe-nexus/releases/tag/v0.1.0
