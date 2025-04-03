"""Text processing utilities for resume optimization."""

import re


def format_analysis_for_prompt(analysis):
    """Format job description analysis for inclusion in a prompt.
    
    Args:
        analysis: Dictionary containing analysis results
        
    Returns:
        Formatted string representation of the analysis
    """
    output = []
    
    # Add Core Role Information
    if analysis.get("core_role"):
        output.append("JOB CORE INFORMATION:")
        for key, value in analysis["core_role"].items():
            if key == "job_title":
                output.append(f"- Job Title: {value}")
            elif key == "seniority":
                output.append(f"- Seniority: {value}")
            elif key == "department":
                output.append(f"- Department: {value}")
            elif key == "responsibilities":
                output.append(f"- Primary Responsibilities: {value}")
    
    # Add Technical Skills
    if analysis.get("technical_skills"):
        output.append("\nTECHNICAL SKILLS (ranked by importance):")
        for item in sorted(analysis["technical_skills"], key=lambda x: x.get("score", 0), reverse=True):
            required_status = ""
            if item["skill"] in analysis.get("required", []):
                required_status = " [REQUIRED]"
            elif item["skill"] in analysis.get("preferred", []):
                required_status = " [PREFERRED]"
            output.append(f"- {item['skill']} ({item.get('score', 'N/A')}/10){required_status}")
    
    # Add Soft Skills
    if analysis.get("soft_skills"):
        output.append("\nSOFT SKILLS (ranked by importance):")
        for item in sorted(analysis["soft_skills"], key=lambda x: x.get("score", 0), reverse=True):
            output.append(f"- {item['skill']} ({item.get('score', 'N/A')}/10)")
    
    # Add Domain Knowledge
    if analysis.get("domain_knowledge"):
        output.append("\nDOMAIN KNOWLEDGE:")
        for item in analysis["domain_knowledge"]:
            output.append(f"- {item}")
    
    # Add Experience Requirements
    if analysis.get("experience"):
        output.append("\nEXPERIENCE REQUIREMENTS:")
        if "years" in analysis["experience"]:
            output.append(f"- Years Required: {analysis['experience']['years']}")
        if "types" in analysis["experience"]:
            output.append(f"- Types of Experience:")
            for exp_type in analysis["experience"]["types"]:
                output.append(f"  * {exp_type}")
        if "accomplishments" in analysis["experience"]:
            output.append(f"- Valued Accomplishments:")
            for accomp in analysis["experience"]["accomplishments"]:
                output.append(f"  * {accomp}")
    
    # Add Keywords
    if analysis.get("keywords"):
        output.append("\nKEYWORDS (ranked by importance):")
        for item in sorted(analysis["keywords"], key=lambda x: x.get("score", 0), reverse=True):
            output.append(f"- {item['keyword']} ({item.get('score', 'N/A')}/10)")
    
    # Add Critical Requirements
    if analysis.get("critical"):
        output.append("\nCRITICAL REQUIREMENTS (must-haves):")
        for i, item in enumerate(analysis["critical"], 1):
            output.append(f"{i}. {item}")
    
    # Add Required Skills (if not already in Technical Skills)
    if analysis.get("required") and not analysis.get("technical_skills"):
        output.append("\nREQUIRED SKILLS:")
        for item in analysis["required"]:
            output.append(f"- {item}")
    
    # Add Preferred Skills (if not already in Technical Skills)
    if analysis.get("preferred") and not analysis.get("technical_skills"):
        output.append("\nPREFERRED SKILLS:")
        for item in analysis["preferred"]:
            output.append(f"- {item}")
    
    # Add Optimization Strategy
    if analysis.get("optimization_strategy"):
        output.append("\nRESUME OPTIMIZATION STRATEGY:")
        if "sections" in analysis["optimization_strategy"]:
            output.append(f"- Key Sections to Emphasize:")
            for section in analysis["optimization_strategy"]["sections"]:
                output.append(f"  * {section}")
        if "achievements" in analysis["optimization_strategy"]:
            output.append(f"- Achievements to Highlight:")
            for achievement in analysis["optimization_strategy"]["achievements"]:
                output.append(f"  * {achievement}")
        if "terminology" in analysis["optimization_strategy"]:
            output.append(f"- Terminology to Align With:")
            for term in analysis["optimization_strategy"]["terminology"]:
                output.append(f"  * {term}")
        if "de-emphasize" in analysis["optimization_strategy"]:
            output.append(f"- Areas to De-emphasize:")
            for area in analysis["optimization_strategy"]["de-emphasize"]:
                output.append(f"  * {area}")
    
    return "\n".join(output)


