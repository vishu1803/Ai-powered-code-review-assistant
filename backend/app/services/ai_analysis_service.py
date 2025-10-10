import ast
import asyncio
import json
import logging
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import tiktoken
from openai import AsyncOpenAI
from transformers import pipeline
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database.repository import Repository
from app.models.database.review import Issue, IssueSeverity
from app.models.schemas.review import IssueCreate
from app.utils.parsers.code_parser import CodeParser
from app.utils.parsers.ast_parser import ASTAnalyzer
from app.services.security_analyzer import SecurityAnalyzer

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Advanced AI-powered code analysis service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_client = None
        self.security_analyzer = SecurityAnalyzer()
        self.code_parser = CodeParser()
        self.ast_analyzer = ASTAnalyzer()
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Initialize Tree-sitter for advanced parsing
        self._init_tree_sitter()
        
        # Load local ML models for offline analysis
        self._init_local_models()
    
    def _init_tree_sitter(self):
        """Initialize Tree-sitter parser for multiple languages."""
        try:
            # Python parser
            PY_LANGUAGE = Language(tspython.language(), "python")
            self.py_parser = Parser()
            self.py_parser.set_language(PY_LANGUAGE)
            
            # Add more language parsers as needed
            self.parsers = {
                'python': self.py_parser,
                'py': self.py_parser,
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter: {e}")
            self.parsers = {}
    
    def _init_local_models(self):
        """Initialize local ML models for offline analysis."""
        try:
            # Load code quality classification model
            self.quality_classifier = pipeline(
                "text-classification",
                model="microsoft/codebert-base",
                device=-1  # Use CPU
            )
            
            # Load vulnerability detection model
            self.vulnerability_detector = pipeline(
                "token-classification",
                model="microsoft/codebert-base",
                device=-1
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize local ML models: {e}")
            self.quality_classifier = None
            self.vulnerability_detector = None
    
    async def analyze_file(
        self,
        file_path: str,
        file_content: str,
        repository: Repository,
        rules: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Comprehensive analysis of a single file."""
        try:
            logger.info(f"Analyzing file: {file_path}")
            
            # Determine file language
            language = self._detect_language(file_path)
            
            # Skip non-code files
            if not self._is_code_file(file_path, file_content):
                return []
            
            # Perform multiple analysis types
            issues = []
            
            # 1. AST-based static analysis
            ast_issues = await self._ast_analysis(file_path, file_content, language)
            issues.extend(ast_issues)
            
            # 2. Security vulnerability analysis
            security_issues = await self._security_analysis(file_path, file_content, language)
            issues.extend(security_issues)
            
            # 3. Code quality analysis
            quality_issues = await self._quality_analysis(file_path, file_content, language)
            issues.extend(quality_issues)
            
            # 4. AI-powered semantic analysis
            if self.openai_client:
                ai_issues = await self._ai_semantic_analysis(file_path, file_content, language, repository)
                issues.extend(ai_issues)
            
            # 5. Pattern-based rule analysis
            if rules:
                rule_issues = await self._rule_based_analysis(file_path, file_content, rules)
                issues.extend(rule_issues)
            
            # Deduplicate and prioritize issues
            issues = self._deduplicate_issues(issues)
            issues = self._prioritize_issues(issues)
            
            logger.info(f"Found {len(issues)} issues in {file_path}")
            return issues
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}", exc_info=True)
            return []
    
    async def _ast_analysis(self, file_path: str, file_content: str, language: str) -> List[Dict[str, Any]]:
        """AST-based static code analysis."""
        issues = []
        
        try:
            if language == 'python':
                # Parse Python code using AST
                tree = ast.parse(file_content)
                
                # Analyze AST for various issues
                ast_issues = self.ast_analyzer.analyze(tree, file_path)
                
                for issue in ast_issues:
                    issues.append({
                        'title': issue['title'],
                        'description': issue['description'],
                        'category': 'code_quality',
                        'severity': issue['severity'],
                        'rule_id': issue['rule_id'],
                        'file_path': file_path,
                        'line_start': issue['line_number'],
                        'line_end': issue.get('line_end'),
                        'column_start': issue.get('column_start'),
                        'column_end': issue.get('column_end'),
                        'code_snippet': issue.get('code_snippet'),
                        'suggested_fix': issue.get('suggested_fix'),
                        'confidence_score': issue.get('confidence', 0.8),
                    })
            
            # Use Tree-sitter for more advanced parsing
            if language in self.parsers:
                tree_sitter_issues = await self._tree_sitter_analysis(
                    file_path, file_content, language
                )
                issues.extend(tree_sitter_issues)
                
        except SyntaxError as e:
            # Handle syntax errors
            issues.append({
                'title': 'Syntax Error',
                'description': f'Syntax error in code: {str(e)}',
                'category': 'syntax',
                'severity': IssueSeverity.HIGH,
                'rule_id': 'syntax_error',
                'file_path': file_path,
                'line_start': getattr(e, 'lineno', 1),
                'line_end': getattr(e, 'lineno', 1),
                'column_start': getattr(e, 'offset', 1),
                'confidence_score': 1.0,
            })
            
        except Exception as e:
            logger.error(f"AST analysis failed for {file_path}: {e}")
        
        return issues
    
    async def _tree_sitter_analysis(self, file_path: str, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Advanced parsing using Tree-sitter."""
        issues = []
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(file_content, "utf8"))
            
            # Analyze the syntax tree
            issues.extend(self._analyze_complexity(tree, file_path))
            issues.extend(self._analyze_patterns(tree, file_path))
            issues.extend(self._analyze_naming_conventions(tree, file_path))
            
        except Exception as e:
            logger.error(f"Tree-sitter analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_complexity(self, tree, file_path: str) -> List[Dict[str, Any]]:
        """Analyze code complexity using Tree-sitter."""
        issues = []
        
        def traverse_node(node, depth=0):
            # Cyclomatic complexity calculation
            complexity_nodes = [
                'if_statement', 'while_statement', 'for_statement',
                'try_statement', 'except_clause', 'with_statement',
                'and', 'or', 'conditional_expression'
            ]
            
            if node.type in complexity_nodes:
                if depth > 10:  # High complexity threshold
                    issues.append({
                        'title': 'High Cyclomatic Complexity',
                        'description': f'Complex control flow detected (depth: {depth})',
                        'category': 'maintainability',
                        'severity': IssueSeverity.MEDIUM,
                        'rule_id': 'high_complexity',
                        'file_path': file_path,
                        'line_start': node.start_point[0] + 1,
                        'line_end': node.end_point[0] + 1,
                        'confidence_score': 0.9,
                    })
            
            for child in node.children:
                traverse_node(child, depth + (1 if node.type in complexity_nodes else 0))
        
        traverse_node(tree.root_node)
        return issues
    
    async def _security_analysis(self, file_path: str, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Security vulnerability analysis."""
        issues = []
        
        try:
            # Use dedicated security analyzer
            security_issues = await self.security_analyzer.analyze_file(
                file_path, file_content, language
            )
            
            for issue in security_issues:
                issues.append({
                    'title': issue['title'],
                    'description': issue['description'],
                    'category': 'security',
                    'severity': issue['severity'],
                    'rule_id': issue['rule_id'],
                    'file_path': file_path,
                    'line_start': issue['line_number'],
                    'line_end': issue.get('line_end'),
                    'code_snippet': issue.get('code_snippet'),
                    'suggested_fix': issue.get('suggested_fix'),
                    'confidence_score': issue.get('confidence', 0.85),
                })
                
        except Exception as e:
            logger.error(f"Security analysis failed for {file_path}: {e}")
        
        return issues
    
    async def _quality_analysis(self, file_path: str, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Code quality analysis using local ML models."""
        issues = []
        
        try:
            if self.quality_classifier:
                # Analyze code quality using transformer model
                chunks = self._chunk_code_for_analysis(file_content)
                
                for i, chunk in enumerate(chunks):
                    try:
                        # Truncate if too long
                        if len(chunk) > 512:
                            chunk = chunk[:512]
                        
                        result = self.quality_classifier(chunk)
                        
                        # Process classification results
                        if result and len(result) > 0:
                            label = result[0]['label']
                            score = result[0]['score']
                            
                            if label.lower() in ['poor', 'bad', 'low_quality'] and score > 0.7:
                                issues.append({
                                    'title': 'Code Quality Issue',
                                    'description': f'Code quality concern detected: {label}',
                                    'category': 'code_quality',
                                    'severity': IssueSeverity.MEDIUM,
                                    'rule_id': 'ml_quality_check',
                                    'file_path': file_path,
                                    'line_start': i * 20 + 1,  # Approximate line number
                                    'line_end': (i + 1) * 20,
                                    'confidence_score': score,
                                })
                                
                    except Exception as e:
                        logger.warning(f"Quality analysis chunk failed: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Quality analysis failed for {file_path}: {e}")
        
        return issues
    
    async def _ai_semantic_analysis(
        self, 
        file_path: str, 
        file_content: str, 
        language: str, 
        repository: Repository
    ) -> List[Dict[str, Any]]:
        """AI-powered semantic code analysis using OpenAI."""
        issues = []
        
        try:
            if not self.openai_client:
                return issues
            
            # Prepare context for AI analysis
            context = self._build_analysis_context(file_path, file_content, language, repository)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(file_path, file_content, language, context)
            
            # Check token count and truncate if necessary
            token_count = len(self.tokenizer.encode(prompt))
            if token_count > 3000:  # Leave room for response
                file_content = self._truncate_content(file_content, 2000)
                prompt = self._create_analysis_prompt(file_path, file_content, language, context)
            
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer. Analyze the provided code for issues, bugs, security vulnerabilities, performance problems, and style violations. Return your findings as a JSON array."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            ai_issues = self._parse_ai_response(ai_response, file_path)
            issues.extend(ai_issues)
            
        except Exception as e:
            logger.error(f"AI semantic analysis failed for {file_path}: {e}")
        
        return issues
    
    def _create_analysis_prompt(self, file_path: str, file_content: str, language: str, context: Dict) -> str:
        """Create analysis prompt for AI."""
        return f"""
Analyze the following {language} code file for issues:

File: {file_path}
Language: {language}
Repository Context: {context.get('repository_info', 'N/A')}

Code:
{file_content}

Please identify and return issues in the following JSON format:
[
  {{
    "title": "Issue title",
    "description": "Detailed description",
    "category": "security|performance|maintainability|style|bug",
    "severity": "critical|high|medium|low",
    "line_number": 123,
    "code_snippet": "problematic code",
    "suggested_fix": "how to fix",
    "explanation": "why this is an issue"
  }}
]

Focus on:
1. Security vulnerabilities
2. Performance bottlenecks  
3. Potential bugs
4. Code maintainability issues
5. Best practice violations
"""
    
    def _parse_ai_response(self, ai_response: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured issues."""
        issues = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if not json_match:
                return issues
            
            json_str = json_match.group(0)
            ai_issues = json.loads(json_str)
            
            for issue in ai_issues:
                # Map severity string to enum
                severity_map = {
                    'critical': IssueSeverity.CRITICAL,
                    'high': IssueSeverity.HIGH,
                    'medium': IssueSeverity.MEDIUM,
                    'low': IssueSeverity.LOW,
                }
                
                issues.append({
                    'title': issue.get('title', 'AI Detected Issue'),
                    'description': issue.get('description', ''),
                    'category': issue.get('category', 'general'),
                    'severity': severity_map.get(issue.get('severity', 'medium'), IssueSeverity.MEDIUM),
                    'rule_id': 'ai_analysis',
                    'file_path': file_path,
                    'line_start': issue.get('line_number', 1),
                    'code_snippet': issue.get('code_snippet', ''),
                    'suggested_fix': issue.get('suggested_fix', ''),
                    'ai_explanation': issue.get('explanation', ''),
                    'confidence_score': 0.75,  # AI confidence
                })
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
        
        return issues
    
    async def _rule_based_analysis(self, file_path: str, file_content: str, rules: List[str]) -> List[Dict[str, Any]]:
        """Apply custom rule-based analysis."""
        issues = []
        
        # Implement custom rules
        rule_patterns = {
            'no_hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
            ],
            'no_debug_prints': [
                r'print\s*\(',
                r'console\.log\s*\(',
            ],
            'no_todo_comments': [
                r'#\s*TODO',
                r'//\s*TODO',
                r'/\*\s*TODO',
            ],
        }
        
        for rule in rules:
            if rule in rule_patterns:
                patterns = rule_patterns[rule]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, file_content, re.IGNORECASE)
                    
                    for match in matches:
                        line_number = file_content[:match.start()].count('\n') + 1
                        
                        issues.append({
                            'title': f'Rule Violation: {rule}',
                            'description': f'Pattern "{pattern}" found in code',
                            'category': 'style',
                            'severity': IssueSeverity.LOW,
                            'rule_id': rule,
                            'file_path': file_path,
                            'line_start': line_number,
                            'code_snippet': match.group(0),
                            'confidence_score': 0.9,
                        })
        
        return issues
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        extension = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
        }
        
        return language_map.get(extension, 'unknown')
    
    def _is_code_file(self, file_path: str, file_content: str) -> bool:
        """Check if file is a code file worth analyzing."""
        # Skip binary files
        try:
            file_content.encode('utf-8')
        except UnicodeDecodeError:
            return False
        
        # Skip empty files
        if len(file_content.strip()) == 0:
            return False
        
        # Skip very large files (>1MB)
        if len(file_content) > 1024 * 1024:
            return False
        
        # Check file extension
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.dart'
        }
        
        extension = Path(file_path).suffix.lower()
        return extension in code_extensions
    
    def _chunk_code_for_analysis(self, file_content: str, chunk_size: int = 20) -> List[str]:
        """Split code into chunks for analysis."""
        lines = file_content.split('\n')
        chunks = []
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunks.append('\n'.join(chunk_lines))
        
        return chunks
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit within token limit."""
        tokens = self.tokenizer.encode(content)
        if len(tokens) <= max_tokens:
            return content
        
        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens)
    
    def _build_analysis_context(self, file_path: str, file_content: str, language: str, repository: Repository) -> Dict:
        """Build context information for AI analysis."""
        return {
            'repository_info': {
                'name': repository.name,
                'language': repository.language,
                'description': repository.description,
            },
            'file_info': {
                'path': file_path,
                'language': language,
                'lines': len(file_content.split('\n')),
            }
        }
    
    def _deduplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate issues."""
        seen = set()
        unique_issues = []
        
        for issue in issues:
            # Create hash of issue characteristics
            issue_key = (
                issue['title'],
                issue['file_path'],
                issue['line_start'],
                issue['category']
            )
            
            if issue_key not in seen:
                seen.add(issue_key)
                unique_issues.append(issue)
        
        return unique_issues
    
    def _prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort issues by priority (severity and confidence)."""
        severity_order = {
            IssueSeverity.CRITICAL: 4,
            IssueSeverity.HIGH: 3,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 1,
        }
        
        def priority_key(issue):
            severity_score = severity_order.get(issue['severity'], 1)
            confidence_score = issue.get('confidence_score', 0.5)
            return (severity_score, confidence_score)
        
        return sorted(issues, key=priority_key, reverse=True)
    
    async def calculate_quality_metrics(
        self,
        repository_id: int,
        issues: List[Dict[str, Any]],
        total_files: int,
    ) -> Dict[str, float]:
        """Calculate comprehensive quality metrics."""
        try:
            # Count issues by severity
            critical_count = sum(1 for i in issues if i['severity'] == IssueSeverity.CRITICAL)
            high_count = sum(1 for i in issues if i['severity'] == IssueSeverity.HIGH)
            medium_count = sum(1 for i in issues if i['severity'] == IssueSeverity.MEDIUM)
            low_count = sum(1 for i in issues if i['severity'] == IssueSeverity.LOW)
            
            # Count issues by category
            security_count = sum(1 for i in issues if i['category'] == 'security')
            performance_count = sum(1 for i in issues if i['category'] == 'performance')
            maintainability_count = sum(1 for i in issues if i['category'] == 'maintainability')
            
            total_issues = len(issues)
            
            # Calculate scores (0-10 scale)
            code_quality_score = max(0, 10 - (
                critical_count * 3 +
                high_count * 2 +
                medium_count * 1 +
                low_count * 0.5
            ) / max(total_files, 1))
            
            security_score = max(0, 10 - (security_count * 2) / max(total_files, 1))
            
            maintainability_score = max(0, 10 - (
                maintainability_count * 1.5 +
                critical_count * 2
            ) / max(total_files, 1))
            
            # Performance score based on performance issues
            performance_score = max(0, 10 - (performance_count * 1.5) / max(total_files, 1))
            
            return {
                'code_quality_score': round(code_quality_score, 2),
                'security_score': round(security_score, 2),
                'maintainability_score': round(maintainability_score, 2),
                'performance_score': round(performance_score, 2),
                'total_issues': total_issues,
                'critical_issues': critical_count,
                'high_issues': high_count,
                'medium_issues': medium_count,
                'low_issues': low_count,
                'security_issues': security_count,
                'performance_issues': performance_count,
                'maintainability_issues': maintainability_count,
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {
                'code_quality_score': 5.0,
                'security_score': 5.0,
                'maintainability_score': 5.0,
                'performance_score': 5.0,
                'total_issues': len(issues),
            }
    
    async def generate_review_summary(self, review, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI-powered review summary."""
        try:
            if not self.openai_client:
                return self._generate_fallback_summary(review, issues)
            
            # Prepare summary context
            context = self._prepare_summary_context(review, issues)
            
            prompt = f"""
Generate a comprehensive code review summary based on the following analysis:

Repository: {review.repository.name}
Total Files Analyzed: {review.total_files}
Total Issues Found: {len(issues)}

Issue Breakdown:
- Critical: {sum(1 for i in issues if i['severity'] == IssueSeverity.CRITICAL)}
- High: {sum(1 for i in issues if i['severity'] == IssueSeverity.HIGH)}
- Medium: {sum(1 for i in issues if i['severity'] == IssueSeverity.MEDIUM)}
- Low: {sum(1 for i in issues if i['severity'] == IssueSeverity.LOW)}

Category Breakdown:
- Security: {sum(1 for i in issues if i['category'] == 'security')}
- Performance: {sum(1 for i in issues if i['category'] == 'performance')}
- Maintainability: {sum(1 for i in issues if i['category'] == 'maintainability')}
- Code Quality: {sum(1 for i in issues if i['category'] == 'code_quality')}

Top Issues:
{self._format_top_issues(issues[:5])}

Please provide:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points)
3. Risk Assessment
4. Recommended Actions
5. Overall Assessment

Format as structured text, not JSON.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code review specialist. Provide clear, actionable summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            
            summary_text = response.choices[0].message.content
            
            return {
                'summary': summary_text,
                'generated_by': 'ai',
                'model': 'gpt-4',
            }
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return self._generate_fallback_summary(review, issues)
    
    def _generate_fallback_summary(self, review, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback summary without AI."""
        critical_count = sum(1 for i in issues if i['severity'] == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in issues if i['severity'] == IssueSeverity.HIGH)
        total_issues = len(issues)
        
        if critical_count > 0:
            risk_level = "High"
        elif high_count > 5:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        summary = f"""
Code Review Summary for {review.repository.name}

Executive Summary:
Analyzed {review.total_files} files and found {total_issues} issues. Risk level: {risk_level}.

Key Findings:
• {critical_count} critical issues requiring immediate attention
• {high_count} high-priority issues affecting code quality
• {sum(1 for i in issues if i['category'] == 'security')} security-related concerns
• {sum(1 for i in issues if i['category'] == 'performance')} performance optimization opportunities

Recommended Actions:
1. Address all critical and high-severity issues first
2. Review security vulnerabilities immediately
3. Consider refactoring for maintainability improvements
4. Implement automated testing for quality assurance

Overall Assessment: {'Needs Improvement' if total_issues > 10 else 'Good' if total_issues > 3 else 'Excellent'}
"""
        
        return {
            'summary': summary,
            'generated_by': 'fallback',
            'model': 'rule_based',
        }
    
    def _format_top_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Format top issues for summary."""
        formatted = []
        for i, issue in enumerate(issues, 1):
            formatted.append(f"{i}. {issue['title']} ({issue['severity'].value}) - {issue['file_path']}:{issue['line_start']}")
        return '\n'.join(formatted)
    
    async def generate_recommendations(self, review, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Group issues by category
        security_issues = [i for i in issues if i['category'] == 'security']
        performance_issues = [i for i in issues if i['category'] == 'performance']
        quality_issues = [i for i in issues if i['category'] == 'code_quality']
        
        # Security recommendations
        if security_issues:
            recommendations.append({
                'category': 'security',
                'priority': 'high',
                'title': 'Address Security Vulnerabilities',
                'description': f'Found {len(security_issues)} security issues that need immediate attention.',
                'action_items': [
                    'Review and fix all security vulnerabilities',
                    'Implement input validation and sanitization',
                    'Add security testing to CI/CD pipeline',
                    'Consider security code review training for team',
                ]
            })
        
        # Performance recommendations
        if performance_issues:
            recommendations.append({
                'category': 'performance',
                'priority': 'medium',
                'title': 'Optimize Performance',
                'description': f'Identified {len(performance_issues)} performance optimization opportunities.',
                'action_items': [
                    'Profile application performance',
                    'Optimize database queries and API calls',
                    'Implement caching strategies',
                    'Consider code splitting and lazy loading',
                ]
            })
        
        # Code quality recommendations
        if quality_issues:
            recommendations.append({
                'category': 'quality',
                'priority': 'medium',
                'title': 'Improve Code Quality',
                'description': f'Found {len(quality_issues)} code quality issues affecting maintainability.',
                'action_items': [
                    'Refactor complex functions and classes',
                    'Add comprehensive unit tests',
                    'Improve code documentation',
                    'Establish coding standards and linting rules',
                ]
            })
        
        return recommendations
