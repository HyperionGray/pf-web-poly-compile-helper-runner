#!/usr/bin/env python3
"""
Firmware Extraction and Analysis Tool

Integrates with flashrom and other firmware extraction tools to provide
automated firmware dumping, unpacking, and analysis capabilities.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import argparse

@dataclass
class FirmwareInfo:
    """Information about extracted firmware"""
    device: str
    chip_type: str
    size: int
    filename: str
    checksum: str
    extraction_method: str
    analysis_results: Dict = None

class FirmwareExtractor:
    """Firmware extraction and analysis system"""
    
    def __init__(self):
        self.supported_tools = {
            'flashrom': self._check_flashrom,
            'binwalk': self._check_binwalk,
            'firmware-mod-kit': self._check_fmk,
            'jefferson': self._check_jefferson,
        }
        self.available_tools = self._check_available_tools()
    
    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which firmware tools are available"""
        available = {}
        for tool, check_func in self.supported_tools.items():
            available[tool] = check_func()
        return available
    
    def _check_flashrom(self) -> bool:
        """Check if flashrom is available"""
        try:
            result = subprocess.run(['flashrom', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_binwalk(self) -> bool:
        """Check if binwalk is available"""
        try:
            result = subprocess.run(['binwalk', '--help'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_fmk(self) -> bool:
        """Check if firmware-mod-kit is available"""
        return shutil.which('extract-firmware.sh') is not None
    
    def _check_jefferson(self) -> bool:
        """Check if jefferson (JFFS2 extractor) is available"""
        try:
            result = subprocess.run(['jefferson', '--help'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def list_devices(self) -> List[Dict]:
        """List available devices for firmware extraction"""
        if not self.available_tools.get('flashrom'):
            return []
        
        try:
            result = subprocess.run(['flashrom', '--list-supported'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return self._parse_flashrom_devices(result.stdout)
        except Exception as e:
            print(f"Error listing devices: {e}")
        
        return []
    
    def _parse_flashrom_devices(self, output: str) -> List[Dict]:
        """Parse flashrom device list output"""
        devices = []
        # Simplified parser - real implementation would be more comprehensive
        for line in output.split('\n'):
            if 'Supported flash chips:' in line:
                continue
            if line.strip() and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({
                        'name': parts[0],
                        'size': parts[1] if len(parts) > 1 else 'unknown'
                    })
        return devices
    
    def extract_firmware(self, device: str = None, programmer: str = 'internal', 
                        output_file: str = None) -> Optional[FirmwareInfo]:
        """Extract firmware from device using flashrom"""
        if not self.available_tools.get('flashrom'):
            raise RuntimeError("flashrom not available")
        
        if not output_file:
            output_file = f"firmware_{device or 'unknown'}.bin"
        
        cmd = ['flashrom', '-p', programmer, '-r', output_file]
        if device:
            cmd.extend(['-c', device])
        
        try:
            print(f"Extracting firmware with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_file):
                # Get file info
                size = os.path.getsize(output_file)
                checksum = self._calculate_checksum(output_file)
                
                firmware_info = FirmwareInfo(
                    device=device or 'unknown',
                    chip_type='unknown',
                    size=size,
                    filename=output_file,
                    checksum=checksum,
                    extraction_method='flashrom'
                )
                
                return firmware_info
            else:
                print(f"Flashrom error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error extracting firmware: {e}")
            return None
    
    def _calculate_checksum(self, filepath: str) -> str:
        """Calculate SHA256 checksum of file"""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def analyze_firmware(self, firmware_path: str) -> Dict:
        """Analyze extracted firmware"""
        analysis = {
            'file_info': self._get_file_info(firmware_path),
            'binwalk_results': None,
            'strings_analysis': None,
            'entropy_analysis': None,
            'extracted_files': []
        }
        
        # Run binwalk analysis
        if self.available_tools.get('binwalk'):
            analysis['binwalk_results'] = self._run_binwalk(firmware_path)
        
        # Extract strings
        analysis['strings_analysis'] = self._extract_strings(firmware_path)
        
        # Entropy analysis
        analysis['entropy_analysis'] = self._analyze_entropy(firmware_path)
        
        return analysis
    
    def _get_file_info(self, filepath: str) -> Dict:
        """Get basic file information"""
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'checksum': self._calculate_checksum(filepath),
            'file_type': self._get_file_type(filepath)
        }
    
    def _get_file_type(self, filepath: str) -> str:
        """Get file type using file command"""
        try:
            result = subprocess.run(['file', filepath], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'
    
    def _run_binwalk(self, filepath: str) -> Dict:
        """Run binwalk analysis on firmware"""
        try:
            # Basic binwalk scan
            result = subprocess.run(['binwalk', filepath], 
                                  capture_output=True, text=True)
            
            binwalk_output = result.stdout if result.returncode == 0 else ""
            
            # Extract files if possible
            extract_dir = f"{filepath}_extracted"
            extract_result = subprocess.run(['binwalk', '-e', '-C', extract_dir, filepath], 
                                          capture_output=True, text=True)
            
            return {
                'scan_output': binwalk_output,
                'extraction_successful': extract_result.returncode == 0,
                'extract_directory': extract_dir if extract_result.returncode == 0 else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_strings(self, filepath: str) -> Dict:
        """Extract strings from firmware"""
        try:
            result = subprocess.run(['strings', '-n', '8', filepath], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                strings = result.stdout.split('\n')
                # Filter interesting strings
                interesting = []
                patterns = ['password', 'admin', 'root', 'telnet', 'ssh', 'http', 'ftp']
                
                for string in strings:
                    if any(pattern in string.lower() for pattern in patterns):
                        interesting.append(string)
                
                return {
                    'total_strings': len(strings),
                    'interesting_strings': interesting[:50]  # Limit output
                }
        except Exception as e:
            return {'error': str(e)}
        
        return {}
    
    def _analyze_entropy(self, filepath: str) -> Dict:
        """Analyze entropy of firmware (detect encryption/compression)"""
        try:
            import math
            from collections import Counter
            
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Calculate byte frequency
            byte_counts = Counter(data)
            entropy = 0
            
            for count in byte_counts.values():
                probability = count / len(data)
                entropy -= probability * math.log2(probability)
            
            return {
                'entropy': entropy,
                'max_entropy': 8.0,
                'likely_encrypted': entropy > 7.5,
                'likely_compressed': 6.0 < entropy < 7.5
            }
        except Exception as e:
            return {'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description='Firmware Extraction and Analysis Tool')
    parser.add_argument('--list-devices', action='store_true',
                       help='List supported devices')
    parser.add_argument('--extract', metavar='DEVICE',
                       help='Extract firmware from device')
    parser.add_argument('--programmer', default='internal',
                       help='Flashrom programmer to use')
    parser.add_argument('--output', '-o',
                       help='Output filename for extracted firmware')
    parser.add_argument('--analyze', metavar='FIRMWARE',
                       help='Analyze existing firmware file')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    extractor = FirmwareExtractor()
    
    if args.list_devices:
        devices = extractor.list_devices()
        if args.format == 'json':
            print(json.dumps(devices, indent=2))
        else:
            print("Supported devices:")
            for device in devices:
                print(f"  {device['name']} ({device['size']})")
    
    elif args.extract:
        firmware_info = extractor.extract_firmware(
            device=args.extract,
            programmer=args.programmer,
            output_file=args.output
        )
        
        if firmware_info:
            if args.format == 'json':
                print(json.dumps(firmware_info.__dict__, indent=2))
            else:
                print(f"Firmware extracted successfully:")
                print(f"  Device: {firmware_info.device}")
                print(f"  Size: {firmware_info.size} bytes")
                print(f"  File: {firmware_info.filename}")
                print(f"  Checksum: {firmware_info.checksum}")
        else:
            print("Firmware extraction failed")
            sys.exit(1)
    
    elif args.analyze:
        if not os.path.exists(args.analyze):
            print(f"File not found: {args.analyze}")
            sys.exit(1)
        
        analysis = extractor.analyze_firmware(args.analyze)
        
        if args.format == 'json':
            print(json.dumps(analysis, indent=2))
        else:
            print(f"Firmware Analysis: {args.analyze}")
            print(f"Size: {analysis['file_info']['size']} bytes")
            print(f"Type: {analysis['file_info']['file_type']}")
            if analysis.get('entropy_analysis'):
                entropy = analysis['entropy_analysis']
                print(f"Entropy: {entropy.get('entropy', 0):.2f}/8.0")
                if entropy.get('likely_encrypted'):
                    print("  Likely encrypted")
                elif entropy.get('likely_compressed'):
                    print("  Likely compressed")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()