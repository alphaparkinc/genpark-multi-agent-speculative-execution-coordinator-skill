"""MCP Server for Multi-Agent Speculative Execution Coordinator."""
import sys
import json
import time
from client import MultiAgentSpeculativeExecutionCoordinator

coordinator = MultiAgentSpeculativeExecutionCoordinator()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "coordinate_speculative_execution":
        raise ValueError(f"Unknown tool: {name}")

    action = args.get("action", "evaluate_speculative_candidates")
    if action == "register_speculative_path":
        return coordinator.register_speculative_path(
            session_id=args.get("session_id", "sess_1"),
            path_id=args.get("path_id", "branch_a"),
            agent_id=args.get("agent_id", "worker_1"),
            hypothesis_description=args.get("milestone_name", "Hypothesis")
        )
    elif action == "update_path_milestone":
        return coordinator.update_path_milestone(
            session_id=args.get("session_id", "sess_1"),
            path_id=args.get("path_id", "branch_a"),
            milestone_name=args.get("milestone_name", "milestone"),
            confidence_score=float(args.get("confidence_score", 0.5)),
            estimated_cost_usd=float(args.get("estimated_cost_usd", 0.0))
        )
    elif action == "evaluate_speculative_candidates":
        return coordinator.evaluate_speculative_candidates(args.get("session_id", "sess_1"))
    elif action == "get_active_paths":
        return coordinator.get_active_paths(args.get("session_id", "sess_1"))
    else:
        raise ValueError(f"Invalid action: {action}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running self-test...")
        sid = "spec_test_01"
        coordinator.register_speculative_path(sid, "path_train", "agent_1", "High-speed rail route")
        coordinator.register_speculative_path(sid, "path_flight", "agent_2", "Direct flight route")
        coordinator.update_path_milestone(sid, "path_flight", "ticket_locked", 0.92, 280.0)
        coordinator.update_path_milestone(sid, "path_train", "booking_error", 0.45, 310.0)
        eval_res = coordinator.evaluate_speculative_candidates(sid)
        assert eval_res["leader_path_id"] == "path_flight"
        print("Self-test PASSED!")
        sys.exit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "MultiAgentSpeculativeExecutionCoordinator", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [{
                            "name": "coordinate_speculative_execution",
                            "description": "Coordinate speculative multi-agent execution: register speculative paths, update milestone progress, select winning trajectory, and issue cooperative cancellation signals.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["register_speculative_path", "update_path_milestone", "evaluate_speculative_candidates", "get_active_paths"]},
                                    "session_id": {"type": "string"},
                                    "path_id": {"type": "string"},
                                    "agent_id": {"type": "string"},
                                    "milestone_name": {"type": "string"},
                                    "confidence_score": {"type": "number"},
                                    "estimated_cost_usd": {"type": "number"}
                                },
                                "required": ["action"]
                            }
                        }]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
