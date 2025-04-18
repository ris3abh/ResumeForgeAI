"""
LaTeX Utilities - Helper functions for working with LaTeX documents.
"""

import re

def fix_latex_issues(modified_content, original_content):
    """
    Fix common LaTeX issues in the modified content.
    
    Args:
        modified_content (str): The modified LaTeX content with issues
        original_content (str): The original LaTeX content for reference
        
    Returns:
        str: The fixed LaTeX content
    """
    # Remove Markdown code block markers
    modified_content = re.sub(r'```(?:latex)?\n', '', modified_content)
    modified_content = re.sub(r'\n```', '', modified_content)
    
    # Remove explanatory comments that might have been added
    modified_content = re.sub(r'###[^\n]*\n', '', modified_content)
    modified_content = re.sub(r'Key Changes[^\n]*\n', '', modified_content)
    
    # Ensure document class is preserved
    if '\\documentclass' not in modified_content and '\\documentclass' in original_content:
        doc_class_match = re.search(r'(\\documentclass.*?\n)', original_content)
        if doc_class_match:
            modified_content = doc_class_match.group(1) + modified_content
    
    # Ensure begin/end document is preserved
    if '\\begin{document}' not in modified_content and '\\begin{document}' in original_content:
        begin_match = re.search(r'(\\begin\{document\}.*?\n)', original_content, re.DOTALL)
        if begin_match:
            modified_content += '\n' + begin_match.group(1)
    
    if '\\end{document}' not in modified_content and '\\end{document}' in original_content:
        modified_content += '\n\\end{document}'
    
    # Fix any unbalanced braces
    def balance_braces(content):
        stack = []
        for char in content:
            if char == '{':
                stack.append('{')
            elif char == '}':
                if stack and stack[-1] == '{':
                    stack.pop()
                else:
                    stack.append('}')  # Unmatched closing brace
        
        # Add any missing closing braces
        if stack.count('{') > 0:
            content += '}' * stack.count('{')
        
        return content
    
    modified_content = balance_braces(modified_content)
    
    return modified_content


def extract_preamble(latex_content):
    """
    Extract the preamble from a LaTeX document.
    
    Args:
        latex_content (str): The LaTeX document content
        
    Returns:
        str: The preamble content
    """
    match = re.search(r'(.*?)\\begin\{document\}', latex_content, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def extract_document_body(latex_content):
    """
    Extract the document body from a LaTeX document.
    
    Args:
        latex_content (str): The LaTeX document content
        
    Returns:
        str: The document body content
    """
    body_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', latex_content, re.DOTALL)
    if body_match:
        return body_match.group(1)
    return ""


def validate_latex_syntax(latex_content):
    """
    Perform basic validation of LaTeX syntax.
    
    Args:
        latex_content (str): The LaTeX document content
        
    Returns:
        bool: True if the syntax appears valid, False otherwise
    """
    # Check for balanced braces
    brace_count = 0
    for char in latex_content:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        if brace_count < 0:
            return False
    
    # Check for essential document structure
    has_document_class = bool(re.search(r'\\documentclass', latex_content))
    has_begin_document = bool(re.search(r'\\begin\{document\}', latex_content))
    has_end_document = bool(re.search(r'\\end\{document\}', latex_content))
    
    return (brace_count == 0 and 
            has_document_class and 
            has_begin_document and 
            has_end_document)

def compare_latex_structure(original, modified):
    """
    Compare the LaTeX structure between original and modified content to ensure
    critical LaTeX commands and environments are preserved.
    
    Args:
        original (str): The original LaTeX content
        modified (str): The modified LaTeX content
        
    Returns:
        tuple: (is_valid, issues)
            - is_valid (bool): True if the structure is preserved
            - issues (list): List of identified issues
    """
    issues = []
    
    # Check for missing or extra begin/end document commands
    orig_begin_count = original.count('\\begin{document}')
    mod_begin_count = modified.count('\\begin{document}')
    
    if orig_begin_count != mod_begin_count:
        issues.append(f"Begin document count mismatch: Original {orig_begin_count}, Modified {mod_begin_count}")
    
    orig_end_count = original.count('\\end{document}')
    mod_end_count = modified.count('\\end{document}')
    
    if orig_end_count != mod_end_count:
        issues.append(f"End document count mismatch: Original {orig_end_count}, Modified {mod_end_count}")
    
    # Check for missing or extra section commands
    import re
    orig_sections = re.findall(r'\\section\{([^}]+)\}', original)
    mod_sections = re.findall(r'\\section\{([^}]+)\}', original)
    
    if len(orig_sections) != len(mod_sections):
        issues.append(f"Section count mismatch: Original {len(orig_sections)}, Modified {len(mod_sections)}")
    
    # Check for balanced braces
    def check_balanced_braces(content):
        stack = []
        for i, char in enumerate(content):
            if char == '{':
                stack.append((i, char))
            elif char == '}':
                if not stack or stack[-1][1] != '{':
                    return False, i
                stack.pop()
        return len(stack) == 0, stack
    
    orig_balanced, orig_issue = check_balanced_braces(original)
    mod_balanced, mod_issue = check_balanced_braces(modified)
    
    if not mod_balanced:
        issues.append(f"Unbalanced braces in modified content")
    
    # Check for any custom commands used in the original that are missing in the modified
    custom_commands = re.findall(r'\\resume[A-Za-z]+', original)
    for cmd in set(custom_commands):
        orig_count = original.count(cmd)
        mod_count = modified.count(cmd)
        if mod_count < orig_count:
            issues.append(f"Custom command usage mismatch: {cmd} appears {orig_count} times in original but {mod_count} times in modified")
    
    return len(issues) == 0, issues