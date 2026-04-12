# Multi-Agent Validation System - Testing Guide

This guide provides comprehensive instructions for testing the multi-agent validation system.

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Clone and navigate to the project
cd SunHacks/hackerTiger/

# Run the automated setup and test script
./setup_and_test.sh
```
> **Note (Nov 2025):** Legacy helper scripts such as `setup_and_test.sh` and `run_tests.py` have been removed from the repository because the production pipeline exercises the agents through Django’s `ai_code_validator()` entry point. Use the backend API flows (or invoke `main.py` directly) for end-to-end validation instead of the deprecated scripts referenced in older sections below.

### 2. Manual Setup (Alternative)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your Gemini API keys
```

## 🧪 Testing Procedures

### 1. Basic Unit Tests
```bash
# Run all unit tests
pytest tests/ -v

# Run with coverage
pytest --cov=agents --cov=utils --cov-report=html
```

### 2. Individual Agent Tests
```bash
# Test Security Agent
python agents/security_agent.py test_payloads/deployment_1.json

# Test Red Team Agent
python agents/red_team_agent.py test_payloads/deployment_1.json
```

### 3. Full System Integration Tests
```bash
# Test with safe deployment
python main.py --input test_payloads/deployment_1.json --verbose

# Test with vulnerable deployment
python main.py --input test_payloads/deployment_2.json --verbose

# Test with live candidate
python main.py --input test_payloads/live_candidate.json --verbose
```

### 4. System Status Check
```bash
# Check system health
python main.py --status
```

### 5. Audit Logging Immutability Tests
```bash
# Test audit logging security
python tests/test_audit_immutability.py
```

### 6. Gemini API Fallback Test
```bash
# Test API key rotation (temporarily modify .env with bad keys)
python main.py --input test_payloads/deployment_1.json
```

### 7. Trap-and-Isolate Test
```bash
# Test with high-confidence vulnerability
python main.py --input test_payloads/deployment_2.json --verbose
```

### 8. Session Management Test
```bash
# Test with specific agents and timeout
python main.py --input test_payloads/deployment_1.json --agents SecurityAgent RedTeamAgent --timeout 60
```

### 9. Compliance Policy Reload Test
```bash
# Test compliance agent
python main.py --input test_payloads/deployment_1.json --agents ComplianceAgent
```

### 10. Explainability Test
```bash
# Test explainability agent
python main.py --input test_payloads/live_candidate.json --agents ExplainabilityAgent
```

### 11. End-to-End Validation Test
```bash
# Test complete pipeline
python main.py --input test_payloads/live_candidate.json --verbose
```

### 12. Monitoring and Metrics Test
```bash
# Test system monitoring
python main.py --status
```

## 🔧 Comprehensive Test Suite

### Run All Tests
```bash
# Run comprehensive test suite
python run_tests.py
```

### Test Categories
1. **Environment Setup** - Python version, dependencies, file structure
2. **Dependencies** - Package installation and compatibility
3. **Unit Tests** - Individual component testing
4. **Agent Standalone** - Individual agent execution
5. **Integration** - Full system integration
6. **System Status** - Health monitoring
7. **Audit Immutability** - Security and tamper-proof logging
8. **Gemini Fallback** - API key rotation and fallback
9. **Trap-and-Isolate** - High-confidence threat detection
10. **Session Management** - Session lifecycle and coordination
11. **Compliance Reload** - Policy management
12. **Explainability** - Human-readable explanations
13. **End-to-End** - Complete validation pipeline
14. **Monitoring** - Metrics and observability

## 📊 Expected Test Results

### Successful Test Output
```
✅ Environment Setup - PASSED
✅ Dependencies - PASSED
✅ Unit Tests - PASSED
✅ Agent Standalone - PASSED
✅ Integration - PASSED
✅ System Status - PASSED
✅ Audit Immutability - PASSED
✅ Gemini Fallback - PASSED
✅ Trap-and-Isolate - PASSED
✅ Session Management - PASSED
✅ Compliance Reload - PASSED
✅ Explainability - PASSED
✅ End-to-End - PASSED
✅ Monitoring - PASSED

🎉 ALL TESTS PASSED! The multi-agent validation system is working correctly.
```

