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
    
    if analysis.get("hard_skills"):
        output.append("HARD SKILLS (ranked by importance):")
        for item in sorted(analysis["hard_skills"], key=lambda x: x.get("score", 0), reverse=True):
            output.append(f"- {item['skill']} ({item.get('score', 'N/A')}/10)")
    
    if analysis.get("soft_skills"):
        output.append("\nSOFT SKILLS (ranked by importance):")
        for item in sorted(analysis["soft_skills"], key=lambda x: x.get("score", 0), reverse=True):
            output.append(f"- {item['skill']} ({item.get('score', 'N/A')}/10)")
    
    if analysis.get("keywords"):
        output.append("\nKEYWORDS (ranked by importance):")
        for item in sorted(analysis["keywords"], key=lambda x: x.get("score", 0), reverse=True):
            output.append(f"- {item['keyword']} ({item.get('score', 'N/A')}/10)")
    
    if analysis.get("critical"):
        output.append("\nCRITICAL REQUIREMENTS:")
        for i, item in enumerate(analysis["critical"], 1):
            output.append(f"{i}. {item}")
    
    if analysis.get("required"):
        output.append("\nREQUIRED SKILLS:")
        for item in analysis["required"]:
            output.append(f"- {item}")
    
    if analysis.get("preferred"):
        output.append("\nPREFERRED SKILLS:")
        for item in analysis["preferred"]:
            output.append(f"- {item}")
    
    return "\n".join(output)


def extract_score_from_text(text, default=75):
    """Extract a numerical score from text.
    
    Args:
        text: Text containing a score
        default: Default score to return if none is found
        
    Returns:
        Extracted score as an integer
    """
    score_match = re.search(r'(?:Score:|ATS Score:)\s*(\d+)/100', text, flags=re.IGNORECASE)
    return int(score_match.group(1)) if score_match else default


def extract_feedback_from_text(text):
    """Extract feedback section from text.
    
    Args:
        text: Text containing feedback
        
    Returns:
        Extracted feedback as a string
    """
    feedback_match = re.search(
        r'(?:Feedback:|ATS Feedback:|Here are some recommendations:|Improvement suggestions:)'
        r'(.*?)(?:$|Conclusion|Overall)', 
        text, 
        flags=re.DOTALL|re.IGNORECASE
    )
    return feedback_match.group(1).strip() if feedback_match else "No specific feedback provided."