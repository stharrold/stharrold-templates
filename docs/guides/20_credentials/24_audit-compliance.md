---
title: Security Auditing & Compliance
version: 3.2
updated: 2025-09-13
parent: ./CLAUDE.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - audit_retention_period
    - compliance_frameworks
    - security_alert_thresholds
security_level: Enterprise-compliance
compliance_frameworks:
  - GDPR
  - HIPAA
  - SOX
  - SOC2
related:
  - ./21_keychain-macos.md
  - ./22_credential-manager-win.md
  - ./23_enterprise-sso.md
  - ../30_implementation/34_performance-metrics.md
changelog:
  - Enhanced with advanced monitoring patterns, anomaly detection, and incident response capabilities
  - Integrated template maintenance tasks for security monitoring
  - Enhanced vulnerability management with CVE tracking
  - Added AI-generated code security review requirements
  - Updated token security best practices with automation
---

# Security Auditing & Compliance

Comprehensive security auditing, compliance monitoring, and vulnerability management for enterprise MCP server deployments with Claude Code.

## Security Context Foundation

Proper credential management is critical for MCP server security and forms the foundation of enterprise compliance. This module emphasizes:

- **Comprehensive audit trails** for all credential access and usage
- **Regulatory compliance** with industry standards (GDPR, HIPAA, SOX, SOC2)
- **Vulnerability monitoring** and automated threat response
- **AI-generated code security review** to address inherent risks

## Audit Trails for Enterprise Knowledge Base Access

### Structured Logging for Credential Operations

**Advanced Credential Monitoring Patterns:**

Implement comprehensive structured logging for all credential operations with anomaly detection:

```javascript
// Enhanced credential operation logging
const logger = require('winston');
const crypto = require('crypto');

class CredentialAuditLogger {
  logCredentialAccess(operation) {
    const auditEvent = {
      event_type: 'credential_access',
      timestamp: new Date().toISOString(),
      user_id: operation.userId,
      resource_id: operation.resourceId,
      action: operation.action, // 'retrieved', 'stored', 'deleted', 'rotated'
      source_ip: operation.sourceIP,
      user_agent: operation.userAgent,
      session_id: operation.sessionId,
      // Hash sensitive identifiers for privacy
      resource_hash: crypto.createHash('sha256').update(operation.resourceId).digest('hex'),
      classification: operation.dataClassification,
      access_method: operation.accessMethod, // 'keychain', 'credential_manager', 'environment'
      success: operation.success,
      error_code: operation.errorCode || null,
      duration_ms: operation.duration
    };

    logger.info('Credential operation completed', auditEvent);

    // Trigger anomaly detection
    this.detectAnomalies(auditEvent);
  }

  detectAnomalies(event) {
    // Unusual access patterns
    if (this.isOutsideBusinessHours(event.timestamp)) {
      this.alertSecurityTeam('after_hours_access', event);
    }

    // High-frequency access detection
    const recentAccess = this.getRecentAccessCount(event.user_id, 5); // 5 minutes
    if (recentAccess > 10) {
      this.alertSecurityTeam('high_frequency_access', event);
    }

    // Failed authentication clustering
    if (!event.success) {
      const failedAttempts = this.getFailedAttempts(event.user_id, 15); // 15 minutes
      if (failedAttempts > 5) {
        this.alertSecurityTeam('credential_brute_force', event);
      }
    }
  }

  alertSecurityTeam(alertType, event) {
    const alert = {
      alert_type: alertType,
      severity: this.calculateSeverity(alertType),
      timestamp: new Date().toISOString(),
      details: event,
      recommended_action: this.getRecommendedAction(alertType)
    };

    // Send to security team via webhook/SIEM
    this.sendAlert(alert);
  }
}
```

**Mandatory Audit Events:**
- **Credential access operations** with user identity, resource hash, and access method
- **Query audit logs** with user identity, timestamp, search terms, and data classification
- **Document access tracking** including retrieved content, usage context, and retention period
- **Permission escalation alerts** for unusual access patterns or privilege changes
- **Data export monitoring** to prevent unauthorized knowledge extraction and IP theft
- **Authentication events** including failed login attempts and suspicious activity

### Enterprise Audit MCP Server Configuration

**Basic Audit Server Setup:**
```bash
# Enterprise audit logging with comprehensive tracking
claude mcp add audit-logger "python -m enterprise_audit" \
  --env LOG_LEVEL="detailed" \
  --env RETENTION_DAYS="2555"  \
  --env ALERT_THRESHOLDS="./security_thresholds.json" \
  --env COMPLIANCE_FRAMEWORKS="GDPR,HIPAA,SOX" \
  --env EXPORT_FORMAT="json,csv,siem"
```

