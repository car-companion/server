# Security Policy

## Supported Versions

The following versions of Car Companion Backend are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Car Companion Backend seriously. If you believe you have found a security vulnerability, please report it to us following these steps:

1. **Do NOT** disclose the vulnerability publicly until it has been resolved.
2. Send a detailed report to carcompanionapp@gmail.com including:
   - A description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Any suggested fixes (if available)

### What to expect

- Acknowledgment of your report within 48 hours
- Regular updates on the progress (every 3-5 days)
- An assessment of the vulnerability and its impact
- A timeline for addressing the vulnerability
- Notification when the vulnerability is fixed

### Bug Bounty Program

Currently, we do not offer a bug bounty program. However, we will acknowledge security researchers who report valid vulnerabilities in our release notes.

### Vulnerability Assessment

Our team will assess reported vulnerabilities based on:
- Severity of potential impact
- Complexity of exploitation
- Authentication requirements
- Potential exposure of sensitive data

### Disclosure Policy

- Security issues will be patched as quickly as possible
- After a fix is deployed, reporters may disclose the vulnerability
- We will publish security advisories for confirmed vulnerabilities

## Security Best Practices

When using Car Companion Backend, ensure you:
- Keep all dependencies up to date
- Use environment variables for sensitive configuration
- Enable HTTPS in production
- Follow the principle of least privilege for component permissions
- Regularly rotate JWT secrets
- Monitor logs for suspicious activity

This policy may be updated at any time based on evolving security needs and practices.
