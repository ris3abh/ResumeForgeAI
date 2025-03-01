# resumeai/utils.py
import html
import logging
import re
import time
import markdown
import inspect

def now():
    """Return current time in YYYYMMDDHHMMSS format."""
    return time.strftime("%Y%m%d%H%M%S", time.localtime())

def log_visualize(role, content=None):
    """
    Log content to file and console with role information.
    Simplified version that doesn't require visualizer.app.
    
    Args:
        role: the agent that sends message
        content: the content of message
    """
    if not content:
        logging.info(role + "\n")
        print(role + "\n")
    else:
        print(str(role) + ": " + str(content) + "\n")
        logging.info(str(role) + ": " + str(content) + "\n")

def convert_to_markdown_table(records_kv):
    """Convert key-value pairs to a markdown table."""
    # Create the Markdown table header
    header = "| Parameter | Value |\n| --- | --- |"
    
    # Create the Markdown table rows
    rows = [f"| **{key}** | {value} |" for (key, value) in records_kv]
    
    # Combine the header and rows to form the final Markdown table
    markdown_table = header + "\n" + '\n'.join(rows)
    
    return markdown_table

def log_arguments(func):
    """Decorator to log function arguments."""
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        params = sig.parameters
        
        all_args = {}
        all_args.update({name: value for name, value in zip(params.keys(), args)})
        all_args.update(kwargs)
        
        records_kv = []
        for name, value in all_args.items():
            if name in ["self", "resume_env", "task_type"]:
                continue
            value = escape_string(value)
            records_kv.append([name, value])
            
        records = f"**[{func.__name__}]**\n\n" + convert_to_markdown_table(records_kv)
        log_visualize("System", records)
        
        return func(*args, **kwargs)
    
    return wrapper

def escape_string(value):
    """Escape and clean a string for display."""
    value = str(value)
    value = html.unescape(value)
    value = markdown.markdown(value)
    value = re.sub(r'<[^>]*>', '', value)
    value = value.replace("\n", " ")
    return value