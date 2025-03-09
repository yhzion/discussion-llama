import os
import yaml
import re
from typing import Dict, List, Optional, Any, Tuple, Set


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
    
    def is_compatible(self, role1: Role, role2: Role) -> bool:
        """
        Check if two roles are compatible with each other.
        Roles are considered compatible if either mentions the other in their interaction_with.
        
        Args:
            role1: The first role to check
            role2: The second role to check
            
        Returns:
            bool: True if the roles are compatible, False otherwise
        """
        return role2.role in role1.interaction_with or role1.role in role2.interaction_with
    
    def find_compatible_roles(self, role: Role, all_roles: Optional[List[Role]] = None) -> List[Role]:
        """
        Find all roles that are compatible with the given role.
        
        Args:
            role: The role to find compatible roles for
            all_roles: Optional list of roles to check against. If None, uses all roles in the manager.
            
        Returns:
            List[Role]: A list of roles compatible with the given role
        """
        if all_roles is None:
            all_roles = self.get_all_roles()
            
        return [r for r in all_roles if r != role and self.is_compatible(role, r)]
    
    def validate_role_compatibility(self, roles: List[Role]) -> Tuple[bool, str]:
        """
        Validate that a set of roles is compatible.
        A set of roles is considered compatible if each role is compatible with at least one other role.
        
        Args:
            roles: The list of roles to validate
            
        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating if the roles are compatible,
                             and a message explaining the result
        """
        for i, role1 in enumerate(roles):
            has_compatible = False
            for j, role2 in enumerate(roles):
                if i != j and self.is_compatible(role1, role2):
                    has_compatible = True
                    break
            if not has_compatible:
                return False, f"{role1.role} is not compatible with any other selected role"
        return True, "All roles are compatible"
    
    def create_compatibility_matrix(self) -> Dict[str, Dict[str, bool]]:
        """
        Create a matrix showing the compatibility between all roles.
        
        Returns:
            Dict[str, Dict[str, bool]]: A nested dictionary where matrix[role1][role2] is True
                                       if role1 and role2 are compatible
        """
        all_roles = self.get_all_roles()
        matrix = {}
        
        for role1 in all_roles:
            matrix[role1.role] = {}
            for role2 in all_roles:
                if role1 != role2:
                    matrix[role1.role][role2.role] = self.is_compatible(role1, role2)
                    
        return matrix
    
    def _calculate_role_relevance(self, role: Role, topic: str) -> float:
        """
        Calculate the relevance of a role to a given topic.
        
        Args:
            role: The role to calculate relevance for
            topic: The discussion topic
            
        Returns:
            float: A relevance score between 0.0 and 1.0
        """
        # Convert topic to lowercase for case-insensitive matching
        topic_lower = topic.lower()
        
        # Extract keywords from the topic
        topic_keywords = set(re.findall(r'\b\w+\b', topic_lower))
        
        # Calculate relevance based on keyword matches in role attributes
        relevance_score = 0.0
        
        # Check role name
        role_name_keywords = set(re.findall(r'\b\w+\b', role.role.lower()))
        role_name_matches = len(topic_keywords.intersection(role_name_keywords))
        relevance_score += role_name_matches * 0.2  # Higher weight for role name matches
        
        # Check role description
        description_keywords = set(re.findall(r'\b\w+\b', role.description.lower()))
        description_matches = len(topic_keywords.intersection(description_keywords))
        relevance_score += description_matches * 0.1
        
        # Check expertise areas (highest weight)
        expertise_keywords = set()
        for expertise in role.expertise:
            expertise_keywords.update(re.findall(r'\b\w+\b', expertise.lower()))
        expertise_matches = len(topic_keywords.intersection(expertise_keywords))
        relevance_score += expertise_matches * 0.4  # Highest weight for expertise matches
        
        # Check responsibilities
        responsibility_keywords = set()
        for resp in role.responsibilities:
            responsibility_keywords.update(re.findall(r'\b\w+\b', resp.lower()))
        responsibility_matches = len(topic_keywords.intersection(responsibility_keywords))
        relevance_score += responsibility_matches * 0.3
        
        # Normalize the score to be between 0 and 1
        # The maximum possible score depends on the number of keywords in the topic
        max_possible_score = len(topic_keywords) * (0.2 + 0.1 + 0.4 + 0.3)
        if max_possible_score > 0:
            normalized_score = min(1.0, relevance_score / max_possible_score)
        else:
            normalized_score = 0.0
        
        return normalized_score
    
    def _analyze_topic_with_llm(self, topic: str) -> Dict[str, Any]:
        """
        Analyze the topic using an LLM to extract key aspects.
        This is a placeholder implementation that would be replaced with actual LLM integration.
        
        Args:
            topic: The discussion topic
            
        Returns:
            Dict[str, Any]: A dictionary containing analysis results
        """
        # This is a placeholder implementation
        # In a real implementation, this would call an LLM to analyze the topic
        
        # Simple keyword-based analysis
        topic_lower = topic.lower()
        
        analysis = {
            "key_aspects": [],
            "technical_complexity": "medium",
            "business_impact": "medium"
        }
        
        # Extract key aspects based on common keywords
        if any(keyword in topic_lower for keyword in ["security", "authentication", "authorization", "privacy"]):
            analysis["key_aspects"].append("security")
        
        if any(keyword in topic_lower for keyword in ["user", "interface", "ui", "ux", "experience", "design"]):
            analysis["key_aspects"].append("user experience")
        
        if any(keyword in topic_lower for keyword in ["api", "database", "backend", "server", "performance"]):
            analysis["key_aspects"].append("backend")
        
        if any(keyword in topic_lower for keyword in ["deploy", "infrastructure", "cloud", "kubernetes", "docker"]):
            analysis["key_aspects"].append("infrastructure")
        
        if any(keyword in topic_lower for keyword in ["business", "strategy", "market", "customer", "product"]):
            analysis["key_aspects"].append("business")
        
        # Determine technical complexity
        if any(keyword in topic_lower for keyword in ["complex", "difficult", "challenging", "advanced"]):
            analysis["technical_complexity"] = "high"
        elif any(keyword in topic_lower for keyword in ["simple", "basic", "easy"]):
            analysis["technical_complexity"] = "low"
        
        # Determine business impact
        if any(keyword in topic_lower for keyword in ["critical", "important", "essential", "key"]):
            analysis["business_impact"] = "high"
        elif any(keyword in topic_lower for keyword in ["minor", "small", "low"]):
            analysis["business_impact"] = "low"
        
        return analysis
    
    def select_roles_for_discussion(self, topic: str, num_roles: int = 3) -> List[Role]:
        """
        Select appropriate roles for a discussion based on the topic.
        This optimized implementation considers topic relevance, role compatibility, and diversity.
        
        Args:
            topic: The discussion topic
            num_roles: The number of roles to select
            
        Returns:
            List[Role]: A list of roles for the discussion
        """
        all_roles = self.get_all_roles()
        
        if not all_roles:
            return []
        
        if len(all_roles) <= num_roles:
            return all_roles
        
        # Analyze the topic to extract key aspects
        topic_analysis = self._analyze_topic_with_llm(topic)
        
        # Calculate relevance scores for all roles
        role_scores = []
        for role in all_roles:
            relevance_score = self._calculate_role_relevance(role, topic)
            
            # Boost scores based on topic analysis
            for aspect in topic_analysis.get("key_aspects", []):
                if any(aspect.lower() in expertise.lower() for expertise in role.expertise):
                    relevance_score += 0.2
            
            # Ensure diversity by boosting scores for different role types
            role_type = self._determine_role_type(role)
            if role_type == "business" and topic_analysis.get("business_impact") == "high":
                relevance_score += 0.1
            elif role_type == "technical" and topic_analysis.get("technical_complexity") == "high":
                relevance_score += 0.1
            
            role_scores.append((role, relevance_score))
        
        # Sort roles by relevance score
        role_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Start with the most relevant role
        selected_roles = [role_scores[0][0]]
        
        # Add remaining roles considering both relevance and compatibility
        remaining_candidates = [r for r, _ in role_scores[1:]]
        
        while len(selected_roles) < num_roles and remaining_candidates:
            best_candidate = None
            best_score = -1
            
            for candidate in remaining_candidates:
                # Calculate compatibility score (how many selected roles this candidate is compatible with)
                compatibility_score = sum(1 for selected_role in selected_roles 
                                         if self.is_compatible(selected_role, candidate))
                
                # Get the candidate's relevance score
                relevance_score = next(score for role, score in role_scores if role == candidate)
                
                # Calculate diversity score (how different this role is from already selected roles)
                selected_role_types = [self._determine_role_type(r) for r in selected_roles]
                candidate_type = self._determine_role_type(candidate)
                diversity_score = 0.3 if candidate_type not in selected_role_types else 0.0
                
                # Combined score with weights
                combined_score = (relevance_score * 0.5) + (compatibility_score * 0.3) + diversity_score
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = candidate
            
            if best_candidate:
                selected_roles.append(best_candidate)
                remaining_candidates.remove(best_candidate)
            else:
                break
        
        return selected_roles
    
    def _determine_role_type(self, role: Role) -> str:
        """
        Determine the type of a role (business, technical, etc.).
        
        Args:
            role: The role to determine the type for
            
        Returns:
            str: The role type
        """
        role_lower = role.role.lower()
        
        # Business roles
        if any(term in role_lower for term in ["product", "business", "manager", "owner", "stakeholder", "analyst"]):
            return "business"
        
        # Design roles
        if any(term in role_lower for term in ["design", "ux", "user experience", "ui"]):
            return "design"
        
        # Security roles
        if any(term in role_lower for term in ["security", "privacy", "compliance"]):
            return "security"
        
        # Operations roles
        if any(term in role_lower for term in ["devops", "operations", "sre", "reliability"]):
            return "operations"
        
        # Default to technical
        return "technical"
    
    def select_compatible_roles(self, topic: str, num_roles: int = 3) -> List[Role]:
        """
        Select a set of compatible roles for a discussion based on the topic.
        
        Args:
            topic: The discussion topic
            num_roles: The number of roles to select
            
        Returns:
            List[Role]: A list of compatible roles for the discussion
        """
        all_roles = self.get_all_roles()
        
        if not all_roles:
            return []
        
        # Calculate relevance scores for all roles
        role_scores = [(role, self._calculate_role_relevance(role, topic)) for role in all_roles]
        
        # Sort roles by relevance score
        role_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Start with the most relevant role
        selected = [role_scores[0][0]]
        
        # Add compatible roles until we reach the desired number
        while len(selected) < num_roles and len(selected) < len(all_roles):
            # Find roles compatible with any of the already selected roles
            compatible_candidates = set()
            for selected_role in selected:
                for candidate, _ in role_scores:
                    if candidate not in selected and self.is_compatible(selected_role, candidate):
                        compatible_candidates.add(candidate)
            
            # If no compatible roles found, break
            if not compatible_candidates:
                break
            
            # Find the most relevant compatible role
            best_candidate = None
            best_score = -1
            
            for candidate in compatible_candidates:
                score = next(score for role, score in role_scores if role == candidate)
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
            else:
                break
        
        return selected


def load_roles_from_yaml(roles_yaml_dir: str) -> List[Role]:
    """
    Utility function to load roles from YAML files.
    """
    manager = RoleManager(roles_yaml_dir)
    return manager.get_all_roles() 