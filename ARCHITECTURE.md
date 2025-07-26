# 🏗️ LazyPreneur System Architecture

## Overview

LazyPreneur is a multi-agent autonomous startup management system built with a modular architecture that separates concerns between UI, orchestration, agents, and tool integrations.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT UI LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  landing_page.py                    streamlit_integration.py               │
│  • User Configuration               • Streamlit-Orchestrator Bridge        │
│  • Business Idea Input              • Async Wrappers                       │
│  • Agent Selection                  • Session State Management             │
│  • Tool Configuration               • Working Session Controls             │
│  • API Key Management               • Status Monitoring                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  orchestrator.py                                                           │
│  • StartupOrchestrator Class                                               │
│  • Agent Lifecycle Management                                              │
│  • Tool Integration Management                                             │
│  • Working Session Orchestration                                           │
│  • Sleep/Wake Cycle Management                                             │
│  • Stateful Integration Management                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AGENT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Agent Class                                                               │
│  • AgentConfig (dataclass)                                                 │
│  • Role-based System Prompts                                               │
│  • Tool Integration Methods                                                │
│  • Communication Methods                                                   │
│  • Documentation Methods                                                   │
│  • Social Media Methods                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TOOL INTEGRATION LAYER                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  tools/                    notion_backend.py                               │
│  ├── slack.py              • NotionBackend Class                          │
│  ├── notion.py             • Database Management                          │
│  └── x.py                  • Data Persistence                             │
│                            • Duplicate Prevention                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL APIs                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  • OpenAI GPT-4 API        • Slack Web API                                │
│  • Google Gemini API       • Notion API                                   │
│  • X Platform API          • GitHub API (planned)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. **Planner Component**

The planning system is distributed across multiple layers:

#### **High-Level Planning (Orchestrator)**
```python
class StartupOrchestrator:
    async def start_working_session(self, start_datetime, end_datetime, duration_minutes)
    async def run_working_session(self)
    async def run_startup_meeting(self, agenda)
    async def execute_marketing_campaign(self, campaign_details)
    async def generate_financial_report(self)
```

#### **Agent-Level Planning**
```python
class Agent:
    async def think(self, context: str) -> str
    def get_system_prompt(self) -> str
```

**Planning Strategy:**
- **Time-based orchestration**: Sessions are divided into intervals (15-minute default)
- **Role-based planning**: Each agent has specific responsibilities and planning context
- **Conversational planning**: Agents build on previous responses in a discussion format
- **Context-aware planning**: Agents consider business context, previous decisions, and current state

### 2. **Executor Component**

The executor handles task execution through multiple mechanisms:

#### **AI Client Execution**
```python
# OpenAI Execution
response = self.ai_client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": context}],
    max_tokens=500
)

# Gemini Execution (Direct HTTP)
response = requests.post(self.url, headers=self.headers, json=data)
```

#### **Tool Execution**
```python
# Slack Communication
async def communicate(self, message: str, channel: str) -> Dict

# Notion Documentation
async def document(self, content: str, title: str, database_id: str) -> Dict

# X Platform Posting
async def post_social(self, message: str) -> Dict
```

#### **Session Execution**
```python
async def _run_agent_interaction(self, topic: str, interaction_number: int, total_interactions: int)
async def _generate_session_summary(self, activities: List[Dict])
```

### 3. **Memory Structure**

The system uses a multi-layered memory approach:

#### **Session State Memory (Streamlit)**
```python
st.session_state.startup_data = {
    'business_info': {...},
    'selected_agents': [...],
    'selected_tools': [...],
    'api_keys': {...},
    'custom_agents': {...}
}
```

#### **Notion Persistent Memory**
```python
class NotionBackend:
    def save_data(self, title: str, content: str, data_type: str)
    def save_startup_config(self, startup_data: Dict)
    def save_working_session(self, session_data: Dict)
    def save_agent_interaction(self, agent_name: str, topic: str, response: str)
```

#### **Agent Conversation Memory**
```python
class Agent:
    self.conversation_history = []
    self.task_queue = []
```

#### **Orchestrator State Memory**
```python
class StartupOrchestrator:
    self.slack_channels = {}  # Cache created Slack channels
    self.notion_databases = {}  # Store created database IDs
    self.working_session = {...}  # Current session state
```

## Tool Integrations