**Advanced Audit Configuration:**
```yaml
# security_thresholds.json
{
  "failed_auth_attempts": {
    "threshold": 5,
    "window_minutes": 15,
    "action": "lock_account",
    "alert_severity": "high"
  },
  "unusual_data_access": {
    "threshold": 100,
    "window_hours": 1,
    "action": "require_additional_auth",
    "alert_severity": "medium"
  },
  "bulk_data_export": {
    "threshold": 50,
    "window_minutes": 30,
    "action": "block_and_alert",
    "alert_severity": "critical"
  },
  "after_hours_access": {
    "business_hours": "09:00-17:00",
    "time_zone": "UTC",
    "action": "enhanced_logging",
    "alert_severity": "low"
  }
}
```

### Advanced Anomaly Detection Implementation

**Automated Threat Detection Patterns:**

```javascript
// Comprehensive anomaly detection system
class SecurityAnomalyDetector {
  constructor() {
    this.patterns = {
      // Time-based anomalies
      outsideBusinessHours: {
        businessStart: 9, businessEnd: 17,
        alertThreshold: 'medium'
      },

      // Frequency-based anomalies
      highFrequencyAccess: {
        timeWindow: 300000, // 5 minutes
        threshold: 15,
        alertThreshold: 'high'
      },

      // Geographic anomalies
      unusualLocation: {
        maxDistanceKm: 1000,
        timeWindow: 3600000, // 1 hour
        alertThreshold: 'critical'
      },

      // Behavioral anomalies
      unusualResourceAccess: {
        baselineWindow: 30, // 30 days
        deviationThreshold: 3, // 3 standard deviations
        alertThreshold: 'medium'
      }
    };
  }

  analyzeAccessPattern(events) {
    const anomalies = [];

    // Time-based analysis
    events.forEach(event => {
      const hour = new Date(event.timestamp).getHours();
      if (hour < this.patterns.outsideBusinessHours.businessStart ||
          hour > this.patterns.outsideBusinessHours.businessEnd) {
        anomalies.push({
          type: 'outside_business_hours',
          event: event,
          severity: 'medium'
        });
      }
    });

    // Frequency analysis
    const frequencyMap = this.groupByTimeWindow(events, 300000);
    Object.entries(frequencyMap).forEach(([window, windowEvents]) => {
      if (windowEvents.length > this.patterns.highFrequencyAccess.threshold) {
        anomalies.push({
          type: 'high_frequency_access',
          events: windowEvents,
          severity: 'high'
        });
      }
    });

    return anomalies;
  }

  groupByTimeWindow(events, windowSize) {
    const groups = {};
    events.forEach(event => {
      const windowStart = Math.floor(new Date(event.timestamp).getTime() / windowSize) * windowSize;
      if (!groups[windowStart]) groups[windowStart] = [];
      groups[windowStart].push(event);
    });
    return groups;
  }
}
```

### Kill Switch and Emergency Response

**Immediate Credential Revocation Capabilities:**

