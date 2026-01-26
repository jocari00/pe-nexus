# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing the maintainers directly.

Include:
- Type of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive a response within 48 hours. If the issue is confirmed, we will release a patch as soon as possible.

## Security Considerations

PE-Nexus handles sensitive financial data. When deploying:

1. **API Keys**: Never commit API keys. Use environment variables.
2. **Database**: Use PostgreSQL in production with proper access controls.
3. **Network**: Deploy behind a reverse proxy with HTTPS.
4. **Authentication**: Implement proper authentication for production use.
5. **Data Encryption**: Consider encrypting sensitive financial data at rest.

## Disclosure Policy

We follow responsible disclosure. We will:
1. Confirm receipt of your report
2. Investigate and determine impact
3. Develop and test a fix
4. Release the fix and credit reporters (if desired)
