---
id: 1
title: Fix login bug
status: backlog
priority: critical
created: 2026-01-15T10:00:00+00:00
updated: 2026-01-15T10:00:00+00:00
project: example-app
tags:
  - bug
  - auth
depends_on: []
cos: expedite
---

## Description
Users cannot log in when using SSO authentication.

## Steps to Reproduce
1. Go to /login
2. Click "Sign in with Google"
3. Complete OAuth flow
4. See error: "Invalid state parameter"

## Expected Behavior
User should be logged in and redirected to dashboard.

## Acceptance Criteria
- [ ] SSO login works with Google
- [ ] SSO login works with GitHub
- [ ] Error is logged for debugging
- [ ] Tests pass
