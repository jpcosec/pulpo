# Architecture Documentation

Generated automatically from your `@datamodel` and `@operation` decorators.

## Overview

- **Models**: 5
- **Operations**: 7

## Diagrams

### [Operation Flow](./operation-flow.md)
Shows how operations connect data models. Models are nodes, operations are edges showing data transformation paths.

### [Model Relationships](./model-relationships.md)
Shows foreign keys and references between models. Displays data dependencies and entity relationships.

## How to Update

1. Modify your `@datamodel` or `@operation` decorators
2. Run `make compile`
3. Graphs will be regenerated automatically

## Legend

- **@datamodel**: Decorated classes become nodes (models)
- **@operation**: Decorated functions become edges (transformations)
- **models_in/models_out**: Define which models an operation connects
