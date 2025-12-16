#!/usr/bin/env python3
"""
Workflow Manager - Manages smart workflow execution and state
Part of the pf smart workflows system
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional

class WorkflowManager:
    """Manages workflow execution, state, and history"""
    
    def __init__(self):
        self.workflow_dir = Path.home() / '.pf' / 'workflows'
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        
    def show_status(self, workflow_id: Optional[str] = None) -> Dict[str, any]:
        """Show status of running workflows"""
        if workflow_id:
            return self._get_workflow_status(workflow_id)
        else:
            return self._get_all_workflows_status()
    
    def _get_workflow_status(self, workflow_id: str) -> Dict[str, any]:
        """Get status of specific workflow"""
        workflow_file = self.workflow_dir / f"{workflow_id}.json"
        if not workflow_file.exists():
            return {'error': f'Workflow {workflow_id} not found'}
        
        with open(workflow_file, 'r') as f:
            return json.load(f)
    
    def _get_all_workflows_status(self) -> Dict[str, any]:
        """Get status of all workflows"""
        workflows = {}
        for workflow_file in self.workflow_dir.glob('*.json'):
            workflow_id = workflow_file.stem
            try:
                with open(workflow_file, 'r') as f:
                    workflows[workflow_id] = json.load(f)
            except Exception as e:
                workflows[workflow_id] = {'error': str(e)}
        
        return {
            'active_workflows': len(workflows),
            'workflows': workflows
        }
    
    def show_history(self, limit: int = 10, filter_term: Optional[str] = None) -> Dict[str, any]:
        """Show workflow execution history"""
        history_file = self.workflow_dir / 'history.json'
        if not history_file.exists():
            return {'history': [], 'total': 0}
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        # Apply filter if specified
        if filter_term:
            history = [entry for entry in history 
                      if filter_term.lower() in entry.get('workflow_type', '').lower()]
        
        # Apply limit
        recent_history = history[-limit:] if limit else history
        
        return {
            'history': recent_history,
            'total': len(history),
            'showing': len(recent_history)
        }


def main():
    parser = argparse.ArgumentParser(description='Workflow Manager')
    parser.add_argument('--status', action='store_true', help='Show workflow status')
    parser.add_argument('--workflow-id', help='Specific workflow ID')
    parser.add_argument('--history', action='store_true', help='Show workflow history')
    parser.add_argument('--limit', type=int, default=10, help='Limit history results')
    parser.add_argument('--filter', help='Filter history by term')
    
    args = parser.parse_args()
    
    manager = WorkflowManager()
    
    if args.status:
        result = manager.show_status(args.workflow_id)
        print(json.dumps(result, indent=2))
    elif args.history:
        result = manager.show_history(args.limit, args.filter)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()