### **Slack Integration**
```python
class Slack:
    def create_slack_channel(self, channel_name: str) -> Dict
    def send_slack_message(self, channel_name: str, bot_name: str, msg: str) -> Dict
    def join_channel(self, channel_name: str) -> Dict
    def archive_channel(self, channel_name: str) -> Dict

class SlackBotManager:
    def add_bot(self, bot_name: str, token: str)
    def get_bot(self, bot_name: str) -> Slack
```

**Features:**
- Multi-bot support (CEO, CFO, CTO, CMO)
- Auto-channel creation and team invitation
- Idempotent channel creation
- Centralized discussion channel

### **Notion Integration**
```python
class NotionAPI:
    def create_database(self, parent_page_id: str, title: str, properties: Dict) -> Dict
    def create_page(self, parent_id: str, properties: Dict, content: Optional[List], is_database: bool) -> Dict
    def query_database(self, database_id: str, filter_params: Optional[Dict], sort_params: Optional[List]) -> Dict
    def search_databases(self, query: str) -> Dict

class NotionBackend:
    def _setup_main_database(self)
    def _find_existing_database(self, database_name: str) -> Optional[str]
    def save_data(self, title: str, content: str, data_type: str) -> Dict
```

**Features:**
- Duplicate prevention by title checking
- Single database architecture for simplicity
- Automatic database creation and management
- Rich text and structured data support

### **X Platform Integration**
```python
class XPlatform:
    def post_x_msg(self, msg: str) -> Dict
    def get_x_post_stats(self) -> Dict
```

**Features:**
- OAuth 1.0a authentication
- Rate limiting with exponential backoff
- Error handling and retry mechanisms
- Character limit enforcement

### **AI Provider Integration**
```python
# OpenAI Integration
openai.api_key = openai_key
self.ai_client = openai

# Gemini Integration
class GeminiClient:
    def __init__(self, api_key: str)
    def generate_content(self, prompt: str) -> str
```

## Logging and Observability

### **Structured Logging**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Usage throughout the system
logger.info("✅ Channel #{channel_name} ready (created by {creator})")
logger.warning(f"⚠️ {agent_name} failed to post to Slack: {error}")
logger.error(f"Error in agent thinking: {e}")
```

### **Status Monitoring**
```python
def get_system_status(self) -> Dict:
    return {
        "agents": {...},
        "tools": [...],
        "notion_database": bool,
        "status": "active" | "sleeping",
        "working_session": {...},
        "agent_status": {...},
        "integration_status": {...}
    }
```

### **Error Handling**
```python
# Comprehensive try-catch blocks
try:
    result = await agent.think(discussion_context)
except Exception as e:
    logger.error(f"Error with agent {agent_name}: {e}")
    meeting_results["discussions"][agent_name] = f"Error: {str(e)}"
```

### **Fallback Mechanisms**
```python
async def _fallback_slack_post(self, agent_name: str, message: str):
    # Try multiple channels if primary fails
    channels_to_try = [self.primary_discussion_channel] + [other_channels]
```

## Data Flow Architecture

### **Configuration Flow**
```
User Input → Streamlit UI → Session State → Orchestrator → Agent Configuration
```

### **Working Session Flow**
```
Session Start → Agent Wake-up → Initial Meeting → Periodic Interactions → Final Summary → Sleep
```

### **Communication Flow**
```
Agent Think → Slack Post → Notion Document → X Platform Post (if applicable)
```

### **Memory Persistence Flow**
```
Agent Interaction → NotionBackend → Notion API → Database Storage
```

## Scalability Considerations

### **Horizontal Scaling**
- Stateless agent design allows multiple instances
- Database-driven state management
- Tool integrations are stateless

### **Vertical Scaling**
- Async/await patterns for concurrent operations
- Efficient memory usage with session state
- Intelligent sleep/wake cycles

### **Performance Optimizations**
- Idempotent operations prevent duplicate work
- Caching of created resources (channels, databases)
- Rate limiting and retry mechanisms
- Duplicate prevention in data storage

## Security Architecture

### **API Key Management**
- Environment variable-based configuration
- No hardcoded credentials
- Secure token handling

### **Access Control**
- Tool-specific authentication
- Role-based agent permissions
- Channel-based communication isolation

### **Data Privacy**
- Local session state management
- Secure API communication
- No persistent credential storage

## Deployment Architecture

### **Development Environment**
```
Local Machine → Streamlit App → Local Environment Variables → External APIs
```

### **Production Considerations**
- Containerization with Docker
- Environment variable management
- API rate limit monitoring
- Error tracking and alerting
- Database backup strategies

