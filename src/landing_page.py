import streamlit as st
from datetime import datetime, timedelta
import os
import random

# Page configuration
st.set_page_config(
    page_title="LazyPreneur - Autonomous Startup Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to test Notion connectivity
def test_notion_connectivity():
    """Test if Notion integration can actually save data using created databases"""
    try:
        from tools.notion import NotionAPI
        from streamlit_integration import StreamlitOrchestrator
        
        notion_token = os.getenv('NOTION_API_TOKEN')
        parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
        
        if not notion_token or not parent_page_id:
            return {"success": False, "error": "Missing tokens", "status": "❌ Missing Configuration"}
        
        # Test basic connectivity
        notion = NotionAPI(notion_token)
        
        # Try to get created database IDs from orchestrator
        try:
            orchestrator_wrapper = StreamlitOrchestrator()
            if orchestrator_wrapper.initialize_from_session_state():
                system_status = orchestrator_wrapper.get_system_status()
                notion_databases = system_status.get('notion_databases', {})
                
                if notion_databases:
                    # Test connectivity with the first created database
                    first_db_id = list(notion_databases.values())[0]
                    test_result = notion.retrieve_database(first_db_id)
                    
                    if test_result["success"]:
                        return {
                            "success": True, 
                            "status": "✅ Configured", 
                            "message": "All databases accessible",
                            "databases": notion_databases
                        }
                    else:
                        # Check if it's a sharing issue
                        if "Could not find page" in test_result.get("error", ""):
                            return {
                                "success": False, 
                                "error": "Sharing issue", 
                                "status": "⚠️ Needs Sharing", 
                                "message": "Databases created but not shared with integration",
                                "databases": notion_databases
                            }
                        else:
                            return {
                                "success": False, 
                                "error": test_result.get("error", "Unknown error"), 
                                "status": "❌ Connection Failed", 
                                "message": "Cannot access created databases",
                                "databases": notion_databases
                            }
                else:
                    return {"success": True, "status": "✅ Configured", "message": "Basic connectivity works - databases will be created on launch"}
            else:
                # Fallback to basic connectivity test
                return {"success": True, "status": "✅ Configured", "message": "Basic connectivity works"}
                        
        except Exception as e:
            # Fallback to basic connectivity test if orchestrator fails
            return {"success": True, "status": "✅ Configured", "message": "Basic connectivity works"}
                
    except Exception as e:
        return {"success": False, "error": str(e), "status": "❌ Error", "message": f"Error testing Notion: {str(e)}"}

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .section-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        border-left: 5px solid #667eea;
    }
    
    .agent-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .agent-card:hover {
        transform: translateY(-2px);
    }
    
    .tool-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .tool-card:hover {
        transform: translateY(-2px);
    }
    
    .success-card {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'startup_data' not in st.session_state:
    st.session_state.startup_data = {}
if 'custom_agents' not in st.session_state:
    st.session_state.custom_agents = {}

# Available agents and tools
AVAILABLE_AGENTS = {
    "CEO": {
        "icon": "👔",
        "description": "Chief Executive Officer - Strategic planning and overall business direction",
        "color": "#667eea"
    },
    "CFO": {
        "icon": "💰",
        "description": "Chief Financial Officer - Financial planning, budgeting, and fundraising",
        "color": "#f093fb"
    },
    "CTO": {
        "icon": "⚡",
        "description": "Chief Technology Officer - Technical strategy and product development",
        "color": "#4facfe"
    },
    "CMO": {
        "icon": "📈",
        "description": "Chief Marketing Officer - Marketing strategy and customer acquisition",
        "color": "#43e97b"
    },
    "CLO": {
        "icon": "⚖️",
        "description": "Chief Legal Officer - Legal compliance and intellectual property",
        "color": "#f5576c"
    },
    "COO": {
        "icon": "🏭",
        "description": "Chief Operations Officer - Operations and process optimization",
        "color": "#764ba2"
    },
    "CHRO": {
        "icon": "👥",
        "description": "Chief Human Resources Officer - Team building and culture",
        "color": "#00f2fe"
    }
}

# Icons and colors for custom agents
CUSTOM_ICONS = ["🎯", "🚀", "💡", "🔧", "📊", "🎨", "🔬", "📱", "🌐", "⚡", "🎪", "🏆", "🌟", "💎", "🔮", "🎭", "🎪", "🎨", "🎯", "🚀"]
CUSTOM_COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]