def extract_score_from_text(text, default=75):
    """Extract a numerical score from text.
    
    Args:
        text: Text containing a score
        default: Default score to return if none is found
        
    Returns:
        Extracted score as an integer
    """
    # Look for score formatted as X/100
    score_match = re.search(r'(?:Score:|ATS Score:|Rating:|Overall score:)\s*(\d+)[\/]?100', text, flags=re.IGNORECASE)
    if score_match:
        return int(score_match.group(1))
    
    # Look for score on a scale of 1-10
    score_match_10 = re.search(r'(?:Score:|ATS Score:|Rating:|Overall score:)\s*(\d+)[\/]?10', text, flags=re.IGNORECASE)
    if score_match_10:
        # Convert to scale of 100
        return int(score_match_10.group(1)) * 10
    
    # Look for any number from 0-100 preceded by "score" or similar
    general_score = re.search(r'(?:Score:|ATS Score:|Rating:|Overall score:|I would rate this|assessment:)\s*(\d+)', text, flags=re.IGNORECASE)
    if general_score:
        score = int(general_score.group(1))
        # If score seems to be on a 10-point scale, convert it
        if score <= 10:
            return score * 10
        return score
    
    return default


def extract_feedback_from_text(text):
    """Extract feedback section from text.
    
    Args:
        text: Text containing feedback
        
    Returns:
        Extracted feedback as a string
    """
    # Try to extract specific feedback sections first
    feedback_patterns = [
        r'(?:Feedback:|ATS Feedback:|Here are some recommendations:|Improvement suggestions:|Areas for improvement:)(.*?)(?:$|Conclusion|Overall|In summary)',
        r'(?:Missing keywords:|Keywords to add:)(.*?)(?:$|Conclusion|Overall|Sections|Formatting)',
        r'(?:Sections that could be|Section improvements:)(.*?)(?:$|Conclusion|Overall|Formatting|Missing)',
        r'(?:Formatting suggestions:|Format recommendations:)(.*?)(?:$|Conclusion|Overall|Assessment)'
    ]
    
    extracted_feedback = []
    for pattern in feedback_patterns:
        match = re.search(pattern, text, flags=re.DOTALL|re.IGNORECASE)
        if match:
            section = match.group(1).strip()
            extracted_feedback.append(section)
    
    # If we found specific sections, join them
    if extracted_feedback:
        return "\n\n".join(extracted_feedback)
    
    # Otherwise, try to find a generic feedback section
    general_match = re.search(
        r'(?:Feedback:|Recommendations:|Suggestions:|Improvements:|Advice:)'
        r'(.*?)(?:$|Conclusion|Overall score|Summary)', 
        text, 
        flags=re.DOTALL|re.IGNORECASE
    )
    
    if general_match:
        return general_match.group(1).strip()
    
    # Extract the whole text after "summary" or "overview" if nothing else matches
    summary_match = re.search(
        r'(?:Summary|Overview|Assessment|Evaluation):(.*?)$',
        text,
        flags=re.DOTALL|re.IGNORECASE
    )
    
    if summary_match:
        return summary_match.group(1).strip()
    
    # If all else fails, use everything after the first 100 characters
    # (assuming the beginning contains greeting/context)
    if len(text) > 100:
        return text[100:].strip()
    
    return text.strip() or "No specific feedback provided."


