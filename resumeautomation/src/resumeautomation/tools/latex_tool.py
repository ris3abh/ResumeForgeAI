from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from jinja2 import Template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LaTeXToolInput(BaseModel):
    """Input schema for LaTeX Tool."""
    operation: str = Field(..., description="Operation: 'generate', 'compile', 'modify', 'optimize'")
    template_name: str = Field(default="professional", description="LaTeX template to use")
    resume_data: str = Field(..., description="JSON string containing resume data")
    output_filename: str = Field(default="resume", description="Output filename without extension")
    optimization_target: Optional[str] = Field(default=None, description="Optimization target: 'reduce_length', 'improve_formatting'")

class LaTeXTool(BaseTool):
    name: str = "LaTeX Resume Tool"
    description: str = (
        "Generate, compile, and optimize LaTeX resumes. Can create resumes from templates, "
        "compile to PDF, and optimize content to fit exactly one page."
    )
    args_schema: Type[BaseModel] = LaTeXToolInput

    def __init__(self):
        super().__init__()
        self.templates = self._load_templates()

    def _run(self, operation: str, template_name: str = "professional", resume_data: str = "", 
             output_filename: str = "resume", optimization_target: str = None) -> str:
        """Execute LaTeX operations."""
        try:
            if operation == "generate":
                return self._generate_latex(template_name, resume_data, output_filename)
            elif operation == "compile":
                return self._compile_latex(output_filename)
            elif operation == "modify":
                return self._modify_latex(output_filename, resume_data)
            elif operation == "optimize":
                return self._optimize_latex(output_filename, optimization_target)
            else:
                return json.dumps({"status": "error", "message": f"Unsupported operation: {operation}"})
                
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _load_templates(self) -> Dict[str, str]:
        """Load LaTeX templates."""
        templates = {
            "professional": """
            \\documentclass[letterpaper,11pt]{article}
            \\usepackage[empty]{fullpage}
            \\usepackage{titlesec}
            \\usepackage{marvosym}
            \\usepackage[usenames,dvipsnames]{color}
            \\usepackage{verbatim}
            \\usepackage{enumitem}
            \\usepackage[hidelinks]{hyperref}
            \\usepackage{fancyhdr}
            \\usepackage[english]{babel}
            \\usepackage{tabularx}
            \\usepackage{geometry}

            % Page layout
            \\geometry{left=0.5in,right=0.5in,top=0.5in,bottom=0.5in}
            \\pagestyle{fancy}
            \\fancyhf{}
            \\fancyfoot{}
            \\renewcommand{\\headrulewidth}{0pt}
            \\renewcommand{\\footrulewidth}{0pt}

            % Section formatting
            \\titleformat{\\section}{
            \\vspace{-4pt}\\scshape\\raggedright\\large
            }{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]

            % Custom commands
            \\newcommand{\\resumeItem}[1]{
            \\item\\small{
                {#1 \\vspace{-2pt}}
            }
            }

            \\newcommand{\\resumeSubheading}[4]{
            \\vspace{-2pt}\\item
                \\begin{tabular*}{0.97\\textwidth}[t]{l@{\\extracolsep{\\fill}}r}
                \\textbf{#1} & #2 \\\\
                \\textit{\\small#3} & \\textit{\\small #4} \\\\
                \\end{tabular*}\\vspace{-7pt}
            }

            \\renewcommand\\labelitemii{$\\vcenter{\\hbox{\\tiny$\\bullet$}}$}

            \\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0.15in, label={}]}
            \\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}
            \\newcommand{\\resumeItemListStart}{\\begin{itemize}}
            \\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{-5pt}}

            \\begin{document}

            % Header
            \\begin{center}
                \\textbf{\\Huge \\scshape {{ name }}} \\\\ \\vspace{1pt}
                \\small {{ phone }} $|$ \\href{mailto:{{ email }}}{\\underline{{ email }}} $|$ 
                {% if linkedin %}\\href{{ linkedin }}{\\underline{{ linkedin_text }}} $|${% endif %}
                {% if github %}\\href{{ github }}{\\underline{{ github_text }}}{% endif %}
            \\end{center}

            {% if summary %}
            %-----------SUMMARY-----------
            \\section{Professional Summary}
            \\small{{{ summary }}}
            {% endif %}

            {% if experience %}
            %-----------EXPERIENCE-----------
            \\section{Experience}
            \\resumeSubHeadingListStart
            {% for exp in experience %}
                \\resumeSubheading
                {{ exp.title }}{{ exp.company }}
                {{ exp.location }}{{ exp.duration }}
                \\resumeItemListStart
            {% for item in exp.items %}
                    \\resumeItem{{{ item }}}
            {% endfor %}
                \\resumeItemListEnd
            {% endfor %}
            \\resumeSubHeadingListEnd
            {% endif %}

            {% if education %}
            %-----------EDUCATION-----------
            \\section{Education}
            \\resumeSubHeadingListStart
            {% for edu in education %}
                \\resumeSubheading
                {{ edu.institution }}{{ edu.location }}
                {{ edu.degree }}{{ edu.graduation }}
            {% endfor %}
            \\resumeSubHeadingListEnd
            {% endif %}

            {% if skills %}
            %-----------TECHNICAL SKILLS-----------
            \\section{Technical Skills}
            \\begin{itemize}[leftmargin=0.15in, label={}]
                \\small{\\item{
            {% for category, skill_list in skills.items() %}
                \\textbf{{ category }}{: {{ skill_list|join(', ') }} \\\\
            {% endfor %}
                }}
            \\end{itemize}
            {% endif %}

            {% if projects %}
            %-----------PROJECTS-----------
            \\section{Projects}
                \\resumeSubHeadingListStart
            {% for project in projects %}
                \\resumeSubheading
                    {{ project.name }}{{ project.tech }}
                    {{ project.description }}{{ project.date }}
                    \\resumeItemListStart
            {% for item in project.items %}
                    \\resumeItem{{{ item }}}
            {% endfor %}
                    \\resumeItemListEnd
            {% endfor %}
                \\resumeSubHeadingListEnd
            {% endif %}

            \\end{document}
            """,
                        "minimal": """
            \\documentclass[11pt,a4paper,sans]{moderncv}
            \\moderncvstyle{classic}
            \\moderncvcolor{blue}
            \\usepackage[scale=0.75]{geometry}

            \\name{{{ name }}}{}
            \\phone[mobile]{{{ phone }}}
            \\email{{{ email }}}
            {% if linkedin %}\\social[linkedin]{{{ linkedin_text }}}{% endif %}

            \\begin{document}
            \\makecvtitle

            {% if summary %}
            \\section{Summary}
            {{ summary }}
            {% endif %}

            {% if experience %}
            \\section{Experience}
            {% for exp in experience %}
            \\cventry{{{ exp.duration }}}{{{ exp.title }}}{{{ exp.company }}}{{{ exp.location }}}{}{
            {% for item in exp.items %}
            \\begin{itemize}
            \\item {{ item }}
            \\end{itemize}
            {% endfor %}
            }
            {% endfor %}
            {% endif %}

            {% if education %}
            \\section{Education}
            {% for edu in education %}
            \\cventry{{{ edu.graduation }}}{{{ edu.degree }}}{{{ edu.institution }}}{{{ edu.location }}}{}{}
            {% endfor %}
            {% endif %}

            \\end{document}
            """
        }
        return templates

    def _generate_latex(self, template_name: str, resume_data: str, output_filename: str) -> str:
        """Generate LaTeX file from template and data."""
        try:
            # Parse resume data
            try:
                data = json.loads(resume_data)
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "message": "Invalid JSON in resume_data"})
            
            # Get template
            if template_name not in self.templates:
                return json.dumps({"status": "error", "message": f"Template '{template_name}' not found"})
            
            template_content = self.templates[template_name]
            
            # Create Jinja2 template
            template = Template(template_content)
            
            # Render template with data
            rendered_latex = template.render(**data)
            
            # Create output directory
            output_dir = "resumeautomation/data/output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save LaTeX file
            latex_path = os.path.join(output_dir, f"{output_filename}.tex")
            with open(latex_path, 'w', encoding='utf-8') as f:
                f.write(rendered_latex)
            
            return json.dumps({
                "status": "success",
                "message": "LaTeX file generated successfully",
                "latex_file": latex_path,
                "template_used": template_name,
                "data_sections": list(data.keys())
            })
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _compile_latex(self, output_filename: str) -> str:
        """Compile LaTeX file to PDF."""
        try:
            output_dir = "resumeautomation/data/output"
            latex_path = os.path.join(output_dir, f"{output_filename}.tex")
            
            if not os.path.exists(latex_path):
                return json.dumps({"status": "error", "message": f"LaTeX file not found: {latex_path}"})
            
            # Check if pdflatex is available
            try:
                subprocess.run(['pdflatex', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return json.dumps({"status": "error", "message": "pdflatex not installed or not in PATH"})
            
            # Compile with pdflatex
            compile_command = [
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory', output_dir,
                latex_path
            ]
            
            result = subprocess.run(compile_command, capture_output=True, text=True, cwd=output_dir)
            
            pdf_path = os.path.join(output_dir, f"{output_filename}.pdf")
            
            if os.path.exists(pdf_path):
                # Clean up auxiliary files
                aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk']
                for ext in aux_extensions:
                    aux_file = os.path.join(output_dir, f"{output_filename}{ext}")
                    if os.path.exists(aux_file):
                        os.remove(aux_file)
                
                return json.dumps({
                    "status": "success",
                    "message": "PDF compiled successfully",
                    "pdf_file": pdf_path,
                    "latex_file": latex_path,
                    "file_size": os.path.getsize(pdf_path)
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": "PDF compilation failed",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _modify_latex(self, output_filename: str, new_data: str) -> str:
        """Modify existing LaTeX file with new data."""
        try:
            # This would regenerate the LaTeX with new data
            return self._generate_latex("professional", new_data, output_filename)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _optimize_latex(self, output_filename: str, optimization_target: str) -> str:
        """Optimize LaTeX content to meet specific targets."""
        try:
            output_dir = "resumeautomation/data/output"
            latex_path = os.path.join(output_dir, f"{output_filename}.tex")
            
            if not os.path.exists(latex_path):
                return json.dumps({"status": "error", "message": f"LaTeX file not found: {latex_path}"})
            
            # Read current LaTeX content
            with open(latex_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            optimizations_applied = []
            
            if optimization_target == "reduce_length":
                # Apply length reduction optimizations
                
                # Reduce font size
                if "11pt" in content:
                    content = content.replace("11pt", "10pt")
                    optimizations_applied.append("Reduced font size to 10pt")
                
                # Reduce margins
                if "0.5in" in content:
                    content = content.replace("0.5in", "0.4in")
                    optimizations_applied.append("Reduced margins to 0.4in")
                
                # Reduce vertical spacing
                content = content.replace("\\vspace{-4pt}", "\\vspace{-6pt}")
                content = content.replace("\\vspace{-5pt}", "\\vspace{-7pt}")
                content = content.replace("\\vspace{-2pt}", "\\vspace{-3pt}")
                optimizations_applied.append("Reduced vertical spacing")
                
                # Make bullet points more compact
                content = content.replace("\\resumeItemListStart", "\\resumeItemListStart\\vspace{-2pt}")
                optimizations_applied.append("Compressed bullet point spacing")
                
            elif optimization_target == "improve_formatting":
                # Apply formatting improvements
                
                # Ensure consistent spacing
                content = content.replace("\\\\", "\\\\ \\vspace{1pt}")
                optimizations_applied.append("Improved line spacing consistency")
                
                # Add better section breaks
                content = content.replace("\\section{", "\\vspace{2pt}\\section{")
                optimizations_applied.append("Enhanced section breaks")
            
            # Save optimized LaTeX
            optimized_path = os.path.join(output_dir, f"{output_filename}_optimized.tex")
            with open(optimized_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return json.dumps({
                "status": "success",
                "message": "LaTeX optimization completed",
                "original_file": latex_path,
                "optimized_file": optimized_path,
                "optimizations_applied": optimizations_applied,
                "target": optimization_target
            })
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def generate_resume_from_template(self, base_template_path: str, job_data: dict, person_data: dict) -> str:
        """Generate customized resume from base template and job requirements."""
        try:
            # Combine job requirements with person data to create targeted resume
            resume_data = {
                "name": person_data.get("name", ""),
                "phone": person_data.get("phone", ""),
                "email": person_data.get("email", ""),
                "linkedin": person_data.get("linkedin", ""),
                "github": person_data.get("github", ""),
                "linkedin_text": person_data.get("linkedin", "").replace("https://linkedin.com/in/", "") if person_data.get("linkedin") else "",
                "github_text": person_data.get("github", "").replace("https://github.com/", "") if person_data.get("github") else "",
                
                # Customize summary based on job
                "summary": self._customize_summary(person_data.get("summary", ""), job_data),
                
                # Prioritize relevant experience
                "experience": self._prioritize_experience(person_data.get("experience", []), job_data),
                
                # Filter and prioritize skills
                "skills": self._filter_skills(person_data.get("skills", {}), job_data),
                
                "education": person_data.get("education", []),
                "projects": self._select_relevant_projects(person_data.get("projects", []), job_data)
            }
            
            resume_data_json = json.dumps(resume_data)
            
            # Generate unique filename based on job
            job_title = job_data.get("job_title", "position").replace(" ", "_").lower()
            company = job_data.get("company", "company").replace(" ", "_").lower()
            filename = f"resume_{company}_{job_title}"
            
            return self._generate_latex("professional", resume_data_json, filename)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _customize_summary(self, base_summary: str, job_data: dict) -> str:
        """Customize summary based on job requirements."""
        # This would use job requirements to tailor the summary
        job_keywords = job_data.get("requirements", "").lower()
        
        # Add job-relevant keywords to summary if not already present
        enhanced_summary = base_summary
        
        # Simple keyword enhancement (in a real implementation, this would be more sophisticated)
        if "python" in job_keywords and "python" not in base_summary.lower():
            enhanced_summary += " Experienced in Python development."
        
        return enhanced_summary

    def _prioritize_experience(self, experiences: list, job_data: dict) -> list:
        """Prioritize and customize experience based on job relevance."""
        # This would reorder and emphasize relevant experience
        return experiences  # Simplified for now

    def _filter_skills(self, skills: dict, job_data: dict) -> dict:
        """Filter and prioritize skills based on job requirements."""
        # This would prioritize job-relevant skills
        return skills  # Simplified for now

    def _select_relevant_projects(self, projects: list, job_data: dict) -> list:
        """Select most relevant projects for the job."""
        # This would select projects that match job requirements
        return projects[:3]  # Simplified - take first 3 projects