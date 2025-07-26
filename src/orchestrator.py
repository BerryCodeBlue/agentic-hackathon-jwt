#!/usr/bin/env python3
"""
LazyPreneur Agent Orchestrator

Manages AI agent interactions and tool integrations for autonomous startup management.
"""

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
import openai
import time
import requests

# Import our tool integrations
try:
    from tools.notion import NotionAPI
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    logger.warning("Notion API not available - tools/notion.py not found")

try:
    from tools.slack import Slack, SlackBotManager
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("Slack API not available - tools/slack.py not found")

try:
    from tools.x import XPlatform
    X_PLATFORM_AVAILABLE = True
except ImportError:
    X_PLATFORM_AVAILABLE = False
    logger.warning("X Platform API not available - tools/x.py not found")

class GeminiClient:
    """Direct Gemini 2.0 API client using HTTP requests"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
    def generate_content(self, prompt: str) -> str:
        data = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        resp = requests.post(self.url, headers=self.headers, json=data)
        if resp.status_code == 200:
            result = resp.json()
            # Try to extract the text from the response
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                return str(result)
        else:
            logger.error(f"Gemini API error: {resp.status_code} {resp.text}")
            return f"[Gemini API error: {resp.status_code}]"

@dataclass
class AgentConfig:
    """Configuration for an AI agent"""
    name: str
    role: str
    description: str
    icon: str
    color: str
    is_custom: bool = False
    tools: List[str] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []



class Agent:
    """Base class for AI agents"""
    
    def __init__(self, config: AgentConfig, ai_client, tools: Dict[str, Any]):
        self.config = config
        self.ai_client = ai_client
        self.tools = tools
        self.conversation_history = []
        self.task_queue = []
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.config.name}, the {self.config.role} of a startup.
        
Role: {self.config.description}

Your responsibilities:
- Make strategic decisions for your area of expertise
- Collaborate with other team members through Slack
- Document important decisions and plans in Notion
- Execute actions using available tools when needed

Available tools: {', '.join(self.config.tools)}

Communication style:
- Keep responses conversational and concise (under 100 words)
- Respond directly to what others have said
- Be collaborative rather than presenting formal reports
- Use natural, engaging language
- Focus on actionable insights and next steps
"""
    
    async def think(self, context: str) -> str:
        """Agent thinks about the given context and returns a response"""
        try:
            if hasattr(self.ai_client, 'chat'):
                # OpenAI client
                response = self.ai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": self.get_system_prompt()},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=500
                )
                return response.choices[0].message.content
            elif hasattr(self.ai_client, 'generate_content'):
                # GeminiClient direct HTTP
                return self.ai_client.generate_content(f"{self.get_system_prompt()}\n\nContext: {context}")
            else:
                # Fallback (should not happen)
                return "[No valid AI client configured]"
        except Exception as e:
            logger.error(f"Error in agent thinking: {e}")
            return f"I'm having trouble processing this right now. Error: {str(e)}"
    
    async def communicate(self, message: str, channel: str = "general") -> Dict:
        """Send a message to Slack channel"""
        if "slack" in self.tools:
            try:
                slack_manager = self.tools["slack"]
                bot = slack_manager.get_bot(self.config.name)
                if bot:
                    result = bot.send_slack_message(channel, self.config.name, message)
                    return {"success": True, "tool": "slack", "result": result}
                else:
                    return {"success": False, "tool": "slack", "error": f"Bot {self.config.name} not found"}
            except Exception as e:
                logger.error(f"Error sending Slack message: {e}")
                return {"success": False, "tool": "slack", "error": str(e)}
        return {"success": False, "tool": "slack", "error": "Slack not available"}
    
    async def document(self, content: str, title: str, database_id: str = None) -> Dict:
        """Document information in Notion"""
        if "notion" in self.tools:
            try:
                notion = self.tools["notion"]
                if database_id:
                    # Create a page in the database
                    properties = {
                        "Title": {"title": [{"text": {"content": title}}]},
                        "Author": {"rich_text": [{"text": {"content": self.config.name}}]},
                        "Date": {"date": {"start": datetime.now().isoformat()}}
                    }
                    
                    # Add content as a paragraph block
                    children = [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": content}}]
                            }
                        }
                    ]
                    
                    result = notion.create_page(database_id, properties, children)
                    return {"success": True, "tool": "notion", "result": result}
                else:
                    return {"success": False, "tool": "notion", "error": "No database ID provided"}
            except Exception as e:
                logger.error(f"Error documenting in Notion: {e}")
                return {"success": False, "tool": "notion", "error": str(e)}
        return {"success": False, "tool": "notion", "error": "Notion not available"}
    
    async def post_social(self, message: str) -> Dict:
        """Post to social media (X/Twitter)"""
        if "x_platform" in self.tools:
            try:
                x_platform = self.tools["x_platform"]
                result = x_platform.post_x_msg(message)
                return {"success": True, "tool": "x_platform", "result": result}
            except Exception as e:
                logger.error(f"Error posting to X: {e}")
                return {"success": False, "tool": "x_platform", "error": str(e)}
        return {"success": False, "tool": "x_platform", "error": "X Platform not available"}