```javascript
// Emergency credential revocation system
class EmergencyCredentialManager {
  constructor() {
    this.killSwitchEnabled = process.env.KILL_SWITCH_ENABLED === 'true';
    this.emergencyContacts = process.env.EMERGENCY_CONTACTS?.split(',') || [];
  }

  async emergencyRevocation(reason, affectedCredentials = 'ALL') {
    if (!this.killSwitchEnabled) {
      throw new Error('Kill switch not enabled in this environment');
    }

    const revocationEvent = {
      timestamp: new Date().toISOString(),
      reason: reason,
      scope: affectedCredentials,
      initiator: process.env.USER || 'system',
      session_id: crypto.randomUUID()
    };

    console.log(`🚨 EMERGENCY REVOCATION INITIATED: ${reason}`);

    try {
      // Revoke all or specific credentials
      if (affectedCredentials === 'ALL') {
        await this.revokeAllCredentials(revocationEvent);
      } else {
        await this.revokeSpecificCredentials(affectedCredentials, revocationEvent);
      }

      // Notify emergency contacts
      await this.notifyEmergencyContacts(revocationEvent);

      // Trigger automated rotation pipeline
      await this.initiateCredentialRotation(revocationEvent);

      console.log('✅ Emergency revocation completed successfully');

    } catch (error) {
      console.error('❌ Emergency revocation failed:', error);
      await this.escalateToSecurityTeam(revocationEvent, error);
    }
  }

  async initiateCredentialRotation(revocationEvent) {
    // Automated credential refresh pipeline
    const rotationJobs = [
      this.rotateGitHubTokens(),
      this.rotateAWSCredentials(),
      this.rotateDatabaseCredentials(),
      this.rotateAPIKeys()
    ];

    console.log('🔄 Starting automated credential rotation...');

    const results = await Promise.allSettled(rotationJobs);
    const failures = results.filter(r => r.status === 'rejected');

    if (failures.length > 0) {
      console.error('❌ Some credential rotations failed:', failures);
      await this.notifyRotationFailures(failures, revocationEvent);
    } else {
      console.log('✅ All credential rotations completed successfully');
    }

    return results;
  }

  async rotateGitHubTokens() {
    // GitHub token rotation implementation
    const newToken = await this.createNewGitHubToken();
    await this.updateStoredCredential('GITHUB_TOKEN', newToken);
    await this.validateNewCredential('GITHUB_TOKEN');
    return newToken;
  }

  async validateNewCredential(credentialKey) {
    // Validation logic specific to each credential type
    const testCalls = {
      'GITHUB_TOKEN': () => this.testGitHubAPI(),
      'AWS_ACCESS_KEY_ID': () => this.testAWSAPI(),
      'DATABASE_URL': () => this.testDatabaseConnection()
    };

    const testFunction = testCalls[credentialKey];
    if (testFunction) {
      await testFunction();
      console.log(`✅ ${credentialKey} validated successfully`);
    }
  }
}

// Usage example
const emergencyManager = new EmergencyCredentialManager();

// Trigger emergency revocation
// emergencyManager.emergencyRevocation('Security breach detected', 'ALL');
```

### Real-Time Monitoring Integration

**SIEM Integration:**
```bash
# Forward audit logs to enterprise SIEM systems
claude mcp add siem-forwarder "python -m siem_integration" \
  --env SPLUNK_HEC_URL="https://splunk.company.com:8088/services/collector" \
  --env ELASTIC_ENDPOINT="https://elastic.company.com:9200" \
  --env LOG_FORMAT="cef"  # Common Event Format for security tools
```

## Data Classification and Retention

### Automated Classification System

**Content Scanning Capabilities:**
- **Pattern-based detection** for sensitive information (SSN, credit cards, PII)
- **Metadata-based classification** using document source, author, and creation date
- **ML-based sensitivity detection** for unstructured content and context analysis
- **Retention policy enforcement** with automatic purging and compliance reporting

**Classification Implementation:**
```bash
# Data Loss Prevention monitoring with ML classification
claude mcp add dlp-monitor "python -m data_loss_prevention" \
  --env SCAN_PATTERNS="./pii_patterns.json" \
  --env ML_MODEL_PATH="./classification_model.joblib" \
  --env ALERT_WEBHOOK="https://security-alerts.company.com/webhook" \
  --env QUARANTINE_ENABLED="true"
```

**PII Detection Patterns:**
```json
{
  "pii_patterns": {
    "ssn": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
    "credit_card": "\\b4\\d{3}[\\s\\-]?\\d{4}[\\s\\-]?\\d{4}[\\s\\-]?\\d{4}\\b",
    "email": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
    "phone": "\\b\\d{3}[\\s\\-\\.]?\\d{3}[\\s\\-\\.]?\\d{4}\\b",
    "ip_address": "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b",
    "api_key": "\\b[A-Za-z0-9]{32,}\\b"
  },
  "classification_rules": {
    "high_sensitivity": ["ssn", "credit_card", "api_key"],
    "medium_sensitivity": ["email", "phone"],
    "low_sensitivity": ["ip_address"]
  }
}
```

### Retention Policy Management

**Automated Retention Enforcement:**
```yaml
# retention_policies.yaml
policies:
  - classification: "public"
    retention_days: 365
    archive_after_days: 90
    purge_method: "secure_delete"

  - classification: "internal"
    retention_days: 1825  # 5 years
    archive_after_days: 365
    purge_method: "cryptographic_erasure"

  - classification: "confidential"
    retention_days: 2555  # 7 years
    archive_after_days: 730
    purge_method: "dod_5220_3_pass"

  - classification: "restricted"
    retention_days: 3650  # 10 years
    archive_after_days: 1095
    purge_method: "gutmann_35_pass"
```

## Security Warnings & Vulnerability Mitigation

