#!/usr/bin/env python3
"""
Streamlit Integration for LazyPreneur

Connects the Streamlit UI to the agent orchestrator for autonomous startup management.
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import logging
import os # Added missing import for os

from orchestrator import StartupOrchestrator
from notion_backend import NotionBackend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamlitOrchestrator:
    """Streamlit wrapper for the StartupOrchestrator with Notion backend integration"""
    
    def __init__(self):
        self.orchestrator = None
        self.notion_backend = None
        self.is_initialized = False
    
    def initialize_from_session_state(self) -> bool:
        """Initialize orchestrator from Streamlit session state"""
        try:
            if 'startup_data' not in st.session_state or not st.session_state.startup_data:
                st.error("❌ No startup data found. Please complete the configuration first.")
                return False
            
            startup_data = st.session_state.startup_data.copy()
            
            # Add custom agents to startup data
            if 'custom_agents' in st.session_state:
                startup_data['custom_agents'] = st.session_state.custom_agents
            
            # Validate required data
            required_fields = ['selected_agents', 'selected_tools', 'api_keys', 'business_info']
            missing_fields = [field for field in required_fields if not startup_data.get(field)]
            
            if missing_fields:
                st.error(f"❌ Missing required configuration: {', '.join(missing_fields)}")
                return False
            
            # Validate API keys
            api_keys = startup_data['api_keys']
            ai_provider = api_keys.get('ai_provider', '')
            
            if 'OpenAI' in ai_provider and not api_keys.get('openai'):
                st.error("❌ OpenAI API key is required")
                return False
            elif 'Gemini' in ai_provider and not api_keys.get('gemini'):
                st.error("❌ Gemini API key is required")
                return False
            
            # Initialize Notion backend if Notion is selected
            if "Notion" in startup_data.get('selected_tools', []):
                try:
                    self.notion_backend = NotionBackend()
                    logger.info("Notion backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Notion backend: {e}")
                    logger.info("Notion integration will be disabled - system will continue without Notion")
                    self.notion_backend = None
            
            # Initialize orchestrator
            try:
                self.orchestrator = StartupOrchestrator(startup_data)
                self.is_initialized = True
                logger.info("Orchestrator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                st.error(f"❌ Failed to initialize orchestrator: {str(e)}")
                return False
            
            # Save startup config to Notion
            if self.notion_backend:
                try:
                    save_result = self.notion_backend.save_startup_config(startup_data)
                    if save_result["success"]:
                        logger.info("Startup configuration saved to Notion")
                    else:
                        logger.warning(f"Failed to save startup config to Notion: {save_result.get('error', 'Unknown error')}")
                        st.error(f"❌ Failed to save startup config to Notion: {save_result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Error saving to Notion backend: {e}")
            else:
                logger.info("Notion backend not available - skipping startup config save")
            
            # Save system update
            if self.notion_backend:
                try:
                    self.notion_backend.save_data(
                        "System Launch",
                        f"LazyPreneur system launched with {len(startup_data.get('selected_agents', []))} agents and {len(startup_data.get('selected_tools', []))} tools",
                        "System Update"
                    )
                except Exception as e:
                    logger.error(f"Error saving system update to Notion: {e}")
            
            # st.success("✅ LazyPreneur system initialized successfully!")
            return True
            
        except Exception as e:
            st.error(f"❌ Failed to initialize system: {str(e)}")
            logger.error(f"Initialization error: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        if not self.is_initialized or not self.orchestrator:
            return {"status": "not_initialized"}
        
        return self.orchestrator.get_system_status()
    
    async def run_startup_meeting_async(self, agenda: str) -> Dict[str, Any]:
        """Run a startup meeting asynchronously"""
        if not self.is_initialized or not self.orchestrator:
            return {"success": False, "error": "System not initialized"}
        
        try:
            result = await self.orchestrator.run_startup_meeting(agenda)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Meeting error: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_marketing_campaign_async(self, campaign_details: str) -> Dict[str, Any]:
        """Execute marketing campaign asynchronously"""
        if not self.is_initialized or not self.orchestrator:
            return {"success": False, "error": "System not initialized"}
        
        try:
            result = await self.orchestrator.execute_marketing_campaign(campaign_details)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Campaign error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_financial_report_async(self) -> Dict[str, Any]:
        """Generate financial report asynchronously"""
        if not self.is_initialized or not self.orchestrator:
            return {"success": False, "error": "System not initialized"}
        
        try:
            result = await self.orchestrator.generate_financial_report()
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Financial report error: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_working_session_async(self, start_datetime, end_datetime, duration_minutes: int) -> Dict[str, Any]:
        """Start a working session asynchronously with Notion logging"""
        if not self.is_initialized or not self.orchestrator:
            return {"success": False, "error": "System not initialized"}
        
        try:
            result = await self.orchestrator.start_working_session(start_datetime, end_datetime, duration_minutes)
            
            # Save working session to Notion
            if result["success"] and self.notion_backend:
                try:
                    session_data = {
                        "session_id": result["result"]["session_id"],
                        "start_time": start_datetime.isoformat(),
                        "end_time": end_datetime.isoformat(),
                        "duration": duration_minutes,
                        "is_active": True,
                        "activities": result["result"].get("initial_meeting", {}).get("discussions", {}),
                        "final_summary": None
                    }
                    save_result = self.notion_backend.save_working_session(session_data)
                    if save_result["success"]:
                        logger.info("Working session saved to Notion")
                    else:
                        logger.warning(f"Failed to save working session to Notion: {save_result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Error saving working session to Notion: {e}")
            elif not self.notion_backend:
                logger.info("Notion backend not available - skipping working session save")
            
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"Working session start error: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_working_session_async(self) -> Dict[str, Any]:
        """Run working session asynchronously with Notion logging"""
        if not self.is_initialized or not self.orchestrator:
            return {"success": False, "error": "System not initialized"}
        
        try:
            result = await self.orchestrator.run_working_session()
            
            # Save final session data to Notion
            if result["success"] and self.notion_backend:
                try:
                    # Update the working session with final data
                    working_session = self.orchestrator.working_session
                    session_data = {
                        "session_id": working_session["session_id"],
                        "start_time": working_session["start_time"].isoformat(),
                        "end_time": working_session["end_time"].isoformat(),
                        "duration": working_session["duration_minutes"],
                        "is_active": False,
                        "activities": working_session.get("activities", []),
                        "final_summary": result.get("final_summary", {}).get("summary", "")
                    }
                    
                    save_result = self.notion_backend.save_working_session(session_data)
                    if save_result["success"]:
                        logger.info("Final working session data saved to Notion")
                    else:
                        logger.warning(f"Failed to save final session data to Notion: {save_result.get('error')}")
                        
                    # Save system update
                    self.notion_backend.save_data(
                        "Working Session Completed",
                        f"Session completed with {result.get('activities_count', 0)} activities",
                        "System Update"
                    )
                    
                except Exception as e:
                    logger.error(f"Error saving final session data to Notion: {e}")
            
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"Working session run error: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_working_session(self) -> Dict[str, Any]:
        """Stop the active working session"""
        if not self.is_initialized or not self.orchestrator:
            return {"success": False, "error": "System not initialized"}
        
        try:
            result = self.orchestrator.stop_working_session()
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Working session stop error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_working_session_status(self) -> Dict[str, Any]:
        """Get current working session status"""
        if not self.is_initialized or not self.orchestrator:
            return {"status": "not_initialized"}
        
        try:
            status = self.orchestrator.get_system_status()
            if not status:
                return {"status": "error", "error": "Could not get system status"}
            
            working_session = status.get('working_session')
            if working_session:
                return working_session
            else:
                return {"status": "no_session"}
        except Exception as e:
            logger.error(f"Status error: {e}")
            return {"status": "error", "error": str(e)}

    def save_agent_interaction(self, agent_name: str, topic: str, response: str, tools_used: List[str], session_id: str) -> Dict[str, Any]:
        """Save agent interaction to Notion"""
        if not self.notion_backend:
            return {"success": False, "error": "Notion backend not available"}
        
        try:
            result = self.notion_backend.save_agent_interaction(agent_name, topic, response, session_id)
            if result["success"]:
                logger.info(f"Agent interaction saved to Notion: {agent_name}")
            else:
                logger.warning(f"Failed to save agent interaction to Notion: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error saving agent interaction to Notion: {e}")
            return {"success": False, "error": str(e)}
    
    def get_notion_data(self) -> Dict[str, Any]:
        """Get all data from Notion databases"""
        if not self.notion_backend:
            return {"success": False, "error": "Notion backend not available"}
        
        try:
            data = {
                "startup_configs": self.notion_backend.get_data("Startup Config"),
                "working_sessions": self.notion_backend.get_data("Working Session"),
                "agent_interactions": self.notion_backend.get_data("Agent Interaction"),
                "system_updates": self.notion_backend.get_data("System Update"),
                "success": True
            }
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving Notion data: {e}")
            return {"success": False, "error": str(e)}

def run_async_function(async_func, *args, **kwargs):
    """Helper function to run async functions in Streamlit"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_func(*args, **kwargs))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Async execution error: {e}")
        return {"success": False, "error": str(e)}