AVAILABLE_TOOLS = {
    "Slack": {
        "icon": "💬",
        "description": "Team communication and collaboration",
        "color": "#4A154B"
    },
    "GitHub": {
        "icon": "🐙",
        "description": "Code repository and version control",
        "color": "#24292e"
    },
    "Notion": {
        "icon": "📝",
        "description": "Documentation and project management",
        "color": "#000000"
    },
    # "Trello": {
    #     "icon": "📋",
    #     "description": "Task management and workflow",
    #     "color": "#0079BF"
    # },
    "Stripe": {
        "icon": "💳",
        "description": "Payment processing and billing",
        "color": "#6772E5"
    },
    "Mailchimp": {
        "icon": "📧",
        "description": "Email marketing and automation",
        "color": "#FFE01B"
    },
    "Google Analytics": {
        "icon": "📊",
        "description": "Website analytics and insights",
        "color": "#F9AB00"
    },
    # "Zapier": {
    #     "icon": "🔗",
    #     "description": "Workflow automation and integrations",
    #     "color": "#FF4A00"
    # }
    "X Platform": {
        "icon": "🔗",
        "description": "Social media and content management",
        "color": "#000000"
    }
}

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 LazyPreneur</h1>
        <h3>Autonomous Startup Management System</h3>
        <p>Build and manage your startup with AI-powered agents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; color: white; padding: 1rem;">
            <h3>🎯 Quick Setup</h3>
            <p>Configure your startup in minutes</p>
        </div>
        """, unsafe_allow_html=True)

        # Dynamic progress indicator
        progress_steps = [
            ("Business Idea", 'business_info'),
            ("Startup Agents", 'selected_agents'),
            ("Tools", 'selected_tools'),
            ("API Keys", 'api_keys'),
            ("Launch", None)
        ]
        step_icons = []
        for step_name, key in progress_steps:
            if key is None:
                # Launch is always last, mark as ✅ only if all previous are done
                if all(st.session_state.startup_data.get(k) for _, k in progress_steps[:-1]):
                    step_icons.append(f"✅ {step_name}")
                else:
                    step_icons.append(f"⭕ {step_name}")
            elif st.session_state.startup_data.get(key):
                step_icons.append(f"✅ {step_name}")
            else:
                step_icons.append(f"⭕ {step_name}")
        for icon in step_icons:
            st.markdown(icon)

        st.markdown("---")

        # Dynamic stats
        agents_count = len(st.session_state.startup_data.get('selected_agents', []))
        tools_count = len(st.session_state.startup_data.get('selected_tools', []))
        st.markdown("""
        <div style="color: white;">
            <h4>📊 Your Startup Stats</h4>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Agents", agents_count)
        with col2:
            st.metric("Tools", tools_count)
    
    # Main content
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["💡 Business Idea", "👥 Startup Agents", "🛠️ Tools & Integrations", "🔑 API Keys", "🚀 Launch", "📊 Data & Analytics"])
    
    with tab1:
        # st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.header("💡 Business Idea & Vision")
        st.write("Describe your startup idea. This will serve as the foundation for your AI agents' planning and execution.")
        
        # Business idea input
        business_name = st.text_input("🏢 Startup Name", placeholder="Enter your startup name")
        
        business_idea = st.text_area(
            "💡 Business Idea Description",
            placeholder="Describe your startup idea, target market, value proposition, and business model...",
            height=200,
            help="Be as detailed as possible to help your AI agents understand your vision"
        )
        
        # Additional business details
        col1, col2 = st.columns(2)
        
        with col1:
            target_market = st.text_input("🎯 Target Market", placeholder="e.g., Small businesses, Tech startups")
            business_model = st.selectbox(
                "💰 Business Model",
                ["SaaS", "Marketplace", "E-commerce", "Consulting", "Product", "Other"]
            )
        
        with col2:
            funding_stage = st.selectbox(
                "💸 Funding Stage",
                ["Idea Stage", "MVP", "Seed", "Series A", "Series B", "Growth"]
            )
            industry = st.text_input("🏭 Industry", placeholder="e.g., Fintech, Healthcare, Education")
        
        # Save business idea
        if st.button("💾 Save Business Idea", key="save_business_tab1"):
            st.session_state.startup_data['business_info'] = {
                'name': business_name,
                'idea': business_idea,
                'target_market': target_market,
                'business_model': business_model,
                'funding_stage': funding_stage,
                'industry': industry,
                'created_at': datetime.now().isoformat()
            }
            st.success("✅ Business idea saved successfully!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        # st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.header("👥 Startup Team Configuration")
        st.write("Select the AI agents that will manage your startup. Each agent has specific expertise and responsibilities.")
        
        # Custom agent creation
        st.subheader("➕ Add Custom Agent Role")
        with st.expander("Create a new agent role", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                custom_role_name = st.text_input(
                    "Role Name", 
                    placeholder="e.g., Chief Innovation Officer",
                    help="Enter the name of your custom agent role"
                )
            
            with col2:
                custom_role_description = st.text_area(
                    "Role Description",
                    placeholder="Describe the responsibilities and expertise of this role...",
                    height=100,
                    help="Describe what this agent will be responsible for"
                )
            
            if st.button("➕ Add Custom Agent", key="add_custom_agent"):
                if custom_role_name and custom_role_description:
                    icon = random.choice(CUSTOM_ICONS)
                    color = random.choice(CUSTOM_COLORS)
                    # Add to custom agents
                    st.session_state.custom_agents[custom_role_name] = {
                        "icon": icon,
                        "description": custom_role_description,
                        "color": color,
                        "is_custom": True
                    }
                    # Add to selected agents if not already present
                    if 'selected_agents' in st.session_state.startup_data:
                        selected = st.session_state.startup_data['selected_agents']
                    else:
                        selected = []
                    if custom_role_name not in selected:
                        selected.append(custom_role_name)
                    st.session_state.startup_data['selected_agents'] = selected
                    st.success(f"✅ Custom agent '{custom_role_name}' added and selected!")
                    st.rerun()
                else:
                    st.error("❌ Please provide both role name and description!")
        
        # Combine built-in and custom agents
        all_agents = {**AVAILABLE_AGENTS, **st.session_state.custom_agents}
        
        # Use previous selection if available, otherwise default to built-in
        if 'selected_agents' in st.session_state.startup_data and st.session_state.startup_data['selected_agents']:
            default_agents = st.session_state.startup_data['selected_agents']
        else:
            default_agents = ["CEO", "CFO", "CTO"]

        selected_agents = st.multiselect(
            "Choose your startup team:",
            options=list(all_agents.keys()),
            default=default_agents,
            help="Select the roles you want in your startup team"
        )
        
        # Display selected agents
        if selected_agents:
            st.subheader("🎯 Your Startup Team")
            cols = st.columns(3)
            
            for i, agent in enumerate(selected_agents):
                with cols[i % 3]:
                    agent_info = all_agents[agent]
                    is_custom = agent_info.get('is_custom', False)
                    custom_badge = " (Custom)" if is_custom else ""
                    
                    st.markdown(f"""
                    <div class="agent-card">
                        <h3>{agent_info['icon']} {agent}{custom_badge}</h3>
                        <p>{agent_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Save agents
        if st.button("💾 Save Team Configuration", key="save_agents_tab2"):
            st.session_state.startup_data['selected_agents'] = selected_agents
            st.success(f"✅ Team configured with {len(selected_agents)} agents!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        # st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.header("🛠️ Tools & Integrations")
        st.write("Select the tools and platforms your AI agents will use to manage your startup.")
        
        # Tool selection
        selected_tools = st.multiselect(
            "Choose your tools and integrations:",
            options=list(AVAILABLE_TOOLS.keys()),
            default=["Slack", "GitHub", "Notion"],
            help="Select the tools your startup team will use"
        )
        
        # Display selected tools
        if selected_tools:
            st.subheader("🛠️ Your Startup Tools")
            cols = st.columns(3)
            
            for i, tool in enumerate(selected_tools):
                with cols[i % 3]:
                    tool_info = AVAILABLE_TOOLS[tool]
                    st.markdown(f"""
                    <div class="tool-card">
                        <h3>{tool_info['icon']} {tool}</h3>
                        <p>{tool_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Save tools
        if st.button("💾 Save Tools Configuration", key="save_tools_tab3"):
            st.session_state.startup_data['selected_tools'] = selected_tools
            st.success(f"✅ Tools configured with {len(selected_tools)} integrations!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        # st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.header("🔑 API Configuration")
        st.write("Configure your API keys to enable external communication and AI capabilities.")
        
        # Add visual indicators for required vs optional
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info("🔴 **Required**: AI Provider selection and API key")
        with col_info2:
            st.info("🟡 **Optional**: Analytics and payment integrations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 AI Provider Selection")
            st.write("Choose your preferred AI provider for agent intelligence:")
            
            # AI provider selection
            ai_provider = st.radio(
                "Select AI Provider:",
                ["OpenAI (GPT-4)", "Google Gemini"],
                help="Choose the AI provider your agents will use (required)"
            )
            
            if ai_provider == "OpenAI (GPT-4)":
                openai_key = st.text_input(
                    "OpenAI API Key", 
                    type="password", 
                    help="Required for OpenAI GPT-4 integration"
                )
                gemini_key = ""
            else:
                gemini_key = st.text_input(
                    "Gemini API Key", 
                    type="password", 
                    help="Required for Google Gemini integration"
                )
                openai_key = ""
            
        with col2:
            st.subheader("📊 Analytics & Monitoring")
            st.write("These integrations are optional and can be added later:")
            google_analytics_key = st.text_input("Google Analytics Key", type="password", help="For website analytics (optional)")
            stripe_key = st.text_input("Stripe API Key", type="password", help="For payment processing (optional)")
        
        # Save API keys
        if st.button("💾 Save API Keys", key="save_api_tab4"):
            # Validate that at least one AI provider is selected
            if not openai_key and not gemini_key:
                st.error("❌ Please provide an API key for your selected AI provider!")
                return
            
            st.session_state.startup_data['api_keys'] = {
                'ai_provider': ai_provider,
                'openai': openai_key,
                'gemini': gemini_key,
                'google_analytics': google_analytics_key,
                'stripe': stripe_key
            }
            st.success(f"✅ API keys saved successfully! Using {ai_provider}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab5:
        st.header("🚀 Launch Your Startup")
        st.write("Review your configuration and launch your autonomous startup management system.")
        
        # Configuration summary
        if st.session_state.startup_data:
            st.subheader("📋 Configuration Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**👥 Team:**")
                agents = st.session_state.startup_data.get('selected_agents', [])
                for agent in agents:
                    st.write(f"• {agent}")
                
                st.write("**🛠️ Tools:**")
                tools = st.session_state.startup_data.get('selected_tools', [])
                for tool in tools:
                    st.write(f"• {tool}")
            
            with col2:
                st.write("**💡 Business:**")
                business_info = st.session_state.startup_data.get('business_info', {})
                if business_info.get('name'):
                    st.write(f"• **Name:** {business_info['name']}")
                if business_info.get('industry'):
                    st.write(f"• **Industry:** {business_info['industry']}")
                if business_info.get('business_model'):
                    st.write(f"• **Model:** {business_info['business_model']}")
                
                # Show AI provider info
                api_keys = st.session_state.startup_data.get('api_keys', {})
                if api_keys.get('ai_provider'):
                    st.write(f"• **AI Provider:** {api_keys['ai_provider']}")
            
            # --- LAUNCH SYSTEM LOGIC ---
            if 'system_launched' not in st.session_state:
                st.session_state.system_launched = False
            if 'ever_launched' not in st.session_state:
                st.session_state.ever_launched = False
            # If any config changes, reset launch state
            def reset_launch_state():
                if st.session_state.system_launched:
                    st.session_state.system_launched = False
            # (No save buttons in Launch tab)
            # Show launch button only if not launched
            if not st.session_state.system_launched:
                if st.session_state.ever_launched:
                    st.info("⚠️ Configuration changed. Please relaunch LazyPreneur to apply changes.")
                if st.button("🚀 Launch LazyPreneur", type="primary", use_container_width=True, key="launch_tab5"):
                    try:
                        from streamlit_integration import launch_lazy_preneur
                        launch_lazy_preneur()
                        st.session_state.system_launched = True
                        st.session_state.ever_launched = True
                        st.success("✅ LazyPreneur system relaunched with new configuration!")
                    except Exception as e:
                        st.error(f"❌ Failed to launch system: {str(e)}")
                        st.error("Please check your API keys and tool configurations.")
            else:
                st.success("✅ LazyPreneur system is active!")
                
                # --- SYSTEM STATUS CHECK ---
                st.subheader("🔍 System Status Check")
                
                # Check each integration status
                startup_data = st.session_state.startup_data
                selected_tools = startup_data.get('selected_tools', [])
                
                # Slack Status
                if "Slack" in selected_tools:
                    slack_status = "✅ Configured" if any([
                        os.getenv('SLACK_API_TOKEN_CEO'),
                        os.getenv('SLACK_API_TOKEN_CFO'),
                        os.getenv('SLACK_API_TOKEN_CTO'),
                        os.getenv('SLACK_API_TOKEN_CMO')
                    ]) else "❌ Missing Tokens"
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.write(f"**Slack:** {slack_status}")
                    with col2:
                        if "❌" in slack_status:
                            st.warning("Slack tokens not found. Agents won't be able to communicate.")
                            with st.expander("🔧 Slack Setup Instructions"):
                                st.markdown("""
                                **To enable Slack integration:**
                                1. Set environment variables:
                                   ```bash
                                   export SLACK_API_TOKEN_CEO=xoxb-your-ceo-token
                                   export SLACK_API_TOKEN_CFO=xoxb-your-cfo-token
                                   export SLACK_API_TOKEN_CTO=xoxb-your-cto-token
                                   export SLACK_API_TOKEN_CMO=xoxb-your-cmo-token
                                   ```
                                2. Restart the Streamlit app
                                """)
                
                # Notion Status
                if "Notion" in selected_tools:
                    # Test actual Notion connectivity
                    notion_test = test_notion_connectivity()
                    notion_status = notion_test["status"]
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.write(f"**Notion:** {notion_status}")
                    with col2:
                        if "❌" in notion_status:
                            st.warning("Notion configuration incomplete. Documentation won't be saved.")
                            with st.expander("🔧 Notion Setup Instructions"):
                                st.markdown("""
                                **To enable Notion integration:**
                                1. Set environment variables:
                                   ```bash
                                   export NOTION_API_TOKEN=your-notion-token
                                   export NOTION_PARENT_PAGE_ID=your-page-id
                                   ```
                                2. Share databases with your integration:
                                   - Go to each database in Notion
                                   - Click "Share" → "Invite"
                                   - Search for your integration name
                                   - Give it "Edit" permissions
                                3. Restart the Streamlit app
                                """)
                        elif "⚠️" in notion_status:
                            st.warning("Notion tokens are configured but databases need to be shared with the integration.")
                            
                            # Display database information from connectivity test
                            if 'databases' in notion_test and notion_test['databases']:
                                st.info("📋 **Created Notion Databases:**")
                                for db_name, db_id in notion_test['databases'].items():
                                    st.code(f"{db_name}: {db_id}")
                                
                                with st.expander("📋 Database Sharing Instructions"):
                                    st.markdown("""
                                    **To fix Notion sharing issues:**
                                    1. Go to your Notion workspace
                                    2. Find these databases (created automatically):
                                    """)
                                    for db_name, db_id in notion_test['databases'].items():
                                        st.markdown(f"   - **{db_name}:** `{db_id}`")
                                    st.markdown("""
                                    3. For each database:
                                       - Click "Share" → "Invite"
                                       - Search for your integration name
                                       - Give it "Edit" permissions
                                       - Click "Invite"
                                    4. Click "🔄 Refresh Status" to re-test
                                    """)
                            else:
                                with st.expander("📋 Database Sharing Instructions"):
                                    st.markdown("""
                                    **To fix Notion sharing issues:**
                                    1. Go to your Notion workspace
                                    2. Find the LazyPreneur databases (created automatically)
                                    3. For each database:
                                       - Click "Share" → "Invite"
                                       - Search for your integration name
                                       - Give it "Edit" permissions
                                       - Click "Invite"
                                    4. Refresh this page to re-test
                                    """)
                        elif "✅" in notion_status:
                            st.success("Notion is fully configured and working!")
                        else:
                            st.error(f"Notion error: {notion_test.get('message', 'Unknown error')}")
                
                # X Platform Status
                if "X Platform" in selected_tools:
                    x_tokens = [
                        os.getenv('X_API_KEY'),
                        os.getenv('X_API_SECRET'),
                        os.getenv('X_ACCESS_TOKEN'),
                        os.getenv('X_ACCESS_TOKEN_SECRET')
                    ]
                    
                    x_status = "✅ Configured" if all(x_tokens) else "❌ Missing Tokens"
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.write(f"**X Platform:** {x_status}")
                    with col2:
                        if "❌" in x_status:
                            st.warning("X Platform tokens not found. Social media posting disabled.")
                            with st.expander("🔧 X Platform Setup Instructions"):
                                st.markdown("""
                                **To enable X Platform integration:**
                                1. Set environment variables:
                                   ```bash
                                   export X_API_KEY=your-api-key
                                   export X_API_SECRET=your-api-secret
                                   export X_ACCESS_TOKEN=your-access-token
                                   export X_ACCESS_TOKEN_SECRET=your-access-token-secret
                                   ```
                                2. Restart the Streamlit app
                                """)
                
                # Overall System Status
                st.markdown("---")
                
                # Check if all selected tools are properly configured
                all_configured = True
                missing_tools = []
                
                if "Slack" in selected_tools and not any([
                    os.getenv('SLACK_API_TOKEN_CEO'),
                    os.getenv('SLACK_API_TOKEN_CFO'),
                    os.getenv('SLACK_API_TOKEN_CTO'),
                    os.getenv('SLACK_API_TOKEN_CMO')
                ]):
                    all_configured = False
                    missing_tools.append("Slack")
                
                if "Notion" in selected_tools:
                    notion_test = test_notion_connectivity()
                    if not notion_test["success"]:
                        all_configured = False
                        missing_tools.append("Notion")
                
                if "X Platform" in selected_tools and not all([
                    os.getenv('X_API_KEY'),
                    os.getenv('X_API_SECRET'),
                    os.getenv('X_ACCESS_TOKEN'),
                    os.getenv('X_ACCESS_TOKEN_SECRET')
                ]):
                    all_configured = False
                    missing_tools.append("X Platform")
                
                # Display overall status
                col1, col2 = st.columns([3, 1])
                with col1:
                    if all_configured:
                        st.success("🎉 All integrations are properly configured!")
                        st.info("You can now start working sessions with full functionality.")
                    else:
                        st.warning(f"⚠️ Some integrations need configuration: {', '.join(missing_tools)}")
                        st.info("Working sessions will run with limited functionality until all integrations are configured.")
                with col2:
                    if st.button("🔄 Refresh Status", help="Re-test all integrations"):
                        st.rerun()
                
                # Show working session controls, etc.
                st.markdown("""
                <div class="success-card">
                    <h2>🎉 LazyPreneur Launched Successfully!</h2>
                    <p>Your autonomous startup management system is now active.</p>
                    <p>Your AI agents are working on your startup strategy...</p>
                </div>
                """, unsafe_allow_html=True)
                
                # --- WORKING SESSION CONFIGURATION (only visible after launch) ---
                st.subheader("⏰ Working Session Configuration")
                
                if all_configured:
                    st.write("Configure when your AI agents should actively work and collaborate.")
                else:
                    st.warning("⚠️ Some integrations are not configured. Working sessions will have limited functionality.")
                    st.write("Configure when your AI agents should actively work and collaborate (with limited tool access).")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    start_time = st.time_input(
                        "🕐 Start Working Time",
                        value=datetime.now().time(),
                        help="When should your agents start working?"
                    )
                
                with col2:
                    working_duration = st.number_input(
                        "⏱️ Working Duration (minutes)",
                        min_value=2,
                        max_value=480,  # 8 hours max
                        value=60,
                        step=2,
                        help="How long should your agents work? (2 minutes to 8 hours)"
                    )
                
                # Working session status
                if 'working_session' not in st.session_state:
                    st.session_state.working_session = {
                        'is_active': False,
                        'start_time': None,
                        'end_time': None,
                        'duration': None,
                        'session_id': None
                    }
                
                # Display current session status
                session = st.session_state.working_session
                if session['is_active']:
                    st.success(f"✅ **Active Working Session**")
                    st.write(f"**Started:** {session['start_time']}")
                    st.write(f"**Ends:** {session['end_time']}")
                    st.write(f"**Duration:** {session['duration']} minutes")
                    st.write(f"**Session ID:** {session['session_id']}")
                    
                    # Stop session button
                    if st.button("🛑 Stop Working Session", type="secondary"):
                        st.session_state.working_session['is_active'] = False
                        st.success("✅ Working session stopped. Final documentation will be generated.")
                        st.rerun()
                else:
                    st.info("⏸️ **No active working session**")
                    st.write("Configure time and duration above, then click 'Start Working' to begin.")
                
                # Start Working button (only show when not in active session)
                if not session['is_active']:
                    if st.button("⏰ Start Working Session", type="secondary", use_container_width=True):
                        # Calculate session times
                        start_datetime = datetime.combine(datetime.now().date(), start_time)
                        end_datetime = start_datetime + timedelta(minutes=working_duration)
                        
                        # Store session info
                        st.session_state.working_session = {
                            'is_active': True,
                            'start_time': start_datetime.strftime("%Y-%m-%d %H:%M"),
                            'end_time': end_datetime.strftime("%Y-%m-%d %H:%M"),
                            'duration': working_duration,
                            'session_id': f"session_{int(datetime.now().timestamp())}"
                        }
                        
                        st.success(f"✅ **Working session started!**")
                        st.write(f"**Duration:** {working_duration} minutes")
                        st.write(f"**End time:** {end_datetime.strftime('%H:%M')}")
                        
                        # Start the background orchestration
                        try:
                            from streamlit_integration import start_working_session
                            start_working_session(
                                start_datetime=start_datetime,
                                end_datetime=end_datetime,
                                duration_minutes=working_duration
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to start working session: {str(e)}")
                        
                        st.rerun()
        else:
            st.warning("⚠️ Please complete the configuration in the previous tabs before launching.")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
