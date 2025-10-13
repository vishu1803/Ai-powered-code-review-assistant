import ast
import logging
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

class ASTAnalyzer:
    """Advanced AST-based code analysis for Python."""
    
    def __init__(self):
        self.issues = []
        self.current_file = ""
        self.lines = []
        
    def analyze(self, tree: ast.AST, file_path: str) -> List[Dict[str, Any]]:
        """Analyze AST and return list of issues."""
        self.issues = []
        self.current_file = file_path
        
        try:
            # Run all analysis methods
            self._analyze_complexity(tree)
            self._analyze_code_smells(tree)
            self._analyze_best_practices(tree)
            self._analyze_potential_bugs(tree)
            self._analyze_performance_issues(tree)
            self._analyze_security_patterns(tree)
            
            return self.issues
            
        except Exception as e:
            logger.error(f"AST analysis failed for {file_path}: {e}")
            return []
    
    def _analyze_complexity(self, tree: ast.AST):
        """Analyze code complexity issues."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    self._add_issue(
                        title="High Cyclomatic Complexity",
                        description=f"Function '{node.name}' has high cyclomatic complexity ({complexity}). Consider breaking it into smaller functions.",
                        severity="medium",
                        rule_id="high_complexity",
                        line_number=node.lineno,
                        suggested_fix="Break down the function into smaller, more focused functions"
                    )
                
                # Check function length
                if hasattr(node, 'end_lineno'):
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        self._add_issue(
                            title="Long Function",
                            description=f"Function '{node.name}' is {length} lines long. Consider breaking it down.",
                            severity="low",
                            rule_id="long_function",
                            line_number=node.lineno,
                            suggested_fix="Split into smaller, single-purpose functions"
                        )
                
                # Check parameter count
                if len(node.args.args) > 5:
                    self._add_issue(
                        title="Too Many Parameters", 
                        description=f"Function '{node.name}' has {len(node.args.args)} parameters. Consider using a configuration object.",
                        severity="low",
                        rule_id="too_many_params",
                        line_number=node.lineno,
                        suggested_fix="Use a dictionary or dataclass for parameters"
                    )
            
            elif isinstance(node, ast.ClassDef):
                # Check class size
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    self._add_issue(
                        title="Large Class",
                        description=f"Class '{node.name}' has {len(methods)} methods. Consider splitting responsibilities.",
                        severity="medium",
                        rule_id="large_class",
                        line_number=node.lineno,
                        suggested_fix="Apply Single Responsibility Principle"
                    )
    
    def _analyze_code_smells(self, tree: ast.AST):
        """Detect common code smells."""
        for node in ast.walk(tree):
            # Long parameter lists
            if isinstance(node, ast.FunctionDef) and len(node.args.args) > 7:
                self._add_issue(
                    title="Long Parameter List",
                    description=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                    severity="medium",
                    rule_id="long_parameter_list",
                    line_number=node.lineno,
                    suggested_fix="Use parameter objects or builder pattern"
                )
            
            # Duplicate code detection (basic)
            if isinstance(node, ast.FunctionDef):
                self._check_duplicate_code(node)
            
            # Dead code detection
            if isinstance(node, ast.FunctionDef):
                self._check_unreachable_code(node)
            
            # Magic numbers
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1]:
                    # Skip if it's in a comparison or obvious context
                    parent = getattr(node, 'parent', None)
                    if not isinstance(parent, (ast.Compare, ast.BinOp)):
                        self._add_issue(
                            title="Magic Number",
                            description=f"Magic number {node.value} should be replaced with a named constant",
                            severity="low", 
                            rule_id="magic_number",
                            line_number=node.lineno,
                            suggested_fix=f"Define as constant: SOME_CONSTANT = {node.value}"
                        )
    
    def _analyze_best_practices(self, tree: ast.AST):
        """Check for Python best practices violations."""
        for node in ast.walk(tree):
            # Missing docstrings
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    self._add_issue(
                        title="Missing Docstring",
                        description=f"Public function '{node.name}' lacks documentation",
                        severity="low",
                        rule_id="missing_docstring",
                        line_number=node.lineno,
                        suggested_fix="Add docstring explaining function purpose, parameters, and return value"
                    )
            
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    self._add_issue(
                        title="Missing Class Docstring",
                        description=f"Class '{node.name}' lacks documentation",
                        severity="low",
                        rule_id="missing_class_docstring", 
                        line_number=node.lineno,
                        suggested_fix="Add class docstring explaining purpose and usage"
                    )
            
            # Naming conventions
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                    self._add_issue(
                        title="Naming Convention Violation",
                        description=f"Function '{node.name}' should use snake_case naming",
                        severity="low",
                        rule_id="function_naming",
                        line_number=node.lineno,
                        suggested_fix=f"Rename to: {self._to_snake_case(node.name)}"
                    )
            
            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    self._add_issue(
                        title="Class Naming Convention",
                        description=f"Class '{node.name}' should use PascalCase naming",
                        severity="low",
                        rule_id="class_naming",
                        line_number=node.lineno,
                        suggested_fix=f"Rename to: {self._to_pascal_case(node.name)}"
                    )
            
            # Mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self._add_issue(
                            title="Mutable Default Argument",
                            description=f"Function '{node.name}' has mutable default argument",
                            severity="high",
                            rule_id="mutable_default",
                            line_number=node.lineno,
                            suggested_fix="Use None as default and create mutable object inside function"
                        )
    
    def _analyze_potential_bugs(self, tree: ast.AST):
        """Detect potential bugs and errors."""
        for node in ast.walk(tree):
            # Unused variables (basic detection)
            if isinstance(node, ast.FunctionDef):
                self._check_unused_variables(node)
            
            # Comparison with None
            if isinstance(node, ast.Compare):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and comparator.value is None:
                        if any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
                            self._add_issue(
                                title="Incorrect None Comparison",
                                description="Use 'is' or 'is not' for None comparisons",
                                severity="medium",
                                rule_id="none_comparison",
                                line_number=node.lineno,
                                suggested_fix="Use 'is None' or 'is not None'"
                            )
            
            # Bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self._add_issue(
                        title="Bare Except Clause",
                        description="Catching all exceptions with bare 'except:' is dangerous",
                        severity="high",
                        rule_id="bare_except",
                        line_number=node.lineno,
                        suggested_fix="Specify exception types or use 'except Exception:'"
                    )
            
            # String formatting issues
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    if '%' in node.left.value:
                        self._add_issue(
                            title="Old-style String Formatting",
                            description="Consider using f-strings or .format() instead of % formatting",
                            severity="low",
                            rule_id="old_string_format",
                            line_number=node.lineno,
                            suggested_fix="Use f-strings: f'text {variable}'"
                        )
    
    def _analyze_performance_issues(self, tree: ast.AST):
        """Detect potential performance issues."""
        for node in ast.walk(tree):
            # List comprehension vs append in loop
            if isinstance(node, ast.For):
                self._check_inefficient_loops(node)
            
            # String concatenation in loops
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        if isinstance(child.target, ast.Name):
                            self._add_issue(
                                title="String Concatenation in Loop",
                                description="String concatenation in loops is inefficient",
                                severity="medium",
                                rule_id="string_concat_loop",
                                line_number=node.lineno,
                                suggested_fix="Use list and join() method or f-strings"
                            )
            
            # Global variables usage
            if isinstance(node, ast.Global):
                for name in node.names:
                    self._add_issue(
                        title="Global Variable Usage",
                        description=f"Global variable '{name}' usage affects performance and maintainability",
                        severity="low",
                        rule_id="global_usage",
                        line_number=node.lineno,
                        suggested_fix="Pass as parameter or use class attributes"
                    )
    
    def _analyze_security_patterns(self, tree: ast.AST):
        """Detect basic security issues in code patterns."""
        for node in ast.walk(tree):
            # eval() usage
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'eval':
                    self._add_issue(
                        title="Dangerous eval() Usage",
                        description="eval() can execute arbitrary code and is a security risk",
                        severity="critical",
                        rule_id="eval_usage",
                        line_number=node.lineno,
                        suggested_fix="Use ast.literal_eval() for safe evaluation or avoid eval()"
                    )
                
                # exec() usage
                elif isinstance(node.func, ast.Name) and node.func.id == 'exec':
                    self._add_issue(
                        title="Dangerous exec() Usage",
                        description="exec() can execute arbitrary code and is a security risk",
                        severity="critical",
                        rule_id="exec_usage",
                        line_number=node.lineno,
                        suggested_fix="Avoid exec() or use safer alternatives"
                    )
                
                # input() in Python 2 style
                elif isinstance(node.func, ast.Name) and node.func.id == 'input':
                    # This is actually safe in Python 3, but flagging for awareness
                    pass
            
            # Hardcoded credentials patterns
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(keyword in var_name for keyword in ['password', 'secret', 'key', 'token']):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                if len(node.value.value) > 8:  # Likely not a placeholder
                                    self._add_issue(
                                        title="Hardcoded Credential",
                                        description=f"Variable '{target.id}' appears to contain hardcoded credentials",
                                        severity="high",
                                        rule_id="hardcoded_credential",
                                        line_number=node.lineno,
                                        suggested_fix="Use environment variables or secure configuration"
                                    )
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                if isinstance(child.op, (ast.And, ast.Or)):
                    complexity += len(child.values) - 1
        
        return complexity
    
    def _check_duplicate_code(self, node: ast.FunctionDef):
        """Basic duplicate code detection."""
        # This is a simplified version - in production, you'd want more sophisticated detection
        function_body = ast.dump(node)
        if len(function_body) > 200:  # Only check substantial functions
            # Hash-based duplicate detection would go here
            pass
    
    def _check_unreachable_code(self, node: ast.FunctionDef):
        """Check for unreachable code after return statements."""
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return):
                # Check if there are statements after this return
                if i < len(node.body) - 1:
                    next_stmt = node.body[i + 1]
                    if not isinstance(next_stmt, (ast.FunctionDef, ast.ClassDef, ast.If, ast.Try)):
                        self._add_issue(
                            title="Unreachable Code",
                            description="Code after return statement is unreachable",
                            severity="medium",
                            rule_id="unreachable_code",
                            line_number=next_stmt.lineno,
                            suggested_fix="Remove unreachable code or restructure logic"
                        )
    
    def _check_unused_variables(self, node: ast.FunctionDef):
        """Check for unused variables in function scope."""
        assigned_vars = set()
        used_vars = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assigned_vars.add(target.id)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                used_vars.add(child.id)
        
        unused = assigned_vars - used_vars
        # Filter out common patterns
        unused = {var for var in unused if not var.startswith('_') and var not in ['self', 'cls']}
        
        for var in unused:
            self._add_issue(
                title="Unused Variable",
                description=f"Variable '{var}' is assigned but never used",
                severity="low",
                rule_id="unused_variable",
                line_number=node.lineno,
                suggested_fix=f"Remove unused variable '{var}' or prefix with '_'"
            )
    
    def _check_inefficient_loops(self, node: ast.For):
        """Check for inefficient loop patterns."""
        # Check for list.append() in loops that could be comprehensions
        append_calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute) and child.func.attr == 'append':
                    append_calls.append(child)
        
        if append_calls and len(append_calls) == 1:
            # Simple case: single append in loop
            self._add_issue(
                title="Loop Could Be List Comprehension",
                description="Consider using list comprehension for better performance",
                severity="low",
                rule_id="inefficient_loop",
                line_number=node.lineno,
                suggested_fix="Use list comprehension: [item for item in iterable]"
            )
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention."""
        return name.islower() and '_' in name or name.islower()
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention."""
        return name[0].isupper() and not '_' in name
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def _add_issue(self, title: str, description: str, severity: str, rule_id: str, 
                   line_number: int, suggested_fix: str = "", code_snippet: str = ""):
        """Add an issue to the results."""
        self.issues.append({
            'title': title,
            'description': description,
            'severity': severity,
            'rule_id': rule_id,
            'line_number': line_number,
            'line_end': line_number,
            'suggested_fix': suggested_fix,
            'code_snippet': code_snippet,
            'confidence': 0.8,
        })

class SecurityPatternAnalyzer:
    """Additional security-focused AST analysis."""
    
    @staticmethod
    def analyze_sql_injection_patterns(tree: ast.AST) -> List[Dict[str, Any]]:
        """Detect potential SQL injection vulnerabilities."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for string formatting in SQL contexts
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    if func_name in ['execute', 'executemany', 'query']:
                        # Check arguments for string concatenation
                        for arg in node.args:
                            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                                issues.append({
                                    'title': 'Potential SQL Injection',
                                    'description': 'String concatenation in SQL query may lead to injection',
                                    'severity': 'critical',
                                    'rule_id': 'sql_injection',
                                    'line_number': node.lineno,
                                    'suggested_fix': 'Use parameterized queries instead'
                                })
        
        return issues
    
    @staticmethod
    def analyze_path_traversal_patterns(tree: ast.AST) -> List[Dict[str, Any]]:
        """Detect potential path traversal vulnerabilities."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check for user input in file paths
                    for arg in node.args:
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                            issues.append({
                                'title': 'Potential Path Traversal',
                                'description': 'File path construction may allow path traversal attacks',
                                'severity': 'high',
                                'rule_id': 'path_traversal',
                                'line_number': node.lineno,
                                'suggested_fix': 'Validate and sanitize file paths'
                            })
        
        return issues
