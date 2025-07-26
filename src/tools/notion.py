#!/usr/bin/env python3
"""
Lightweight Notion API Connection

A simple class for interacting with Notion databases and pages.
"""

import os
import requests
from typing import Dict, List, Optional

class NotionAPI:
    """Lightweight Notion API client for database operations"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Notion API client
        
        Args:
            api_token: Notion API token. If not provided, will try to get from environment
        """
        self.api_token = api_token or os.getenv('NOTION_API_TOKEN')
        
        if not self.api_token:
            raise ValueError("Notion API token is required. Set NOTION_API_TOKEN environment variable or pass api_token to constructor.")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def create_database(self, parent_page_id: str, title: str, properties: Dict) -> Dict:
        """
        Create a new database in Notion
        
        Args:
            parent_page_id: ID of the parent page where database will be created
            title: Title of the database
            properties: Database properties configuration
            
        Returns:
            Dict with database creation result
        """
        try:
            url = f"{self.base_url}/databases"
            
            payload = {
                "parent": {"page_id": parent_page_id},
                "title": [{"text": {"content": title}}],
                "properties": properties
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Database '{title}' created successfully",
                    "database_id": result["id"],
                    "database_url": result["url"],
                    "title": title
                }
            else:
                error_result = response.json() if response.content else {}
                error_msg = error_result.get('message', f"HTTP {response.status_code}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to create database: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while creating database: {str(e)}"
            }
    
    def search_databases(self, query: str) -> Dict:
        """
        Search for databases by name
        
        Args:
            query: Search query for database name
            
        Returns:
            Dict with search results
        """
        try:
            url = f"{self.base_url}/search"
            
            payload = {
                "query": query,
                "filter": {
                    "value": "database",
                    "property": "object"
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                databases = result.get("results", [])
                
                return {
                    "success": True,
                    "message": f"Found {len(databases)} databases matching '{query}'",
                    "databases": databases,
                    "count": len(databases)
                }
            else:
                error_result = response.json() if response.content else {}
                error_msg = error_result.get('message', f"HTTP {response.status_code}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to search databases: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while searching databases: {str(e)}"
            }
    
    def retrieve_database(self, database_id: str) -> Dict:
        """
        Retrieve database structure and metadata
        
        Args:
            database_id: ID of the database to retrieve
            
        Returns:
            Dict with database information
        """
        try:
            url = f"{self.base_url}/databases/{database_id}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Database '{result.get('title', [{}])[0].get('text', {}).get('content', 'Unknown')}' retrieved successfully",
                    "database_id": result["id"],
                    "database_url": result["url"],
                    "title": result.get('title', [{}])[0].get('text', {}).get('content', 'Unknown'),
                    "properties": result.get("properties", {}),
                    "created_time": result.get("created_time"),
                    "last_edited_time": result.get("last_edited_time")
                }
            else:
                error_result = response.json() if response.content else {}
                error_msg = error_result.get('message', f"HTTP {response.status_code}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to retrieve database: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while retrieving database: {str(e)}"
            }
    
    def query_database(self, database_id: str, filter_params: Optional[Dict] = None, sort_params: Optional[List] = None) -> Dict:
        """
        Query a database to retrieve pages/entries
        
        Args:
            database_id: ID of the database to query
            filter_params: Optional filter parameters
            sort_params: Optional sort parameters
            
        Returns:
            Dict with query results
        """
        try:
            url = f"{self.base_url}/databases/{database_id}/query"
            
            payload = {}
            if filter_params:
                payload["filter"] = filter_params
            if sort_params:
                payload["sorts"] = sort_params
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                pages = result.get("results", [])
                
                return {
                    "success": True,
                    "message": f"Retrieved {len(pages)} pages from database",
                    "pages": pages,
                    "count": len(pages),
                    "has_more": result.get("has_more", False),
                    "next_cursor": result.get("next_cursor")
                }
            else:
                error_result = response.json() if response.content else {}
                error_msg = error_result.get('message', f"HTTP {response.status_code}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to query database: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while querying database: {str(e)}"
            }
    
    def _check_existing_page_by_title(self, database_id: str, title: str) -> Optional[str]:
        """
        Check if a page with the given title already exists in the database
        
        Args:
            database_id: ID of the database to search in
            title: Title to search for
            
        Returns:
            Page ID if found, None otherwise
        """
        try:
            # Query the database for pages with the same title
            filter_params = {
                "property": "Title",
                "title": {
                    "equals": title
                }
            }
            
            result = self.query_database(database_id, filter_params=filter_params)
            
            if result["success"] and result["pages"]:
                # Return the ID of the first matching page
                return result["pages"][0]["id"]
            
            return None
            
        except Exception as e:
            # If there's an error checking, assume no duplicate exists
            return None
    
    def create_page(self, parent_id: str, properties: Dict, content: Optional[List] = None, is_database: bool = True) -> Dict:
        """
        Create a new page in a database or as a child of another page
        
        Args:
            parent_id: ID of the parent (database or page)
            properties: Page properties
            content: Optional page content blocks
            is_database: Whether the parent_id is a database ID (default: True)
            
        Returns:
            Dict with page creation result
        """
        try:
            # If creating in a database, check for existing page with same title
            if is_database:
                # Extract title from properties
                title_property = properties.get("Title", {})
                title_text = ""
                
                # Handle different title property formats
                if isinstance(title_property, dict):
                    if "title" in title_property and title_property["title"]:
                        title_text = title_property["title"][0].get("text", {}).get("content", "")
                    elif "rich_text" in title_property and title_property["rich_text"]:
                        title_text = title_property["rich_text"][0].get("text", {}).get("content", "")
                
                # If we have a title, check for duplicates
                if title_text:
                    existing_page_id = self._check_existing_page_by_title(parent_id, title_text)
                    if existing_page_id:
                        return {
                            "success": True,
                            "message": f"Page with title '{title_text}' already exists",
                            "page_id": existing_page_id,
                            "already_exists": True,
                            "page_url": f"https://notion.so/{existing_page_id.replace('-', '')}"
                        }
            
            url = f"{self.base_url}/pages"
            
            # Use the is_database parameter to determine parent type
            if is_database:
                payload = {
                    "parent": {"database_id": parent_id},
                    "properties": properties
                }
            else:
                payload = {
                    "parent": {"page_id": parent_id},
                    "properties": properties
                }
            
            if content:
                payload["children"] = content
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": "Page created successfully",
                    "page_id": result["id"],
                    "page_url": result["url"],
                    "created_time": result.get("created_time"),
                    "already_exists": False
                }
            else:
                error_result = response.json() if response.content else {}
                error_msg = error_result.get('message', f"HTTP {response.status_code}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to create page: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while creating page: {str(e)}"
            }


