# 🎯 Master WhatsWorking Platform

A unified system that enforces **Goal-First Thinking**, **Validation Gates**, **Critical Path Focus**, **Architectural Decision Tracking**, and **Health Monitoring** for LLMs through MCP integration.

This platform consolidates the best functionality from scattered `whatsworking` implementations into a cohesive, methodology-driven system.

## 🏗️ Architecture

```
whatsworking_platform/
├── core/                    # Core engine and data models
│   ├── engine.py           # Main orchestrator
│   ├── models.py           # Data structures
│   └── config.py           # Configuration management
├── collectors/              # Data collection modules
│   ├── codebase_analyzer.py # AST-based code analysis
│   ├── feature_tracker.py   # Feature usage tracking
│   └── infrastructure_monitor.py # Infrastructure monitoring
├── cli/                     # Command-line interface
│   └── main.py             # CLI implementation
├── integration/             # External integrations
│   └── mcp_server.py       # MCP server for LLM integration
└── main.py                  # Main entry point
```

## 🚀 Quick Start

### 1. Initialize the Platform

```bash
python -m whatsworking_platform.main init
```

### 2. Set a Project Goal

```bash
python -m whatsworking_platform.main goal "Implement MCP server integration"
```

### 3. Run Analysis

```bash
python -m whatsworking_platform.main analyze
```

### 4. Check Status

```bash
python -m whatsworking_platform.main status
```

### 5. Add Critical Path Items

```bash
python -m whatsworking_platform.main critical "Fix authentication bug"
```

## 🎯 Methodology Enforcement

The platform enforces five core principles:

### 1. **Goal-First Thinking**

- All actions must align with the current project goal
- Prevents scope creep and misaligned work
- Forces focus on high-impact activities

### 2. **Validation Gates**

- Actions must pass through required checkpoints
- Ensures quality and compliance
- Prevents premature implementation

### 3. **Critical Path Focus**

- Prioritizes work on critical path items
- Maximizes project velocity
- Identifies and addresses blockers

### 4. **Architectural Decision Tracking**

- Documents all architectural decisions
- Records rationale and impact assessment
- Maintains decision history

### 5. **Health Monitoring**

- Continuous project health assessment
- Tracks issues and trends
- Provides early warning systems

## 🔧 CLI Commands

| Command           | Description                | Example                                                   |
| ----------------- | -------------------------- | --------------------------------------------------------- |
| `init`            | Initialize the platform    | `python -m whatsworking_platform.main init`               |
| `analyze`         | Run comprehensive analysis | `python -m whatsworking_platform.main analyze`            |
| `status`          | Show current status        | `python -m whatsworking_platform.main status`             |
| `goal <text>`     | Set project goal           | `python -m whatsworking_platform.main goal "Build API"`   |
| `critical <item>` | Add critical path item     | `python -m whatsworking_platform.main critical "Fix bug"` |
| `help`            | Show help                  | `python -m whatsworking_platform.main help`               |

## 🔌 MCP Integration

The platform provides an MCP server that exposes:

### Resources

- `project://whatsworking/state` - Current project state
- `project://whatsworking/methodology` - Methodology compliance
- `project://whatsworking/health` - Project health metrics
- `project://whatsworking/goals` - Project goals
- `project://whatsworking/critical-path` - Critical path items
- `project://whatsworking/architecture` - Architectural decisions

### Tools

- `enforce_methodology` - Validate action compliance
- `set_project_goal` - Set project goal
- `add_critical_path_item` - Add critical path item
- `run_project_analysis` - Run analysis
- `validate_action_gates` - Validate through gates

## 🧩 Integration with Existing Systems

The platform integrates with your existing `project_intelligence/` system:

- **ProjectIntelligence** - For project health and context
- **GoalFocusEnforcer** - For goal management
- **Existing analyzers** - For codebase analysis

## 📊 Analysis Output

The platform generates comprehensive reports including:

- **Project Overview** - Basic project information
- **Health Metrics** - Overall score, issues, status
- **Methodology Compliance** - Compliance scores for each principle
- **Critical Path** - Current critical path items
- **Architectural Decisions** - Recent decisions and rationale

## 🎨 Rich CLI Interface

Uses the `rich` library for beautiful terminal output:

- Color-coded status indicators
- Tables for structured data
- Panels for important information
- Progress indicators for long operations

## 🔧 Configuration

Configuration is managed through `PlatformConfig`:

- Methodology enforcement settings
- Analysis module enable/disable
- Output format and directory settings
- Integration settings
- Validation thresholds

## 🚀 Future Enhancements

- **Test Aggregation** - Collect and analyze test results
- **CI/CD Integration** - Automated health checks
- **Slack Integration** - Notifications and updates
- **Docker Support** - Containerized deployment
- **Advanced Validation** - Custom validation rules

## 📚 Usage Examples

### Basic Workflow

```bash
# Initialize platform
python -m whatsworking_platform.main init

# Set project goal
python -m whatsworking_platform.main goal "Implement user authentication system"

# Add critical path items
python -m whatsworking_platform.main critical "Design database schema"
python -m whatsworking_platform.main critical "Implement login endpoint"
python -m whatsworking_platform.main critical "Add password hashing"

# Run analysis
python -m whatsworking_platform.main analyze

# Check status
python -m whatsworking_platform.main status
```

### MCP Server Usage

```bash
# Run MCP server
python -m whatsworking_platform.integration.mcp_server

# Configure in Warp or other MCP clients
# Use resources and tools to enforce methodology
```

## 🤝 Contributing

This platform consolidates the best parts of your existing `whatsworking` implementations. To extend it:

1. **Add new collectors** in the `collectors/` directory
2. **Extend validation logic** in the engine
3. **Add new MCP resources/tools** in the integration module
4. **Enhance CLI commands** in the CLI module

## 📄 License

Part of the WhatsWorking project - consolidating scattered implementations into a unified, methodology-driven platform.
