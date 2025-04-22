"""
Agent communication framework for the resume customization system.
Utilizes CAMEL's Workforce for task-based agent collaboration.
"""

from typing import Dict, Any, List, Optional
from camel.societies.workforce import Workforce
from camel.tasks import Task
from camel.agents import ChatAgent

class ResumeForgeWorkforce:
    """Manages communication and collaboration between specialized agents."""
    
    def __init__(self, description="Resume Customization System"):
        """Initialize the workforce with a description."""
        self.workforce = Workforce(description)
        self.results_cache = {}
    
    def add_worker(self, description: str, worker: ChatAgent) -> 'ResumeForgeWorkforce':
        """Add a worker agent to the workforce."""
        self.workforce.add_single_agent_worker(description, worker=worker)
        return self
    
    def create_task(self, content: str, task_id: str) -> Task:
        """Create a task for the workforce."""
        return Task(content=content, id=task_id)
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """Process a task using the workforce and return results."""
        result_task = self.workforce.process_task(task)
        
        # Store the result in the cache
        self.results_cache[task.id] = result_task.result
        
        return result_task.result
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get a task result from the cache."""
        return self.results_cache.get(task_id)
    
    def create_subtasks(self, main_task_id: str, subtasks_content: List[str]) -> List[Task]:
        """Create subtasks for a main task."""
        tasks = []
        for i, content in enumerate(subtasks_content):
            subtask_id = f"{main_task_id}.{i}"
            task = Task(content=content, id=subtask_id)
            tasks.append(task)
        return tasks
    
    def process_sequential_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Process a list of tasks sequentially, where each task depends on the previous."""
        results = {}
        for task in tasks:
            result = self.process_task(task)
            results[task.id] = result
        return results
    
    def process_parallel_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Process a list of tasks in parallel."""
        # Note: In current implementation, this actually runs sequentially
        # In a production environment, you would implement true parallelism
        return self.process_sequential_tasks(tasks)