def extract_keywords_from_jd(text):
    """Extract potential keywords from job description text.
    
    Args:
        text: Job description text
        
    Returns:
        List of potential keywords
    """
    # Common tech terms and skills patterns
    tech_pattern = r'\b(?:Python|Java|AWS|Azure|GCP|SQL|Docker|Kubernetes|CI/CD|DevOps|Machine Learning|AI|ML|Data Science|MLOps|Cloud|API|REST|Jenkins|GitLab|Git|GitHub|Spark|Hadoop|TensorFlow|PyTorch|Scikit-learn|NLP|Deep Learning|Agile|Scrum|Kanban|Linux|UNIX|Windows|MacOS|React|Angular|Vue|Node\.js|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|HTML|CSS|R|Scala|Kotlin|Redis|MongoDB|Cassandra|DynamoDB|PostgreSQL|MySQL|Oracle|NoSQL|ETL|ELT|Data Warehouse|Data Lake|Big Data|Analytics|Visualization|Tableau|Power BI|Excel|VBA|Terraform|CloudFormation|Ansible|Chef|Puppet|Grafana|Prometheus|ELK|Elasticsearch|Kibana|Logstash|Splunk|Security|Compliance|GDPR|HIPAA|PCI|SOC|ISO|NIST|Performance Tuning|Optimization|Microservices|Serverless|Lambda|Container|Orchestration|Networking|VPC|Subnet|Routing|Load Balancer|Firewall|VPN|DNS|DHCP|TCP/IP|HTTP|HTTPS|SSL|TLS|Authentication|Authorization|OAuth|SAML|JWT|IAM|Active Directory|LDAP|Single Sign-On|SSO|Multi-Factor Authentication|MFA|Encryption|PKI|Testing|Unit Testing|Integration Testing|System Testing|Acceptance Testing|QA|Quality Assurance|CI|Continuous Integration|CD|Continuous Delivery|Continuous Deployment|Version Control|SCM|Software Configuration Management|Backup|Recovery|Disaster Recovery|High Availability|Fault Tolerance|Scalability|Monitoring|Logging|Tracing|Debugging|Troubleshooting|Support|Maintenance|Documentation|Technical Writing|Project Management|Program Management|Product Management|Business Analysis|Budget|Finance|Accounting|Marketing|Sales|HR|Human Resources|Legal|Compliance|Audit|Training|Presentation|Public Speaking|Leadership|Management|Executive|Strategy|Vision|Mission|Goals|Objectives|KPIs|Metrics|SLAs|Customer Service|Client Relations|Stakeholder Management|Vendor Management|Contract Negotiation|Procurement|Supply Chain|Inventory|Manufacturing|Production|Design|UX|UI|User Experience|User Interface|Front-End|Back-End|Full-Stack|Database|Architecture|System Design|Software Engineering|Computer Science|Information Technology|IT|Telecommunications|Hardware|Firmware|Embedded Systems|IoT|Internet of Things|Mobile|iOS|Android|Cross-Platform|Hybrid|Native|Responsive|Adaptive|Accessibility|Internationalization|Localization|SEO|Search Engine Optimization|Analytics|Digital Marketing|Content Marketing|Social Media|Email Marketing|CRM|Customer Relationship Management|ERP|Enterprise Resource Planning|SCM|Supply Chain Management|HCM|Human Capital Management|POS|Point of Sale|E-commerce|Payment Processing|Blockchain|Cryptocurrency|Smart Contracts|Quantum Computing|Augmented Reality|AR|Virtual Reality|VR|Mixed Reality|MR|Extended Reality|XR|Computer Vision|Image Processing|Speech Recognition|Voice Recognition|Natural Language Processing|NLP|Chatbot|Virtual Assistant|Digital Assistant|Robotic Process Automation|RPA|Workflow Automation|Business Intelligence|BI|Data Mining|Data Analysis|Statistical Analysis|Machine Learning|Artificial Intelligence|AI|Deep Learning|Neural Networks|Reinforcement Learning|Supervised Learning|Unsupervised Learning|Semi-Supervised Learning|Transfer Learning|Feature Engineering|Model Training|Model Deployment|Model Monitoring|MLOps|DevOps|DataOps|AIOps|GitOps|Infrastructure as Code|IaC|Platform as a Service|PaaS|Software as a Service|SaaS|Infrastructure as a Service|IaaS|Function as a Service|FaaS|Backend as a Service|BaaS|Database as a Service|DBaaS|Containers as a Service|CaaS|Authentication as a Service|AaaS|Desktop as a Service|DaaS|Disaster Recovery as a Service|DRaaS|Security as a Service|SECaaS|Testing as a Service|TaaS|Identity as a Service|IDaaS)\b'
    
    # Extract terms
    tech_terms = re.findall(tech_pattern, text, re.IGNORECASE)
    
    # Extract requirements (often in bullet points)
    requirement_pattern = r'(?:requirements|qualifications|what you need|what we\'re looking for|must have|required|qualification)(?:(?:\s*:|s\s*:).*?)(?:•|\*|\-|\d+\.)\s*(.+?)(?=(?:•|\*|\-|\d+\.)|$)'
    requirements_block = re.search(requirement_pattern, text, re.DOTALL|re.IGNORECASE)
    
    requirements = []
    if requirements_block:
        req_text = requirements_block.group(1)
        bullet_pattern = r'(?:•|\*|\-|\d+\.)\s*([^•\*\-\d\.]+)'
        requirements = re.findall(bullet_pattern, req_text, re.DOTALL)
        requirements = [r.strip() for r in requirements if r.strip()]
    
    # Combine and deduplicate
    all_keywords = list(set([t.lower() for t in tech_terms] + requirements))
    
    return all_keywords


