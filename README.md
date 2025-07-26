# 🚀 LazyPreneur - Autonomous Startup Management System

A comprehensive AI-powered system that manages startups autonomously through intelligent agents, each representing different executive roles (CEO, CFO, CTO, CMO, etc.) and integrating with popular business tools.

## 🎯 Overview

LazyPreneur is an autonomous startup management system that:

- **Creates AI agents** for different startup roles (CEO, CFO, CTO, CMO, custom roles)
- **Integrates with business tools** (Slack, Notion, X Platform, GitHub, etc.)
- **Orchestrates agent interactions** through meetings, campaigns, and reports
- **Provides a beautiful Streamlit UI** for easy configuration and monitoring
- **Supports time-based working sessions** where agents collaborate autonomously

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Orchestrator  │    │   Tool APIs     │
│                 │    │                 │    │                 │
│ • Configuration │◄──►│ • Agent Manager │◄──►│ • Slack API     │
│ • Dashboard     │    │ • Tool Manager  │    │ • Notion API    │
│ • Monitoring    │    │ • AI Client     │    │ • X Platform    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Agents     │
                       │                 │
                       │ • CEO Agent     │
                       │ • CFO Agent     │
                       │ • CTO Agent     │
                       │ • CMO Agent     │
                       │ • Custom Agents │
                       └─────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic-hackathon-jwt

# Install dependencies
pip install -r requirements_streamlit.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure API Keys

Set up your environment variables:

```bash
# AI Provider (choose one)
export OPENAI_API_KEY="your-openai-key"
# OR
export GOOGLE_API_KEY="your-gemini-key"

# Tool Integrations
export NOTION_API_TOKEN="your-notion-token"
export NOTION_PARENT_PAGE_ID="your-notion-page-id"

# Slack (for each agent)
export SLACK_API_TOKEN_CEO="your-ceo-slack-token"
export SLACK_API_TOKEN_CFO="your-cfo-slack-token"
export SLACK_API_TOKEN_CTO="your-cto-slack-token"
export SLACK_API_TOKEN_CMO="your-cmo-slack-token"

# X Platform
export X_API_KEY="your-x-api-key"
export X_API_SECRET="your-x-api-secret"
export X_ACCESS_TOKEN="your-x-access-token"
export X_ACCESS_TOKEN_SECRET="your-x-access-token-secret"
```

### 3. Run the Application

```bash
# Start the Streamlit app
streamlit run src/landing_page.py
```

### 4. Configure Your Startup

1. **Business Idea**: Describe your startup concept
2. **Startup Agents**: Select and configure AI agents
3. **Tools & Integrations**: Choose business tools
4. **API Keys**: Configure your API credentials
5. **Launch**: Start your autonomous startup!

### 5. Working Sessions

1. **Set Working Time**: Choose when agents should start working
2. **Set Duration**: Specify how long agents should collaborate (2 min - 8 hours)
3. **Start Session**: Launch time-based agent orchestration
4. **Monitor Progress**: Watch agents work in real-time
5. **Review Results**: Check final documentation and summaries

## 🎭 Agent Roles

### Built-in Agents

| Agent | Role | Responsibilities | Tools |
|-------|------|------------------|-------|
| **CEO** | Chief Executive Officer | Strategic planning, business direction | Slack, Notion |
| **CFO** | Chief Financial Officer | Financial planning, budgeting, fundraising | Slack, Notion |
| **CTO** | Chief Technology Officer | Technical strategy, product development | Slack, Notion, GitHub |
| **CMO** | Chief Marketing Officer | Marketing strategy, customer acquisition | Slack, Notion, X Platform |

### Custom Agents

You can create custom agents with:
- Custom role names and descriptions
- Auto-assigned icons and colors
- Configurable tool access

## 🛠️ Tool Integrations

### Available Tools

| Tool | Purpose | API Status |
|------|---------|------------|
| **Slack** | Team communication and collaboration | ✅ Implemented |
| **Notion** | Documentation and project management | ✅ Implemented |
| **X Platform** | Social media and content management | ✅ Implemented |
| **GitHub** | Code repository and version control | 🔄 Planned |
| **Stripe** | Payment processing and billing | 🔄 Planned |
| **Mailchimp** | Email marketing and automation | 🔄 Planned |

### Tool Setup Guides

#### Slack Setup
1. Create a Slack app at https://api.slack.com/apps
2. Add required scopes: `channels:read`, `channels:write`, `chat:write`, `team:read`, `admin.users:write`, `channels:manage`
3. Install the app to your workspace
4. Generate OAuth tokens for each agent

#### Notion Setup
1. Create an integration at https://www.notion.so/my-integrations
2. Copy the Internal Integration Token
3. Share a page with your integration
4. Get the page ID from the URL

#### X Platform Setup
1. Create an app at https://developer.x.com
2. Set permissions to "Read and Write"
3. Generate OAuth 1.0a credentials
4. Add callback URI and website URL

## 🔄 Agent Interactions