### Recent Security Vulnerabilities

**Critical Vulnerabilities (2025):**

**CVE-2025-52882 (Critical - Score: 9.8/10)**
- **Impact**: WebSocket authentication bypass in Claude Code Extension allowing unauthorized MCP server access
- **Affected Versions**: All versions < 1.0.24
- **Attack Vector**: Network-accessible WebSocket endpoints with weak authentication
- **Exploitation**: Remote attackers can bypass authentication and execute arbitrary MCP commands
- **Mitigation**: Update to Claude Code version 1.0.24 or higher immediately
- **Verification**: `gemini --version` should show 1.0.24 or higher
- **Additional Protection**: Enable network-level access controls and monitor WebSocket traffic

**PostgreSQL MCP Server SQL Injection (High - Score: 7.5/10)**
- **Impact**: Potential for arbitrary SQL execution and database compromise
- **Attack Vector**: Unsanitized user input in MCP query parameters
- **Mitigation Actions**:
  - Use parameterized queries exclusively
  - Create dedicated MCP database users with minimal permissions
  - Enable query logging and monitoring
  - Implement input validation and sanitization
  - Regular security audits of database configurations

**Node.js Dependency Vulnerabilities:**
```bash
# Regular vulnerability scanning for MCP servers
npm audit --audit-level high
npm audit fix --force

# Automated dependency monitoring
claude mcp add vuln-scanner "python -m vulnerability_monitor" \
  --env SCAN_FREQUENCY="daily" \
  --env ALERT_SEVERITY="medium" \
  --env AUTO_UPDATE="patch_only"
```

### Vulnerability Response Procedures

**Incident Response Workflow:**
1. **Detection**: Automated vulnerability scanning and threat intelligence feeds
2. **Assessment**: Risk analysis and impact evaluation within 4 hours
3. **Containment**: Immediate threat isolation and access revocation within 2 hours
4. **Mitigation**: Patch deployment and system hardening within 24 hours
5. **Recovery**: System restoration and validation within 48 hours
6. **Lessons Learned**: Post-incident review and process improvement within 1 week

## AI-Generated Code Security Review Requirements

### Critical Security Statistics

**Research-Backed Risk Assessment:**
- **27-50% of AI-generated code contains vulnerabilities** according to recent studies
- **Security review is mandatory rather than optional** for all AI-generated code
- **Tiered review processes** required where code touching authentication, payments, or sensitive data requires additional scrutiny
- **Multi-model verification** reduces vulnerability rates by 60-70%

### Security Review Implementation

**Mandatory Code Labeling:**
```bash
# All AI-generated code must be clearly labeled in commits
git commit -m "feat: add user authentication

AI-Generated: Claude Code assisted implementation
Security-Review: Required for authentication logic
Reviewer: @security-team
Risk-Level: High
Components: authentication,session-management"
```

**Automated Security Integration:**
```yaml
# .github/workflows/ai-code-security.yml
name: AI-Generated Code Security Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-code-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Detect AI-Generated Code
        run: |
          grep -r "AI-Generated" . --include="*.py" --include="*.js" > ai_files.txt
      - name: Security Scan AI Code
        run: |
          codacy-cli analyze --tool semgrep --file-list ai_files.txt
          codacy-cli analyze --tool eslint --file-list ai_files.txt
      - name: Require Human Review
        run: |
          gh pr review --request-reviewer security-team --comment "AI-generated code requires security review"
```

### Mandatory Security Practices

**1. Code Identification and Tracking:**
- All AI-generated code clearly marked in comments and commit messages
- Tracking of AI model used (Gemini Opus 4, Sonnet 4, etc.)
- Documentation of human review and approval process

**2. Automated Security Scanning:**
- Static analysis tools run automatically on Gemini-generated code
- Dynamic testing and runtime behavior validation
- Dependency vulnerability scanning with enhanced scrutiny

**3. Multi-Model Review Process:**
- Different AI models used for generation versus security review
- Human security expert review for high-risk components
- Cross-validation using multiple security analysis tools

**4. Enhanced Testing Requirements:**
```python
# Example: Enhanced test coverage for AI-generated code
"""
AI-Generated: True
Model: Gemini Opus 4
Human-Reviewer: @security-expert
Test-Coverage-Required: >95%
Security-Tests: Included
"""

def test_authentication_security():
    """Security-focused tests for AI-generated auth code."""
    # SQL injection attempts
    assert not vulnerable_to_sql_injection(malicious_input)

    # XSS prevention
    assert sanitized_output_prevents_xss(user_input)

    # Session management security
    assert secure_session_handling(session_data)

    # Rate limiting effectiveness
    assert rate_limiting_blocks_brute_force(auth_attempts)
```

