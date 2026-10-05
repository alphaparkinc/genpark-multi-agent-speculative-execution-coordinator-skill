"""Example usage for MultiAgentSpeculativeExecutionCoordinator."""
import sys
import json
from client import MultiAgentSpeculativeExecutionCoordinator

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== Multi-Agent Speculative Execution & Early Cancellation Demo ===")
    coordinator = MultiAgentSpeculativeExecutionCoordinator(win_margin_threshold=0.30)
    sess_id = "vacation_booking_swarm_2026"

    # 1. Register candidate speculative branches exploring alternatives
    print("\n--- 1. Spawning Concurrent Speculative Paths ---")
    coordinator.register_speculative_path(sess_id, "path_a_expedia", "agent_expedia", "Direct flight + Boutique Hotel package")
    coordinator.register_speculative_path(sess_id, "path_b_airbnb", "agent_airbnb", "Split layover flight + Airbnb apartment")

    # 2. Update milestones
    print("\n--- 2. Updating Intermediate Milestones ---")
    coordinator.update_path_milestone(sess_id, "path_b_airbnb", "apartment_found", 0.55, 1200.0)
    
    # Path A finds exceptional direct bundle
    res = coordinator.update_path_milestone(sess_id, "path_a_expedia", "direct_deal_locked", 0.95, 890.0)
    print("Milestone Update Evaluation:")
    print(json.dumps(res["evaluation_outcome"], indent=2))

    # 3. Check session status
    final_state = coordinator.get_active_paths(sess_id)
    print(f"\nSession Status: {final_state['status']}")
    print(f"Winning Trajectory: {final_state['winner_path_id']}")

if __name__ == "__main__":
    main()
