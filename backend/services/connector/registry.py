from typing import Dict, Type, Optional
from services.connector.base import BaseConnector
from services.connector.leetcode import LeetCodeConnector
from services.connector.codeforces import CodeforcesConnector
from services.connector.github import GitHubConnector
from services.connector.codechef import CodeChefConnector
from services.connector.hackerrank import HackerRankConnector
from services.connector.geeksforgeeks import GeeksforGeeksConnector

class ConnectorRegistry:
    """Registry for managing platform connectors"""
    
    _connectors: Dict[str, Type[BaseConnector]] = {
        "leetcode": LeetCodeConnector,
        "codeforces": CodeforcesConnector,
        "github": GitHubConnector,
        "codechef": CodeChefConnector,
        "hackerrank": HackerRankConnector,
        "geeksforgeeks": GeeksforGeeksConnector,
    }
    
    @classmethod
    def register(cls, platform_name: str, connector_class: Type[BaseConnector]):
        """Register a new connector"""
        cls._connectors[platform_name] = connector_class
    
    @classmethod
    def get_connector(cls, platform_name: str, username: str, credentials: Optional[Dict] = None) -> BaseConnector:
        """Get connector instance for a platform"""
        connector_class = cls._connectors.get(platform_name)
        if not connector_class:
            raise ValueError(f"Unknown platform: {platform_name}")
        return connector_class(username, credentials)
    
    @classmethod
    def list_platforms(cls) -> list:
        """List all available platforms"""
        return list(cls._connectors.keys())
