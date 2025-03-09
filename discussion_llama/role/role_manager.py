import os
import yaml
from typing import Dict, List, Optional, Any


class Role:
    """
    Represents a role in a discussion with specific attributes and behaviors.
    """
    def __init__(self, role_data: Dict[str, Any]):
        self.role = role_data.get('role', '')
        self.description = role_data.get('description', '')
        self.responsibilities = role_data.get('responsibilities', [])
        self.expertise = role_data.get('expertise', [])
        self.characteristics = role_data.get('characteristics', [])
        self.interaction_with = role_data.get('interaction_with', {})
        self.success_criteria = role_data.get('success_criteria', [])
        
        # Optional attributes
        self.tools_and_technologies = role_data.get('tools_and_technologies', [])
        self.decision_authority = role_data.get('decision_authority', [])
        self.scalability = role_data.get('scalability', {})
        self.agile_mapping = role_data.get('agile_mapping', {})
        self.knowledge_sharing = role_data.get('knowledge_sharing', [])
        self.career_path = role_data.get('career_path', {})
        self.remote_work_considerations = role_data.get('remote_work_considerations', [])
        self.key_performance_indicators = role_data.get('key_performance_indicators', [])
        
        # Additional data for runtime
        self._raw_data = role_data
    
    def __str__(self) -> str:
        return f"Role: {self.role}"
    
    def __repr__(self) -> str:
        return f"Role('{self.role}')"
    
    def get_prompt_description(self) -> str:
        """
        Returns a formatted description of the role suitable for inclusion in a prompt.
        """
        prompt = f"You are a {self.role}.\n\n"
        prompt += f"Role Description: {self.description}\n\n"
        
        if self.responsibilities:
            prompt += "Key Responsibilities:\n"
            for resp in self.responsibilities:
                prompt += f"- {resp}\n"
            prompt += "\n"
        
        if self.expertise:
            prompt += "Areas of Expertise:\n"
            for exp in self.expertise:
                prompt += f"- {exp}\n"
            prompt += "\n"
        
        if self.characteristics:
            prompt += "Key Characteristics:\n"
            for char in self.characteristics:
                prompt += f"- {char}\n"
            prompt += "\n"
        
        return prompt
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the role object back to a dictionary.
        """
        return self._raw_data


class RoleManager:
    """
    Manages the loading and selection of roles for discussions.
    """
    def __init__(self, roles_dir: str):
        self.roles_dir = roles_dir
        self.roles: Dict[str, Role] = {}
        self._load_roles()
    
    def _load_roles(self) -> None:
        """
        Load all role definitions from YAML files in the roles directory.
        """
        if not os.path.exists(self.roles_dir):
            raise FileNotFoundError(f"Roles directory not found: {self.roles_dir}")
        
        for filename in os.listdir(self.roles_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                file_path = os.path.join(self.roles_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        role_data = yaml.safe_load(file)
                        if role_data and 'role' in role_data:
                            role = Role(role_data)
                            self.roles[role.role] = role
                except Exception as e:
                    print(f"Error loading role from {filename}: {e}")
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """
        Get a role by name.
        """
        return self.roles.get(role_name)
    
    def get_all_roles(self) -> List[Role]:
        """
        Get all available roles.
        """
        return list(self.roles.values())
    
    def select_roles_for_discussion(self, topic: str, num_roles: int = 3) -> List[Role]:
        """
        Select appropriate roles for a discussion based on the topic.
        This is a placeholder implementation that should be enhanced with
        more sophisticated selection logic.
        """
        # For now, just return the first N roles
        # In a real implementation, this would analyze the topic and select relevant roles
        all_roles = self.get_all_roles()
        return all_roles[:min(num_roles, len(all_roles))]


def load_roles_from_yaml(roles_yaml_dir: str) -> List[Role]:
    """
    Utility function to load roles from YAML files.
    """
    manager = RoleManager(roles_yaml_dir)
    return manager.get_all_roles() 