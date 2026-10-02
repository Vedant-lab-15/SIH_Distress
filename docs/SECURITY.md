# Security Design

## Implemented in prototype

- Pydantic request validation.
- SQLAlchemy parameterized persistence.
- Optional API-key authentication.
- CORS allow-list configuration.
- Environment-based secret configuration.
- Audit events for interaction and prediction creation.
- Sensitive free-text is not written to application logs.
- Minimal synthetic identifiers in the demo.

## Production controls still required

- Institutional SSO / OIDC.
- Fine-grained RBAC/ABAC.
- TLS and secure cookie/token handling where applicable.
- Database encryption at rest and encrypted backups.
- Secret manager / key rotation.
- Network segmentation.
- Dependency and container vulnerability scanning.
- Centralized security monitoring.
- Rate limiting and abuse controls.
- Backup/restore testing.
- Incident response and breach procedures.
- Formal threat modeling and penetration testing.

No security certification is claimed.
