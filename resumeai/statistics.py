# resumeai/statistics.py
import os
import numpy as np

def prompt_cost(model_type: str, num_prompt_tokens: float, num_completion_tokens: float):
    """Calculate the cost of API calls based on token usage."""
    input_cost_map = {
        "gpt-3.5-turbo": 0.0005,
        "gpt-3.5-turbo-16k": 0.003,
        "gpt-3.5-turbo-0613": 0.0015,
        "gpt-3.5-turbo-16k-0613": 0.003,
        "gpt-4": 0.03,
        "gpt-4-0613": 0.03,
        "gpt-4-32k": 0.06,
        "gpt-4-turbo": 0.01,
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
    }

    output_cost_map = {
        "gpt-3.5-turbo": 0.0015,
        "gpt-3.5-turbo-16k": 0.004,
        "gpt-3.5-turbo-0613": 0.002,
        "gpt-3.5-turbo-16k-0613": 0.004,
        "gpt-4": 0.06,
        "gpt-4-0613": 0.06,
        "gpt-4-32k": 0.12,
        "gpt-4-turbo": 0.03,
        "gpt-4o": 0.015,
        "gpt-4o-mini": 0.0006,
    }

    if model_type not in input_cost_map or model_type not in output_cost_map:
        return -1

    return num_prompt_tokens * input_cost_map[model_type] / 1000.0 + num_completion_tokens * output_cost_map[model_type] / 1000.0

def get_info(dir, log_filepath):
    """
    Generate statistics about the resume tailoring process.
    
    Args:
        dir: Directory containing resume files
        log_filepath: Path to log file
        
    Returns:
        Formatted string with statistics
    """
    print("dir:", dir)

    model_type = ""
    num_doc_files = -1
    duration = -1
    num_utterance = -1
    num_reflection = -1
    num_prompt_tokens = -1
    num_completion_tokens = -1
    num_total_tokens = -1
    original_resume_size = -1
    tailored_resume_size = -1

    if os.path.exists(dir):
        filenames = os.listdir(dir)
        
        # Count document files
        num_doc_files = len([f for f in filenames if os.path.isfile(os.path.join(dir, f))])
        
        # Check resume files
        if "original_resume.tex" in filenames:
            with open(os.path.join(dir, "original_resume.tex"), "r", encoding="utf8") as f:
                content = f.read()
                original_resume_size = len(content)
                
        if "tailored_resume.tex" in filenames:
            with open(os.path.join(dir, "tailored_resume.tex"), "r", encoding="utf8") as f:
                content = f.read()
                tailored_resume_size = len(content)
        
        # Process log file
        if os.path.exists(log_filepath):
            lines = open(log_filepath, "r", encoding="utf8").read().split("\n")
            
            # Find model type
            sublines = [line for line in lines if "| **model_type** |" in line]
            if len(sublines) > 0:
                model_type = sublines[0].split("| **model_type** | ModelType.")[-1].split(" | ")[0]
                model_type = model_type[:-2]
                if model_type == "GPT_3_5_TURBO" or model_type == "GPT_3_5_TURBO_NEW":
                    model_type = "gpt-3.5-turbo"
                elif model_type == "GPT_4":
                    model_type = "gpt-4"
                elif model_type == "GPT_4_32k":
                    model_type = "gpt-4-32k"
                elif model_type == "GPT_4_TURBO":
                    model_type = "gpt-4-turbo"
                elif model_type == "GPT_4O":
                    model_type = "gpt-4o"
                elif model_type == "GPT_4O_MINI":
                    model_type = "gpt-4o-mini"
            
            # Count conversations
            start_lines = [line for line in lines if "**[Start Chat]**" in line]
            chat_lines = [line for line in lines if "<->" in line]
            num_utterance = len(start_lines) + len(chat_lines)
            
            # Count reflections
            num_reflection = 0
            for line in lines:
                if "on : Reflection" in line:
                    num_reflection += 1
            
            # Count tokens
            sublines = [line for line in lines if line.startswith("prompt_tokens:")]
            if len(sublines) > 0:
                nums = [int(line.split(": ")[-1]) for line in sublines]
                num_prompt_tokens = np.sum(nums)
            
            sublines = [line for line in lines if line.startswith("completion_tokens:")]
            if len(sublines) > 0:
                nums = [int(line.split(": ")[-1]) for line in sublines]
                num_completion_tokens = np.sum(nums)
            
            sublines = [line for line in lines if line.startswith("total_tokens:")]
            if len(sublines) > 0:
                nums = [int(line.split(": ")[-1]) for line in sublines]
                num_total_tokens = np.sum(nums)

    # Calculate cost
    cost = 0.0
    if prompt_cost(model_type, num_prompt_tokens, num_completion_tokens) != -1:
        cost += prompt_cost(model_type, num_prompt_tokens, num_completion_tokens)

    # Format the information for resume tailoring
    info = (
        "\n\n💰**cost**=${:.6f}"
        "\n\n📄**original_resume_size**={}"
        "\n\n📝**tailored_resume_size**={}"
        "\n\n📊**size_change**={}"
        "\n\n📚**num_doc_files**={}"
        "\n\n🗣**num_utterances**={}"
        "\n\n🤔**num_reflections**={}"
        "\n\n❓**num_prompt_tokens**={}"
        "\n\n❗**num_completion_tokens**={}"
        "\n\n🌟**num_total_tokens**={}"
    ).format(
        cost,
        original_resume_size,
        tailored_resume_size,
        tailored_resume_size - original_resume_size,
        num_doc_files,
        num_utterance,
        num_reflection,
        num_prompt_tokens,
        num_completion_tokens,
        num_total_tokens
    )

    return info