**5. Integration with Security Platforms:**

**Local Codacy CLI (Mandatory per Repository Guidelines):**
```bash
# Required after ANY file edit per CLAUDE.md guidelines
./.codacy/cli.sh analyze --tool pylint edited_file.py
```

**Sentry Integration for Runtime Security:**
```bash
# Error tracking and security incident detection
claude mcp add sentry "python -m sentry_mcp" \
  --env SENTRY_DSN="https://key@sentry.io/project" \
  --env ENVIRONMENT="production" \
  --env ENABLE_SECURITY_ALERTS="true"
```

## Token Security Best Practices

### Automated Token Rotation Schedule

**Industry-Standard Rotation Frequencies:**
- **GitHub Personal Access Tokens**: Every 90 days
- **Database credentials**: Every 60 days
- **Cloud provider keys (AWS, Azure, GCP)**: Every 30 days
- **API keys (third-party services)**: Based on provider recommendations (typically 30-90 days)
- **Certificate-based authentication**: 12 months before expiration

### Automated Rotation Implementation

**macOS Keychain Rotation:**
```bash
#!/bin/bash
# token-rotation-macos.sh - Automated token rotation script

ROTATION_LOG="/var/log/mcp-token-rotation.log"
ALERT_EMAIL="security@company.com"

rotate_github_token() {
    echo "$(date): Starting GitHub token rotation" >> $ROTATION_LOG

    # Generate new token via GitHub CLI
    NEW_TOKEN=$(gh auth token --scopes repo,workflow,read:org)

    # Update keychain
    security delete-generic-password -a "$USER" -s "GITHUB_TOKEN"
    security add-generic-password -a "$USER" -s "GITHUB_TOKEN" -w "$NEW_TOKEN"

    # Test new token
    if curl -H "Authorization: token $NEW_TOKEN" https://api.github.com/user > /dev/null 2>&1; then
        echo "$(date): GitHub token rotation successful" >> $ROTATION_LOG
    else
        echo "$(date): GitHub token rotation FAILED" >> $ROTATION_LOG
        mail -s "Token Rotation Failure" $ALERT_EMAIL < $ROTATION_LOG
    fi
}

# Schedule via cron: 0 2 1 */3 * /path/to/token-rotation-macos.sh
```

**Windows Credential Manager Rotation:**
```powershell
# token-rotation-windows.ps1 - Automated Windows token rotation

function Rotate-GitHubToken {
    param(
        [Parameter(Mandatory)]
        [string]$NewToken
    )

    $LogPath = "C:\Logs\mcp-token-rotation.log"
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    try {
        # Remove old credential
        Remove-StoredCredential -Target "GITHUB_TOKEN" -ErrorAction SilentlyContinue

        # Add new credential
        $SecureToken = ConvertTo-SecureString $NewToken -AsPlainText -Force
        New-StoredCredential -Target "GITHUB_TOKEN" -UserName "token" -SecurePassword $SecureToken -Persist LocalMachine

        # Test new token
        $Headers = @{ "Authorization" = "token $NewToken"; "User-Agent" = "PowerShell-Token-Test" }
        $Response = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $Headers

        Add-Content -Path $LogPath -Value "$Timestamp: GitHub token rotation successful"
    }
    catch {
        Add-Content -Path $LogPath -Value "$Timestamp: GitHub token rotation FAILED - $($_.Exception.Message)"
        Send-MailMessage -To "security@company.com" -Subject "Token Rotation Failure" -Body $_.Exception.Message
    }
}

# Schedule via Task Scheduler for automated execution
```

### Access Auditing Implementation

**macOS Audit Logging:**
```bash
# Monitor keychain access events
log show --predicate 'subsystem == "com.apple.security" and category == "keychain"' --last 1h --style syslog

# Parse and analyze keychain access patterns
grep "security find-generic-password" /var/log/system.log | \
  awk '{print $1, $2, $3, $12}' | \
  sort | uniq -c | sort -nr
```

**Windows Audit Configuration:**
```powershell
# Enable credential access auditing
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable

# Review credential access events
Get-EventLog -LogName Security -InstanceId 4648 -After (Get-Date).AddHours(-24) |
  Select-Object TimeGenerated, Message |
  Format-Table -AutoSize
```

### Emergency Response Procedures

