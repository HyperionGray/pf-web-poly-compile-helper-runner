/**
 * Small spawn helper with timeout and buffered stdout/stderr.
 *
 * NOTE: Intentionally does not override `env`; callers should avoid env-var
 * based configuration and instead use CLI flags or config files.
 */

import { spawn } from 'child_process';

export function runCommand(command, args = [], { cwd, timeoutMs = 30000 } = {}) {
  return new Promise((resolve) => {
    const start = Date.now();
    const child = spawn(command, args, { cwd, stdio: 'pipe' });

    let stdout = '';
    let stderr = '';
    let settled = false;

    const finish = (payload) => {
      if (settled) return;
      settled = true;
      resolve({
        command,
        args,
        cwd,
        stdout,
        stderr,
        durationMs: Date.now() - start,
        ...payload
      });
    };

    child.stdout.on('data', (d) => {
      stdout += d.toString();
    });
    child.stderr.on('data', (d) => {
      stderr += d.toString();
    });

    child.on('error', (err) => {
      finish({ exitCode: -1, success: false, error: err.message });
    });

    child.on('close', (code) => {
      finish({ exitCode: code ?? -1, success: code === 0 });
    });

    const t = setTimeout(() => {
      try {
        child.kill('SIGTERM');
      } catch {
        // ignore
      }
      finish({ exitCode: -1, success: false, timedOut: true });
    }, timeoutMs);

    child.on('exit', () => clearTimeout(t));
  });
}

