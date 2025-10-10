import re
import ast
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.models.database.review import IssueSeverity

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """Security vulnerability detection and analysis."""
    
    def __init__(self):
        self.security_patterns = self._load_security_patterns()
        self.vulnerability_rules = self._load_vulnerability_rules()
    
    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load security vulnerability patterns by language."""
        return {
            'python': [
                {
                    'rule_id': 'hardcoded_password',
                    'pattern': r'password\s*=\s*["\'][^"\']{8,}["\']',
                    'severity': IssueSeverity.CRITICAL,
                    'title': 'Hardcoded Password',
                    'description': 'Hardcoded password found in source code',
                    'cwe': 'CWE-798',
                },
                {
                    'rule_id': 'sql_injection',
                    'pattern': r'\.execute\s*\(\s*["\'].*%.*["\'].*%',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Potential SQL Injection',
                    'description': 'String formatting in SQL query may lead to injection',
                    'cwe': 'CWE-89',
                },
                {
                    'rule_id': 'command_injection',
                    'pattern': r'(subprocess|os\.system|os\.popen)\s*\([^)]*\+|%',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Command Injection Risk',
                    'description': 'Dynamic command construction may allow injection',
                    'cwe': 'CWE-78',
                },
                {
                    'rule_id': 'weak_crypto',
                    'pattern': r'hashlib\.(md5|sha1)\(',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'Weak Cryptographic Hash',
                    'description': 'MD5/SHA1 are cryptographically weak',
                    'cwe': 'CWE-327',
                },
                {
                    'rule_id': 'insecure_random',
                    'pattern': r'random\.(random|randint|choice)',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'Insecure Random Generator',
                    'description': 'Use secrets module for security-sensitive random values',
                    'cwe': 'CWE-330',
                },
                {
                    'rule_id': 'eval_usage',
                    'pattern': r'\beval\s*\(',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Dangerous eval() Usage',
                    'description': 'eval() can execute arbitrary code',
                    'cwe': 'CWE-94',
                },
                {
                    'rule_id': 'pickle_usage',
                    'pattern': r'pickle\.loads?\s*\(',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Unsafe Deserialization',
                    'description': 'pickle.load can execute arbitrary code',
                    'cwe': 'CWE-502',
                },
                {
                    'rule_id': 'debug_mode',
                    'pattern': r'debug\s*=\s*True',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'Debug Mode Enabled',
                    'description': 'Debug mode should not be enabled in production',
                    'cwe': 'CWE-489',
                },
            ],
            'javascript': [
                {
                    'rule_id': 'eval_usage',
                    'pattern': r'\beval\s*\(',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Dangerous eval() Usage',
                    'description': 'eval() can execute arbitrary code',
                    'cwe': 'CWE-94',
                },
                {
                    'rule_id': 'innerHTML_xss',
                    'pattern': r'\.innerHTML\s*=.*\+',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Potential XSS via innerHTML',
                    'description': 'Dynamic content in innerHTML may allow XSS',
                    'cwe': 'CWE-79',
                },
                {
                    'rule_id': 'document_write',
                    'pattern': r'document\.write\s*\(',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'document.write Usage',
                    'description': 'document.write can be exploited for XSS',
                    'cwe': 'CWE-79',
                },
                {
                    'rule_id': 'insecure_random',
                    'pattern': r'Math\.random\s*\(',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'Insecure Random Generator',
                    'description': 'Math.random is not cryptographically secure',
                    'cwe': 'CWE-330',
                },
            ],
            'java': [
                {
                    'rule_id': 'sql_injection',
                    'pattern': r'Statement.*executeQuery\s*\([^?]*\+',
                    'severity': IssueSeverity.HIGH,
                    'title': 'SQL Injection Vulnerability',
                    'description': 'String concatenation in SQL query',
                    'cwe': 'CWE-89',
                },
                {
                    'rule_id': 'path_traversal',
                    'pattern': r'new\s+File\s*\([^)]*\+',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Path Traversal Risk',
                    'description': 'Dynamic file path construction',
                    'cwe': 'CWE-22',
                },
                {
                    'rule_id': 'weak_crypto',
                    'pattern': r'MessageDigest\.getInstance\s*\(\s*["\']MD5|SHA1["\']',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'Weak Cryptographic Hash',
                    'description': 'MD5/SHA1 are cryptographically weak',
                    'cwe': 'CWE-327',
                },
            ],
        }
    
    def _load_vulnerability_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load AST-based vulnerability detection rules."""
        return {
            'python': [
                {
                    'rule_id': 'assert_in_production',
                    'node_type': 'Assert',
                    'severity': IssueSeverity.LOW,
                    'title': 'Assert Statement in Production Code',
                    'description': 'Assert statements are ignored when optimization is enabled',
                    'check': lambda node: True,
                },
                {
                    'rule_id': 'except_pass',
                    'node_type': 'ExceptHandler',
                    'severity': IssueSeverity.MEDIUM,
                    'title': 'Empty Exception Handler',
                    'description': 'Empty except blocks can hide errors',
                    'check': lambda node: (
                        len(node.body) == 1 and
                        isinstance(node.body[0], ast.Pass)
                    ),
                },
                {
                    'rule_id': 'shell_true',
                    'node_type': 'Call',
                    'severity': IssueSeverity.HIGH,
                    'title': 'Subprocess with shell=True',
                    'description': 'shell=True can lead to command injection',
                    'check': lambda node: (
                        isinstance(node.func, ast.Attribute) and
                        node.func.attr in ('call', 'run', 'Popen') and
                        any(
                            isinstance(keyword.value, ast.Constant) and
                            keyword.value.value is True and
                            keyword.arg == 'shell'
                            for keyword in node.keywords
                        )
                    ),
                },
            ],
        }
    
    async def analyze_file(
        self,
        file_path: str,
        file_content: str,
        language: str,
    ) -> List[Dict[str, Any]]:
        """Perform comprehensive security analysis on file."""
        issues = []
        
        try:
            # Pattern-based analysis
            pattern_issues = self._pattern_based_analysis(
                file_path, file_content, language
            )
            issues.extend(pattern_issues)
            
            # AST-based analysis for supported languages
            if language == 'python':
                ast_issues = await self._python_ast_analysis(file_path, file_content)
                issues.extend(ast_issues)
            
            # Context-aware analysis
            context_issues = self._context_aware_analysis(
                file_path, file_content, language
            )
            issues.extend(context_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Security analysis failed for {file_path}: {e}")
            return []
    
    def _pattern_based_analysis(
        self,
        file_path: str,
        file_content: str,
        language: str,
    ) -> List[Dict[str, Any]]:
        """Pattern-based security vulnerability detection."""
        issues = []
        
        # Get patterns for the language
        patterns = self.security_patterns.get(language, [])
        
        for pattern_rule in patterns:
            try:
                pattern = pattern_rule['pattern']
                matches = re.finditer(pattern, file_content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    line_number = file_content[:match.start()].count('\n') + 1
                    
                    # Get context around the match
                    lines = file_content.split('\n')
                    start_line = max(0, line_number - 2)
                    end_line = min(len(lines), line_number + 1)
                    context = '\n'.join(lines[start_line:end_line])
                    
                    issue = {
                        'title': pattern_rule['title'],
                        'description': pattern_rule['description'],
                        'severity': pattern_rule['severity'],
                        'rule_id': pattern_rule['rule_id'],
                        'line_number': line_number,
                        'code_snippet': match.group(0),
                        'context': context,
                        'cwe': pattern_rule.get('cwe'),
                        'confidence': 0.8,
                        'suggested_fix': self._get_suggested_fix(pattern_rule['rule_id']),
                    }
                    
                    issues.append(issue)
                    
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {pattern_rule['pattern']}: {e}")
                continue
        
        return issues
    
    async def _python_ast_analysis(
        self,
        file_path: str,
        file_content: str,
    ) -> List[Dict[str, Any]]:
        """AST-based analysis for Python files."""
        issues = []
        
        try:
            tree = ast.parse(file_content)
            
            # Get vulnerability rules for Python
            rules = self.vulnerability_rules.get('python', [])
            
            for node in ast.walk(tree):
                for rule in rules:
                    if isinstance(node, getattr(ast, rule['node_type'])):
                        if rule['check'](node):
                            line_number = getattr(node, 'lineno', 1)
                            
                            issue = {
                                'title': rule['title'],
                                'description': rule['description'],
                                'severity': rule['severity'],
                                'rule_id': rule['rule_id'],
                                'line_number': line_number,
                                'code_snippet': self._get_node_source(node, file_content),
                                'confidence': 0.9,
                                'suggested_fix': self._get_suggested_fix(rule['rule_id']),
                            }
                            
                            issues.append(issue)
            
        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            logger.error(f"AST analysis failed for {file_path}: {e}")
        
        return issues
    
    def _context_aware_analysis(
        self,
        file_path: str,
        file_content: str,
        language: str,
    ) -> List[Dict[str, Any]]:
        """Context-aware security analysis."""
        issues = []
        
        try:
            # Check for security-sensitive file types
            if self._is_config_file(file_path):
                config_issues = self._analyze_config_file(file_path, file_content)
                issues.extend(config_issues)
            
            # Check for test files with security implications
            if self._is_test_file(file_path):
                test_issues = self._analyze_test_file(file_path, file_content)
                issues.extend(test_issues)
            
            # Check for dependency files
            if self._is_dependency_file(file_path):
                dep_issues = self._analyze_dependency_file(file_path, file_content)
                issues.extend(dep_issues)
            
        except Exception as e:
            logger.error(f"Context-aware analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_config_file(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        """Analyze configuration files for security issues."""
        issues = []
        
        # Check for exposed secrets in config files
        secret_patterns = [
            (r'password\s*[=:]\s*["\'][^"\']{4,}["\']', 'Password in config file'),
            (r'api[_-]?key\s*[=:]\s*["\'][^"\']{10,}["\']', 'API key in config file'),
            (r'secret[_-]?key\s*[=:]\s*["\'][^"\']{10,}["\']', 'Secret key in config file'),
            (r'token\s*[=:]\s*["\'][^"\']{10,}["\']', 'Token in config file'),
        ]
        
        for pattern, title in secret_patterns:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            
            for match in matches:
                line_number = file_content[:match.start()].count('\n') + 1
                
                issues.append({
                    'title': title,
                    'description': 'Sensitive information should not be stored in config files',
                    'severity': IssueSeverity.HIGH,
                    'rule_id': 'config_secrets',
                    'line_number': line_number,
                    'code_snippet': match.group(0),
                    'confidence': 0.9,
                    'suggested_fix': 'Use environment variables or secure configuration management',
                })
        
        return issues
    
    def _analyze_test_file(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        """Analyze test files for security issues."""
        issues = []
        
        # Check for hardcoded credentials in tests
        if re.search(r'password.*=.*["\'][^"\']{8,}["\']', file_content, re.IGNORECASE):
            issues.append({
                'title': 'Hardcoded Credentials in Tests',
                'description': 'Test files should not contain real credentials',
                'severity': IssueSeverity.MEDIUM,
                'rule_id': 'test_credentials',
                'line_number': 1,
                'confidence': 0.7,
                'suggested_fix': 'Use mock credentials or environment variables for testing',
            })
        
        return issues
    
    def _analyze_dependency_file(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        """Analyze dependency files for known vulnerabilities."""
        issues = []
        
        # This is a simplified check - in production, integrate with vulnerability databases
        vulnerable_packages = {
            'requests': ['2.25.0', '2.25.1'],  # Example vulnerable versions
            'flask': ['1.0.0', '1.0.1'],
            'django': ['2.2.0', '2.2.1'],
        }
        
        for package, vulnerable_versions in vulnerable_packages.items():
            pattern = rf'{package}\s*[=><~!]+\s*({"|".join(re.escape(v) for v in vulnerable_versions)})'
            
            if re.search(pattern, file_content):
                issues.append({
                    'title': f'Vulnerable Dependency: {package}',
                    'description': f'Package {package} has known security vulnerabilities',
                    'severity': IssueSeverity.HIGH,
                    'rule_id': 'vulnerable_dependency',
                    'line_number': 1,
                    'confidence': 0.8,
                    'suggested_fix': f'Update {package} to a secure version',
                })
        
        return issues
    
    def _get_suggested_fix(self, rule_id: str) -> Optional[str]:
        """Get suggested fix for a security rule."""
        fixes = {
            'hardcoded_password': 'Use environment variables or secure configuration management',
            'sql_injection': 'Use parameterized queries or prepared statements',
            'command_injection': 'Validate and sanitize all inputs, avoid shell=True',
            'weak_crypto': 'Use SHA-256 or stronger cryptographic hash functions',
            'insecure_random': 'Use secrets module for cryptographically secure random values',
            'eval_usage': 'Avoid eval(), use safer alternatives like ast.literal_eval',
            'pickle_usage': 'Use JSON or other safe serialization formats',
            'debug_mode': 'Disable debug mode in production environments',
            'innerHTML_xss': 'Sanitize user input or use textContent instead of innerHTML',
            'document_write': 'Use DOM manipulation methods instead of document.write',
            'assert_in_production': 'Use proper error handling instead of assert statements',
            'except_pass': 'Log errors or handle them appropriately, avoid silent failures',
            'shell_true': 'Use shell=False and validate inputs, or use safer alternatives',
        }
        
        return fixes.get(rule_id)
    
    def _get_node_source(self, node: ast.AST, file_content: str) -> str:
        """Extract source code for an AST node."""
        try:
            lines = file_content.split('\n')
            if hasattr(node, 'lineno') and node.lineno <= len(lines):
                return lines[node.lineno - 1].strip()
        except Exception:
            pass
        
        return ""
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_extensions = {'.ini', '.conf', '.config', '.cfg', '.toml', '.yaml', '.yml', '.json'}
        config_names = {'config', 'settings', '.env', 'environment'}
        
        path = Path(file_path)
        
        return (
            path.suffix.lower() in config_extensions or
            path.name.lower() in config_names or
            path.name.startswith('.env')
        )
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        path = Path(file_path)
        
        return (
            'test' in path.name.lower() or
            path.name.startswith('test_') or
            path.name.endswith('_test.py') or
            'test' in path.parts
        )
    
    def _is_dependency_file(self, file_path: str) -> bool:
        """Check if file is a dependency specification file."""
        dependency_files = {
            'requirements.txt', 'requirements-dev.txt', 'setup.py', 'pyproject.toml',
            'Pipfile', 'package.json', 'package-lock.json', 'yarn.lock',
            'Gemfile', 'Gemfile.lock', 'composer.json', 'composer.lock'
        }
        
        path = Path(file_path)
        return path.name in dependency_files
