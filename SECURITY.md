# Security Policy

## Supported Versions

We actively maintain and provide security updates for:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by:

1. **DO NOT** create a public GitHub issue
2. Create a private security advisory on GitHub or contact maintainers
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Investigation**: We will validate the vulnerability
- **Timeline**: Initial response within 5 business days
- **Updates**: Regular progress updates
- **Credit**: You will be credited in security advisories

## Security Considerations

### pf Task Runner Security

- Review task definitions before execution, especially from untrusted sources
- Be cautious with remote execution (`hosts=` parameter)
- Validate parameters passed to tasks
- Use containers when possible for isolation

### Binary Analysis & Debugging Tools

- These are legitimate security research tools
- Users are responsible for legal and ethical use
- Obtain proper authorization before testing systems
- Follow responsible disclosure practices

### Container Security

- Container images built from Ubuntu 24.04
- Some debugging features require privileged containers
- Be careful with volume mounts
- Consider network isolation for untrusted workloads

For security questions, please:
- Create a private security advisory on GitHub
- Contact maintainers through appropriate channels
- Follow responsible disclosure practices

Thank you for helping keep this project secure!