### Working Session Flow
1. **Session Configuration**: User sets start time and duration
2. **Initial Meeting**: Agents meet to set agenda and goals
3. **Periodic Interactions**: Agents collaborate every 15 minutes (or custom interval)
4. **Real-time Communication**: Agents discuss via Slack channels
5. **Continuous Documentation**: All discussions saved to Notion
6. **Final Summary**: Comprehensive session summary generated
7. **Action Items**: Next steps and decisions documented

### Meeting Flow
1. **Agenda Input**: User provides meeting agenda
2. **Agent Discussion**: Each agent provides input based on their role
3. **Slack Communication**: Agents discuss in dedicated channels
4. **Notion Documentation**: Decisions and plans are documented
5. **Summary Generation**: CEO generates meeting summary

### Marketing Campaign Flow
1. **Campaign Planning**: CMO creates comprehensive campaign plan
2. **Notion Documentation**: Plan is documented in Notion
3. **Social Media Posts**: CMO creates and posts to X Platform
4. **Status Updates**: Campaign status shared in Slack

### Financial Report Flow
1. **Analysis**: CFO analyzes business data
2. **Report Generation**: Comprehensive financial report created
3. **Documentation**: Report stored in Notion
4. **Team Communication**: Highlights shared with executive team

## 📁 Project Structure

```
src/
├── landing_page.py              # Main Streamlit UI
├── orchestrator.py              # Core agent orchestration
├── streamlit_integration.py     # Streamlit-orchestrator bridge
├── notion_backend.py            # Notion data persistence
├── tools/
│   ├── notion.py                # Notion API integration
│   ├── slack.py                 # Slack API integration
│   └── x.py                     # X Platform API integration
├── utils/
│   └── cleanup_slack.py         # Slack cleanup utilities
└── tests/
    ├── test_notion.py           # Notion API tests
    └── test_x_api.py            # X Platform API tests
```

## 🧪 Testing

### Run Tests

```bash
# Test Notion API
python src/tools/test_notion.py

# Test X Platform API
python src/tools/test_x_api.py

# Clean up test Slack channels
python src/utils/cleanup_slack.py
```

### Test Coverage

- ✅ Agent creation and configuration
- ✅ Tool integration setup
- ✅ Streamlit integration components
- ✅ Orchestrator initialization
- ✅ API connectivity tests

## 🚀 Advanced Features

### Time-Based Working Sessions
```python
# Example: Starting a working session
start_time = datetime.now()
end_time = start_time + timedelta(minutes=60)

result = await orchestrator.start_working_session(
    start_datetime=start_time,
    end_datetime=end_time,
    duration_minutes=60
)

# Run the session with periodic interactions
session_result = await orchestrator.run_working_session()
```

### Custom Agent Creation
```python
# Example: Creating a custom agent
custom_agent = AgentConfig(
    name="Chief Innovation Officer",
    role="Innovation Strategy",
    description="Drives innovation and R&D initiatives",
    icon="💡",
    color="#FF6B6B",
    is_custom=True,
    tools=["slack", "notion", "github"]
)
```

### Sleep/Wake Cycle
The system implements intelligent agent lifecycle management:
- **Sleep Mode**: Agents stop reinitializing when not in working sessions
- **Wake Mode**: Agents activate when working sessions begin
- **Resource Optimization**: Prevents unnecessary API calls and reinitialization

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes (if using OpenAI) |
| `GOOGLE_API_KEY` | Google Gemini API key | Yes (if using Gemini) |
| `NOTION_API_TOKEN` | Notion integration token | Yes (if using Notion) |
| `NOTION_PARENT_PAGE_ID` | Notion parent page ID | Yes (if using Notion) |
| `SLACK_API_TOKEN_*` | Slack OAuth tokens | Yes (if using Slack) |
| `X_*` | X Platform credentials | Yes (if using X Platform) |

### Streamlit Configuration

The app uses Streamlit session state to store:
- Business information
- Selected agents and tools
- API keys
- Custom agent configurations
- Working session status

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify API keys are correctly set
   - Check API key permissions
   - Ensure proper environment variable names

2. **Tool Integration Failures**
   - Verify tool credentials
   - Check API rate limits
   - Ensure proper scopes/permissions

3. **Agent Communication Issues**
   - Check Slack channel creation
   - Verify agent tokens
   - Ensure channels are accessible

4. **Notion Duplicate Entries**
   - The system now prevents duplicate page creation
   - Check existing pages before creating new ones

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🧹 Cleanup

### Slack Channel Cleanup
```bash
# Clean up test channels
python src/utils/cleanup_slack.py
```

This utility will archive channels created during testing.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Acknowledgments

- Built with Streamlit for the UI
- Powered by OpenAI GPT-4 and Google Gemini
- Integrated with popular business tools
- Designed for autonomous startup management

---

**Ready to launch your autonomous startup?** 🚀

Run `streamlit run src/landing_page.py` and start building your AI-powered startup team!