def start_working_session(start_datetime, end_datetime, duration_minutes: int):
    """Start a working session from Streamlit"""
    try:
        # Initialize orchestrator
        orchestrator_wrapper = StreamlitOrchestrator()
        
        if not orchestrator_wrapper.initialize_from_session_state():
            return {"success": False, "error": "Failed to initialize orchestrator"}
        
        # Start the working session
        start_result = run_async_function(
            orchestrator_wrapper.start_working_session_async,
            start_datetime, end_datetime, duration_minutes
        )
        
        if start_result["success"]:
            # Start the background working session
            run_result = run_async_function(
                orchestrator_wrapper.run_working_session_async
            )
            
            return {
                "success": True,
                "start_result": start_result["result"],
                "run_result": run_result
            }
        else:
            return start_result
            
    except Exception as e:
        logger.error(f"Error starting working session: {e}")
        return {"success": False, "error": str(e)}

def show_working_session_monitor():
    """Show working session monitoring and status"""
    st.subheader("⏰ Working Session Monitor")
    
    # Initialize orchestrator
    orchestrator_wrapper = StreamlitOrchestrator()
    
    if not orchestrator_wrapper.initialize_from_session_state():
        st.error("❌ System not initialized. Please complete configuration first.")
        return
    
    # Get working session status
    session_status = orchestrator_wrapper.get_working_session_status()
    
    if session_status.get('is_active'):
        st.success("✅ **Active Working Session**")
        
        # Display session info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Session ID", session_status.get('session_id', 'N/A'))
        with col2:
            st.metric("Duration", f"{session_status.get('duration_minutes', 0)} min")
        with col3:
            st.metric("Activities", len(session_status.get('activities', [])))
        
        # Show session details
        with st.expander("📋 Session Details", expanded=True):
            st.write(f"**Start Time:** {session_status.get('start_time')}")
            st.write(f"**End Time:** {session_status.get('end_time')}")
            st.write(f"**Status:** {'Active' if session_status.get('is_active') else 'Completed'}")
        
        # Show recent activities
        activities = session_status.get('activities', [])
        if activities:
            st.subheader("📈 Recent Activities")
            
            for i, activity in enumerate(activities[-5:]):  # Show last 5 activities
                with st.expander(f"Activity {i+1}: {activity.get('type', 'Unknown')}"):
                    if activity.get('type') == 'initial_meeting':
                        st.write("**Initial Team Meeting**")
                        if 'result' in activity and 'summary' in activity['result']:
                            st.write(activity['result']['summary'])
                    elif activity.get('type') == 'agent_interaction':
                        st.write(f"**Topic:** {activity.get('topic', 'Unknown')}")
                        st.write(f"**Interaction:** {activity.get('interaction_number', 'N/A')}")
                        if 'summary' in activity:
                            st.write(f"**Summary:** {activity['summary']}")
        
        # Stop session button
        if st.button("🛑 Stop Working Session", type="secondary"):
            result = orchestrator_wrapper.stop_working_session()
            if result["success"]:
                st.success("✅ Working session stopped. Final documentation will be generated.")
                st.rerun()
            else:
                st.error(f"❌ Failed to stop session: {result['error']}")
    
    else:
        st.info("⏸️ **No Active Working Session**")
        st.write("Start a working session from the main launch page to begin agent collaboration.")
        
        # Show previous session summary if available
        if session_status.get('final_summary'):
            with st.expander("📋 Previous Session Summary"):
                st.write(session_status['final_summary'])

