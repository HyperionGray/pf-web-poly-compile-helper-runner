#!/usr/bin/env python3
"""
MicroVM Swarm Orchestrator

Manages parallel execution of kernel fuzzing across multiple lightweight VMs
for scalable security testing.
"""

import os
import sys
import json
import time
import subprocess
import threading
import multiprocessing
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import argparse

@dataclass
class VMConfig:
    """VM configuration"""
    vm_id: str
    memory: int = 512  # MB
    vcpus: int = 1
    kernel_path: str = ""
    rootfs_path: str = ""
    network: bool = False
    
@dataclass
class FuzzJob:
    """Fuzzing job configuration"""
    job_id: str
    target: str
    duration: int
    fuzzer_config: Dict
    vm_config: VMConfig

class MicroVMSwarm:
    """Orchestrates multiple lightweight VMs for parallel fuzzing"""
    
    def __init__(self):
        self.vms = {}
        self.jobs = {}
        self.results = {}
        self.running = False
        
    def create_vm(self, vm_id: str, config: VMConfig) -> bool:
        """Create a new microVM"""
        try:
            # Use firecracker or similar lightweight VMM
            vm_cmd = self._build_vm_command(config)
            
            process = subprocess.Popen(
                vm_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.vms[vm_id] = {
                'config': config,
                'process': process,
                'status': 'starting',
                'start_time': time.time()
            }
            
            return True
            
        except Exception as e:
            print(f"Failed to create VM {vm_id}: {e}")
            return False
    
    def _build_vm_command(self, config: VMConfig) -> List[str]:
        """Build VM launch command"""
        # This would use firecracker, QEMU, or similar
        cmd = [
            'qemu-system-x86_64',
            '-enable-kvm',
            '-m', str(config.memory),
            '-smp', str(config.vcpus),
            '-nographic',
            '-serial', 'stdio',
        ]
        
        if config.kernel_path:
            cmd.extend(['-kernel', config.kernel_path])
        
        if config.rootfs_path:
            cmd.extend(['-drive', f'file={config.rootfs_path},format=raw'])
        
        if not config.network:
            cmd.extend(['-netdev', 'none'])
        
        return cmd
    
    def deploy_fuzzer(self, vm_id: str, fuzzer_path: str) -> bool:
        """Deploy fuzzer to VM"""
        if vm_id not in self.vms:
            return False
        
        try:
            # Copy fuzzer to VM (simplified - would use proper VM communication)
            # In practice, this would use SSH, virtio-fs, or similar
            return True
        except Exception as e:
            print(f"Failed to deploy fuzzer to {vm_id}: {e}")
            return False
    
    def start_fuzzing_job(self, job: FuzzJob) -> bool:
        """Start a fuzzing job on a VM"""
        vm_id = job.vm_config.vm_id
        
        if vm_id not in self.vms:
            if not self.create_vm(vm_id, job.vm_config):
                return False
        
        # Deploy fuzzer
        if not self.deploy_fuzzer(vm_id, "kernel_fuzzer.py"):
            return False
        
        # Start fuzzing job
        job_thread = threading.Thread(
            target=self._run_fuzzing_job,
            args=(job,)
        )
        job_thread.start()
        
        self.jobs[job.job_id] = {
            'job': job,
            'thread': job_thread,
            'status': 'running',
            'start_time': time.time()
        }
        
        return True
    
    def _run_fuzzing_job(self, job: FuzzJob):
        """Run fuzzing job in VM"""
        try:
            # Execute fuzzer in VM
            fuzzer_cmd = self._build_fuzzer_command(job)
            
            # In practice, this would execute inside the VM
            result = subprocess.run(
                fuzzer_cmd,
                capture_output=True,
                text=True,
                timeout=job.duration + 60
            )
            
            self.results[job.job_id] = {
                'job_id': job.job_id,
                'status': 'completed',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'end_time': time.time()
            }
            
        except subprocess.TimeoutExpired:
            self.results[job.job_id] = {
                'job_id': job.job_id,
                'status': 'timeout',
                'end_time': time.time()
            }
        except Exception as e:
            self.results[job.job_id] = {
                'job_id': job.job_id,
                'status': 'error',
                'error': str(e),
                'end_time': time.time()
            }
    
    def _build_fuzzer_command(self, job: FuzzJob) -> List[str]:
        """Build fuzzer command"""
        cmd = [
            'python3', 'kernel_fuzzer.py',
            job.target,
            '--duration', str(job.duration)
        ]
        
        # Add fuzzer-specific options
        for key, value in job.fuzzer_config.items():
            cmd.extend([f'--{key}', str(value)])
        
        return cmd
    
    def scale_swarm(self, target_vms: int, base_config: VMConfig):
        """Scale the VM swarm to target size"""
        current_vms = len(self.vms)
        
        if target_vms > current_vms:
            # Scale up
            for i in range(current_vms, target_vms):
                vm_id = f"vm_{i:03d}"
                config = VMConfig(
                    vm_id=vm_id,
                    memory=base_config.memory,
                    vcpus=base_config.vcpus,
                    kernel_path=base_config.kernel_path,
                    rootfs_path=base_config.rootfs_path
                )
                self.create_vm(vm_id, config)
        
        elif target_vms < current_vms:
            # Scale down
            vms_to_remove = list(self.vms.keys())[target_vms:]
            for vm_id in vms_to_remove:
                self.destroy_vm(vm_id)
    
    def destroy_vm(self, vm_id: str) -> bool:
        """Destroy a VM"""
        if vm_id not in self.vms:
            return False
        
        try:
            vm_info = self.vms[vm_id]
            process = vm_info['process']
            
            # Terminate VM process
            process.terminate()
            process.wait(timeout=10)
            
            del self.vms[vm_id]
            return True
            
        except Exception as e:
            print(f"Error destroying VM {vm_id}: {e}")
            return False
    
    def get_swarm_status(self) -> Dict:
        """Get status of entire swarm"""
        status = {
            'total_vms': len(self.vms),
            'active_jobs': len([j for j in self.jobs.values() 
                              if j['status'] == 'running']),
            'completed_jobs': len([r for r in self.results.values() 
                                 if r['status'] == 'completed']),
            'vms': {},
            'jobs': {}
        }
        
        for vm_id, vm_info in self.vms.items():
            status['vms'][vm_id] = {
                'status': vm_info['status'],
                'uptime': time.time() - vm_info['start_time']
            }
        
        for job_id, job_info in self.jobs.items():
            status['jobs'][job_id] = {
                'status': job_info['status'],
                'runtime': time.time() - job_info['start_time']
            }
        
        return status
    
    def shutdown_swarm(self):
        """Shutdown entire swarm"""
        print("Shutting down VM swarm...")
        
        # Stop all jobs
        for job_id in list(self.jobs.keys()):
            job_info = self.jobs[job_id]
            if job_info['status'] == 'running':
                # In practice, would send stop signal to VM
                pass
        
        # Destroy all VMs
        for vm_id in list(self.vms.keys()):
            self.destroy_vm(vm_id)
        
        print("Swarm shutdown complete")

def main():
    parser = argparse.ArgumentParser(description='MicroVM Swarm Orchestrator')
    parser.add_argument('--scale', type=int, default=4,
                       help='Number of VMs in swarm')
    parser.add_argument('--memory', type=int, default=512,
                       help='Memory per VM (MB)')
    parser.add_argument('--kernel', help='Kernel image path')
    parser.add_argument('--rootfs', help='Root filesystem path')
    parser.add_argument('--target', help='Fuzzing target')
    parser.add_argument('--duration', type=int, default=300,
                       help='Fuzzing duration per job')
    parser.add_argument('--jobs', type=int, default=1,
                       help='Number of fuzzing jobs')
    parser.add_argument('--output', '-o', help='Output file for results')
    
    args = parser.parse_args()
    
    swarm = MicroVMSwarm()
    
    try:
        # Create base VM configuration
        base_config = VMConfig(
            vm_id="base",
            memory=args.memory,
            kernel_path=args.kernel or "",
            rootfs_path=args.rootfs or ""
        )
        
        # Scale up swarm
        print(f"Scaling swarm to {args.scale} VMs...")
        swarm.scale_swarm(args.scale, base_config)
        
        # Create fuzzing jobs
        if args.target:
            jobs = []
            for i in range(args.jobs):
                job = FuzzJob(
                    job_id=f"job_{i:03d}",
                    target=args.target,
                    duration=args.duration,
                    fuzzer_config={},
                    vm_config=VMConfig(vm_id=f"vm_{i % args.scale:03d}")
                )
                jobs.append(job)
                swarm.start_fuzzing_job(job)
            
            # Monitor jobs
            print(f"Started {len(jobs)} fuzzing jobs")
            
            while True:
                status = swarm.get_swarm_status()
                print(f"Active jobs: {status['active_jobs']}, "
                      f"Completed: {status['completed_jobs']}")
                
                if status['active_jobs'] == 0:
                    break
                
                time.sleep(10)
            
            # Collect results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(swarm.results, f, indent=2)
            else:
                print(json.dumps(swarm.results, indent=2))
        
        else:
            # Just show swarm status
            status = swarm.get_swarm_status()
            print(json.dumps(status, indent=2))
    
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    
    finally:
        swarm.shutdown_swarm()

if __name__ == '__main__':
    main()