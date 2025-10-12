import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import ast

logger = logging.getLogger(__name__)

class CodeParser:
    """Advanced code parsing utilities for multiple languages."""
    
    def __init__(self):
        self.language_parsers = {
            'python': self._parse_python,
            'javascript': self._parse_javascript,
            'typescript': self._parse_typescript,
            'java': self._parse_java,
            'cpp': self._parse_cpp,
            'c': self._parse_c,
        }
    
    def parse_file(self, file_path: str, file_content: str, language: str) -> Dict[str, Any]:
        """Parse a code file and extract structural information."""
        try:
            parser_func = self.language_parsers.get(language, self._parse_generic)
            return parser_func(file_path, file_content)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return self._get_empty_parse_result()
    
    def _parse_python(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Parse Python code and extract structural information."""
        try:
            tree = ast.parse(file_content)
            
            functions = []
            classes = []
            imports = []
            variables = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', node.lineno),
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node),
                        'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list],
                        'complexity': self._calculate_complexity(node),
                    })
                
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', node.lineno),
                        'methods': methods,
                        'docstring': ast.get_docstring(node),
                        'bases': [b.id if hasattr(b, 'id') else str(b) for b in node.bases],
                        'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list],
                    })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({
                                'module': alias.name,
                                'alias': alias.asname,
                                'line': node.lineno,
                                'type': 'import'
                            })
                    else:  # ImportFrom
                        for alias in node.names:
                            imports.append({
                                'module': node.module,
                                'name': alias.name,
                                'alias': alias.asname,
                                'line': node.lineno,
                                'type': 'from_import'
                            })
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append({
                                'name': target.id,
                                'line': node.lineno,
                                'type': self._infer_type(node.value),
                            })
            
            return {
                'language': 'python',
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'variables': variables,
                'metrics': {
                    'lines_of_code': len(file_content.splitlines()),
                    'function_count': len(functions),
                    'class_count': len(classes),
                    'import_count': len(imports),
                    'avg_function_complexity': sum(f['complexity'] for f in functions) / max(len(functions), 1),
                }
            }
            
        except SyntaxError as e:
            logger.error(f"Python syntax error in {file_path}: {e}")
            return self._get_error_parse_result(str(e))
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {e}")
            return self._get_error_parse_result(str(e))
    
    def _parse_javascript(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Parse JavaScript code using regex patterns."""
        functions = []
        classes = []
        imports = []
        variables = []
        
        # Function patterns
        function_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)\s*\{',  # function declarations
            r'(\w+)\s*:\s*function\s*\([^)]*\)\s*\{',  # object methods
            r'(\w+)\s*=\s*function\s*\([^)]*\)\s*\{',  # function expressions
            r'(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{',  # arrow functions
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, file_content, re.MULTILINE):
                line_no = file_content[:match.start()].count('\n') + 1
                functions.append({
                    'name': match.group(1),
                    'line_start': line_no,
                    'type': 'function'
                })
        
        # Class patterns
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        for match in re.finditer(class_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            classes.append({
                'name': match.group(1),
                'line_start': line_no,
                'extends': match.group(2),
                'type': 'class'
            })
        
        # Import patterns
        import_patterns = [
            r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',  # default imports
            r'import\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]',  # named imports
            r'import\s+[\'"]([^\'"]+)[\'"]',  # side-effect imports
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, file_content, re.MULTILINE):
                line_no = file_content[:match.start()].count('\n') + 1
                imports.append({
                    'module': match.group(2) if len(match.groups()) > 1 else match.group(1),
                    'line': line_no,
                    'type': 'import'
                })
        
        return {
            'language': 'javascript',
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'variables': variables,
            'metrics': {
                'lines_of_code': len(file_content.splitlines()),
                'function_count': len(functions),
                'class_count': len(classes),
                'import_count': len(imports),
            }
        }
    
    def _parse_typescript(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Parse TypeScript code (similar to JavaScript with type annotations)."""
        # Start with JavaScript parsing
        result = self._parse_javascript(file_path, file_content)
        result['language'] = 'typescript'
        
        # Add TypeScript-specific patterns
        interface_pattern = r'interface\s+(\w+)\s*\{'
        interfaces = []
        
        for match in re.finditer(interface_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            interfaces.append({
                'name': match.group(1),
                'line_start': line_no,
                'type': 'interface'
            })
        
        result['interfaces'] = interfaces
        result['metrics']['interface_count'] = len(interfaces)
        
        return result
    
    def _parse_java(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Parse Java code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        # Class pattern
        class_pattern = r'(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{'
        for match in re.finditer(class_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            classes.append({
                'name': match.group(1),
                'line_start': line_no,
                'extends': match.group(2),
                'implements': match.group(3),
                'type': 'class'
            })
        
        # Method pattern
        method_pattern = r'(?:public|private|protected|static).*?\s+(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(method_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            functions.append({
                'name': match.group(1),
                'line_start': line_no,
                'type': 'method'
            })
        
        # Import pattern
        import_pattern = r'import\s+(?:static\s+)?([^;]+);'
        for match in re.finditer(import_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            imports.append({
                'module': match.group(1).strip(),
                'line': line_no,
                'type': 'import'
            })
        
        return {
            'language': 'java',
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'variables': [],
            'metrics': {
                'lines_of_code': len(file_content.splitlines()),
                'function_count': len(functions),
                'class_count': len(classes),
                'import_count': len(imports),
            }
        }
    
    def _parse_cpp(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Parse C++ code using regex patterns."""
        functions = []
        classes = []
        includes = []
        
        # Function pattern
        function_pattern = r'(?:inline\s+)?(?:static\s+)?(?:virtual\s+)?(?:\w+(?:\s*\*|\s*&)?)\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?(?:final\s*)?\{'
        for match in re.finditer(function_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            functions.append({
                'name': match.group(1),
                'line_start': line_no,
                'type': 'function'
            })
        
        # Class pattern  
        class_pattern = r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?\s*\{'
        for match in re.finditer(class_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            classes.append({
                'name': match.group(1),
                'line_start': line_no,
                'inherits': match.group(2),
                'type': 'class'
            })
        
        # Include pattern
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            includes.append({
                'header': match.group(1),
                'line': line_no,
                'type': 'include'
            })
        
        return {
            'language': 'cpp',
            'functions': functions,
            'classes': classes,
            'includes': includes,
            'variables': [],
            'metrics': {
                'lines_of_code': len(file_content.splitlines()),
                'function_count': len(functions),
                'class_count': len(classes),
                'include_count': len(includes),
            }
        }
    
    def _parse_c(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Parse C code using regex patterns."""
        functions = []
        includes = []
        structs = []
        
        # Function pattern
        function_pattern = r'(?:static\s+)?(?:inline\s+)?(?:\w+(?:\s*\*)?)\s+(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(function_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            functions.append({
                'name': match.group(1),
                'line_start': line_no,
                'type': 'function'
            })
        
        # Struct pattern
        struct_pattern = r'(?:typedef\s+)?struct\s+(\w+)?\s*\{'
        for match in re.finditer(struct_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            struct_name = match.group(1) or 'anonymous'
            structs.append({
                'name': struct_name,
                'line_start': line_no,
                'type': 'struct'
            })
        
        # Include pattern (same as C++)
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, file_content, re.MULTILINE):
            line_no = file_content[:match.start()].count('\n') + 1
            includes.append({
                'header': match.group(1),
                'line': line_no,
                'type': 'include'
            })
        
        return {
            'language': 'c',
            'functions': functions,
            'structs': structs,
            'includes': includes,
            'variables': [],
            'metrics': {
                'lines_of_code': len(file_content.splitlines()),
                'function_count': len(functions),
                'struct_count': len(structs),
                'include_count': len(includes),
            }
        }
    
    def _parse_generic(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Generic parsing for unsupported languages."""
        return {
            'language': 'unknown',
            'functions': [],
            'classes': [],
            'imports': [],
            'variables': [],
            'metrics': {
                'lines_of_code': len(file_content.splitlines()),
                'function_count': 0,
                'class_count': 0,
                'import_count': 0,
            }
        }
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _infer_type(self, node: ast.AST) -> str:
        """Infer the type of a variable assignment."""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return 'list'
        elif isinstance(node, ast.Dict):
            return 'dict'
        elif isinstance(node, ast.Set):
            return 'set'
        elif isinstance(node, ast.Tuple):
            return 'tuple'
        elif isinstance(node, ast.Call):
            if hasattr(node.func, 'id'):
                return f'call_{node.func.id}'
            return 'call'
        else:
            return 'unknown'
    
    def _get_empty_parse_result(self) -> Dict[str, Any]:
        """Return empty parse result structure."""
        return {
            'language': 'unknown',
            'functions': [],
            'classes': [],
            'imports': [],
            'variables': [],
            'metrics': {
                'lines_of_code': 0,
                'function_count': 0,
                'class_count': 0,
                'import_count': 0,
            }
        }
    
    def _get_error_parse_result(self, error: str) -> Dict[str, Any]:
        """Return error parse result structure."""
        result = self._get_empty_parse_result()
        result['error'] = error
        return result
    
    def extract_functions_with_context(self, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Extract functions with their full context and body."""
        if language != 'python':
            return []  # Only implemented for Python for now
        
        try:
            tree = ast.parse(file_content)
            functions = []
            lines = file_content.splitlines()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    start_line = node.lineno - 1
                    end_line = getattr(node, 'end_lineno', len(lines)) - 1
                    
                    function_body = '\n'.join(lines[start_line:end_line + 1])
                    
                    functions.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', len(lines)),
                        'body': function_body,
                        'args': [arg.arg for arg in node.args.args],
                        'returns': ast.unparse(node.returns) if node.returns else None,
                        'docstring': ast.get_docstring(node),
                        'complexity': self._calculate_complexity(node),
                    })
            
            return functions
            
        except Exception as e:
            logger.error(f"Error extracting functions: {e}")
            return []