class StartupOrchestrator:
    """Main orchestrator for managing startup agents and tools"""
    
    def __init__(self, startup_data: Dict):
        self.startup_data = startup_data
        self.agents: Dict[str, Agent] = {}
        self.tools: Dict[str, Any] = {}
        self.ai_client = None
        self.notion_database_id = None
        self.notion_databases = {}  # Store all created database IDs
        
        # Agent lifecycle management
        self.is_initialized = False
        self.is_sleeping = False
        self.sleep_task = None
        self.working_session = None
        
        # Stateful integration management
        self.slack_channels = {}  # Cache created Slack channels
        self.slack_bots_initialized = False
        self.notion_initialized = False
        
        # Centralized channel configuration - all discussions go to executive-meeting
        self.primary_discussion_channel = "executive-meeting"
        
        # Initialize AI client
        self._setup_ai_client()
        
        # Initialize tools (only once)
        self._setup_tools()
        
        # Initialize agents
        self._setup_agents()
        
        # Setup integrations (idempotent)
        self._setup_slack_channels()
        self._setup_notion_database()
        
        # Mark as initialized
        self.is_initialized = True
        logger.info("StartupOrchestrator initialized and ready")
    
    def _setup_ai_client(self):
        """Setup AI client based on user preference"""
        api_keys = self.startup_data.get('api_keys', {})
        ai_provider = api_keys.get('ai_provider', 'OpenAI (GPT-4)')
        
        if 'OpenAI' in ai_provider:
            openai_key = api_keys.get('openai')
            if openai_key:
                openai.api_key = openai_key
                self.ai_client = openai
            else:
                raise ValueError("OpenAI API key not provided")
        else:
            gemini_key = api_keys.get('gemini')
            if gemini_key:
                self.ai_client = GeminiClient(gemini_key)
            else:
                raise ValueError("Gemini API key not provided")
    
    def _setup_tools(self):
        """Initialize tool integrations"""
        api_keys = self.startup_data.get('api_keys', {})
        selected_tools = self.startup_data.get('selected_tools', [])
        
        # Setup Slack
        if "Slack" in selected_tools and SLACK_AVAILABLE:
            try:
                # Create a Slack bot manager for multiple bots
                slack_manager = SlackBotManager()
                
                # Add bots for all potential agents (we'll check if they exist later)
                bot_names = ["CEO", "CFO", "CTO", "CMO"]
                bots_added = 0
                
                for bot_name in bot_names:
                    # Try to get token from environment with correct naming convention
                    token_env_var = f"SLACK_API_TOKEN_{bot_name}"
                    token = os.getenv(token_env_var)
                    if token:
                        try:
                            slack_manager.add_bot(bot_name, token)
                            logger.info(f"Added Slack bot: {bot_name}")
                            bots_added += 1
                        except Exception as e:
                            logger.warning(f"Failed to add Slack bot {bot_name}: {e}")
                    else:
                        logger.warning(f"Slack token not found for {bot_name} ({token_env_var})")
                
                if bots_added > 0:
                    self.tools["slack"] = slack_manager
                    logger.info(f"Slack integration initialized with {bots_added} bots")
                else:
                    logger.warning("No Slack bots could be added - Slack integration disabled")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Slack: {e}")
        elif "Slack" in selected_tools:
            logger.warning("Slack selected but not available - skipping initialization")
        
        # Setup Notion
        if "Notion" in selected_tools and NOTION_AVAILABLE:
            try:
                notion_token = os.getenv('NOTION_API_TOKEN')
                if notion_token:
                    self.tools["notion"] = NotionAPI(notion_token)
                    logger.info("Notion integration initialized")
                else:
                    logger.warning("Notion API token not found")
            except Exception as e:
                logger.error(f"Failed to initialize Notion: {e}")
        elif "Notion" in selected_tools:
            logger.warning("Notion selected but not available - skipping initialization")
        
        # Setup X Platform
        if "X Platform" in selected_tools and X_PLATFORM_AVAILABLE:
            try:
                # For now, using environment variables
                # In real implementation, store in startup_data
                x_config = {
                    "api_key": os.getenv('X_API_KEY'),
                    "api_secret": os.getenv('X_API_SECRET'),
                    "access_token": os.getenv('X_ACCESS_TOKEN'),
                    "access_token_secret": os.getenv('X_ACCESS_TOKEN_SECRET')
                }
                if all(x_config.values()):
                    self.tools["x_platform"] = XPlatform(**x_config)
                    logger.info("X Platform integration initialized")
                else:
                    logger.warning("X Platform credentials not found")
            except Exception as e:
                logger.error(f"Failed to initialize X Platform: {e}")
        elif "X Platform" in selected_tools:
            logger.warning("X Platform selected but not available - skipping initialization")
    
    def _setup_agents(self):
        """Initialize AI agents based on user selection"""
        selected_agents = self.startup_data.get('selected_agents', [])
        custom_agents = self.startup_data.get('custom_agents', {})
        
        # Define default agent configurations
        default_agents = {
            "CEO": {
                "name": "CEO",
                "role": "Chief Executive Officer",
                "description": "Strategic planning and overall business direction",
                "icon": "👔",
                "color": "#667eea",
                "tools": ["slack", "notion"]
            },
            "CFO": {
                "name": "CFO",
                "role": "Chief Financial Officer",
                "description": "Financial planning, budgeting, and fundraising",
                "icon": "💰",
                "color": "#f093fb",
                "tools": ["slack", "notion"]
            },
            "CTO": {
                "name": "CTO",
                "role": "Chief Technology Officer",
                "description": "Technical strategy and product development",
                "icon": "⚡",
                "color": "#4facfe",
                "tools": ["slack", "notion", "github"]
            },
            "CMO": {
                "name": "CMO",
                "role": "Chief Marketing Officer",
                "description": "Marketing strategy and customer acquisition",
                "icon": "📈",
                "color": "#43e97b",
                "tools": ["slack", "notion", "x_platform"]
            }
        }
        
        for agent_name in selected_agents:
            if agent_name in default_agents:
                config_data = default_agents[agent_name]
            elif agent_name in custom_agents:
                custom_data = custom_agents[agent_name]
                config_data = {
                    "name": agent_name,
                    "role": agent_name,
                    "description": custom_data.get("description", ""),
                    "icon": custom_data.get("icon", "🤖"),
                    "color": custom_data.get("color", "#000000"),
                    "is_custom": True,
                    "tools": ["slack", "notion"]  # Default tools for custom agents
                }
            else:
                continue
            
            config = AgentConfig(**config_data)
            self.agents[agent_name] = Agent(config, self.ai_client, self.tools)
            logger.info(f"Initialized agent: {agent_name}")
    
    def _setup_slack_channels(self):
        """Setup Slack channels for team communication (idempotent)"""
        if "slack" not in self.tools or self.slack_bots_initialized:
            return
        
        try:
            slack_manager = self.tools["slack"]
            
            # Define channel configuration with auto-invite logic
            channel_configs = {
                # "startup-team": {
                #     "creator": "CEO",
                #     "description": "Main team communication channel",
                #     "auto_invite": ["CEO", "CFO", "CTO", "CMO"],  # All agents
                #     "is_public": True
                # },
                "executive-meeting": {
                    "creator": "CEO", 
                    "description": "Executive decision making",
                    "auto_invite": ["CEO", "CFO", "CTO"],
                    "is_public": False
                },
                # "financial-report": {
                #     "creator": "CFO",
                #     "description": "Financial planning and reporting",
                #     "auto_invite": ["CEO", "CFO"],
                #     "is_public": False
                # },
                # "technical-implementation": {
                #     "creator": "CTO",
                #     "description": "Technical strategy and development",
                #     "auto_invite": ["CEO", "CTO"],
                #     "is_public": False
                # },
                # "marketing-discussion": {
                #     "creator": "CMO",
                #     "description": "Marketing strategy and campaigns",
                #     "auto_invite": ["CEO", "CMO"],
                #     "is_public": False
                # }
            }
            
            # Create channels with auto-invites
            for channel_name, config in channel_configs.items():
                creator_bot = slack_manager.get_bot(config["creator"])
                if not creator_bot:
                    logger.warning(f"No bot found for {config['creator']}, skipping {channel_name}")
                    continue
                
                # Create or get existing channel
                channel_result = creator_bot.create_slack_channel(channel_name)
                if channel_result["success"]:
                    channel_id = channel_result.get("channel_id")
                    self.slack_channels[channel_name] = {
                        "id": channel_id,
                        "creator": config["creator"],
                        "auto_invite": config["auto_invite"],
                        "is_public": config["is_public"]
                    }
                    
                    # Auto-invite other team members
                    if not channel_result.get("already_exists"):
                        logger.info(f"{channel_name} already exists")
                    self._invite_team_members_to_channel(channel_name, config["auto_invite"], slack_manager)
                    logger.info(f"✅ Channel #{channel_name} ready (created by {config['creator']})")
                else:
                    logger.warning(f"Failed to create {channel_name}: {channel_result.get('error', 'Unknown error')}")
            
            self.slack_bots_initialized = True
            logger.info(f"✅ Slack channels initialized: {list(self.slack_channels.keys())}")
                        
        except Exception as e:
            logger.error(f"Error setting up Slack channels: {e}")
    
    def _invite_team_members_to_channel(self, channel_name: str, invite_bots: List[str], slack_manager):
        """Invite team members to a channel"""
        try:
            channel_info = self.slack_channels.get(channel_name)
            if not channel_info:
                return
            
            channel_id = channel_info["id"]
            
            # Get all available bots for this channel
            available_bots = []
            for bot_name in invite_bots:
                bot = slack_manager.get_bot(bot_name)
                if bot:
                    available_bots.append(bot)
            
            # Invite each bot to the channel
            for bot in available_bots:
                try:
                    join_result = bot.join_channel(channel_name)
                    if join_result["success"]:
                        logger.info(f"✅ {bot.bot_name} joined #{channel_name}")
                    else:
                        logger.warning(f"⚠️ {bot.bot_name} could not join #{channel_name}: {join_result.get('error')}")
                except Exception as e:
                    logger.warning(f"⚠️ Error inviting {bot.bot_name} to #{channel_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error inviting team members to {channel_name}: {e}")
    
    def _setup_notion_database(self):
        """Setup Notion database for documentation (idempotent)"""
        if "notion" not in self.tools or self.notion_initialized:
            return
        
        try:
            # Use the NotionBackend to get the created databases
            from notion_backend import NotionBackend
            
            notion_backend = NotionBackend()
            
            # Get the database IDs from the backend
            if notion_backend.databases:
                self.notion_databases = notion_backend.databases
                # Use the main database for agent documentation
                if "main" in notion_backend.databases:
                    self.notion_database_id = notion_backend.databases["main"]
                logger.info(f"✅ Using existing Notion databases: {list(notion_backend.databases.keys())}")
            else:
                logger.warning("⚠️ No Notion databases available - will be created on first use")
            
            self.notion_initialized = True
                
        except Exception as e:
            logger.error(f"Error setting up Notion database: {e}")
    
    async def run_startup_meeting(self, agenda: str) -> Dict:
        """Run a startup team meeting with all agents"""
        logger.info("Starting startup team meeting")
        
        # Create meeting context
        business_info = self.startup_data.get('business_info', {})
        context = f"""
Business: {business_info.get('name', 'Startup')}
Industry: {business_info.get('industry', 'Unknown')}
Business Model: {business_info.get('business_model', 'Unknown')}
Funding Stage: {business_info.get('funding_stage', 'Unknown')}

Meeting Agenda: {agenda}

Please provide your thoughts and recommendations based on your role.
"""
        
        meeting_results = {
            "meeting_id": f"meeting_{int(time.time())}",
            "agenda": agenda,
            "participants": list(self.agents.keys()),
            "discussions": {},
            "decisions": [],
            "action_items": []
        }
        
        # Start the discussion with the first agent
        discussion_history = []
        agent_names = list(self.agents.keys())
        
        for i, agent_name in enumerate(agent_names):
            agent = self.agents[agent_name]
            
            try:
                # Build context based on previous responses
                if i == 0:
                    # First agent starts the discussion
                    discussion_context = f"""
Discussion Topic: {agenda}

You are {agent_name} ({agent.config.role}). Start the discussion on this topic.
Keep your response under 100 words and conversational in tone.
"""
                else:
                    # Subsequent agents respond to previous thoughts
                    previous_agent = agent_names[i-1]
                    previous_response = meeting_results["discussions"][previous_agent]
                    
                    discussion_context = f"""
Discussion Topic: {agenda}

{previous_agent} just said: "{previous_response[:200]}..."

You are {agent_name} ({agent.config.role}). Respond to {previous_agent}'s thoughts and add your perspective.
Keep your response under 100 words and conversational in tone.
"""
                
                # Agent thinks and responds
                response = await agent.think(discussion_context)
                
                # Ensure response is concise (under 100 words)
                words = response.split()
                if len(words) > 100:
                    response = ' '.join(words[:100]) + "..."
                
                meeting_results["discussions"][agent_name] = response
                discussion_history.append(f"{agent_name}: {response}")
                
                # Agent communicates in Slack
                slack_result = await agent.communicate(
                    response,
                    self.primary_discussion_channel
                )
                
                # Log Slack communication result
                if slack_result["success"]:
                    logger.info(f"✅ {agent_name} posted to Slack")
                else:
                    logger.warning(f"⚠️ {agent_name} failed to post to Slack: {slack_result.get('error', 'Unknown error')}")
                    # Fallback: try to post to any available channel
                    await self._fallback_slack_post(agent_name, response)
                
                # Document the discussion
                if self.notion_database_id:
                    doc_result = await agent.document(
                        response,
                        f"{agent_name} - Discussion on {agenda}",
                        self.notion_database_id
                    )
                
                logger.info(f"{agent_name} contributed to discussion")
                
            except Exception as e:
                logger.error(f"Error with agent {agent_name}: {e}")
                meeting_results["discussions"][agent_name] = f"Error: {str(e)}"
        
        # Generate meeting summary
        summary_context = f"""
Meeting Summary Request:
Agenda: {agenda}
Discussions: {json.dumps(meeting_results['discussions'], indent=2)}

Please provide a concise summary of the key decisions and action items from this meeting.
"""
        
        try:
            # Use CEO to generate summary
            ceo_agent = self.agents.get("CEO")
            if ceo_agent:
                summary = await ceo_agent.think(summary_context)
                meeting_results["summary"] = summary
                
                # Document the meeting summary
                if self.notion_database_id:
                    await ceo_agent.document(
                        summary,
                        f"Meeting Summary - {agenda}",
                        self.notion_database_id
                    )
                
                # Post summary to Slack
                await ceo_agent.communicate(
                    f"📋 **Meeting Summary**\n{summary}",
                    self.primary_discussion_channel
                )
        except Exception as e:
            logger.error(f"Error generating meeting summary: {e}")
        
        return meeting_results
    
    async def execute_marketing_campaign(self, campaign_details: str) -> Dict:
        """Execute a marketing campaign using CMO agent"""
        if "CMO" not in self.agents:
            return {"success": False, "error": "CMO agent not available"}
        
        cmo_agent = self.agents["CMO"]
        
        try:
            # CMO plans the campaign
            planning_context = f"""
Marketing Campaign Planning:
{campaign_details}

Please create a comprehensive marketing campaign plan including:
1. Target audience analysis
2. Key messaging
3. Social media strategy
4. Content calendar
5. Success metrics
"""
            
            campaign_plan = await cmo_agent.think(planning_context)
            
            # Document the campaign plan
            doc_result = await cmo_agent.document(
                campaign_plan,
                f"Marketing Campaign Plan - {datetime.now().strftime('%Y-%m-%d')}",
                self.notion_database_id
            )
            
            # Create social media posts
            social_context = f"""
Based on this campaign plan, create 3 engaging social media posts for X (Twitter):
{campaign_plan}

Make the posts engaging, professional, and aligned with the campaign goals.
"""
            
            social_posts = await cmo_agent.think(social_context)
            
            # Split into individual posts (simple approach)
            posts = [post.strip() for post in social_posts.split('\n\n') if post.strip()][:3]
            
            # Post to X Platform
            posted_results = []
            for i, post in enumerate(posts):
                if len(post) <= 280:  # X character limit
                    result = await cmo_agent.post_social(post)
                    posted_results.append({
                        "post_number": i + 1,
                        "content": post,
                        "result": result
                    })
                    
                    # Wait between posts to avoid rate limiting
                    await asyncio.sleep(2)
            
            # Communicate campaign status
            await cmo_agent.communicate(
                f"📈 **Marketing Campaign Launched**\n\n"
                f"Campaign Plan: Documented in Notion\n"
                f"Social Posts: {len([r for r in posted_results if r['result']['success']])} posted to X\n"
                f"Next Steps: Monitor engagement and adjust strategy",
                "marketing-strategy"
            )
            
            return {
                "success": True,
                "campaign_plan": campaign_plan,
                "social_posts": posted_results,
                "documentation": doc_result
            }
            
        except Exception as e:
            logger.error(f"Error executing marketing campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_financial_report(self) -> Dict:
        """Generate financial report using CFO agent"""
        if "CFO" not in self.agents:
            return {"success": False, "error": "CFO agent not available"}
        
        cfo_agent = self.agents["CFO"]
        
        try:
            business_info = self.startup_data.get('business_info', {})
            
            context = f"""
Financial Report Generation:
Business: {business_info.get('name', 'Startup')}
Industry: {business_info.get('industry', 'Unknown')}
Business Model: {business_info.get('business_model', 'Unknown')}
Funding Stage: {business_info.get('funding_stage', 'Unknown')}

Please generate a comprehensive financial report including:
1. Revenue projections
2. Cost analysis
3. Funding requirements
4. Key financial metrics
5. Risk assessment
6. Recommendations
"""
            
            financial_report = await cfo_agent.think(context)
            
            # Document the report
            doc_result = await cfo_agent.document(
                financial_report,
                f"Financial Report - {datetime.now().strftime('%Y-%m-%d')}",
                self.notion_database_id
            )
            
            # Share with executive team
            await cfo_agent.communicate(
                f"💰 **Financial Report Generated**\n\n"
                f"Report has been documented in Notion.\n"
                f"Key highlights:\n{financial_report[:200]}...",
                "executive-meetings"
            )
            
            return {
                "success": True,
                "financial_report": financial_report,
                "documentation": doc_result
            }
            
        except Exception as e:
            logger.error(f"Error generating financial report: {e}")
            return {"success": False, "error": str(e)}
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "agents": {
                name: {
                    "role": agent.config.role,
                    "tools": agent.config.tools,
                    "is_custom": agent.config.is_custom
                }
                for name, agent in self.agents.items()
            },
            "tools": list(self.tools.keys()),
            "notion_database": self.notion_database_id is not None,
            "notion_databases": self.notion_databases,
            "business_info": self.startup_data.get('business_info', {}),
            "status": "active" if not self.is_sleeping else "sleeping",
            "working_session": getattr(self, 'working_session', None),
            "agent_status": self.get_agent_status(),
            "integration_status": self.get_integration_status(),
            "slack_channels": self.slack_channels
        }
    
    async def start_working_session(self, start_datetime, end_datetime, duration_minutes: int) -> Dict:
        """Start a time-based working session for agents"""
        logger.info(f"Starting working session from {start_datetime} to {end_datetime}")
        
        # Wake up agents if they're sleeping
        if self.is_sleeping:
            self._wake_up_agents()
        
        # Ensure integrations are ready (idempotent)
        if not self.slack_bots_initialized:
            logger.info("🔄 Ensuring Slack channels are ready...")
            self._setup_slack_channels()
        
        if not self.notion_initialized:
            logger.info("🔄 Ensuring Notion database is ready...")
            self._setup_notion_database()
        
        self.working_session = {
            "is_active": True,
            "start_time": start_datetime,
            "end_time": end_datetime,
            "duration_minutes": duration_minutes,
            "session_id": f"session_{int(time.time())}",
            "activities": [],
            "decisions": [],
            "documentation": []
        }
        
        # Start the working session
        try:
            # Initial team meeting to set agenda
            initial_agenda = f"""
Working Session Agenda:
Duration: {duration_minutes} minutes
Start Time: {start_datetime.strftime('%H:%M')}
End Time: {end_datetime.strftime('%H:%M')}

Business Context: {self.startup_data.get('business_info', {}).get('idea', 'Startup management')}

Please provide your initial thoughts on what should be accomplished during this working session.
"""
            
            meeting_result = await self.run_startup_meeting(initial_agenda)
            
            # Store the initial meeting
            self.working_session["activities"].append({
                "type": "initial_meeting",
                "timestamp": datetime.now().isoformat(),
                "result": meeting_result
            })
            
            return {
                "success": True,
                "message": f"Working session started successfully for {duration_minutes} minutes",
                "session_id": self.working_session["session_id"],
                "initial_meeting": meeting_result
            }
            
        except Exception as e:
            logger.error(f"Error starting working session: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_working_session(self) -> Dict:
        """Run the active working session with periodic agent interactions"""
        if not hasattr(self, 'working_session') or not self.working_session.get('is_active'):
            return {"success": False, "error": "No active working session"}
        
        session = self.working_session
        start_time = session['start_time']
        end_time = session['end_time']
        duration = session['duration_minutes']
        
        logger.info(f"Running working session: {start_time} to {end_time}")
        
        # Calculate interaction intervals (every 15 minutes or at least 3 interactions)
        interaction_count = max(3, duration // 15)
        interval_minutes = duration // interaction_count
        
        activities = []
        
        try:
            # Run periodic agent interactions
            for i in range(interaction_count):
                current_time = datetime.now()
                
                # Check if session should end
                if current_time >= end_time:
                    logger.info("Working session time limit reached")
                    break
                
                # Generate interaction topic based on business context
                business_info = self.startup_data.get('business_info', {})
                interaction_topics = [
                    f"Progress update and next steps for {business_info.get('name', 'our startup')}",
                    f"Strategic decisions needed for {business_info.get('industry', 'our industry')}",
                    f"Financial considerations for {business_info.get('business_model', 'our business model')}",
                    f"Marketing opportunities and customer acquisition strategies",
                    f"Technical roadmap and product development priorities"
                ]
                
                topic = interaction_topics[i % len(interaction_topics)]
                
                # Run agent interaction
                interaction_result = await self._run_agent_interaction(topic, i + 1, interaction_count)
                activities.append(interaction_result)
                
                # Wait for next interaction (if not the last one)
                if i < interaction_count - 1:
                    await asyncio.sleep(interval_minutes * 60)  # Convert to seconds
            
            # Generate final session summary
            final_summary = await self._generate_session_summary(activities)
            
            # Update session with final results
            session["activities"].extend(activities)
            session["final_summary"] = final_summary
            session["is_active"] = False
            
            return {
                "success": True,
                "message": "Working session completed successfully",
                "activities_count": len(activities),
                "final_summary": final_summary
            }
            
        except Exception as e:
            logger.error(f"Error during working session: {e}")
            return {"success": False, "error": str(e)}
    
    async def _run_agent_interaction(self, topic: str, interaction_number: int, total_interactions: int) -> Dict:
        """Run a single agent interaction during the working session"""
        logger.info(f"Running agent interaction {interaction_number}/{total_interactions}: {topic}")
        
        interaction = {
            "type": "agent_interaction",
            "interaction_number": interaction_number,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "agent_contributions": {},
            "decisions": [],
            "action_items": []
        }
        
        # Start the discussion with the first agent
        agent_names = list(self.agents.keys())
        
        for i, agent_name in enumerate(agent_names):
            agent = self.agents[agent_name]
            
            try:
                # Build context based on previous responses
                if i == 0:
                    # First agent starts the discussion
                    discussion_context = f"""
Working Session Interaction {interaction_number}/{total_interactions}
Topic: {topic}

You are {agent_name} ({agent.config.role}). Start the discussion on this topic.
Keep your response under 100 words and conversational in tone.
"""
                else:
                    # Subsequent agents respond to previous thoughts
                    previous_agent = agent_names[i-1]
                    previous_response = interaction["agent_contributions"][previous_agent]
                    
                    discussion_context = f"""
Working Session Interaction {interaction_number}/{total_interactions}
Topic: {topic}

{previous_agent} just said: "{previous_response[:500]}..."

You are {agent_name} ({agent.config.role}). Respond to {previous_agent}'s thoughts and add your perspective.
Keep your response under 100 words and conversational in tone.
"""
                
                # Agent thinks and responds
                response = await agent.think(discussion_context)
                
                # Ensure response is concise (under 100 words)
                words = response.split()
                if len(words) > 100:
                    response = ' '.join(words[:100]) + "..."
                
                interaction["agent_contributions"][agent_name] = response
                
                # Agent communicates in Slack
                await agent.communicate(
                    response,
                    self.primary_discussion_channel
                )
                
                # Document in Notion
                if self.notion_database_id:
                    await agent.document(
                        response,
                        f"{agent_name} - {topic} (Interaction {interaction_number})",
                        self.notion_database_id
                    )
                
            except Exception as e:
                logger.error(f"Error with agent {agent_name}: {e}")
                interaction["agent_contributions"][agent_name] = f"Error: {str(e)}"
        
        # Generate interaction summary
        summary_context = f"""
Interaction Summary Request:
Topic: {topic}
Agent Contributions: {json.dumps(interaction['agent_contributions'], indent=2)}

Please provide a concise summary of key decisions and action items from this interaction.
"""
        
        try:
            ceo_agent = self.agents.get("CEO")
            if ceo_agent:
                summary = await ceo_agent.think(summary_context)
                interaction["summary"] = summary
                
                # Document the interaction summary
                if self.notion_database_id:
                    await ceo_agent.document(
                        summary,
                        f"Interaction Summary - {topic}",
                        self.notion_database_id
                    )
                
                # Post summary to Slack
                await ceo_agent.communicate(
                    f"📋 **Interaction {interaction_number} Summary**\n{summary}",
                    self.primary_discussion_channel
                )
        except Exception as e:
            logger.error(f"Error generating interaction summary: {e}")
        
        return interaction
    
    async def _generate_session_summary(self, activities: List[Dict]) -> Dict:
        """Generate final summary of the working session"""
        logger.info("Generating final working session summary")
        
        # Collect all activities and decisions
        all_contributions = []
        all_decisions = []
        
        for activity in activities:
            if activity.get("agent_contributions"):
                all_contributions.extend(activity["agent_contributions"].values())
            if activity.get("summary"):
                all_contributions.append(activity["summary"])
        
        summary_context = f"""
Working Session Final Summary Request:

Session Activities: {len(activities)} interactions completed
Total Contributions: {len(all_contributions)} agent inputs

Please provide a comprehensive summary of:
1. Key decisions made during the session
2. Action items and next steps
3. Strategic insights gained
4. Recommendations for follow-up

Business Context: {self.startup_data.get('business_info', {}).get('idea', 'Startup management')}
"""
        
        try:
            ceo_agent = self.agents.get("CEO")
            if ceo_agent:
                final_summary = await ceo_agent.think(summary_context)
                
                # Document the final summary
                if self.notion_database_id:
                    await ceo_agent.document(
                        final_summary,
                        f"Working Session Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        self.notion_database_id
                    )
                
                # Post final summary to Slack
                await ceo_agent.communicate(
                    f"🎯 **Working Session Complete**\n\n"
                    f"Session Summary:\n{final_summary}\n\n"
                    f"All documentation has been saved to Notion.",
                    self.primary_discussion_channel
                )
                
                return {
                    "summary": final_summary,
                    "activities_count": len(activities),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error generating final summary: {e}")
            return {"error": str(e)}
    
    def stop_working_session(self) -> Dict:
        """Stop the active working session"""
        if hasattr(self, 'working_session') and self.working_session.get('is_active'):
            self.working_session['is_active'] = False
            logger.info("Working session stopped by user")
            
            # Start sleep cycle
            self._start_sleep_cycle()
            
            return {"success": True, "message": "Working session stopped"}
        else:
            return {"success": False, "error": "No active working session"}
    
    def _start_sleep_cycle(self):
        """Start the sleep cycle for agents"""
        if not self.is_sleeping:
            self.is_sleeping = True
            logger.info("🤖 Agents entering sleep mode - no more reinitialization")
            
            # Cancel any existing sleep task
            if self.sleep_task and not self.sleep_task.done():
                self.sleep_task.cancel()
            
            # Start new sleep task
            self.sleep_task = asyncio.create_task(self._sleep_cycle())
    
    async def _sleep_cycle(self):
        """Sleep cycle - agents wait until next working session"""
        try:
            logger.info("💤 Agents are sleeping... Waiting for next working session")
            
            # Sleep indefinitely until woken up
            while self.is_sleeping:
                await asyncio.sleep(60)  # Check every minute
                
                # If working session becomes active, wake up
                if hasattr(self, 'working_session') and self.working_session.get('is_active'):
                    self._wake_up_agents()
                    break
                    
        except asyncio.CancelledError:
            logger.info("Sleep cycle cancelled")
        except Exception as e:
            logger.error(f"Error in sleep cycle: {e}")
    
    def _wake_up_agents(self):
        """Wake up agents for working session"""
        if self.is_sleeping:
            self.is_sleeping = False
            logger.info("🌅 Agents waking up for working session!")
            
            # Cancel sleep task
            if self.sleep_task and not self.sleep_task.done():
                self.sleep_task.cancel()
    
    def get_agent_status(self) -> Dict:
        """Get current agent status"""
        return {
            "is_initialized": self.is_initialized,
            "is_sleeping": self.is_sleeping,
            "has_working_session": hasattr(self, 'working_session') and self.working_session is not None,
            "working_session_active": hasattr(self, 'working_session') and self.working_session.get('is_active', False) if self.working_session else False,
            "agents_count": len(self.agents),
            "tools_available": list(self.tools.keys()),
            "slack_channels_ready": len(self.slack_channels),
            "notion_ready": self.notion_initialized
        }
    
    async def _fallback_slack_post(self, agent_name: str, message: str):
        """Fallback method to post to any available Slack channel"""
        if "slack" not in self.tools:
            return
        
        try:
            slack_manager = self.tools["slack"]
            agent_bot = slack_manager.get_bot(agent_name)
            
            if not agent_bot:
                logger.warning(f"No bot found for {agent_name} in fallback posting")
                return
            
            # Try to post to primary discussion channel first, then any other available channel
            channels_to_try = [self.primary_discussion_channel] + [ch for ch in self.slack_channels.keys() if ch != self.primary_discussion_channel]
            
            for channel_name in channels_to_try:
                try:
                    result = agent_bot.send_slack_message(channel_name, agent_name, message)
                    if result["success"]:
                        logger.info(f"✅ {agent_name} fallback posted to #{channel_name}")
                        return
                except Exception as e:
                    logger.warning(f"⚠️ {agent_name} fallback failed for #{channel_name}: {e}")
                    continue
            
            logger.warning(f"⚠️ {agent_name} could not post to any Slack channel")
            
        except Exception as e:
            logger.error(f"Error in fallback Slack posting: {e}")
    
    def get_integration_status(self) -> Dict:
        """Get detailed integration status"""
        return {
            "slack": {
                "initialized": self.slack_bots_initialized,
                "channels_ready": len(self.slack_channels),
                "channels": list(self.slack_channels.keys()),
                "primary_channel": self.primary_discussion_channel,
                "bots_available": len(self.tools.get("slack", {}).bots) if "slack" in self.tools else 0
            },
            "notion": {
                "initialized": self.notion_initialized,
                "database_ready": self.notion_database_id is not None,
                "databases": list(self.notion_databases.keys())
            },
            "x_platform": {
                "available": "x_platform" in self.tools,
                "initialized": "x_platform" in self.tools and self.tools["x_platform"] is not None
            }
        }


