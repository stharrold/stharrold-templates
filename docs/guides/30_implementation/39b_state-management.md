---
title: Advanced State Management & Task Queues
version: 4.0
updated: 2025-09-13
parent: ./39_multi-agent-systems.md
template_version: 1.0
project_template:
  enabled: true
  customizable_fields:
    - state_management_patterns
    - task_queue_configuration
    - distributed_coordination
system_focus: state_persistence_queues
coordination_level: enterprise_scale
state_technologies: ["redis", "celery", "kafka", "postgresql"]
related:
  - ./39_multi-agent-systems.md
  - ./39a_langgraph-orchestration.md
  - ./39c_workflow-implementation.md
  - ./38_enterprise-deployment.md
  - ../10_mcp/12_servers.md
changelog:
  - 4.0: Initial state management and task queue guide extracted from multi-agent systems
---

# Advanced State Management & Task Queues

Enterprise-grade state persistence, task queue management, and distributed coordination patterns for multi-agent orchestration workflows using Redis Cluster, Celery, and event-driven architectures.

## State Management Architecture

### Redis Cluster with Celery Integration

**Redis Cluster**[Redis-ByteByteGo] for distributed state management combined with **Celery**[Celery-docs] for task queuing provides production-grade reliability and horizontal scalability:

```python
# Celery configuration for agent tasks
from celery import Celery
from kombu import Queue
import redis
from datetime import datetime, timedelta

# Redis Cluster configuration
redis_cluster_nodes = [
    {"host": "redis-node1", "port": 6379},
    {"host": "redis-node2", "port": 6379},
    {"host": "redis-node3", "port": 6379},
]

# Celery application with Redis Cluster backend
app = Celery('agent_workflow',
             broker='redis://redis-cluster:6379/0',
             backend='redis://redis-cluster:6379/1')

# Advanced Celery configuration
app.conf.update(
    # Task routing
    task_routes={
        'agent_workflow.execute_tool': {'queue': 'tool_execution'},
        'agent_workflow.validate_output': {'queue': 'validation'},
        'agent_workflow.coordinate_agents': {'queue': 'coordination'},
        'agent_workflow.persist_state': {'queue': 'persistence'},
    },

    # Task retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,

    # Result expiration
    result_expires=3600,

    # Task compression and serialization
    task_compression='gzip',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Queue definitions
    task_queues=(
        Queue('tool_execution', routing_key='tools'),
        Queue('validation', routing_key='validation'),
        Queue('coordination', routing_key='coordination'),
        Queue('persistence', routing_key='persistence'),
    ),
)

def exponential_backoff(task_self, retries):
    """Exponential backoff with jitter for retry strategies"""
    import random
    backoff = min(300, (2 ** retries) + random.uniform(0, 1))
    return backoff

@app.task(bind=True,
          autoretry_for=(Exception,),
          retry_kwargs={'max_retries': 3, 'countdown': exponential_backoff})
def execute_tool(self, tool_name: str, params: dict, context: dict):
    """Execute tool with automatic retry and state persistence"""

    try:
        # Store execution start state
        state_key = f"tool_execution:{self.request.id}"
        store_execution_state(state_key, {
            'tool_name': tool_name,
            'params': params,
            'context': context,
            'status': 'executing',
            'started_at': datetime.utcnow().isoformat(),
            'retry_count': self.request.retries
        })

        # Simulate tool execution logic
        result = perform_tool_execution(tool_name, params, context)

        # Store successful completion
        store_execution_state(state_key, {
            'status': 'completed',
            'result': result,
            'completed_at': datetime.utcnow().isoformat()
        })

        return result

    except Exception as exc:
        # Store error state
        store_execution_state(state_key, {
            'status': 'failed',
            'error': str(exc),
            'failed_at': datetime.utcnow().isoformat(),
            'retry_count': self.request.retries
        })

        # Re-raise for Celery retry handling
        raise self.retry(exc=exc, countdown=exponential_backoff(self, self.request.retries))

def store_execution_state(key: str, state_data: dict):
    """Store execution state in Redis with expiration"""
    import json

    redis_client = redis.Redis(host='redis-cluster', port=6379, decode_responses=True)

    # Merge with existing state
    existing_state = redis_client.get(key)
    if existing_state:
        current_state = json.loads(existing_state)
        current_state.update(state_data)
        state_data = current_state

    # Store with 24-hour expiration
    redis_client.setex(key, 86400, json.dumps(state_data))

def perform_tool_execution(tool_name: str, params: dict, context: dict):
    """Placeholder for actual tool execution logic"""
    # This would integrate with actual MCP servers and tools
    return {
        'tool': tool_name,
        'result': 'execution_successful',
        'output_data': {'processed': True, 'timestamp': datetime.utcnow().isoformat()}
    }
```

### Event Sourcing with Kafka

**Event sourcing**[Kafka-streaming] provides complete audit trails and enables complex state reconstruction:

