import time
from typing import Dict, List
import statistics


class PerformanceMetrics:
    """Tracking výkonu a kvality odpovědí"""

    def __init__(self):
        self.query_times: List[float] = []
        self.confidence_scores: List[str] = []
        self.chunk_usage: List[int] = []
        self.agent_types: List[str] = []

    def track_query(self, duration: float, confidence: str, chunks_used: int, agent_type: str = "general"):
        """Zaznamenání metriky"""
        self.query_times.append(duration)
        self.confidence_scores.append(confidence)
        self.chunk_usage.append(chunks_used)
        self.agent_types.append(agent_type)

    def get_stats(self) -> Dict:
        """Získání statistik"""
        if not self.query_times:
            return {}

        return {
            "total_queries": len(self.query_times),
            "avg_response_time": f"{statistics.mean(self.query_times):.2f}s",
            "min_response_time": f"{min(self.query_times):.2f}s",
            "max_response_time": f"{max(self.query_times):.2f}s",
            "avg_chunks_used": f"{statistics.mean(self.chunk_usage):.1f}",
            "high_confidence_rate": f"{(self.confidence_scores.count('Vysoká') / len(self.confidence_scores) * 100):.1f}%"
        }

    def reset(self):
        """Reset všech metrik"""
        self.query_times.clear()
        self.confidence_scores.clear()
        self.chunk_usage.clear()
        self.agent_types.clear()
