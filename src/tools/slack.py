import os
import requests
import time
from typing import Dict, List, Optional

class Slack:
    """Simple Slack class for basic channel and message operations with multiple bot support"""
    
    def __init__(self, bot_name: str, api_token: Optional[str] = None):
        """
        Initialize Slack client for a specific bot
        
        Args:
            bot_name: Name of the bot (used to get token from environment and identify the bot)
            api_token: Slack API token. If not provided, will try to get from environment using bot_name
        """
        if not bot_name:
            raise ValueError("bot_name is required to identify the bot")
        
        if api_token:
            self.api_token = api_token
        else:
            # Try to get token from environment using bot name
            env_var_name = f"SLACK_API_TOKEN_{bot_name.upper()}"
            self.api_token = os.getenv(env_var_name) or os.getenv('SLACK_API_TOKEN')
        
        if not self.api_token:
            raise ValueError(f"Slack API token is required for bot '{bot_name}'. Set {env_var_name} environment variable or pass api_token to constructor.")
        
        self.bot_name = bot_name
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Cache for bot identity
        self._bot_identity = None
    
    def get_bot_identity(self) -> Dict:
        """
        Get the bot's identity from Slack API
        
        Returns:
            Dict with bot identity information
        """
        if self._bot_identity:
            return self._bot_identity
        
        try:
            # Try to get bot info first
            response = requests.get(
                f"{self.base_url}/auth.test",
                headers=self.headers
            )
            
            result = response.json()
            
            if result.get('ok'):
                self._bot_identity = {
                    "success": True,
                    "user_id": result.get("user_id"),
                    "user_name": result.get("user"),
                    "team_id": result.get("team_id"),
                    "team_name": result.get("team"),
                    "bot_name": self.bot_name,
                    "message": f"Bot identity: {result.get('user')} ({result.get('user_id')}) in {result.get('team')}"
                }
                return self._bot_identity
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to get bot identity: {error_msg}",
                    "bot_name": self.bot_name
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while getting bot identity",
                "bot_name": self.bot_name
            }
    
    def create_slack_channel(self, channel_name: str) -> Dict:
        """
        Create a Slack channel
        
        Args:
            channel_name: Name of the channel to create
            
        Returns:
            Dict with success status and response
        """
        try:
            # First check if channel already exists
            existing_channel_id = self._get_channel_id(channel_name)
            if existing_channel_id:
                return {
                    "success": True,
                    "message": f"Channel #{channel_name} already exists",
                    "channel_id": existing_channel_id,
                    "already_exists": True
                }
            
            payload = {
                "name": channel_name,
                "is_private": False
            }
            
            response = requests.post(
                f"{self.base_url}/conversations.create",
                headers=self.headers,
                json=payload
            )
            
            result = response.json()
            
            if result.get('ok'):
                # Add a small delay to allow Slack to propagate the channel
                time.sleep(2)
                return {
                    "success": True,
                    "message": f"Channel #{channel_name} created successfully by {self.bot_name}",
                    "channel_id": result.get("channel", {}).get("id")
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to create channel #{channel_name}: {error_msg}",
                    "full_response": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while creating channel #{channel_name}"
            }
    
    def join_channel(self, channel_name: str) -> Dict:
        """
        Join a Slack channel
        
        Args:
            channel_name: Name of the channel to join
            
        Returns:
            Dict with success status and response
        """
        try:
            # Get bot identity to know who's joining
            bot_identity = self.get_bot_identity()
            if not bot_identity["success"]:
                return {
                    "success": False,
                    "error": "Could not identify bot",
                    "message": f"Failed to get bot identity: {bot_identity.get('error')}"
                }
            
            # First get the channel ID
            channel_id = self._get_channel_id_with_retry(channel_name)
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel #{channel_name} not found",
                    "message": f"Could not find channel #{channel_name} to join"
                }
            
            payload = {
                "channel": channel_id
            }
            
            response = requests.post(
                f"{self.base_url}/conversations.join",
                headers=self.headers,
                json=payload
            )
            
            result = response.json()
            
            if result.get('ok'):
                # Now we know exactly who's joining
                return {
                    "success": True,
                    "message": f"Successfully joined channel #{channel_name} as {bot_identity.get('user_name', self.bot_name)}",
                    "channel_id": channel_id,
                    "bot_identity": bot_identity
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                # If already in channel, that's fine
                if "already_in_channel" in error_msg:
                    return {
                        "success": True,
                        "message": f"Already in channel #{channel_name} as {bot_identity.get('user_name', self.bot_name)}",
                        "channel_id": channel_id,
                        "already_joined": True,
                        "bot_identity": bot_identity
                    }
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Failed to join channel #{channel_name}: {error_msg}"
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while joining channel #{channel_name}"
            }
    
    def send_slack_message(self, channel_name: str, bot_name: str, msg: str) -> Dict:
        """
        Send a message to a Slack channel (automatically joins if needed)
        
        Args:
            channel_name: Name of the channel to send message to
            bot_name: Name of the bot sending the message (can be different from self.bot_name)
            msg: Message content
            
        Returns:
            Dict with success status and response
        """
        try:
            # Get bot identity
            bot_identity = self.get_bot_identity()
            
            # First get the channel ID with retries
            channel_id = self._get_channel_id_with_retry(channel_name)
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel #{channel_name} not found",
                    "message": f"Could not find channel #{channel_name}"
                }
            
            # Try to join the channel first (in case we're not in it)
            join_result = self.join_channel(channel_name)
            if not join_result["success"]:
                return {
                    "success": False,
                    "error": f"Could not join channel #{channel_name}",
                    "message": f"Failed to join channel before sending message: {join_result.get('error')}"
                }
            
            payload = {
                "channel": channel_id,
                "text": msg,
                "username": bot_name
            }
            
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers=self.headers,
                json=payload
            )
            
            result = response.json()
            
            if result.get('ok'):
                return {
                    "success": True,
                    "message": f"Message sent to #{channel_name} successfully by {bot_identity.get('user_name', self.bot_name)}",
                    "timestamp": result.get("ts")
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to send message to #{channel_name}: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while sending message to #{channel_name}"
            }
    
    def read_slack_message(self, channel_name: str) -> Dict:
        """
        Read messages from a Slack channel (automatically joins if needed)
        
        Args:
            channel_name: Name of the channel to read messages from
            
        Returns:
            Dict with success status and messages
        """
        try:
            # Get bot identity
            bot_identity = self.get_bot_identity()
            
            # First get the channel ID with retries
            channel_id = self._get_channel_id_with_retry(channel_name)
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel #{channel_name} not found",
                    "message": f"Could not find channel #{channel_name}"
                }
            
            # Try to join the channel first (in case we're not in it)
            join_result = self.join_channel(channel_name)
            if not join_result["success"]:
                return {
                    "success": False,
                    "error": f"Could not join channel #{channel_name}",
                    "message": f"Failed to join channel before reading messages: {join_result.get('error')}"
                }
            
            payload = {
                "channel": channel_id,
                "limit": 100  # Get last 100 messages
            }
            
            response = requests.get(
                f"{self.base_url}/conversations.history",
                headers=self.headers,
                params=payload
            )
            
            result = response.json()
            
            if result.get('ok'):
                messages = result.get("messages", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(messages)} messages from #{channel_name} using {bot_identity.get('user_name', self.bot_name)}",
                    "messages": messages,
                    "count": len(messages)
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to read messages from #{channel_name}: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while reading messages from #{channel_name}"
            }
    
    def list_all_channels(self) -> Dict:
        """
        List all channels the bot can see
        
        Returns:
            Dict with success status and list of channels
        """
        try:
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers=self.headers,
                params={"types": "public_channel,private_channel"}
            )
            
            result = response.json()
            
            if result.get('ok'):
                channels = result.get('channels', [])
                channel_names = [channel.get("name") for channel in channels]
                return {
                    "success": True,
                    "message": f"Found {len(channels)} channels",
                    "channels": channels,
                    "channel_names": channel_names,
                    "count": len(channels)
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to list channels: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while listing channels"
            }
    
    def archive_channel(self, channel_name: str) -> Dict:
        """
        Archive a channel (requires admin permissions)
        
        Args:
            channel_name: Name of the channel to archive
            
        Returns:
            Dict with success status and response
        """
        try:
            # Get channel ID
            channel_id = self._get_channel_id(channel_name)
            if not channel_id:
                return {
                    "success": False,
                    "error": f"Channel '{channel_name}' not found",
                    "message": f"Cannot archive channel: {channel_name} not found"
                }
            
            # Archive the channel
            response = requests.post(
                f"{self.base_url}/conversations.archive",
                headers=self.headers,
                json={"channel": channel_id}
            )
            
            result = response.json()
            
            if result.get('ok'):
                return {
                    "success": True,
                    "message": f"Successfully archived channel: {channel_name}",
                    "channel_id": channel_id
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to archive channel {channel_name}: {error_msg}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while archiving channel {channel_name}"
            }
    
    def _get_channel_id(self, channel_name: str) -> Optional[str]:
        """
        Get channel ID from channel name
        
        Args:
            channel_name: Name of the channel
            
        Returns:
            Channel ID or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers=self.headers,
                params={"types": "public_channel,private_channel"}
            )
            
            result = response.json()
            
            if result.get('ok'):
                channels = result.get('channels', [])
                for channel in channels:
                    if channel.get("name") == channel_name:
                        return channel.get("id")
            
            return None
            
        except Exception:
            return None
    
    def _get_channel_id_with_retry(self, channel_name: str, max_retries: int = 3) -> Optional[str]:
        """
        Get channel ID with retries (useful for newly created channels)
        
        Args:
            channel_name: Name of the channel
            max_retries: Maximum number of retries
            
        Returns:
            Channel ID or None if not found after retries
        """
        for attempt in range(max_retries):
            channel_id = self._get_channel_id(channel_name)
            if channel_id:
                return channel_id
            
            if attempt < max_retries - 1:
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** attempt)
        
        return None

class SlackBotManager:
    """Manager class to handle multiple Slack bots"""
    
    def __init__(self):
        """Initialize the bot manager"""
        self.bots = {}
    
    def add_bot(self, bot_name: str, api_token: Optional[str] = None) -> Slack:
        """
        Add a bot to the manager
        
        Args:
            bot_name: Name of the bot
            api_token: API token for the bot (optional, will use environment variable if not provided)
            
        Returns:
            Slack instance for the bot
        """
        bot = Slack(bot_name, api_token)
        self.bots[bot_name] = bot
        return bot
    
    def get_bot(self, bot_name: str) -> Optional[Slack]:
        """
        Get a bot by name
        
        Args:
            bot_name: Name of the bot
            
        Returns:
            Slack instance or None if not found
        """
        return self.bots.get(bot_name)
    
    def list_bots(self) -> List[str]:
        """
        List all available bots
        
        Returns:
            List of bot names
        """
        return list(self.bots.keys())

 