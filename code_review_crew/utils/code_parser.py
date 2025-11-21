"""
Code Parser Utility

Utilities for parsing Python code using AST (Abstract Syntax Tree).
Extracts functions, classes, imports, and other code structures.
"""

import ast
from typing import Dict, List, Optional, Any


class CodeParser:
    """Parser for Python source code using AST"""
    
    def __init__(self):
        self.tree = None
        self.source_code = ""
    
    def parse(self, code: str) -> Dict:
        """
        Parse Python code and extract all information
        
        Args:
            code: Python source code
        
        Returns:
            Dictionary containing all parsed information
        """
        self.source_code = code
        
        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            return {
                'error': 'syntax_error',
                'message': str(e),
                'line': e.lineno,
                'offset': e.offset
            }
        
        return {
            'functions': self.extract_functions(),
            'classes': self.extract_classes(),
            'imports': self.extract_imports(),
            'global_variables': self.extract_global_variables(),
            'docstrings': self.extract_docstrings(),
            'complexity': self.calculate_basic_complexity(),
            'lines_of_code': len(code.split('\n'))
        }
    
    def extract_functions(self) -> List[Dict]:
        """Extract all function definitions"""
        if not self.tree:
            return []
        
        functions = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'returns': self._get_return_annotation(node),
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node),
                    'is_async': False,
                    'body_lines': self._count_body_lines(node)
                }
                functions.append(func_info)
            
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'returns': self._get_return_annotation(node),
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node),
                    'is_async': True,
                    'body_lines': self._count_body_lines(node)
                }
                functions.append(func_info)
        
        return functions
    
    def extract_classes(self) -> List[Dict]:
        """Extract all class definitions"""
        if not self.tree:
            return []
        
        classes = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [self._get_name(base) for base in node.bases],
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node),
                    'methods': self._extract_methods(node),
                    'attributes': self._extract_attributes(node)
                }
                classes.append(class_info)
        
        return classes
    
    def extract_imports(self) -> Dict:
        """Extract all import statements"""
        if not self.tree:
            return {}
        
        imports = {
            'standard': [],
            'third_party': [],
            'from_imports': []
        }
        
        standard_libs = {
            'os', 'sys', 'json', 'math', 'datetime', 'collections',
            'itertools', 'functools', 're', 'typing', 'pathlib'
        }
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    target = 'standard' if module in standard_libs else 'third_party'
                    imports[target].append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module.split('.')[0] if node.module else ''
                target = 'standard' if module in standard_libs else 'third_party'
                
                for alias in node.names:
                    imports['from_imports'].append({
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'type': target
                    })
        
        return imports
    
    def extract_global_variables(self) -> List[Dict]:
        """Extract global variable assignments"""
        if not self.tree:
            return []
        
        variables = []
        
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({
                            'name': target.id,
                            'line': node.lineno,
                            'type': self._infer_type(node.value)
                        })
        
        return variables
    
    def extract_docstrings(self) -> Dict:
        """Extract all docstrings from code"""
        if not self.tree:
            return {}
        
        docstrings = {
            'module': ast.get_docstring(self.tree),
            'functions': {},
            'classes': {}
        }
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    docstrings['functions'][node.name] = doc
            
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                if doc:
                    docstrings['classes'][node.name] = doc
        
        return docstrings
    
    def calculate_basic_complexity(self) -> Dict:
        """Calculate basic complexity metrics"""
        if not self.tree:
            return {}
        
        complexity = {
            'num_functions': 0,
            'num_classes': 0,
            'num_imports': 0,
            'max_nesting_depth': 0,
            'num_loops': 0,
            'num_conditionals': 0
        }
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity['num_functions'] += 1
            elif isinstance(node, ast.ClassDef):
                complexity['num_classes'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                complexity['num_imports'] += 1
            elif isinstance(node, (ast.For, ast.While)):
                complexity['num_loops'] += 1
            elif isinstance(node, ast.If):
                complexity['num_conditionals'] += 1
        
        complexity['max_nesting_depth'] = self._calculate_max_depth()
        
        return complexity
    
    def find_function(self, function_name: str) -> Optional[Dict]:
        """Find a specific function by name"""
        functions = self.extract_functions()
        for func in functions:
            if func['name'] == function_name:
                return func
        return None
    
    def find_class(self, class_name: str) -> Optional[Dict]:
        """Find a specific class by name"""
        classes = self.extract_classes()
        for cls in classes:
            if cls['name'] == class_name:
                return cls
        return None
    
    def get_function_calls(self) -> List[Dict]:
        """Extract all function calls in the code"""
        if not self.tree:
            return []
        
        calls = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node.func)
                if func_name:
                    calls.append({
                        'function': func_name,
                        'line': node.lineno,
                        'num_args': len(node.args),
                        'has_kwargs': len(node.keywords) > 0
                    })
        
        return calls
    
    def get_dependencies(self) -> Dict:
        """Get code dependencies (imported modules and function calls)"""
        imports = self.extract_imports()
        calls = self.get_function_calls()
        
        return {
            'imported_modules': list(set(
                [imp['module'] for imp in imports['standard']] +
                [imp['module'] for imp in imports['third_party']]
            )),
            'function_calls': list(set([call['function'] for call in calls])),
            'total_dependencies': len(imports['standard']) + len(imports['third_party'])
        }
    
    # Helper methods
    
    def _extract_methods(self, class_node: ast.ClassDef) -> List[Dict]:
        """Extract methods from a class"""
        methods = []
        
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    'name': node.name,
                    'line': node.lineno,
                    'is_private': node.name.startswith('_'),
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'args': [arg.arg for arg in node.args.args]
                })
        
        return methods
    
    def _extract_attributes(self, class_node: ast.ClassDef) -> List[str]:
        """Extract class attributes"""
        attributes = []
        
        for node in ast.walk(class_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            attributes.append(target.attr)
        
        return list(set(attributes))
    
    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation"""
        if node.returns:
            return ast.unparse(node.returns)
        return None
    
    def _get_decorator_name(self, decorator: Any) -> str:
        """Get decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        return str(decorator)
    
    def _get_name(self, node: Any) -> str:
        """Get name from various node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_call_name(self, node: Any) -> Optional[str]:
        """Get function call name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return None
    
    def _count_body_lines(self, node: ast.FunctionDef) -> int:
        """Count lines in function body"""
        if not node.body:
            return 0
        first_line = node.body[0].lineno
        last_line = node.body[-1].lineno
        return last_line - first_line + 1
    
    def _infer_type(self, node: Any) -> str:
        """Infer type from assignment value"""
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
        return 'unknown'
    
    def _calculate_max_depth(self, node: Optional[Any] = None, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        if node is None:
            node = self.tree
        
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_max_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth


# Convenience functions

def parse_code(code: str) -> Dict:
    """Quick parse function"""
    parser = CodeParser()
    return parser.parse(code)


def extract_function_signatures(code: str) -> List[str]:
    """Extract just function signatures"""
    parser = CodeParser()
    parser.parse(code)
    functions = parser.extract_functions()
    
    signatures = []
    for func in functions:
        args_str = ', '.join(func['args'])
        sig = f"def {func['name']}({args_str})"
        if func['returns']:
            sig += f" -> {func['returns']}"
        signatures.append(sig)
    
    return signatures


def get_code_summary(code: str) -> str:
    """Get a text summary of the code"""
    result = parse_code(code)
    
    if 'error' in result:
        return f"Syntax Error: {result['message']} at line {result['line']}"
    
    summary = f"""
Code Summary:
- {result['complexity']['num_functions']} functions
- {result['complexity']['num_classes']} classes
- {result['complexity']['num_imports']} imports
- {result['lines_of_code']} lines of code
- Max nesting depth: {result['complexity']['max_nesting_depth']}
- {result['complexity']['num_loops']} loops
- {result['complexity']['num_conditionals']} conditionals
"""
    
    return summary.strip()