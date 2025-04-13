# resume_optimizer/tasks/task_utils.py
from typing import Dict, List, Any
from camel.tasks import Task
from resume_optimizer.tasks.task_definitions import get_task_metadata

def parse_task_result(task: Task) -> Dict[str, Any]:
    """Parse the result of a task into a structured format."""
    if not task.result:
        return {}
    
    try:
        # If the result is already a dict, return it
        if isinstance(task.result, dict):
            return task.result
        
        # Otherwise, try to parse it as a string
        if ":" in task.result:
            lines = task.result.split("\n")
            result_dict = {}
            current_key = None
            current_value = []
            
            for line in lines:
                if ":" in line and not line.startswith(" "):
                    # Save previous key-value pair
                    if current_key:
                        result_dict[current_key] = "\n".join(current_value).strip()
                        current_value = []
                    
                    # Start new key-value pair
                    parts = line.split(":", 1)
                    current_key = parts[0].strip()
                    if len(parts) > 1:
                        current_value.append(parts[1].strip())
                else:
                    # Continue with current value
                    if current_key:
                        current_value.append(line)
            
            # Save last key-value pair
            if current_key:
                result_dict[current_key] = "\n".join(current_value).strip()
            
            return result_dict
        else:
            # Simple result
            return {"result": task.result}
    except Exception as e:
        print(f"Error parsing task result: {e}")
        return {"raw_result": task.result}

def format_task_for_agent(task: Task) -> str:
    """Format a task for consumption by an agent."""
    metadata = get_task_metadata(task.id)
    
    task_desc = f"Task ID: {task.id}\nTask: {task.content}\n\n"
    
    # Add metadata if available
    if metadata.get("resume_path"):
        task_desc += f"Resume Path: {metadata['resume_path']}\n"
    if metadata.get("section_name"):
        task_desc += f"Section: {metadata['section_name']}\n"
    if metadata.get("job_description"):
        task_desc += f"Job Description:\n{metadata['job_description']}\n\n"
    if metadata.get("section_content"):
        task_desc += f"Section Content:\n{metadata['section_content']}\n\n"
    if metadata.get("analysis_results"):
        task_desc += "Analysis Results:\n"
        for key, value in metadata["analysis_results"].items():
            task_desc += f"- {key}: {value}\n"
    
    return task_desc