def launch_lazy_preneur():
    """Launch the LazyPreneur system from Streamlit"""
    
    try:
        # Initialize orchestrator
        orchestrator_wrapper = StreamlitOrchestrator()
        
        if not orchestrator_wrapper.initialize_from_session_state():
            st.error("❌ Failed to initialize system. Please check your configuration.")
            return
        
        # Get system status with error handling
        try:
            status = orchestrator_wrapper.get_system_status()
            if not status:
                st.error("❌ Failed to get system status")
                return
        except Exception as e:
            st.error(f"❌ Error getting system status: {str(e)}")
            return
        
        # Display system status
        st.subheader("📊 System Status")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Agents", len(status.get('agents', {})))
        with col2:
            st.metric("Connected Tools", len(status.get('tools', [])))
        with col3:
            st.metric("Slack Channels", status.get('integration_status', {}).get('slack', {}).get('channels_ready', 0))
        with col4:
            st.metric("System Status", status.get('status', 'unknown').title())
        
        # Display integration status
        integration_status = status.get('integration_status', {})
        
        st.subheader("🔗 Integration Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            slack_status = integration_status.get('slack', {})
            if slack_status.get('initialized'):
                st.success("✅ **Slack Ready**")
                st.write(f"Channels: {slack_status.get('channels_ready', 0)}")
                st.write(f"Primary: #{slack_status.get('primary_channel', 'N/A')}")
                st.write(f"Bots: {slack_status.get('bots_available', 0)}")
            else:
                st.warning("⚠️ **Slack Not Ready**")
        
        with col2:
            notion_status = integration_status.get('notion', {})
            if notion_status.get('initialized'):
                st.success("✅ **Notion Ready**")
                st.write(f"Databases: {len(notion_status.get('databases', []))}")
            else:
                st.warning("⚠️ **Notion Not Ready**")
        
        with col3:
            x_status = integration_status.get('x_platform', {})
            if x_status.get('available') and x_status.get('initialized'):
                st.success("✅ **X Platform Ready**")
            elif x_status.get('available'):
                st.warning("⚠️ **X Platform Not Ready**")
            else:
                st.info("ℹ️ **X Platform Not Selected**")
        
        # Display active agents
        st.subheader("👥 Active Agents")
        agents = status.get('agents', {})
        if agents:
            agent_cols = st.columns(3)
            for i, (name, info) in enumerate(agents.items()):
                with agent_cols[i % 3]:
                    st.info(f"**{name}** ({info['role']})")
                    st.write(f"Tools: {', '.join(info['tools'])}")
        else:
            st.warning("⚠️ No agents initialized")
        
        # System Status Information
        st.subheader("🤖 Autonomous Agent Status")
        
        # Get agent status with error handling
        try:
            agent_status = orchestrator_wrapper.orchestrator.get_agent_status()
            
            # Display agent lifecycle status
            col1, col2 = st.columns(2)
            
            with col1:
                if agent_status.get("is_sleeping"):
                    st.warning("💤 **Agents are sleeping**")
                    st.write("Agents are in sleep mode, waiting for next working session")
                else:
                    st.success("🌅 **Agents are awake**")
                    st.write("Agents are ready for autonomous work")
            
            with col2:
                if agent_status.get("working_session_active"):
                    st.success("⏰ **Working session active**")
                    st.write("Agents are actively working")
                else:
                    st.info("⏸️ **No active working session**")
                    st.write("Set up a working session to start autonomous work")
                    
        except Exception as e:
            st.warning(f"⚠️ Could not get agent status: {str(e)}")
        
        st.info("""
        **🎯 LazyPreneur is designed to work autonomously!**
        
        Your AI agents will automatically:
        - 📋 Hold team meetings and strategic discussions
        - 📈 Plan and execute marketing campaigns  
        - 💰 Generate financial reports and analysis
        - 📝 Document all activities in Notion
        - 💬 Communicate via Slack channels
        - 📱 Post to social media when appropriate
        
        **No manual intervention needed** - just set your working session time and let the agents work!
        """)
        
        # Show current working session status if active
        try:
            working_session = orchestrator_wrapper.get_working_session_status()
            if working_session and working_session.get('is_active'):
                st.success(f"✅ **Active Working Session**")
                st.write(f"**Session ID:** {working_session.get('session_id', 'Unknown')}")
                st.write(f"**Started:** {working_session.get('start_time', 'Unknown')}")
                st.write(f"**Ends:** {working_session.get('end_time', 'Unknown')}")
                st.write(f"**Duration:** {working_session.get('duration_minutes', 0)} minutes")
                
                # Show recent activities from Notion if available
                try:
                    notion_data = orchestrator_wrapper.get_notion_data()
                    if notion_data and notion_data.get("success"):
                        recent_activities = notion_data.get("agent_interactions", [])
                        if recent_activities:
                            st.subheader("📈 Recent Agent Activities")
                            for activity in recent_activities[-5:]:  # Show last 5 activities
                                props = activity.get('properties', {})
                                agent_name = props.get('Agent Name', {}).get('select', {}).get('name', 'Unknown')
                                topic = props.get('Topic', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'No topic')
                                st.info(f"🤖 **{agent_name}**: {topic}")
                        else:
                            st.info("📝 No recent activities recorded yet. Agents will start working during the scheduled session.")
                    else:
                        st.info("📝 Activity tracking will be available once agents start working.")
                except Exception as e:
                    st.info("📝 Activity tracking will be available once agents start working.")
            else:
                st.info("⏸️ **No active working session**")
                st.write("Configure a working session in the 'Working Session Configuration' section above to start autonomous agent activities.")
        except Exception as e:
            st.warning(f"⚠️ Could not get working session status: {str(e)}")
            st.info("⏸️ **No active working session**")
            st.write("Configure a working session to start autonomous agent activities.")
            
    except Exception as e:
        st.error(f"❌ Failed to launch system: {str(e)}")
        st.info("Please check your API keys and tool configurations.")
        logger.error(f"Launch error: {e}")

 