import argparse
import os
import json
from typing import Dict, List, Any, Optional

from ..role.role_manager import load_roles_from_yaml, RoleManager
from ..engine.discussion_engine import DiscussionEngine
from ..llm.llm_client import create_llm_client
from ..engine.consensus_detector import ConsensusDetector


def format_message(message: Dict[str, Any]) -> str:
    """
    Format a message for display.
    """
    role = message.get("role", "Unknown")
    content = message.get("content", "")
    return f"[{role}]: {content}"


def run_discussion(args: argparse.Namespace) -> None:
    """
    Run a discussion based on command-line arguments.
    """
    # Load roles
    role_manager = RoleManager(args.roles_dir)
    
    # Select roles for the discussion
    if args.roles:
        # Use specified roles
        selected_roles = [role_manager.get_role(role) for role in args.roles.split(",")]
        # Filter out None values (roles that weren't found)
        selected_roles = [role for role in selected_roles if role]
    else:
        # Auto-select roles based on the topic
        selected_roles = role_manager.select_roles_for_discussion(args.topic, args.num_roles)
    
    if not selected_roles:
        print(f"Error: No valid roles selected for discussion.")
        return
    
    print(f"\n🚀 Starting discussion on topic: {args.topic}")
    print(f"👥 Participants: {', '.join(role.role for role in selected_roles)}")
    print("-" * 80)
    
    # Create LLM client
    llm_client = create_llm_client(args.llm_client, model=args.model)
    
    # Create consensus detector
    consensus_detector = ConsensusDetector(llm_client)
    
    # Create and run discussion engine
    engine = DiscussionEngine(args.topic, selected_roles, args.state_dir)
    engine.max_turns = args.max_turns
    
    # In a real implementation, we would integrate the LLM client and consensus detector
    # For now, we'll just run the placeholder implementation
    result = engine.run_discussion()
    
    # Display results
    print("\n📝 Discussion Summary:")
    print("-" * 80)
    
    for message in result["discussion"]:
        print(format_message(message))
        print("-" * 80)
    
    print(f"\n🏁 Discussion ended after {result['turns']} turns.")
    if result["consensus_reached"]:
        print("✅ Consensus was reached!")
    else:
        print("❌ No consensus was reached.")
    
    # Save results if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Results saved to {args.output}")


def main() -> None:
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(description="Discussion-Llama: A multi-role discussion system")
    
    parser.add_argument("topic", help="The topic for discussion")
    parser.add_argument("--roles-dir", default="./roles", help="Directory containing role YAML files")
    parser.add_argument("--roles", help="Comma-separated list of role names to include")
    parser.add_argument("--num-roles", type=int, default=3, help="Number of roles to include (if not specified)")
    parser.add_argument("--max-turns", type=int, default=30, help="Maximum number of turns")
    parser.add_argument("--state-dir", default="./discussion_state", help="Directory for storing discussion state")
    parser.add_argument("--llm-client", default="mock", choices=["mock", "ollama"], help="LLM client to use")
    parser.add_argument("--model", default="llama2:7b-chat-q4_0", help="Model to use (for Ollama)")
    parser.add_argument("--output", help="Output file for discussion results (JSON)")
    
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs(args.roles_dir, exist_ok=True)
    os.makedirs(args.state_dir, exist_ok=True)
    
    try:
        run_discussion(args)
    except KeyboardInterrupt:
        print("\n\n⚠️ Discussion interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main() 