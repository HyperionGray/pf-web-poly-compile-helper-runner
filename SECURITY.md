# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in pf-web-poly-compile-helper-runner, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. **Email** the maintainers directly or create a private security advisory on GitHub
3. **Include** as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Investigation**: We will investigate and validate the vulnerability
- **Timeline**: We aim to provide an initial response within 5 business days
- **Updates**: We will keep you informed of our progress
- **Credit**: We will credit you in our security advisory (unless you prefer to remain anonymous)

## Security Considerations

### pf Task Runner Security

The pf task runner executes shell commands and code in multiple languages. When using pf:

- **Review task definitions** before execution, especially from untrusted sources
- **Be cautious with remote execution** (`hosts=` parameter) - ensure SSH keys and access are properly secured
- **Validate parameters** passed to tasks, especially when accepting user input
- **Use containers** when possible to isolate execution environments

### Polyglot Shell Execution

The polyglot shell feature executes code in 40+ languages:

- **Code injection risks**: Never pass untrusted input directly to shell commands
- **Language-specific security**: Each supported language has its own security considerations
- **File system access**: Be aware that executed code has access to the file system
- **Network access**: Executed code can make network requests

### Container Security

When using the container infrastructure:

- **Image security**: Container images are built from Ubuntu 24.04 with debugging tools
- **Privileged containers**: Some debugging features may require privileged containers
- **Volume mounts**: Be careful with volume mounts, especially rshared mounts
- **Network isolation**: Consider network isolation for untrusted workloads

### WebAssembly Compilation

WASM compilation involves multiple toolchains:

- **Toolchain security**: Keep Rust, Emscripten, and other toolchains updated
- **Supply chain**: Verify integrity of downloaded toolchains and dependencies
- **Sandboxing**: WASM provides some sandboxing, but host system access is still possible

### Binary Injection and Debugging

The binary injection and debugging features are powerful but potentially dangerous:

- **Code injection**: Only inject code you trust into binaries
- **Privilege escalation**: Debugging tools may require elevated privileges
- **System modification**: Binary patching can modify system behavior
- **Reverse engineering**: Use these tools responsibly and legally

### Web Security Testing

The web security testing framework includes vulnerability scanners:

- **Authorization**: Only test applications you own or have explicit permission to test
- **Rate limiting**: Be respectful of target systems and implement appropriate delays
- **Legal compliance**: Ensure your security testing complies with applicable laws
- **Data handling**: Be careful with sensitive data discovered during testing

### REST API Security

The REST API server provides remote access to pf functionality:

- **Authentication**: The API currently has no built-in authentication - implement your own if needed
- **Network exposure**: By default, the API binds to localhost only
- **Input validation**: API endpoints execute pf tasks - validate all input
- **Rate limiting**: Consider implementing rate limiting for production use

## Security Best Practices

### For Users

1. **Keep dependencies updated**: Regularly update Python packages, Node.js dependencies, and system packages
2. **Use containers**: Isolate potentially dangerous operations in containers
3. **Review code**: Always review task definitions and scripts before execution
4. **Limit privileges**: Run with minimal necessary privileges
5. **Network security**: Use firewalls and network isolation appropriately

### For Contributors

1. **Secure coding**: Follow secure coding practices for all languages used
2. **Input validation**: Validate all user input and parameters
3. **Dependency management**: Keep dependencies updated and audit for vulnerabilities
4. **Code review**: All code changes should be reviewed for security implications
5. **Testing**: Include security testing in your test suites

### For Deployment

1. **Environment isolation**: Use separate environments for development, testing, and production
2. **Access control**: Implement proper access controls for systems running pf
3. **Monitoring**: Monitor for unusual activity or unauthorized access
4. **Backup and recovery**: Maintain secure backups and test recovery procedures
5. **Incident response**: Have a plan for responding to security incidents

## Known Security Considerations

### Inherent Risks

This project includes tools for:
- **Binary manipulation and injection**
- **Kernel debugging and fuzzing**
- **Web application security testing**
- **Reverse engineering and exploitation**

These are legitimate security research and development tools, but they can be misused. Users are responsible for:
- Using these tools legally and ethically
- Obtaining proper authorization before testing systems
- Following responsible disclosure practices
- Complying with applicable laws and regulations

### Mitigation Strategies

- **Education**: Comprehensive documentation explains proper usage
- **Containerization**: Dangerous operations can be isolated in containers
- **Privilege separation**: Tools can run with minimal necessary privileges
- **Audit logging**: Operations can be logged for accountability

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 1-2**: Acknowledgment sent to reporter
3. **Day 3-7**: Initial investigation and validation
4. **Day 8-30**: Development of fix (timeline depends on severity)
5. **Day 31+**: Public disclosure after fix is available

Critical vulnerabilities may have accelerated timelines.

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Container Security Best Practices](https://kubernetes.io/docs/concepts/security/)

## Contact

For security-related questions or concerns, please:
- Create a private security advisory on GitHub
- Contact the maintainers through appropriate channels
- Follow responsible disclosure practices

Thank you for helping keep pf-web-poly-compile-helper-runner secure!