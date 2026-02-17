#!/usr/bin/env python3
"""
Unified Security Configuration Manager
Manages settings and preferences for the unified security framework
"""

import json
import os
from pathlib import Path

class SecurityConfigManager:
    """Manage unified security framework configuration"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.pf-security'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
        
        self.default_config = {
            'fuzzing': {
                'default_duration': 300,
                'parallel_processes': 4,
                'timeout_multiplier': 1.0
            },
            'reporting': {
                'include_exploits': True,
                'risk_threshold': 5,
                'output_formats': ['html', 'json']
            },
            'analysis': {
                'deep_analysis_threshold': 7,
                'complexity_weight': 0.3,
                'vulnerability_weight': 0.7
            },
            'targets': {
                'auto_detect_types': True,
                'max_concurrent_targets': 3,
                'priority_scoring': True
            }
        }
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                return self._merge_config(self.default_config, config)
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
                return self.default_config
        else:
            return self.default_config
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Configuration saved to: {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def _merge_config(self, default, user):
        """Merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def interactive_config(self):
        """Interactive configuration setup"""
        print("🔧 Unified Security Framework Configuration")
        print("=" * 50)
        
        config = self.load_config()
        
        print("\n📊 Fuzzing Settings:")
        config['fuzzing']['default_duration'] = self._get_int_input(
            "Default fuzzing duration (seconds)", 
            config['fuzzing']['default_duration']
        )
        config['fuzzing']['parallel_processes'] = self._get_int_input(
            "Parallel fuzzing processes", 
            config['fuzzing']['parallel_processes']
        )
        
        print("\n📋 Reporting Settings:")
        config['reporting']['include_exploits'] = self._get_bool_input(
            "Generate exploit templates", 
            config['reporting']['include_exploits']
        )
        config['reporting']['risk_threshold'] = self._get_int_input(
            "Risk threshold for high-priority findings (1-10)", 
            config['reporting']['risk_threshold']
        )
        
        print("\n🔍 Analysis Settings:")
        config['analysis']['deep_analysis_threshold'] = self._get_int_input(
            "Risk score threshold for deep analysis (1-10)", 
            config['analysis']['deep_analysis_threshold']
        )
        
        print("\n🎯 Target Settings:")
        config['targets']['auto_detect_types'] = self._get_bool_input(
            "Auto-detect target types", 
            config['targets']['auto_detect_types']
        )
        config['targets']['max_concurrent_targets'] = self._get_int_input(
            "Maximum concurrent targets", 
            config['targets']['max_concurrent_targets']
        )
        
        self.save_config(config)
        print("\n✅ Configuration updated successfully!")
    
    def _get_int_input(self, prompt, default):
        """Get integer input with default"""
        try:
            response = input(f"{prompt} [{default}]: ").strip()
            return int(response) if response else default
        except ValueError:
            print("Invalid input, using default")
            return default
    
    def _get_bool_input(self, prompt, default):
        """Get boolean input with default"""
        default_str = "y" if default else "n"
        response = input(f"{prompt} [y/n, default {default_str}]: ").strip().lower()
        
        if response in ['y', 'yes', 'true', '1']:
            return True
        elif response in ['n', 'no', 'false', '0']:
            return False
        else:
            return default
    
    def show_config(self):
        """Display current configuration"""
        config = self.load_config()
        print("🔧 Current Unified Security Framework Configuration:")
        print("=" * 55)
        print(json.dumps(config, indent=2))
    
    def reset_config(self):
        """Reset configuration to defaults"""
        self.save_config(self.default_config)
        print("🔄 Configuration reset to defaults")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Security Framework Configuration Manager')
    parser.add_argument('--interactive', action='store_true', help='Interactive configuration')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--reset', action='store_true', help='Reset to defaults')
    
    args = parser.parse_args()
    
    manager = SecurityConfigManager()
    
    if args.interactive:
        manager.interactive_config()
    elif args.show:
        manager.show_config()
    elif args.reset:
        manager.reset_config()
    else:
        manager.interactive_config()

if __name__ == '__main__':
    main()