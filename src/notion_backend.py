#!/usr/bin/env python3
"""
Simple Notion Backend for LazyPreneur

Provides basic database operations for storing startup data.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from tools.notion import NotionAPI

logger = logging.getLogger(__name__)

class NotionBackend:
    """Simple Notion backend for LazyPreneur data storage"""
    
    def __init__(self, notion_token: Optional[str] = None, parent_page_id: Optional[str] = None):
        """Initialize Notion backend"""
        self.notion_token = notion_token or os.getenv('NOTION_API_TOKEN')
        self.parent_page_id = parent_page_id or os.getenv('NOTION_PARENT_PAGE_ID')
        
        if not self.notion_token:
            raise ValueError("Notion API token is required")
        if not self.parent_page_id:
            raise ValueError("Notion parent page ID is required")
        
        self.notion = NotionAPI(self.notion_token)
        self.databases = {}
        
        # Create main database if it doesn't exist
        self._setup_main_database()
    
    def _find_existing_database(self, database_name: str) -> Optional[str]:
        """Find an existing database by name"""
        try:
            # Search for databases by name
            search_result = self.notion.search_databases(database_name)
            if search_result["success"]:
                databases = search_result.get("databases", [])
                for db in databases:
                    # Check if the database title matches (name is the same)
                    db_title = db.get("title", [])
                    if db_title and any(title.get("text", {}).get("content", "") == database_name for title in db_title):
                        # If name matches, return the database ID (regardless of parent page)
                        logger.info(f"Found existing database '{database_name}' with ID: {db.get('id')}")
                        return db.get("id")
            
            logger.info(f"No existing database found with name '{database_name}'")
            return None
        except Exception as e:
            logger.warning(f"Error searching for existing database: {e}")
            return None
    
    def _create_main_database(self):
        """Create the main LazyPreneur database"""
        try:
            # Simple database with basic properties
            properties = {
                "Title": {"title": {}},
                "Type": {"select": {
                    "options": [
                        {"name": "Startup Config", "color": "blue"},
                        {"name": "Working Session", "color": "green"},
                        {"name": "Agent Interaction", "color": "yellow"},
                        {"name": "System Update", "color": "red"}
                    ]
                }},
                "Content": {"rich_text": {}},
                "Created At": {"date": {}},
                "Status": {"select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Completed", "color": "blue"},
                        {"name": "Archived", "color": "gray"}
                    ]
                }}
            }
            
            result = self.notion.create_database(
                self.parent_page_id,
                "LazyPreneur Data",
                properties
            )
            
            if result["success"]:
                self.databases["main"] = result["database_id"]
                logger.info(f"Created main database: {result['database_id']}")
            else:
                logger.error(f"Failed to create database: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error creating database: {e}")
    
    def _setup_main_database(self):
        """Setup the main database - find existing or create new"""
        database_name = "LazyPreneur Data"
        
        # First, try to find an existing database
        existing_db_id = self._find_existing_database(database_name)
        
        if existing_db_id:
            self.databases["main"] = existing_db_id
            logger.info(f"✅ Reusing existing database '{database_name}' with ID: {existing_db_id}")
        else:
            # Create new database if none exists
            logger.info(f"🆕 Creating new database '{database_name}'...")
            self._create_main_database()
            
            # Verify creation was successful
            if "main" in self.databases:
                logger.info(f"✅ Successfully created new database '{database_name}' with ID: {self.databases['main']}")
            else:
                logger.error(f"❌ Failed to create database '{database_name}' - system will have limited functionality")
    
    def set_database_id(self, database_id: str):
        """Manually set the database ID if you know it exists"""
        self.databases["main"] = database_id
        logger.info(f"Manually set database ID: {database_id}")
    
    def save_data(self, title: str, content: str, data_type: str = "System Update") -> Dict[str, Any]:
        """Save any data to Notion"""
        try:
            if "main" not in self.databases:
                return {"success": False, "error": "Database not available"}
            
            properties = {
                "Title": {"title": [{"text": {"content": title}}]},
                "Type": {"select": {"name": data_type}},
                "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},  # Notion limit
                "Created At": {"date": {"start": datetime.now().isoformat()}},
                "Status": {"select": {"name": "Active"}}
            }
            
            result = self.notion.create_page(
                self.databases["main"],
                properties,
                is_database=True
            )
            
            if result["success"]:
                logger.info(f"Saved data: {title}")
                return {"success": True, "page_id": result["page_id"]}
            else:
                logger.error(f"Failed to save data: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return {"success": False, "error": str(e)}
    
    def save_startup_config(self, startup_data: Dict) -> Dict[str, Any]:
        """Save startup configuration"""
        business_info = startup_data.get('business_info', {})
        content = f"""
Startup: {business_info.get('name', 'Unnamed')}
Industry: {business_info.get('industry', 'Unknown')}
Business Model: {business_info.get('business_model', 'Unknown')}
Funding Stage: {business_info.get('funding_stage', 'Unknown')}
Agents: {', '.join(startup_data.get('selected_agents', []))}
Tools: {', '.join(startup_data.get('selected_tools', []))}
AI Provider: {startup_data.get('api_keys', {}).get('ai_provider', 'Unknown')}
        """.strip()
        
        return self.save_data(
            f"Startup Config - {business_info.get('name', 'Unnamed')}",
            content,
            "Startup Config"
        )
    
    def save_working_session(self, session_data: Dict) -> Dict[str, Any]:
        """Save working session data"""
        content = f"""
Session ID: {session_data.get('session_id', 'Unknown')}
Duration: {session_data.get('duration', 0)} minutes
Activities: {len(session_data.get('activities', []))}
Summary: {session_data.get('final_summary', 'No summary')}
        """.strip()
        
        return self.save_data(
            f"Working Session - {session_data.get('session_id', 'Unknown')}",
            content,
            "Working Session"
        )
    
    def save_agent_interaction(self, agent_name: str, topic: str, response: str, session_id: str = "") -> Dict[str, Any]:
        """Save agent interaction"""
        content = f"""
Agent: {agent_name}
Topic: {topic}
Session: {session_id}
Response: {response}
        """.strip()
        
        return self.save_data(
            f"Agent Interaction - {agent_name}",
            content,
            "Agent Interaction"
        )
    
    def get_data(self, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get data from Notion"""
        try:
            if "main" not in self.databases:
                return []
            
            # Simple query - get all pages
            result = self.notion.query_database(self.databases["main"])
            
            if result["success"]:
                pages = result.get("pages", [])
                if data_type:
                    # Filter by type if specified
                    filtered_pages = []
                    for page in pages:
                        page_type = page.get("properties", {}).get("Type", {}).get("select", {}).get("name", "")
                        if page_type == data_type:
                            filtered_pages.append(page)
                    return filtered_pages
                return pages
            else:
                logger.error(f"Failed to query database: {result['error']}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting data: {e}")
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "databases": self.databases,
            "main_database": self.databases.get("main"),
            "data_count": len(self.get_data())
        }

 