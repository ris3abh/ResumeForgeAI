#!/usr/bin/env python3
# =========== Copyright 2025 @ ResumeAI. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2025 @ ResumeAI. All Rights Reserved. ===========

import argparse
import logging
import os
import sys

from camel.typing import ModelType

root = os.path.dirname(__file__)
sys.path.append(root)

from resumeai.resume_chain import ResumeChain

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version
    print(
        "Warning: Your OpenAI version is outdated. \n "
        "Please update as specified in requirement.txt. \n "
        "The old API interface is deprecated and will no longer be supported.")


def get_config(company):
    """
    Return configuration JSON files for ResumeChain
    User can customize only parts of configuration JSON files, others will use defaults
    
    Args:
        company: customized configuration name under CompanyConfig/

    Returns:
        path to three configuration jsons: [config_path, config_phase_path, config_role_path]
    """
    config_dir = os.path.join(root, "CompanyConfig", company)
    default_config_dir = os.path.join(root, "CompanyConfig", "Default")

    config_files = [
        "ChatChainConfig.json",
        "PhaseConfig.json",
        "RoleConfig.json"
    ]

    config_paths = []

    for config_file in config_files:
        company_config_path = os.path.join(config_dir, config_file)
        default_config_path = os.path.join(default_config_dir, config_file)

        if os.path.exists(company_config_path):
            config_paths.append(company_config_path)
        else:
            config_paths.append(default_config_path)

    return tuple(config_paths)


parser = argparse.ArgumentParser(description='ResumeAI - AI-powered resume tailoring')
parser.add_argument('--resume', type=str, required=True,
                    help="Path to the LaTeX resume file")
parser.add_argument('--job-description', type=str, required=True,
                    help="Path to the job description file")
parser.add_argument('--config', type=str, default="Default",
                    help="Name of config, which is used to load configuration under CompanyConfig/")
parser.add_argument('--org', type=str, default="ResumeAI",
                    help="Name of organization, your tailored resume will be generated in Outputs/name_org_timestamp")
parser.add_argument('--name', type=str, default="TailoredResume",
                    help="Name of output, your tailored resume will be generated in Outputs/name_org_timestamp")
parser.add_argument('--model', type=str, default="GPT_4O",
                    help="GPT Model, choose from {'GPT_3_5_TURBO', 'GPT_4', 'GPT_4_TURBO', 'GPT_4O', 'GPT_4O_MINI'}")
parser.add_argument('--output-dir', type=str, default="Outputs",
                    help="Directory to save the output files")
args = parser.parse_args()

# Read the resume and job description
try:
    with open(args.resume, 'r', encoding='utf-8') as f:
        resume_content = f.read()
    with open(args.job_description, 'r', encoding='utf-8') as f:
        job_description = f.read()
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please provide valid paths to the resume and job description files.")
    sys.exit(1)

# Start ResumeAI

# ----------------------------------------
#          Init ResumeChain
# ----------------------------------------
config_path, config_phase_path, config_role_path = get_config(args.config)
args2type = {'GPT_3_5_TURBO': ModelType.GPT_3_5_TURBO,
             'GPT_4': ModelType.GPT_4,
             'GPT_4_TURBO': ModelType.GPT_4_TURBO,
             'GPT_4O': ModelType.GPT_4O,
             'GPT_4O_MINI': ModelType.GPT_4O_MINI,
             }
if openai_new_api:
    args2type['GPT_3_5_TURBO'] = ModelType.GPT_3_5_TURBO_NEW

resume_chain = ResumeChain(
    config_path=config_path,
    config_phase_path=config_phase_path,
    config_role_path=config_role_path,
    resume_content=resume_content,
    job_description=job_description,
    project_name=args.name,
    org_name=args.org,
    model_type=args2type[args.model],
    output_dir=args.output_dir
)

# ----------------------------------------
#          Init Log
# ----------------------------------------
logging.basicConfig(filename=resume_chain.log_filepath, level=logging.INFO,
                    format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S', encoding="utf-8")

# ----------------------------------------
#          Pre Processing
# ----------------------------------------
resume_chain.pre_processing()

# ----------------------------------------
#          Personnel Recruitment
# ----------------------------------------
resume_chain.make_recruitment()

# ----------------------------------------
#          Resume Chain
# ----------------------------------------
resume_chain.execute_chain()

# ----------------------------------------
#          Post Processing
# ----------------------------------------
resume_chain.post_processing()

print(f"\nResume tailoring complete! Check {resume_chain.output_dir} for your tailored resume.")