**Immediate Response Checklist (Execute within 15 minutes of compromise detection):**

1. **Token Revocation:**
   ```bash
   # Immediate token revocation
   security delete-generic-password -a "$USER" -s "COMPROMISED_TOKEN"
   claude mcp disable --all  # Disable all MCP servers temporarily
   ```

2. **Threat Assessment:**
   - Review access logs for unauthorized usage
   - Identify affected systems and data
   - Assess potential data exposure scope

3. **New Token Generation:**
   - Generate new token with different naming convention
   - Use minimum required scope/permissions
   - Enable enhanced monitoring for new token

4. **System Updates:**
   ```bash
   # Update all MCP server configurations
   claude mcp update-credentials --interactive

   # Restart services with new credentials
   claude mcp restart --all
   ```

5. **Incident Documentation:**
   - Log all response actions with timestamps
   - Document lessons learned and process improvements
   - Update incident response procedures based on findings

## Template Maintenance Integration

### Daily Security Tasks (Automated)

```bash
# Daily security monitoring script
#!/bin/bash
# daily-security-check.sh

echo "$(date): Starting daily security checks"

# Check for failed authentication attempts
failed_auths=$(grep "authentication failed" /var/log/gemini-mcp.log | wc -l)
if [ $failed_auths -gt 10 ]; then
    echo "ALERT: $failed_auths failed authentication attempts detected"
fi

# Monitor credential usage patterns
gemini audit --daily-summary --export-csv

# Check for vulnerability updates
npm audit --audit-level moderate --json > /tmp/vuln-report.json
python3 -c "
import json, sys
with open('/tmp/vuln-report.json') as f:
    data = json.load(f)
    if data.get('metadata', {}).get('vulnerabilities', {}).get('total', 0) > 0:
        print('ALERT: New vulnerabilities detected')
        sys.exit(1)
"

# Verify backup integrity
gemini backup --verify --silent || echo "ALERT: Backup verification failed"
```

### Weekly Security Reviews (Human + Automated)

```yaml
# weekly-security-tasks.yml
schedule: "0 9 * * 1"  # Every Monday at 9 AM

tasks:
  - name: "Credential rotation audit"
    command: "python3 scripts/audit-token-ages.py"
    threshold: "warning_if_older_than_60_days"

  - name: "Access pattern analysis"
    command: "gemini audit --weekly-report --anomaly-detection"
    alert_on: "unusual_patterns"

  - name: "Dependency security scan"
    command: "npm audit --audit-level high && pip-audit"
    action: "create_jira_ticket_if_high_severity"

  - name: "MCP server health check"
    command: "claude mcp health-check --all --detailed"
    alert_on: "any_failures"
```

### Monthly Compliance Reporting

```python
# monthly-compliance-report.py
import json
from datetime import datetime, timedelta

def generate_compliance_report():
    """Generate monthly compliance report for audit purposes."""

    report = {
        "reporting_period": {
            "start": (datetime.now() - timedelta(days=30)).isoformat(),
            "end": datetime.now().isoformat()
        },
        "metrics": {
            "total_authentication_events": get_auth_events_count(),
            "failed_authentication_attempts": get_failed_auth_count(),
            "data_access_events": get_data_access_count(),
            "policy_violations": get_policy_violations(),
            "vulnerability_remediation": get_vuln_remediation_stats()
        },
        "compliance_status": {
            "gdpr_compliant": check_gdpr_compliance(),
            "hipaa_compliant": check_hipaa_compliance(),
            "sox_compliant": check_sox_compliance()
        }
    }

    return json.dumps(report, indent=2)

# Export for compliance team
if __name__ == "__main__":
    print(generate_compliance_report())
```

## Integration with Performance Monitoring

Cross-reference with performance metrics to identify security impacts:
- Monitor authentication latency and failure rates
- Track credential rotation impact on system availability
- Analyze audit logging overhead on system performance
- Correlate security events with performance degradation

## Next Steps for Security Implementation

1. **Deploy audit infrastructure** - Set up comprehensive logging and monitoring
2. **Configure automated scanning** - Implement vulnerability and compliance checks
3. **Train security team** - Establish incident response procedures and escalation paths
4. **Test security measures** - Conduct penetration testing and security audits
5. **Monitor and improve** - Continuous security posture assessment and enhancement
6. **Document procedures** - Maintain up-to-date security policies and procedures

---

*This module completes the security and compliance framework. For implementation patterns, see [../30_implementation/CLAUDE.md](../30_implementation/CLAUDE.md).*
