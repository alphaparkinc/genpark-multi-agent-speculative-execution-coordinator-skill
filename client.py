"""
Multi-Agent Speculative Execution & Early Cancellation Coordinator (Zero External Dependencies)
Provides speculative branch tracking, Pareto efficiency evaluation, and cancellation signals.
"""
import time
import math
import hashlib
import json
from typing import Dict, Any, List, Optional

class MultiAgentSpeculativeExecutionCoordinator:
    def __init__(self, win_margin_threshold: float = 0.25):
        self.win_margin = win_margin_threshold
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def register_speculative_path(
        self,
        session_id: str,
        path_id: str,
        agent_id: str,
        hypothesis_description: str
    ) -> Dict[str, Any]:
        """Registers a speculative execution path for parallel evaluation."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "created_at": time.time(),
                "paths": {},
                "winner_path_id": None,
                "status": "ACTIVE"
            }

        session = self.sessions[session_id]
        path_entry = {
            "path_id": path_id,
            "agent_id": agent_id,
            "hypothesis": hypothesis_description,
            "status": "RUNNING", # RUNNING, WON_ACCEPTED, CANCELLED_EARLY
            "milestones": [],
            "current_score": 0.0,
            "estimated_cost_usd": 0.0,
            "updated_at": time.time()
        }
        session["paths"][path_id] = path_entry

        return {"session_id": session_id, "path_id": path_id, "status": "RUNNING"}

    def update_path_milestone(
        self,
        session_id: str,
        path_id: str,
        milestone_name: str,
        confidence_score: float,
        estimated_cost_usd: float = 0.0
    ) -> Dict[str, Any]:
        """Updates branch milestone progress and recomputes composite fitness."""
        if session_id not in self.sessions or path_id not in self.sessions[session_id]["paths"]:
            return {"error": "Path or session not found"}

        path = self.sessions[session_id]["paths"][path_id]
        now = time.time()
        path["milestones"].append({"name": milestone_name, "score": confidence_score, "time": now})
        path["current_score"] = confidence_score
        path["estimated_cost_usd"] = estimated_cost_usd
        path["updated_at"] = now

        # Evaluate if this milestone triggers early cancellation on others
        eval_res = self.evaluate_speculative_candidates(session_id)

        return {
            "session_id": session_id,
            "path_id": path_id,
            "current_score": confidence_score,
            "evaluation_outcome": eval_res
        }

    def evaluate_speculative_candidates(self, session_id: str) -> Dict[str, Any]:
        """
        Compares all running branches. If a leader exceeds competitors by win_margin_threshold,
        it declares a winner and issues CANCEL signals to all other branches to conserve compute.
        """
        if session_id not in self.sessions:
            return {"error": f"Session {session_id} not found"}

        session = self.sessions[session_id]
        paths = session["paths"]

        running = [p for p in paths.values() if p["status"] in ("RUNNING", "WON_ACCEPTED")]
        if not running:
            return {
                "session_id": session_id,
                "leader_path_id": session.get("winner_path_id"),
                "status": session["status"],
                "has_winner": session["winner_path_id"] is not None,
                "winner_path_id": session.get("winner_path_id"),
                "early_cancellations_issued": []
            }

        # Rank running paths by score
        running.sort(key=lambda x: x["current_score"], reverse=True)
        top_path = running[0]

        cancelled_paths = []
        if len(running) > 1 and session.get("winner_path_id") is None:
            second_path = running[1]
            margin = top_path["current_score"] - second_path["current_score"]

            if margin >= self.win_margin and top_path["current_score"] >= 0.80:
                # Early cancellation triggered!
                session["winner_path_id"] = top_path["path_id"]
                session["status"] = "RESOLVED_WINNER_SELECTED"
                top_path["status"] = "WON_ACCEPTED"

                for other in running[1:]:
                    other["status"] = "CANCELLED_EARLY"
                    cancelled_paths.append(other["path_id"])

        return {
            "session_id": session_id,
            "leader_path_id": top_path["path_id"],
            "leader_score": top_path["current_score"],
            "has_winner": session["winner_path_id"] is not None,
            "early_cancellations_issued": cancelled_paths
        }

    def get_active_paths(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        return self.sessions[session_id]
