# Privacy and Safety Notes

This repository is designed as a prototype with synthetic data.

## Data minimization

The demo stores only fields needed to illustrate longitudinal prediction and review. Avoid collecting names, addresses, phone numbers, precise geolocation, or other identifiers unless a separately approved production design requires them.

## Synthetic vs real data

The included dataset is explicitly synthetic. It must not be represented as clinical evidence, a government dataset, or real victim records.

## Access control

Local demo authentication is disabled by default. Production should enable institutional authentication and role-based authorization, use short-lived credentials/tokens, and separate least-privilege permissions for reviewers, administrators and operators.

## Secrets

Secrets must be supplied through environment variables or a managed secret store. Never commit `.env`, credentials or API keys.

## Transport and storage protection

Use TLS for deployed APIs and encrypt production databases/backups at rest. The demo's SQLite file is not a substitute for a secured production data store.

## Audit logging

Prediction creation, interaction storage and demo seeding create audit records. Do not include sensitive free-text content or secrets in logs.

## Retention

Define and enforce a documented retention schedule based on the actual institutional and legal context. Do not retain interaction data indefinitely by default.

## Consent and governance

Before real deployment, define lawful basis/consent and human-review procedures appropriate to the actual jurisdiction and organization.

## Compliance

The software is designed with privacy principles in mind; formal legal/compliance review is required before real-world deployment. No claim of GDPR, DPDP, HIPAA or other legal certification is made.

## Emergency support

The application intentionally does not invent or hard-code a real emergency/helpline number. Configure the official approved contact through `EMERGENCY_CONTACT_PLACEHOLDER`.
