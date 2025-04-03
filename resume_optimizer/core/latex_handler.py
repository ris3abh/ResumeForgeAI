"""Latex handler for managing LaTeX documents and agent interactions."""

import re
import logging
from typing import Dict, List, Tuple, Optional
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
    
    def __init__(self, debug_mode: bool = True):
        """Initialize the LaTeX handler.
        
        Args:
            debug_mode: Whether to print debug information
        """
        self.debug_mode = debug_mode
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging for the LaTeX handler."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("resume_optimization.log")
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
        
        return sections
    
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
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(),
            optimized.splitlines(),
            lineterm='',
        )
        
        self.logger.info(f"\n{Fore.CYAN}Differences:{Style.RESET_ALL}")
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
    
    def compare_resumes(self, original_path: str, optimized_path: str) -> None:
        """Compare the original and optimized resumes.
        
        Args:
            original_path: Path to the original resume
            optimized_path: Path to the optimized resume
        """
        original = read_latex_file(original_path)
        optimized = read_latex_file(optimized_path)
        
        original_sections = self.extract_sections(original)
        optimized_sections = self.extract_sections(optimized)
        
        self.logger.info(f"\n{Fore.YELLOW}{'='*30} RESUME COMPARISON {'='*30}{Style.RESET_ALL}")
        
        # Find sections in both resumes
        for section in set(original_sections.keys()) | set(optimized_sections.keys()):
            self.logger.info(f"\n{Fore.MAGENTA}Section: {section}{Style.RESET_ALL}")
            
            if section not in original_sections:
                self.logger.info(f"{Fore.GREEN}New section added{Style.RESET_ALL}")
                self.logger.info(f"{Fore.GREEN}{optimized_sections[section]}{Style.RESET_ALL}")
            elif section not in optimized_sections:
                self.logger.info(f"{Fore.RED}Section removed{Style.RESET_ALL}")
                self.logger.info(f"{Fore.RED}{original_sections[section]}{Style.RESET_ALL}")
            else:
                # Compare section content
                import difflib
                diff = difflib.unified_diff(
                    original_sections[section].splitlines(),
                    optimized_sections[section].splitlines(),
                    lineterm='',
                )
                
                self.logger.info(f"{Fore.CYAN}Differences:{Style.RESET_ALL}")
                has_diff = False
                for line in diff:
                    has_diff = True
                    if line.startswith('+'):
                        self.logger.info(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
                    elif line.startswith('-'):
                        self.logger.info(f"{Fore.RED}{line}{Style.RESET_ALL}")
                    elif line.startswith('@@'):
                        self.logger.info(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
                    else:
                        self.logger.info(line)
                
                if not has_diff:
                    self.logger.info(f"{Fore.BLUE}No changes in this section{Style.RESET_ALL}")
        
        self.logger.info(f"\n{Fore.YELLOW}{'='*80}{Style.RESET_ALL}\n")