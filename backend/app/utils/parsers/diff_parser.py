import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """Types of changes in a diff."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"

class DiffParser:
    """Parse Git diffs and extract meaningful information."""
    
    def __init__(self):
        self.current_file = None
        self.changes = []
    
    def parse_diff(self, diff_text: str) -> Dict[str, Any]:
        """Parse a Git diff and return structured information."""
        try:
            if not diff_text or not diff_text.strip():
                return self._empty_diff_result()
            
            files = self._split_diff_by_files(diff_text)
            parsed_files = []
            
            for file_diff in files:
                parsed_file = self._parse_file_diff(file_diff)
                if parsed_file:
                    parsed_files.append(parsed_file)
            
            return {
                'files': parsed_files,
                'total_files': len(parsed_files),
                'total_additions': sum(f['additions'] for f in parsed_files),
                'total_deletions': sum(f['deletions'] for f in parsed_files),
                'total_changes': sum(f['changes'] for f in parsed_files),
            }
            
        except Exception as e:
            logger.error(f"Error parsing diff: {e}")
            return self._empty_diff_result()
    
    def _split_diff_by_files(self, diff_text: str) -> List[str]:
        """Split diff text into individual file diffs."""
        # Split by diff --git lines
        file_pattern = r'diff --git a/.*? b/.*?\n'
        files = re.split(file_pattern, diff_text)
        
        # Remove empty first element if exists
        if files and not files[0].strip():
            files = files[1:]
        
        # Add back the diff headers
        file_headers = re.findall(file_pattern, diff_text)
        
        result = []
        for i, file_content in enumerate(files):
            if i < len(file_headers):
                result.append(file_headers[i] + file_content)
            else:
                result.append(file_content)
        
        return result
    
    def _parse_file_diff(self, file_diff: str) -> Optional[Dict[str, Any]]:
        """Parse a single file's diff."""
        try:
            lines = file_diff.split('\n')
            
            if not lines:
                return None
            
            # Extract file information
            file_info = self._extract_file_info(lines)
            if not file_info:
                return None
            
            # Parse hunks
            hunks = self._parse_hunks(lines)
            
            # Calculate statistics
            additions = sum(len(hunk['added_lines']) for hunk in hunks)
            deletions = sum(len(hunk['removed_lines']) for hunk in hunks)
            
            return {
                'file_path': file_info['file_path'],
                'old_file': file_info['old_file'],
                'new_file': file_info['new_file'],
                'change_type': file_info['change_type'],
                'is_binary': file_info['is_binary'],
                'hunks': hunks,
                'additions': additions,
                'deletions': deletions,
                'changes': additions + deletions,
                'file_mode_change': file_info.get('mode_change'),
            }
            
        except Exception as e:
            logger.error(f"Error parsing file diff: {e}")
            return None
    
    def _extract_file_info(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract file information from diff header."""
        try:
            file_info = {
                'file_path': None,
                'old_file': None,
                'new_file': None,
                'change_type': ChangeType.MODIFIED,
                'is_binary': False,
                'mode_change': None,
            }
            
            for line in lines[:10]:  # Check first few lines for headers
                # diff --git a/file b/file
                if line.startswith('diff --git'):
                    match = re.match(r'diff --git a/(.*?) b/(.*)', line)
                    if match:
                        file_info['old_file'] = match.group(1)
                        file_info['new_file'] = match.group(2)
                        file_info['file_path'] = match.group(2)  # Use new file path
                
                # new file mode
                elif line.startswith('new file mode'):
                    file_info['change_type'] = ChangeType.ADDED
                    file_info['mode_change'] = line.split()[-1]
                
                # deleted file mode
                elif line.startswith('deleted file mode'):
                    file_info['change_type'] = ChangeType.REMOVED
                    file_info['mode_change'] = line.split()[-1]
                
                # Binary files differ
                elif 'Binary files' in line and 'differ' in line:
                    file_info['is_binary'] = True
                
                # index line (contains file hashes)
                elif line.startswith('index'):
                    match = re.match(r'index ([a-f0-9]+)\.\.([a-f0-9]+)', line)
                    if match:
                        file_info['old_hash'] = match.group(1)
                        file_info['new_hash'] = match.group(2)
                
                # --- and +++ lines (file paths)
                elif line.startswith('---'):
                    old_path = line[4:].strip()
                    if old_path != '/dev/null':
                        file_info['old_file'] = old_path.lstrip('a/')
                
                elif line.startswith('+++'):
                    new_path = line[4:].strip()
                    if new_path != '/dev/null':
                        file_info['new_file'] = new_path.lstrip('b/')
                        if not file_info['file_path']:
                            file_info['file_path'] = new_path.lstrip('b/')
            
            return file_info if file_info['file_path'] else None
            
        except Exception as e:
            logger.error(f"Error extracting file info: {e}")
            return None
    
    def _parse_hunks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse diff hunks from file lines."""
        hunks = []
        current_hunk = None
        
        try:
            for line in lines:
                # Hunk header: @@ -start1,count1 +start2,count2 @@
                if line.startswith('@@'):
                    if current_hunk:
                        hunks.append(current_hunk)
                    
                    current_hunk = self._parse_hunk_header(line)
                    if not current_hunk:
                        continue
                
                elif current_hunk is not None:
                    # Added line
                    if line.startswith('+') and not line.startswith('+++'):
                        current_hunk['added_lines'].append({
                            'line_number': current_hunk['new_start'] + len(current_hunk['added_lines']),
                            'content': line[1:],  # Remove + prefix
                        })
                    
                    # Removed line
                    elif line.startswith('-') and not line.startswith('---'):
                        current_hunk['removed_lines'].append({
                            'line_number': current_hunk['old_start'] + len(current_hunk['removed_lines']),
                            'content': line[1:],  # Remove - prefix
                        })
                    
                    # Context line (unchanged)
                    elif line.startswith(' '):
                        current_hunk['context_lines'].append({
                            'line_number': current_hunk['old_start'] + len(current_hunk['context_lines']),
                            'content': line[1:],  # Remove space prefix
                        })
                    
                    # No newline at end of file
                    elif line.startswith('\\'):
                        current_hunk['no_newline'] = True
            
            # Add the last hunk
            if current_hunk:
                hunks.append(current_hunk)
            
            return hunks
            
        except Exception as e:
            logger.error(f"Error parsing hunks: {e}")
            return []
    
    def _parse_hunk_header(self, header_line: str) -> Optional[Dict[str, Any]]:
        """Parse a hunk header line."""
        try:
            # @@ -start1,count1 +start2,count2 @@ optional context
            match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)', header_line)
            
            if not match:
                return None
            
            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) else 1
            context = match.group(5).strip() if match.group(5) else ""
            
            return {
                'old_start': old_start,
                'old_count': old_count,
                'new_start': new_start,
                'new_count': new_count,
                'context': context,
                'added_lines': [],
                'removed_lines': [],
                'context_lines': [],
                'no_newline': False,
            }
            
        except Exception as e:
            logger.error(f"Error parsing hunk header: {e}")
            return None
    
    def extract_changed_functions(self, file_diff: str, language: str = 'python') -> List[Dict[str, Any]]:
        """Extract functions that were changed in the diff."""
        try:
            parsed_diff = self._parse_file_diff(file_diff)
            if not parsed_diff:
                return []
            
            changed_functions = []
            
            for hunk in parsed_diff['hunks']:
                # Look for function definitions in added/modified lines
                all_lines = hunk['added_lines'] + hunk['removed_lines']
                
                for line_info in all_lines:
                    content = line_info['content'].strip()
                    
                    if language == 'python':
                        # Python function definition
                        if content.startswith('def '):
                            func_match = re.match(r'def\s+(\w+)\s*\(', content)
                            if func_match:
                                changed_functions.append({
                                    'name': func_match.group(1),
                                    'line_number': line_info['line_number'],
                                    'definition': content,
                                    'language': language,
                                })
                    
                    elif language in ['javascript', 'typescript']:
                        # JavaScript/TypeScript function definitions
                        patterns = [
                            r'function\s+(\w+)\s*\(',
                            r'(\w+)\s*:\s*function\s*\(',
                            r'(\w+)\s*=\s*function\s*\(',
                            r'(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{',
                        ]
                        
                        for pattern in patterns:
                            func_match = re.search(pattern, content)
                            if func_match:
                                changed_functions.append({
                                    'name': func_match.group(1),
                                    'line_number': line_info['line_number'],
                                    'definition': content,
                                    'language': language,
                                })
                                break
                    
                    elif language == 'java':
                        # Java method definitions
                        if re.search(r'(public|private|protected).*?\s+\w+\s*\(', content):
                            method_match = re.search(r'\s+(\w+)\s*\(', content)
                            if method_match:
                                changed_functions.append({
                                    'name': method_match.group(1),
                                    'line_number': line_info['line_number'],
                                    'definition': content,
                                    'language': language,
                                })
            
            return changed_functions
            
        except Exception as e:
            logger.error(f"Error extracting changed functions: {e}")
            return []
    
    def get_complexity_metrics(self, parsed_diff: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate complexity metrics for the diff."""
        try:
            metrics = {
                'total_files_changed': parsed_diff['total_files'],
                'total_lines_changed': parsed_diff['total_changes'],
                'additions': parsed_diff['total_additions'],
                'deletions': parsed_diff['total_deletions'],
                'files_by_type': {},
                'largest_file_changes': [],
                'complexity_score': 0.0,
            }
            
            # Group files by extension
            for file_info in parsed_diff['files']:
                file_path = file_info['file_path']
                extension = file_path.split('.')[-1] if '.' in file_path else 'no_extension'
                
                if extension not in metrics['files_by_type']:
                    metrics['files_by_type'][extension] = {
                        'count': 0,
                        'additions': 0,
                        'deletions': 0,
                    }
                
                metrics['files_by_type'][extension]['count'] += 1
                metrics['files_by_type'][extension]['additions'] += file_info['additions']
                metrics['files_by_type'][extension]['deletions'] += file_info['deletions']
            
            # Find files with most changes
            files_by_changes = sorted(
                parsed_diff['files'],
                key=lambda f: f['changes'],
                reverse=True
            )
            
            metrics['largest_file_changes'] = [
                {
                    'file_path': f['file_path'],
                    'changes': f['changes'],
                    'additions': f['additions'],
                    'deletions': f['deletions'],
                }
                for f in files_by_changes[:5]
            ]
            
            # Calculate complexity score (0-10)
            # Based on: number of files, lines changed, and distribution
            file_factor = min(parsed_diff['total_files'] / 10, 1.0)
            lines_factor = min(parsed_diff['total_changes'] / 500, 1.0)
            
            metrics['complexity_score'] = round((file_factor + lines_factor) * 5, 2)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating complexity metrics: {e}")
            return {'complexity_score': 0.0}
    
    def extract_commit_message_from_diff(self, diff_text: str) -> Optional[str]:
        """Extract commit message if present in diff."""
        try:
            lines = diff_text.split('\n')
            
            for line in lines:
                # Look for common commit message patterns
                if line.startswith('Subject:') or line.startswith('commit '):
                    return line.split(':', 1)[1].strip() if ':' in line else line
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting commit message: {e}")
            return None
    
    def identify_risky_changes(self, parsed_diff: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potentially risky changes in the diff."""
        risky_changes = []
        
        try:
            for file_info in parsed_diff['files']:
                file_path = file_info['file_path']
                
                # Large files changes
                if file_info['changes'] > 100:
                    risky_changes.append({
                        'type': 'large_change',
                        'severity': 'medium',
                        'file_path': file_path,
                        'description': f"Large change ({file_info['changes']} lines) in {file_path}",
                        'changes': file_info['changes'],
                    })
                
                # Binary file changes
                if file_info['is_binary']:
                    risky_changes.append({
                        'type': 'binary_change',
                        'severity': 'low',
                        'file_path': file_path,
                        'description': f"Binary file change in {file_path}",
                    })
                
                # Critical file changes
                critical_patterns = [
                    r'.*config.*',
                    r'.*\.env.*',
                    r'.*security.*',
                    r'.*auth.*',
                    r'.*password.*',
                    r'.*secret.*',
                    r'.*key.*',
                    r'requirements\.txt',
                    r'package\.json',
                    r'Dockerfile',
                    r'.*\.sql',
                ]
                
                for pattern in critical_patterns:
                    if re.match(pattern, file_path, re.IGNORECASE):
                        risky_changes.append({
                            'type': 'critical_file',
                            'severity': 'high',
                            'file_path': file_path,
                            'description': f"Change in critical file: {file_path}",
                            'pattern': pattern,
                        })
                        break
                
                # New file additions
                if file_info['change_type'] == ChangeType.ADDED:
                    risky_changes.append({
                        'type': 'new_file',
                        'severity': 'low',
                        'file_path': file_path,
                        'description': f"New file added: {file_path}",
                    })
                
                # File deletions
                elif file_info['change_type'] == ChangeType.REMOVED:
                    risky_changes.append({
                        'type': 'file_deletion',
                        'severity': 'medium',
                        'file_path': file_path,
                        'description': f"File deleted: {file_path}",
                    })
            
            return risky_changes
            
        except Exception as e:
            logger.error(f"Error identifying risky changes: {e}")
            return []
    
    def _empty_diff_result(self) -> Dict[str, Any]:
        """Return empty diff result structure."""
        return {
            'files': [],
            'total_files': 0,
            'total_additions': 0,
            'total_deletions': 0,
            'total_changes': 0,
        }

class PatchAnalyzer:
    """Analyze patches and diffs for additional insights."""
    
    @staticmethod
    def analyze_change_patterns(parsed_diff: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in the changes."""
        patterns = {
            'import_changes': 0,
            'function_additions': 0,
            'function_deletions': 0,
            'comment_changes': 0,
            'test_changes': 0,
            'documentation_changes': 0,
        }
        
        try:
            for file_info in parsed_diff['files']:
                file_path = file_info['file_path']
                
                # Check if it's a test file
                if 'test' in file_path.lower() or file_path.endswith('_test.py'):
                    patterns['test_changes'] += file_info['changes']
                
                # Check if it's documentation
                if any(ext in file_path.lower() for ext in ['.md', '.rst', '.txt', 'readme', 'doc']):
                    patterns['documentation_changes'] += file_info['changes']
                
                # Analyze hunks for specific patterns
                for hunk in file_info['hunks']:
                    for line_info in hunk['added_lines'] + hunk['removed_lines']:
                        content = line_info['content'].strip()
                        
                        # Import statements
                        if content.startswith(('import ', 'from ', '#include', 'require(')):
                            patterns['import_changes'] += 1
                        
                        # Function definitions
                        elif content.startswith(('def ', 'function ', 'class ')):
                            if line_info in hunk['added_lines']:
                                patterns['function_additions'] += 1
                            else:
                                patterns['function_deletions'] += 1
                        
                        # Comments
                        elif content.startswith(('#', '//', '/*', '*')):
                            patterns['comment_changes'] += 1
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing change patterns: {e}")
            return patterns

def create_diff_summary(parsed_diff: Dict[str, Any]) -> str:
    """Create a human-readable summary of the diff."""
    try:
        if not parsed_diff['files']:
            return "No changes detected."
        
        summary_parts = [
            f"Changed {parsed_diff['total_files']} file(s)",
            f"{parsed_diff['total_additions']} additions",
            f"{parsed_diff['total_deletions']} deletions",
        ]
        
        # Most changed files
        if parsed_diff['files']:
            largest_changes = sorted(
                parsed_diff['files'],
                key=lambda f: f['changes'],
                reverse=True
            )[:3]
            
            if largest_changes:
                summary_parts.append("Most changed files:")
                for file_info in largest_changes:
                    summary_parts.append(
                        f"  - {file_info['file_path']}: {file_info['changes']} changes"
                    )
        
        return "\n".join(summary_parts)
        
    except Exception as e:
        logger.error(f"Error creating diff summary: {e}")
        return "Error creating summary."