### JSON Structure Validation
Each agent should return properly structured JSON:
```json
{
  "agent_name": "Securo-Sentinel",
  "session_id": "test-session-123",
  "status": "COMPLETED",
  "verdict": "APPROVE|REJECT|ISOLATE",
  "confidence": 0.8,
  "details": {
    "security_report": "...",
    "vulnerabilities": [...],
    "recommendations": [...],
    "bug_bar_score": 3,
    "risk_score": 5.0
  },
  "threat_level": "MEDIUM",
  "execution_time": 1.5
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**
   - Ensure .env file has valid Gemini API keys
   - Check API key format: `GEMINI_API_KEYS=key1,key2,key3`

3. **Import Errors**
   ```bash
   # Ensure you're in the correct directory
   cd SunHacks/hackerTiger/
   
   # Check Python path
   export PYTHONPATH=$PWD:$PYTHONPATH
   ```

4. **Test Failures**
   - Check logs for specific error messages
   - Verify all required files exist
   - Ensure virtual environment is activated

### Debug Mode
```bash
# Run with verbose logging
python main.py --input test_payloads/deployment_1.json --verbose

# Run specific agent with debug
python -c "
import asyncio
from agents.security_agent import SecurityAgent
from utils.config import load_config
from utils.gemini_api import GeminiAPI
from utils.session import Session
from utils.logging_utils import AuditLogger
from datetime import datetime
import json

async def debug_agent():
    config = load_config()
    gemini_api = GeminiAPI(config.gemini_api_keys, config.gemini_model)
    session = Session('debug-session', datetime.now(), {})
    audit_logger = AuditLogger('debug.log')
    
    agent = SecurityAgent(gemini_api, audit_logger, session)
    result = await agent.execute({'code': 'def test(): pass'})
    print(json.dumps(result.to_dict(), indent=2))

asyncio.run(debug_agent())
"
```

## 📈 Performance Testing

### Load Testing
```bash
# Test with multiple concurrent sessions
for i in {1..5}; do
  python main.py --input test_payloads/deployment_1.json &
done
wait
```

### Memory Testing
```bash
# Monitor memory usage
python -m memory_profiler main.py --input test_payloads/deployment_1.json
```

### Timeout Testing
```bash
# Test with short timeout
python main.py --input test_payloads/deployment_1.json --timeout 30
```

## 🔒 Security Testing

### Audit Log Verification
```bash
# Verify audit log integrity
python -c "
from utils.logging_utils import AuditLogger
audit_logger = AuditLogger('audit.log')
result = audit_logger.verify_audit_integrity()
print(f'Verified: {result[\"verified\"]}')
print(f'Total entries: {result[\"total_entries\"]}')
print(f'Failed entries: {result[\"failed_entries\"]}')
"
```

### Hash Verification
```bash
# Check log file hashes
sha256sum audit.log
```

## 📝 Test Data

### Test Payloads
- `test_payloads/deployment_1.json` - Safe deployment
- `test_payloads/deployment_2.json` - Vulnerable deployment
- `test_payloads/live_candidate.json` - Production-like deployment

### Sample Commands
```bash
# Test with specific agents
python main.py --input test_payloads/deployment_1.json --agents SecurityAgent RedTeamAgent

# Test with custom timeout
python main.py --input test_payloads/deployment_1.json --timeout 600

# Test system status
python main.py --status

# Test with verbose output
python main.py --input test_payloads/deployment_1.json --verbose
```

## 🎯 Success Criteria

The system is working correctly if:

1. ✅ All unit tests pass
2. ✅ Individual agents execute without errors
3. ✅ Full system integration works
4. ✅ System status shows "operational"
5. ✅ Audit logging is immutable and verifiable
6. ✅ API key fallback works
7. ✅ Trap-and-isolate triggers for high-confidence threats
8. ✅ Session management works correctly
9. ✅ Compliance policies can be reloaded
10. ✅ Explainability agent provides clear explanations
11. ✅ End-to-end validation produces final verdict
12. ✅ Monitoring and metrics are available

## 🚀 Next Steps

After successful testing:

1. **Deploy to Production** - Use the system for real deployments
2. **Monitor Performance** - Track system metrics and performance
3. **Update Policies** - Modify compliance and security policies as needed
4. **Scale System** - Add more agents or increase concurrency
5. **Integrate** - Connect with CI/CD pipelines and deployment systems

---

**Note**: This testing guide ensures the multi-agent validation system is functioning correctly and securely. All tests should pass before using the system in production.
