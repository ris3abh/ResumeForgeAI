"""Tool for evaluating resume optimization results."""

import os
import re
import difflib
from colorama import Fore, Style
import argparse
import json
from pathlib import Path

from resume_optimizer.utils.latex_utils import read_latex_file, extract_section


class ResumeEvaluator:
    """Tool for evaluating resume optimization results."""
    
    def __init__(self, original_resume_path, optimized_resume_path, job_description_path=None):
        """Initialize the resume evaluator.
        
        Args:
            original_resume_path: Path to the original resume
            optimized_resume_path: Path to the optimized resume
            job_description_path: Optional path to the job description
        """
        self.original_resume_path = original_resume_path
        self.optimized_resume_path = optimized_resume_path
        self.job_description_path = job_description_path
        
        # Create output directory
        os.makedirs("evaluation_output", exist_ok=True)
    
    def load_files(self):
        """Load the necessary files for evaluation."""
        print(f"{Fore.CYAN}Loading resume files...{Style.RESET_ALL}")
        self.original_resume = read_latex_file(self.original_resume_path)
        self.optimized_resume = read_latex_file(self.optimized_resume_path)
        
        if self.job_description_path:
            with open(self.job_description_path, 'r') as f:
                self.job_description = f.read()
            print(f"{Fore.GREEN}Job description loaded ({len(self.job_description)} chars){Style.RESET_ALL}")
        else:
            self.job_description = None
            print(f"{Fore.YELLOW}No job description provided{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Resume files loaded successfully{Style.RESET_ALL}")
    
    def extract_keywords_from_jd(self):
        """Extract keywords from the job description.
        
        Returns:
            List of keywords
        """
        if not self.job_description:
            print(f"{Fore.YELLOW}No job description provided for keyword extraction{Style.RESET_ALL}")
            return []
        
        # Common tech terms and skills patterns
        tech_pattern = r'\b(?:Python|Java|AWS|Azure|GCP|Google Cloud|SQL|Docker|Kubernetes|K8s|CI/CD|DevOps|Machine Learning|AI|ML|MLOps|Cloud|API|REST|Jenkins|GitLab|Git|GitHub|Spark|Hadoop|TensorFlow|PyTorch|Scikit-learn|sklearn|NLP|Deep Learning|RAG|Agile|Scrum|Kanban|Linux|UNIX|Windows|MacOS|Architecture|Solution|Enterprise|Compliance|Privacy|Security|Customer|Client|Business|Stakeholder|Lead|Communicate|Collaboration|Problem-Solving|Project Management|Requirements|Technical|ROI|Workflow|Data|Process|System|Applications|Infrastructure|Value)\b'
        
        tech_terms = re.findall(tech_pattern, self.job_description, re.IGNORECASE)
        
        # Extract key phrases
        phrase_pattern = r'[A-Z][a-z]+ [A-Za-z]+ [A-Za-z]+'
        phrases = re.findall(phrase_pattern, self.job_description)
        
        # Combine and deduplicate
        all_keywords = list(set([t.lower() for t in tech_terms] + [p.lower() for p in phrases]))
        
        # Save keywords to file
        with open("evaluation_output/extracted_keywords.txt", 'w') as f:
            f.write("\n".join(all_keywords))
        
        print(f"{Fore.GREEN}Extracted {len(all_keywords)} keywords from job description{Style.RESET_ALL}")
        return all_keywords
    
    def check_keyword_coverage(self, keywords):
        """Check how many keywords from the job description are in each resume.
        
        Args:
            keywords: List of keywords to check for
            
        Returns:
            Dictionary with coverage statistics
        """
        original_coverage = 0
        optimized_coverage = 0
        
        # Check each keyword
        keyword_results = {}
        for keyword in keywords:
            in_original = keyword.lower() in self.original_resume.lower()
            in_optimized = keyword.lower() in self.optimized_resume.lower()
            
            if in_original:
                original_coverage += 1
            if in_optimized:
                optimized_coverage += 1
            
            keyword_results[keyword] = {
                "in_original": in_original,
                "in_optimized": in_optimized,
                "added": not in_original and in_optimized,
                "removed": in_original and not in_optimized
            }
        
        # Calculate statistics
        total_keywords = len(keywords)
        original_percent = (original_coverage / total_keywords) * 100 if total_keywords > 0 else 0
        optimized_percent = (optimized_coverage / total_keywords) * 100 if total_keywords > 0 else 0
        improvement = optimized_percent - original_percent
        
        # Count added and removed keywords
        added_keywords = [k for k, v in keyword_results.items() if v["added"]]
        removed_keywords = [k for k, v in keyword_results.items() if v["removed"]]
        
        results = {
            "total_keywords": total_keywords,
            "original_coverage": original_coverage,
            "original_percent": original_percent,
            "optimized_coverage": optimized_coverage,
            "optimized_percent": optimized_percent,
            "improvement": improvement,
            "added_keywords": added_keywords,
            "removed_keywords": removed_keywords,
            "keyword_details": keyword_results
        }
        
        # Save results to file
        with open("evaluation_output/keyword_coverage.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{Fore.CYAN}Keyword Coverage Results:{Style.RESET_ALL}")
        print(f"Total keywords: {total_keywords}")
        print(f"Original resume: {original_coverage} keywords ({original_percent:.1f}%)")
        print(f"Optimized resume: {optimized_coverage} keywords ({optimized_percent:.1f}%)")
        print(f"Improvement: {improvement:.1f}%")
        print(f"Added keywords: {len(added_keywords)}")
        print(f"Removed keywords: {len(removed_keywords)}")
        
        if added_keywords:
            print(f"\n{Fore.GREEN}Added Keywords:{Style.RESET_ALL}")
            for keyword in added_keywords[:10]:  # Show first 10
                print(f"- {keyword}")
            if len(added_keywords) > 10:
                print(f"... and {len(added_keywords) - 10} more")
        
        if removed_keywords:
            print(f"\n{Fore.RED}Removed Keywords:{Style.RESET_ALL}")
            for keyword in removed_keywords[:10]:  # Show first 10
                print(f"- {keyword}")
            if len(removed_keywords) > 10:
                print(f"... and {len(removed_keywords) - 10} more")
        
        return results
    
    def compare_sections(self):
        """Compare sections between the original and optimized resumes.
        
        Returns:
            Dictionary with section comparison results
        """
        print(f"\n{Fore.CYAN}Comparing resume sections...{Style.RESET_ALL}")
        
        # Extract sections
        sections = ["PROFESSIONAL SUMMARY", "TECHNICAL SKILLS", "EXPERIENCE", "CERTIFICATIONS", "EDUCATION"]
        section_comparisons = {}
        
        for section_name in sections:
            original_section = extract_section(self.original_resume, section_name)
            optimized_section = extract_section(self.optimized_resume, section_name)
            
            # Skip if section doesn't exist in both
            if not original_section or not optimized_section:
                print(f"{Fore.YELLOW}Section '{section_name}' not found in both resumes{Style.RESET_ALL}")
                section_comparisons[section_name] = {
                    "exists_in_original": bool(original_section),
                    "exists_in_optimized": bool(optimized_section),
                    "changes": []
                }
                continue
            
            # Compare the sections
            diff = list(difflib.unified_diff(
                original_section.splitlines(),
                optimized_section.splitlines(),
                lineterm=''
            ))
            
            # Extract changes
            changes = []
            for i, line in enumerate(diff):
                if line.startswith('+') and not line.startswith('+++'):
                    changes.append({
                        "type": "added",
                        "content": line[1:].strip()
                    })
                elif line.startswith('-') and not line.startswith('---'):
                    changes.append({
                        "type": "removed",
                        "content": line[1:].strip()
                    })
            
            # Calculate change statistics
            lines_changed = len([c for c in changes if c["type"] in ["added", "removed"]])
            original_line_count = len(original_section.splitlines())
            optimized_line_count = len(optimized_section.splitlines())
            change_percent = (lines_changed / original_line_count) * 100 if original_line_count > 0 else 0
            
            section_comparisons[section_name] = {
                "exists_in_original": True,
                "exists_in_optimized": True,
                "original_line_count": original_line_count,
                "optimized_line_count": optimized_line_count,
                "lines_changed": lines_changed,
                "change_percent": change_percent,
                "changes": changes
            }
            
            # Print summary
            print(f"\n{Fore.MAGENTA}Section: {section_name}{Style.RESET_ALL}")
            print(f"Changes: {lines_changed} lines ({change_percent:.1f}% change rate)")
            
            # Show some changes
            added_changes = [c for c in changes if c["type"] == "added"]
            removed_changes = [c for c in changes if c["type"] == "removed"]
            
            if added_changes:
                print(f"\n{Fore.GREEN}Added Content (sample):{Style.RESET_ALL}")
                for change in added_changes[:5]:  # Show first 5
                    print(f"+ {change['content']}")
                if len(added_changes) > 5:
                    print(f"... and {len(added_changes) - 5} more additions")
            
            if removed_changes:
                print(f"\n{Fore.RED}Removed Content (sample):{Style.RESET_ALL}")
                for change in removed_changes[:5]:  # Show first 5
                    print(f"- {change['content']}")
                if len(removed_changes) > 5:
                    print(f"... and {len(removed_changes) - 5} more removals")
        
        # Save results to file
        with open("evaluation_output/section_comparison.json", 'w') as f:
            json.dump(section_comparisons, f, indent=2)
        
        return section_comparisons
    
    def run_evaluation(self):
        """Run the full evaluation pipeline.
        
        Returns:
            Dictionary with all evaluation results
        """
        print(f"{Fore.YELLOW}🚀 Starting Resume Optimization Evaluation{Style.RESET_ALL}")
        
        # Load files
        self.load_files()
        
        # Extract keywords if job description is available
        keywords = []
        keyword_results = {}
        if self.job_description:
            keywords = self.extract_keywords_from_jd()
            keyword_results = self.check_keyword_coverage(keywords)
        
        # Compare sections
        section_results = self.compare_sections()
        
        # Summarize results
        results = {
            "keyword_coverage": keyword_results if self.job_description else None,
            "section_comparison": section_results
        }
        
        # Save overall results
        with open("evaluation_output/evaluation_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{Fore.GREEN}✅ Evaluation completed. Results saved to evaluation_output/ directory.{Style.RESET_ALL}")
        return results


def main():
    """Main function to run the resume evaluator from command line."""
    parser = argparse.ArgumentParser(description="Evaluate resume optimization results")
    parser.add_argument("--original", required=True, help="Path to the original LaTeX resume file")
    parser.add_argument("--optimized", required=True, help="Path to the optimized LaTeX resume file")
    parser.add_argument("--job-description", help="Path to the job description file (optional)")
    
    args = parser.parse_args()
    
    evaluator = ResumeEvaluator(
        original_resume_path=args.original,
        optimized_resume_path=args.optimized,
        job_description_path=args.job_description
    )
    
    evaluator.run_evaluation()


if __name__ == "__main__":
    main()