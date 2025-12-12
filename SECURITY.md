# Security Policy

The security of pf-web-poly-compile-helper-runner is important to us. If you discover a security vulnerability, please follow these guidelines:

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by:

1. Opening a GitHub Security Advisory at: https://github.com/P4X-ng/pf-web-poly-compile-helper-runner/security/advisories/new
2. Or by creating a private issue with the `security` label and marking it as confidential

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: We aim to acknowledge receipt of your vulnerability report within 48 hours
- **Status Update**: We will send you regular updates about our progress, at least every 7 days
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### What to Expect

After you submit a report, we will:

1. Confirm the receipt of your vulnerability report
2. Investigate and validate the vulnerability
3. Work on a fix and coordinate with you on the disclosure timeline
4. Release a security update
5. Publicly acknowledge your responsible disclosure (if you wish)

## Security Best Practices

When using pf-web-poly-compile-helper-runner:

### Container Security

- Always run containers with appropriate security contexts
- Use read-only filesystems where possible
- Limit container capabilities to minimum required
- Keep container base images up to date

### Code Execution

- Be cautious when executing untrusted code with polyglot shell support
- Validate and sanitize all inputs to pf tasks
- Use containers or sandboxes for executing untrusted code
- Review Pfyfile configurations before execution

### Debugging and Development

- Do not expose debugging ports to untrusted networks
- Use strong authentication for remote debugging sessions
- Be aware that debugging tools (GDB, LLDB, etc.) can expose sensitive information

### Binary Injection and Exploitation Tools

- This repository includes educational tools for binary exploitation
- These tools should only be used in authorized testing environments
- Never use exploitation tools on systems without explicit permission
- Follow responsible disclosure practices for any vulnerabilities discovered

### REST API Security

- Use authentication and authorization for production deployments
- Bind API server to localhost (127.0.0.1) unless remote access is required
- Use HTTPS/TLS for remote API access
- Implement rate limiting and request validation

## Known Security Considerations

### Educational Security Tools

This repository contains educational tools for:
- Binary exploitation (ROP chains, buffer overflows)
- Kernel debugging and fuzzing
- Code injection techniques
- Web security testing

**Important**: These tools are for educational and authorized testing purposes only. Users are responsible for ensuring compliance with applicable laws and regulations.

### Polyglot Shell Execution

The polyglot shell feature allows executing code in 40+ languages. This is powerful but requires careful handling:
- Always validate and sanitize code before execution
- Use containers or sandboxes for untrusted code
- Be aware of the security implications of executing user-provided code

### Container and Privilege Escalation

Some features require elevated privileges or container runtime access. Always:
- Follow the principle of least privilege
- Review container configurations before deployment
- Use rootless containers where possible

## Disclosure Policy

When we receive a security vulnerability report, we follow these steps:

1. **Confirmation**: Confirm the vulnerability and determine its severity
2. **Development**: Develop and test a fix
3. **Release**: Release security updates
4. **Announcement**: Publish a security advisory with:
   - Description of the vulnerability
   - Affected versions
   - Fixed versions
   - Workarounds (if available)
   - Credit to the reporter (with permission)

## Security Updates

Security updates are released as:
- Patch versions (e.g., 1.0.1) for critical security fixes
- Minor versions (e.g., 1.1.0) for security enhancements

Subscribe to GitHub releases or watch this repository to receive security notifications.

## Additional Resources

- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Contact

For non-security issues, please use the regular GitHub issue tracker.

## Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors who report valid security issues will be acknowledged in our security advisories (unless they prefer to remain anonymous).
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
