"""LaTeX handler for managing LaTeX documents and agent interactions."""

import re
import logging
import os
import difflib
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from colorama import Fore, Style

from resume_optimizer.utils.latex_utils import (
    read_latex_file, 
    save_latex_file, 
    extract_section, 
    replace_section,
    extract_latex_content
)


class LatexHandler:
    """Handler for LaTeX document operations and agent communication debugging."""
    
    def __init__(self, debug_mode: bool = True, debug_dir: str = "debug_output"):
        """Initialize the LaTeX handler.
        
        Args:
            debug_mode: Whether to print debug information
            debug_dir: Directory for debug output files
        """
        self.debug_mode = debug_mode
        self.debug_dir = debug_dir
        if debug_mode:
            os.makedirs(debug_dir, exist_ok=True)
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging for the LaTeX handler."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/resume_optimization.log")
            ]
        )
        self.logger = logging.getLogger("LatexHandler")
    
    def read_resume(self, resume_path: str) -> str:
        """Read a resume file and return its content.
        
        Args:
            resume_path: Path to the resume file
            
        Returns:
            The content of the resume file
        """
        if self.debug_mode:
            self.logger.info(f"{Fore.BLUE}Reading resume from {resume_path}{Style.RESET_ALL}")
        
        content = read_latex_file(resume_path)
        
        if self.debug_mode:
            self.logger.info(f"{Fore.GREEN}Successfully read resume ({len(content)} characters){Style.RESET_ALL}")
            # Save a copy in debug directory
            with open(os.path.join(self.debug_dir, "original_resume.tex"), "w") as f:
                f.write(content)
            
        return content
    
    def save_resume(self, content: str, output_path: str) -> None:
        """Save resume content to a file.
        
        Args:
            content: The resume content to save
            output_path: Path where the resume will be saved
        """
        if self.debug_mode:
            self.logger.info(f"{Fore.BLUE}Saving resume to {output_path}{Style.RESET_ALL}")
            
        save_latex_file(content, output_path)
        
        if self.debug_mode:
            self.logger.info(f"{Fore.GREEN}Successfully saved resume ({len(content)} characters){Style.RESET_ALL}")
            # Save a copy in debug directory
            with open(os.path.join(self.debug_dir, "optimized_resume.tex"), "w") as f:
                f.write(content)
    
    def extract_sections(self, content: str) -> Dict[str, str]:
        """Extract all sections from a LaTeX document.
        
        Args:
            content: The LaTeX document content
            
        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        section_pattern = r"\\section{([^}]+)}(.*?)(?=\\section{|\\end{document})"
        matches = re.finditer(section_pattern, content, re.DOTALL)
        
        for match in matches:
            section_name = match.group(1)
            section_content = match.group(2).strip()
            sections[section_name] = section_content
            
            if self.debug_mode:
                self.logger.info(f"{Fore.CYAN}Extracted section '{section_name}' ({len(section_content)} characters){Style.RESET_ALL}")
                # Save each section in debug directory
                safe_name = section_name.replace(" ", "_").lower()
                with open(os.path.join(self.debug_dir, f"original_{safe_name}.tex"), "w") as f:
                    f.write(section_content)
        
        return sections
    
    def update_section(self, resume_content: str, section_name: str, new_content: str) -> str:
        """Update a section in the resume with new content.
        
        Args:
            resume_content: The full resume content
            section_name: Name of the section to update
            new_content: New content for the section
            
        Returns:
            Updated resume content
        """
        if self.debug_mode:
            self.logger.info(f"{Fore.BLUE}Updating section '{section_name}'{Style.RESET_ALL}")
            # Save new section content in debug directory
            safe_name = section_name.replace(" ", "_").lower()
            with open(os.path.join(self.debug_dir, f"optimized_{safe_name}.tex"), "w") as f:
                f.write(new_content)
        
        updated_content = replace_section(resume_content, section_name, new_content)
        
        if self.debug_mode:
            self.logger.info(f"{Fore.GREEN}Successfully updated section '{section_name}'{Style.RESET_ALL}")
        
        return updated_content
    
    def log_agent_communication(self, 
                               agent_name: str, 
                               input_data: str, 
                               output_data: str, 
                               context: Optional[Dict] = None):
        """Log communication between agents for debugging.
        
        Args:
            agent_name: Name of the agent
            input_data: Input data received by the agent
            output_data: Output data produced by the agent
            context: Optional context information
        """
        if not self.debug_mode:
            return
            
        self.logger.info(f"\n{Fore.YELLOW}{'='*30} AGENT COMMUNICATION {'='*30}{Style.RESET_ALL}")
        self.logger.info(f"{Fore.MAGENTA}Agent: {agent_name}{Style.RESET_ALL}")
        
        # Save to files in debug directory
        agent_dir = os.path.join(self.debug_dir, agent_name.replace(" ", "_").lower())
        os.makedirs(agent_dir, exist_ok=True)
        
        # Generate timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save input
        with open(os.path.join(agent_dir, f"{timestamp}_input.txt"), "w") as f:
            f.write(input_data)
        
        # Save output
        with open(os.path.join(agent_dir, f"{timestamp}_output.txt"), "w") as f:
            f.write(output_data)
        
        # Save context if provided
        if context:
            with open(os.path.join(agent_dir, f"{timestamp}_context.json"), "w") as f:
                context_copy = {k: v for k, v in context.items()}
                # Convert any non-serializable values to strings
                for k, v in context_copy.items():
                    if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                        context_copy[k] = str(v)
                json.dump(context_copy, f, indent=2)
        
        if context:
            self.logger.info(f"\n{Fore.BLUE}Context:{Style.RESET_ALL}")
            for key, value in context.items():
                if isinstance(value, str) and len(value) > 500:
                    value = value[:500] + "... [truncated]"
                self.logger.info(f"{Fore.BLUE}{key}: {value}{Style.RESET_ALL}")
        
        truncated_input = input_data
        if len(input_data) > 1000:
            truncated_input = input_data[:1000] + "... [truncated]"
            
        truncated_output = output_data
        if len(output_data) > 1000:
            truncated_output = output_data[:1000] + "... [truncated]"
        
        self.logger.info(f"\n{Fore.GREEN}Input:{Style.RESET_ALL}\n{truncated_input}")
        self.logger.info(f"\n{Fore.GREEN}Output:{Style.RESET_ALL}\n{truncated_output}")
        self.logger.info(f"\n{Fore.YELLOW}{'='*80}{Style.RESET_ALL}\n")
        
    def log_optimization_result(self, 
                               section_name: str, 
                               original: str, 
                               optimized: str,
                               analysis_results: Optional[Dict] = None):
        """Log the before and after of a section optimization.
        
        Args:
            section_name: Name of the section
            original: Original section content
            optimized: Optimized section content
            analysis_results: Optional job analysis results
        """
        if not self.debug_mode:
            return
            
        self.logger.info(f"\n{Fore.YELLOW}{'='*30} OPTIMIZATION RESULT: {section_name} {'='*30}{Style.RESET_ALL}")
        
        # Save to files in debug directory
        section_dir = os.path.join(self.debug_dir, "section_optimizations")
        os.makedirs(section_dir, exist_ok=True)
        
        safe_name = section_name.replace(" ", "_").lower()
        
        # Save original
        with open(os.path.join(section_dir, f"{safe_name}_original.tex"), "w") as f:
            f.write(original)
        
        # Save optimized
        with open(os.path.join(section_dir, f"{safe_name}_optimized.tex"), "w") as f:
            f.write(optimized)
        
        # Save analysis results if provided
        if analysis_results:
            with open(os.path.join(section_dir, f"{safe_name}_analysis.json"), "w") as f:
                analysis_copy = {k: v for k, v in analysis_results.items()}
                # Convert any non-serializable values to strings
                for k, v in analysis_copy.items():
                    if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                        analysis_copy[k] = str(v)
                json.dump(analysis_copy, f, indent=2)
        
        if analysis_results:
            self.logger.info(f"\n{Fore.BLUE}Analysis Used:{Style.RESET_ALL}")
            for key, value in analysis_results.items():
                if isinstance(value, list) and len(value) > 5:
                    self.logger.info(f"{Fore.BLUE}{key}: {value[:5]} ... [+{len(value)-5} more]{Style.RESET_ALL}")
                else:
                    self.logger.info(f"{Fore.BLUE}{key}: {value}{Style.RESET_ALL}")
        
        self.logger.info(f"\n{Fore.RED}Original:{Style.RESET_ALL}\n{original}")
        self.logger.info(f"\n{Fore.GREEN}Optimized:{Style.RESET_ALL}\n{optimized}")
        
        # Highlight differences
        diff = difflib.unified_diff(
            original.splitlines(),
            optimized.splitlines(),
            lineterm='',
        )
        
        self.logger.info(f"\n{Fore.CYAN}Differences:{Style.RESET_ALL}")
        
        # Save diff to file
        diff_lines = list(diff)  # Convert generator to list
        with open(os.path.join(section_dir, f"{safe_name}_diff.txt"), "w") as f:
            f.write("\n".join(diff_lines))
        
        # Reset diff generator
        diff = difflib.unified_diff(
            original.splitlines(),
            optimized.splitlines(),
            lineterm='',
        )
        
        for line in diff:
            if line.startswith('+'):
                self.logger.info(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
            elif line.startswith('-'):
                self.logger.info(f"{Fore.RED}{line}{Style.RESET_ALL}")
            elif line.startswith('@@'):
                self.logger.info(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
            else:
                self.logger.info(line)
        
        self.logger.info(f"\n{Fore.YELLOW}{'='*80}{Style.RESET_ALL}\n")
    
    def compare_resumes(self, original_path: str, optimized_path: str) -> Dict[str, Any]:
        """Compare the original and optimized resumes.
        
        Args:
            original_path: Path to the original resume
            optimized_path: Path to the optimized resume
            
        Returns:
            Dictionary with comparison results
        """
        original = read_latex_file(original_path)
        optimized = read_latex_file(optimized_path)
        
        original_sections = self.extract_sections(original)
        optimized_sections = self.extract_sections(optimized)
        
        self.logger.info(f"\n{Fore.YELLOW}{'='*30} RESUME COMPARISON {'='*30}{Style.RESET_ALL}")
        
        # Save comparison results
        comparison_dir = os.path.join(self.debug_dir, "comparison")
        os.makedirs(comparison_dir, exist_ok=True)
        
        # Create a report file
        report_file = os.path.join(comparison_dir, "comparison_report.txt")
        with open(report_file, "w") as report:
            report.write(f"Resume Comparison Report\n")
            report.write(f"=======================\n\n")
            report.write(f"Original Resume: {original_path}\n")
            report.write(f"Optimized Resume: {optimized_path}\n\n")
        
        comparison_results = {
            "sections": {},
            "added_sections": [],
            "removed_sections": [],
            "unchanged_sections": []
        }
        
        # Find sections in both resumes
        for section in set(original_sections.keys()) | set(optimized_sections.keys()):
            self.logger.info(f"\n{Fore.MAGENTA}Section: {section}{Style.RESET_ALL}")
            
            with open(report_file, "a") as report:
                report.write(f"\nSection: {section}\n")
                report.write(f"{'-' * (len(section) + 9)}\n")
            
            if section not in original_sections:
                self.logger.info(f"{Fore.GREEN}New section added{Style.RESET_ALL}")
                self.logger.info(f"{Fore.GREEN}{optimized_sections[section]}{Style.RESET_ALL}")
                
                comparison_results["added_sections"].append(section)
                
                with open(report_file, "a") as report:
                    report.write(f"Status: NEW SECTION ADDED\n\n")
                    report.write(f"Content:\n{optimized_sections[section]}\n")
                
            elif section not in optimized_sections:
                self.logger.info(f"{Fore.RED}Section removed{Style.RESET_ALL}")
                self.logger.info(f"{Fore.RED}{original_sections[section]}{Style.RESET_ALL}")
                
                comparison_results["removed_sections"].append(section)
                
                with open(report_file, "a") as report:
                    report.write(f"Status: SECTION REMOVED\n\n")
                    report.write(f"Original Content:\n{original_sections[section]}\n")
                
            else:
                # Compare section content
                diff = difflib.unified_diff(
                    original_sections[section].splitlines(),
                    optimized_sections[section].splitlines(),
                    lineterm='',
                )
                
                self.logger.info(f"{Fore.CYAN}Differences:{Style.RESET_ALL}")
                
                # Save diff to file
                diff_lines = list(diff)  # Convert generator to list
                
                # Calculate section similarity percentage
                orig_lines = original_sections[section].splitlines()
                opt_lines = optimized_sections[section].splitlines()
                matcher = difflib.SequenceMatcher(None, original_sections[section], optimized_sections[section])
                similarity = matcher.ratio() * 100
                
                with open(report_file, "a") as report:
                    if len(diff_lines) <= 2:  # Just headers, no actual diff
                        report.write(f"Status: UNCHANGED (100% similar)\n\n")
                        comparison_results["unchanged_sections"].append(section)
                    else:
                        changes = len([l for l in diff_lines if l.startswith('+') or l.startswith('-')])
                        report.write(f"Status: MODIFIED ({similarity:.1f}% similar)\n")
                        report.write(f"Changes: {changes} lines\n\n")
                        report.write("Differences:\n")
                        report.write("\n".join(diff_lines))
                        report.write("\n\n")
                
                has_diff = len(diff_lines) > 2  # More than just headers
                
                if has_diff:
                    # Reset diff generator
                    diff = difflib.unified_diff(
                        original_sections[section].splitlines(),
                        optimized_sections[section].splitlines(),
                        lineterm='',
                    )
                    
                    section_changes = []
                    
                    for line in diff:
                        if line.startswith('+'):
                            self.logger.info(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
                            if not line.startswith('+++'):
                                section_changes.append({"type": "added", "content": line[1:]})
                        elif line.startswith('-'):
                            self.logger.info(f"{Fore.RED}{line}{Style.RESET_ALL}")
                            if not line.startswith('---'):
                                section_changes.append({"type": "removed", "content": line[1:]})
                        elif line.startswith('@@'):
                            self.logger.info(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
                        else:
                            self.logger.info(line)
                    
                    comparison_results["sections"][section] = {
                        "changes": section_changes,
                        "similarity": similarity,
                        "original_line_count": len(orig_lines),
                        "optimized_line_count": len(opt_lines)
                    }
                    
                else:
                    self.logger.info(f"{Fore.BLUE}No changes in this section{Style.RESET_ALL}")
                    comparison_results["unchanged_sections"].append(section)
        
        # Save the full comparison results
        with open(os.path.join(comparison_dir, "comparison_results.json"), "w") as f:
            # Convert any non-serializable values to strings
            json_compatible = json.dumps(comparison_results, default=str)
            f.write(json_compatible)
        
        self.logger.info(f"\n{Fore.YELLOW}{'='*80}{Style.RESET_ALL}\n")
        
        return comparison_results
    
    def extract_latex_stats(self, content: str) -> Dict[str, Any]:
        """Extract various statistics from LaTeX content.
        
        Args:
            content: LaTeX content to analyze
            
        Returns:
            Dictionary with LaTeX statistics
        """
        stats = {
            "total_characters": len(content),
            "sections": {},
            "section_count": 0,
            "command_usage": {},
            "total_lines": len(content.splitlines())
        }
        
        # Count sections
        section_pattern = r"\\section{([^}]+)}"
        section_matches = re.findall(section_pattern, content)
        stats["section_count"] = len(section_matches)
        
        # Count specific LaTeX commands
        commands = [
            "resumeSubheading", "resumeItem", "resumeSubHeadingListStart", 
            "resumeSubHeadingListEnd", "resumeItemListStart", "resumeItemListEnd"
        ]
        
        for command in commands:
            pattern = fr"\\{command}"
            matches = re.findall(pattern, content)
            stats["command_usage"][command] = len(matches)
        
        # Extract sections and analyze each
        sections = self.extract_sections(content)
        
        for section_name, section_content in sections.items():
            section_stats = {
                "characters": len(section_content),
                "lines": len(section_content.splitlines()),
                "items": len(re.findall(r"\\resumeItem", section_content))
            }
            stats["sections"][section_name] = section_stats
        
        return stats
    
    def validate_latex(self, content: str) -> Tuple[bool, List[str]]:
        """Validate LaTeX content for common errors.
        
        Args:
            content: LaTeX content to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"Unmatched braces: {open_braces} opening vs {close_braces} closing")
        
        # Check for common LaTeX errors
        error_patterns = [
            (r"\\[a-zA-Z]+\s+{", "Space between command and opening brace"),
            (r"\\begin{[^}]*}[^\\]*\\end{[^}]*}", "Empty environment"),
            (r"\$[^\$]*[\\]$", "Dollar sign inside mathematics"),
            (r"\\\\\\\\", "Too many consecutive line breaks")
        ]
        
        for pattern, message in error_patterns:
            if re.search(pattern, content):
                issues.append(message)
        
        # Check for missing \end{document}
        if not re.search(r"\\end{document}", content):
            issues.append("Missing \\end{document}")
        
        # Check for missing \begin{document}
        if not re.search(r"\\begin{document}", content):
            issues.append("Missing \\begin{document}")
        
        # Check for unclosed environments
        begin_envs = re.findall(r"\\begin{([^}]*)}", content)
        end_envs = re.findall(r"\\end{([^}]*)}", content)
        
        for env in begin_envs:
            if begin_envs.count(env) != end_envs.count(env):
                issues.append(f"Unmatched environment: {env}")
        
        return len(issues) == 0, issues