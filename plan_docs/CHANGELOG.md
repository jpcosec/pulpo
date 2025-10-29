# Changelog

All notable changes to the JobHunter Core Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-16

### Added
- Initial release of JobHunter Core Framework
- `@datamodel` decorator for registering Beanie Document models
- `@operation` decorator for registering typed operations
- `ModelRegistry` for centralized model metadata storage
- `OperationRegistry` for centralized operation metadata storage
- FastAPI code generation from model decorators
- React + Refine.dev UI generation with CRUD pages
- TypeScript configuration generation for frontend
- CLI integration via Typer
- MongoDB/Beanie database integration
- Prefect workflow orchestration support
- TaskRun observability model for operation tracking
- Docker deployment configuration
- Comprehensive documentation suite
- Example models and operations for testing and demonstration

### Framework Features
- Metadata-driven "Define Once, Generate Everywhere" architecture
- Auto-generated REST API with CRUD endpoints
- Auto-generated admin UI with list/show/create/edit pages
- Auto-generated CLI commands from operations
- Cache-aware code generation with hash-based invalidation
- Optional base classes for enhanced functionality
- Extensible code generator architecture

[0.1.0]: https://github.com/yourorg/jobhunter-core/releases/tag/v0.1.0