```python
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class EventStore:
    """Event sourcing implementation with Kafka backend"""

    def __init__(self, kafka_brokers: List[str], topic_prefix: str = "agent_events"):
        self.kafka_brokers = kafka_brokers
        self.topic_prefix = topic_prefix

        self.producer = KafkaProducer(
            bootstrap_servers=kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all', retries=3, enable_idempotence=True
        )

    def append_event(self, aggregate_id: str, event_type: str, event_data: Dict[str, Any]) -> str:
        """Append event to event stream with optimistic concurrency control"""

        event_id = str(uuid.uuid4())
        event = {
            'event_id': event_id,
            'aggregate_id': aggregate_id,
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': self._get_next_version(aggregate_id)
        }

        topic = f"{self.topic_prefix}_{event_type.lower()}"

        try:
            future = self.producer.send(topic, key=aggregate_id, value=event)
            future.get(timeout=10)
            return event_id
        except KafkaError as e:
            raise Exception(f"Failed to append event: {e}")

    def get_events(self, aggregate_id: str, from_version: int = 0) -> List[Dict[str, Any]]:
        """Retrieve events for aggregate from specified version"""
        # Simplified implementation
        return []

    def _get_next_version(self, aggregate_id: str) -> int:
        """Get next version number for aggregate"""
        return len(self.get_events(aggregate_id)) + 1
```

### CQRS Pattern Implementation

**Command Query Responsibility Segregation (CQRS)**[CQRS-pattern] separates read and write operations for optimal performance:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
import asyncio
import asyncpg

@dataclass
class Command(ABC):
    aggregate_id: str
    correlation_id: str
    user_id: str

@dataclass
class StartWorkflowCommand(Command):
    workflow_type: str
    configuration: Dict[str, Any]

class CommandHandler:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle_start_workflow(self, command: StartWorkflowCommand) -> Dict[str, Any]:
        event_id = self.event_store.append_event(
            aggregate_id=command.aggregate_id,
            event_type='workflow_started',
            event_data={
                'workflow_type': command.workflow_type,
                'configuration': command.configuration,
                'initiated_by': command.user_id,
                'correlation_id': command.correlation_id
            }
        )
        return {'event_id': event_id, 'status': 'workflow_started'}

class QueryHandler:
    def __init__(self, read_db_pool: asyncpg.Pool):
        self.read_db = read_db_pool

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        async with self.read_db.acquire() as connection:
            workflow = await connection.fetchrow("""
                SELECT workflow_id, status, current_step, progress_percentage
                FROM workflow_status WHERE workflow_id = $1
            """, workflow_id)
            return dict(workflow) if workflow else None

class CQRSCoordinator:
    def __init__(self, command_handler: CommandHandler, query_handler: QueryHandler):
        self.command_handler = command_handler
        self.query_handler = query_handler
```

### Saga Pattern for Distributed Transactions

**Saga pattern**[Saga-pattern] manages distributed transactions across multiple services with automatic compensation:

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    step_id: str
    service_name: str
    action: str
    parameters: Dict[str, Any]
    compensation_action: Optional[str] = None
    status: SagaStepStatus = SagaStepStatus.PENDING

class SagaOrchestrator:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.service_handlers: Dict[str, callable] = {}

    async def execute_saga(self, steps: List[SagaStep]) -> bool:
        completed_steps = []

        try:
            for step in steps:
                handler = self.service_handlers[step.service_name]
                result = await handler(step.action, step.parameters)
                step.status = SagaStepStatus.COMPLETED
                completed_steps.append(step)

            return True

        except Exception:
            # Compensate in reverse order
            for step in reversed(completed_steps):
                if step.compensation_action:
                    await self.service_handlers[step.service_name](
                        step.compensation_action, step.parameters
                    )
                    step.status = SagaStepStatus.COMPENSATED

            return False
```

## XState Integration for Frontend

**State machines** (XState) provide predictable state management for workflow control:

```typescript
import { createMachine, assign } from 'xstate';

interface WorkflowContext {
  workflowId: string;
  progress: number;
  retryCount: number;
}

const workflowStateMachine = createMachine({
  id: 'multiAgentWorkflow',
  initial: 'idle',
  context: { workflowId: '', progress: 0, retryCount: 0 },
  states: {
    idle: {
      on: { START_WORKFLOW: 'initializing' }
    },
    initializing: {
      on: {
        STEP_COMPLETED: 'executing',
        STEP_FAILED: 'retrying'
      }
    },
    executing: {
      on: {
        STEP_COMPLETED: 'completed',
        STEP_FAILED: 'retrying'
      }
    },
    retrying: {
      always: [
        { target: 'failed', cond: 'maxRetriesExceeded' },
        { target: 'initializing' }
      ]
    },
    completed: { type: 'final' },
    failed: { type: 'final' }
  }
}, {
  guards: {
    maxRetriesExceeded: (context) => context.retryCount >= 3
  }
});
```

## References

[Redis-ByteByteGo]: The 6 Most Impactful Ways Redis is Used in Production Systems. ByteByteGo. https://blog.bytebytego.com/p/the-6-most-impactful-ways-redis-is
[Celery-docs]: First Steps with Celery – Celery 5.5.3 documentation. https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html
[Kafka-streaming]: What is Event Streaming in Apache Kafka? SOC Prime. https://socprime.com/blog/what-is-event-streaming-in-apache-kafka/
[CQRS-pattern]: Microservices Pattern: Command Query Responsibility Segregation (CQRS). https://microservices.io/patterns/data/cqrs.html
[Saga-pattern]: Saga pattern - AWS Prescriptive Guidance. https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/saga-pattern.html

---

*This guide provides enterprise-grade state management and task queue patterns for distributed multi-agent coordination workflows.*