def extract_action_verbs(text):
    """Extract action verbs from a text.
    
    Args:
        text: Text to extract action verbs from
        
    Returns:
        List of action verbs
    """
    # Common resume action verbs
    action_verb_pattern = r'\b(?:Achieved|Administered|Advanced|Analyzed|Assembled|Assigned|Attained|Authored|Balanced|Budgeted|Built|Calculated|Chaired|Coached|Collaborated|Communicated|Compiled|Completed|Composed|Computed|Conceptualized|Conducted|Consolidated|Contracted|Controlled|Converted|Coordinated|Created|Cultivated|Debugged|Decreased|Defined|Delegated|Delivered|Demonstrated|Designed|Determined|Developed|Devised|Diagnosed|Directed|Discovered|Documented|Doubled|Edited|Eliminated|Engineered|Enhanced|Established|Estimated|Evaluated|Examined|Exceeded|Executed|Expanded|Expedited|Extracted|Facilitated|Forecasted|Formulated|Founded|Generated|Guided|Identified|Implemented|Improved|Increased|Influenced|Informed|Initiated|Innovated|Inspected|Installed|Instituted|Instructed|Integrated|Interpreted|Interviewed|Introduced|Invented|Investigated|Launched|Led|Leveraged|Maintained|Managed|Marketed|Maximized|Measured|Mediated|Minimized|Modeled|Monitored|Motivated|Navigated|Negotiated|Operated|Optimized|Orchestrated|Organized|Originated|Overhauled|Oversaw|Performed|Pioneered|Planned|Prepared|Presented|Prioritized|Processed|Produced|Programmed|Promoted|Proposed|Provided|Published|Purchased|Recommended|Reconciled|Recorded|Recruited|Reduced|Refined|Reengineered|Reinforced|Renewed|Reorganized|Repaired|Replaced|Researched|Resolved|Restructured|Revamped|Reviewed|Revised|Revitalized|Scheduled|Secured|Selected|Separated|Served|Shaped|Simplified|Sold|Solved|Spearheaded|Standardized|Streamlined|Strengthened|Structured|Studied|Substituted|Summarized|Supervised|Supported|Surpassed|Surveyed|Synthesized|Systematized|Tabulated|Targeted|Taught|Tested|Tracked|Trained|Transformed|Translated|Troubleshot|Unified|Updated|Upgraded|Utilized|Validated|Verified|Visualized|Won|Wrote)\b'
    
    # Extract action verbs
    action_verbs = re.findall(action_verb_pattern, text, re.IGNORECASE)
    
    # Remove duplicates and convert to lowercase for consistency
    unique_verbs = list(set([v.lower() for v in action_verbs]))
    
    return unique_verbs