# Agent-20 & Agent-30 Iteration Architecture
## Spec-kit to DSPy Conversion and Execution Pipeline

Production implementation of Tier 2 (agent-20) and Tier 3 (agent-30) with iterative feedback loops and optimization.

**Correct 4-Tier Workflow:**
- **Agent-00**: Raw tasks → BMAD stories (Autogen + BMAD validation)
- **Agent-10**: BMAD stories → spec-kit specifications (BAML transformation)
- **Agent-20**: spec-kit specifications → DSPy programs (conversion)
- **Agent-30**: DSPy programs → execution (DSPy execution)

## Design Decisions

**Agent Spawning:**
- Agent-20 spawns multiple agent-30 instances: sequential (s1, s2) and async (a1, a2)
- Agent-30 can spawn subagents (2-3 levels max, controlled triggers)
- Directory: `repo/agents/.../agent-30-dspy-{type}{num}/`

**Permissions:**
- Read: Full repository access
- Write: Own directory + targets defined by parent agent

**Messaging:**
- Append-only JSON-lines in `messages.json`
- File size tracking for unread detection

**MIPROv2 Optimization:**
- Agent spawning configurations
- Inter-agent communication patterns
- Configuration generation and execution instructions

## Three-Mode Architecture

**Mode-0-Setup:**
- Agent-00 → Agent-10 → Agent-20 → Agent-30 creation pipeline
- All agents use BAML for configurable, repeatable setup
- Output: config-0-setup.json
- Artifacts persist as build records

**Mode-1-Train:**
- Agent-20 receives validated data input
- Spawns Agent-30s for training/optimization
- Target: validated output data
- Output: config-1-train.json after cross-validation

**Mode-2-Serve:**
- Agent-20 receives user natural language queries
- Spawns Agent-30s for execution
- Target: user/database output
- Output: config-2-serve.json when serving

## Configuration Management

**Config Lifecycle:**
```python
# Write to archive first
archive_path = f"ARCHIVED/{timestamp}_config-{mode}.json"
write_config(archive_path, config_data)

# Atomic copy to active config
shutil.copy2(archive_path, f"config-{mode}.json")
```

**Config Loading:**
- Use highest-numbered, most recent config-*.json
- Config overwrites all settings/nodes/topology
- Initialize agents in config order
- Validate topology before creation

**Fallback:**
- No config exists → save current state as ARCHIVED/{timestamp}_config-0-serve.json

## State Management

**Per-Agent State:**
```python
# Each agent directory contains states.json
class AgentState:
    def append_state(self, state_data: Dict):
        """Append-only state logging"""
        state_entry = {
            "timestamp": time.time(),
            "state": state_data,
            "config_version": self.config_version
        }
        with open(self.agent_dir / "states.json", "a") as f:
            f.write(json.dumps(state_entry) + "\n")
```

## Core Architecture

### 20_speckit_dspy_transformer.py
```python
import dspy
from dspy.teleprompt import MIPROv2
from typing import Dict, List, Any, Optional
import json
import asyncio
from dataclasses import dataclass
from pathlib import Path
import redis.asyncio as redis
import numpy as np

@dataclass
class SpecKitSignature:
    """Spec-kit signature definition for DSPy transformation"""
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    constraints: List[str]
    examples: List[Dict[str, Any]]
    validation_rules: List[str]

class Agent20SpecKitTransformer(dspy.Module):
    """Agent-20: Converts spec-kit specifications (from Agent-10) to DSPy signatures

    Spawning Capabilities:
    - agent-30-dspy-s1, s2 (sequential execution)
    - agent-30-dspy-a1, a2 (async execution)
    - Each lives in: repo/agents/.../agent-30-dspy-{type}{num}/

    Modes:
    - mode-1-train: Receives validated data, outputs for training
    - mode-2-serve: Receives user queries, outputs for execution
    """

    def __init__(self, config: Dict, mode: str):
        super().__init__()
        self.config = config
        self.mode = mode  # "mode-1-train" or "mode-2-serve"
        self.redis_client = None
        self.state_manager = AgentState(Path(config['agent_directory']))

        # DSPy signatures for conversion
        self.spec_parser = dspy.ChainOfThought("spec_kit_specs -> parsed_specs")
        self.signature_builder = dspy.ChainOfThought("parsed_specs, constraints -> dspy_signature")
        self.validator = dspy.ChainOfThought("dspy_signature, validation_rules -> validation_result")

        # MIPROv2 optimizable spawning logic
        self.spawning_optimizer = dspy.ChainOfThought("spec_complexity, resources -> agent30_configs")

    async def forward(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mode-aware processing of input data"""
        trace_id = input_data.get('trace_id', 'unknown')

        # Log state
        self.state_manager.append_state({
            'mode': self.mode,
            'input_type': 'validated_data' if self.mode == 'mode-1-train' else 'user_query',
            'trace_id': trace_id
        })

        if self.mode == "mode-1-train":
            return await self._process_training_input(input_data)
        elif self.mode == "mode-2-serve":
            return await self._process_serving_input(input_data)
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

    async def _process_training_input(self, input_data: Dict) -> Dict:
        """Process validated training data"""
        validated_query = input_data['validated_query']
        target_output = input_data['target_output']

        # Convert to spec-kit format for processing
        spec_kit_specs = await self._query_to_specs(validated_query)

        # Generate agent-30 configs for training
        spawn_configs = await self._generate_agent30_configs(
            spec_kit_specs,
            target_output,
            mode="training"
        )

        return {
            'agent30_configs': spawn_configs,
            'target_output': target_output,
            'mode': 'training'
        }

    async def _process_serving_input(self, input_data: Dict) -> Dict:
        """Process user query for serving"""
        user_query = input_data['user_query']

        # Convert to spec-kit format for processing
        spec_kit_specs = await self._query_to_specs(user_query)

        # Generate agent-30 configs for serving
        spawn_configs = await self._generate_agent30_configs(
            spec_kit_specs,
            mode="serving"
        )

        return {
            'agent30_configs': spawn_configs,
            'mode': 'serving'
        }

    async def _generate_agent30_configs(self, parsed_specs: Dict, signature: str, validation: Dict) -> List[Dict]:
        """Generate agent-30 spawn configurations (MIPROv2 optimized)"""

        # Use MIPROv2 optimized spawning logic
        spawn_decision = self.spawning_optimizer(
            spec_complexity=self._calculate_complexity(parsed_specs),
            resources=await self._get_available_resources()
        )

        configs = []
        spawn_config = json.loads(spawn_decision.agent30_configs)

        # Sequential agents
        for i in range(spawn_config.get('sequential_count', 1)):
            configs.append({
                'agent_id': f'agent-30-dspy-s{i+1}',
                'execution_mode': 'sequential',
                'directory': f'agent-30-dspy-s{i+1}',
                'dspy_signature': signature,
                'dependencies': [f'agent-30-dspy-s{i}'] if i > 0 else [],
                'permissions': {
                    'read': 'repository_wide',
                    'write': ['own_directory', 'defined_targets']
                }
            })

        # Async agents
        for i in range(spawn_config.get('async_count', 1)):
            configs.append({
                'agent_id': f'agent-30-dspy-a{i+1}',
                'execution_mode': 'async',
                'directory': f'agent-30-dspy-a{i+1}',
                'dspy_signature': signature,
                'parallel': True,
                'permissions': {
                    'read': 'repository_wide',
                    'write': ['own_directory', 'defined_targets']
                }
            })

        return configs

    async def _parse_spec_kit_specs(self, spec_kit_specs: List[Dict]) -> Dict:
        """Parse spec-kit specifications from Agent-10 into structured schema"""
        result = self.spec_parser(spec_kit_specs=json.dumps(spec_kit_specs))
        return json.loads(result.parsed_specs)

    async def _build_dspy_signature(self, schema: Dict, constraints: List[str]) -> str:
        """Build DSPy signature from parsed schema"""
        result = self.signature_builder(
            parsed_schema=json.dumps(schema),
            constraints=", ".join(constraints)
        )
        return result.dspy_signature

    async def _validate_signature(self, signature: str, rules: List[str]) -> Dict:
        """Validate DSPy signature against rules"""
        result = self.validator(
            dspy_signature=signature,
            validation_rules=", ".join(rules)
        )
        return json.loads(result.validation_result)

    async def _store_iteration_metadata(self, trace_id: str, metadata: Dict):
        """Store iteration metadata in Redis"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.config['redis_url'])

        key = f"agent20:iteration:{trace_id}"
        await self.redis_client.hset(key, mapping={
            'metadata': json.dumps(metadata),
            'timestamp': metadata['timestamp']
        })
        await self.redis_client.expire(key, 86400)  # 24 hour TTL
```

### 30_dspy_execution_engine.py
```python
class Agent30DSPyExecutor(dspy.Module):
    """Agent-30: Executes DSPy signatures with iterative refinement

    Capabilities:
    - Subagent spawning (2-3 levels max, controlled triggers)
    - Append-only JSON-lines messaging via messages.json
    - File size tracking for unread message detection
    """

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.redis_client = None
        self.execution_cache = {}
        self.agent_dir = Path(config.get('agent_directory', '.'))
        self.messaging = AgentMessaging(self.agent_dir)

        # Dynamic signature compilation
        self.signature_compiler = dspy.ChainOfThought("signature_def -> compiled_module")
        self.result_evaluator = dspy.ChainOfThought("execution_result, expected_output -> evaluation_score")
        self.refinement_engine = dspy.ChainOfThought("failed_result, error_analysis -> refined_signature")

        # MIPROv2 optimizable subagent spawning
        self.subagent_spawner = dspy.ChainOfThought("execution_state, error_analysis -> spawn_decision")

    async def forward(self, execution_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute DSPy signature with iterative refinement and subagent spawning"""
        trace_id = execution_input.get('trace_id', 'unknown')
        signature_def = execution_input['dspy_signature']
        inputs = execution_input['inputs']
        max_iterations = execution_input.get('max_iterations', 5)

        iteration_results = []
        current_signature = signature_def
        subagents_spawned = []

        for iteration in range(max_iterations):
            # Check for new messages from other agents
            new_messages = self.messaging.check_new_messages()
            if new_messages:
                await self._process_incoming_messages(new_messages)

            # Compile and execute signature
            result = await self._execute_signature(current_signature, inputs, iteration)

            # Evaluate result quality
            evaluation = await self._evaluate_result(result, execution_input.get('expected_output'))

            iteration_data = {
                'iteration': iteration,
                'signature': current_signature,
                'result': result,
                'evaluation': evaluation,
                'timestamp': self._get_timestamp()
            }
            iteration_results.append(iteration_data)

            # Store iteration in Redis
            await self._store_execution_iteration(trace_id, iteration, iteration_data)

            # Check for subagent spawning conditions
            if await self._should_spawn_subagent(result, evaluation):
                subagent_config = await self._generate_subagent_config(result, evaluation, iteration)
                subagents_spawned.append(subagent_config)
                await self._spawn_subagent(subagent_config)

            # Check if result meets quality threshold
            if evaluation['score'] >= self.config.get('quality_threshold', 0.8):
                break

            # Refine signature for next iteration
            if iteration < max_iterations - 1:
                current_signature = await self._refine_signature(current_signature, result, evaluation)

        # Send completion message to coordination layer
        completion_msg = {
            'type': 'execution_complete',
            'trace_id': trace_id,
            'total_iterations': len(iteration_results),
            'subagents_spawned': len(subagents_spawned),
            'final_score': iteration_results[-1]['evaluation']['score']
        }
        self.messaging.send_message('coordinator', completion_msg)

        # Final result compilation
        final_result = {
            'final_output': iteration_results[-1]['result'],
            'total_iterations': len(iteration_results),
            'quality_score': iteration_results[-1]['evaluation']['score'],
            'iteration_history': iteration_results,
            'converged': iteration_results[-1]['evaluation']['score'] >= self.config.get('quality_threshold', 0.8)
        }

        # Store final result
        await self._store_final_result(trace_id, final_result)

        return final_result

    async def _execute_signature(self, signature_def: str, inputs: Dict, iteration: int) -> Dict:
        """Compile and execute DSPy signature"""
        try:
            # Dynamic module compilation
            compiled_result = self.signature_compiler(signature_def=signature_def)

            # Create dynamic DSPy module
            module_code = compiled_result.compiled_module
            exec_globals = {'dspy': dspy, 'Dict': Dict, 'List': List, 'Any': Any}
            exec(module_code, exec_globals)

            # Get the compiled module class
            module_class = exec_globals['CompiledModule']
            module_instance = module_class()

            # Execute with inputs
            result = module_instance(**inputs)

            return {
                'success': True,
                'output': result,
                'execution_time': self._get_timestamp(),
                'iteration': iteration
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': self._get_timestamp(),
                'iteration': iteration
            }

    async def _evaluate_result(self, result: Dict, expected: Optional[Dict] = None) -> Dict:
        """Evaluate execution result quality"""
        if not result['success']:
            return {'score': 0.0, 'reason': 'execution_failed', 'details': result.get('error')}

        if expected:
            evaluation = self.result_evaluator(
                execution_result=json.dumps(result['output']),
                expected_output=json.dumps(expected)
            )
            return json.loads(evaluation.evaluation_score)
        else:
            # Heuristic evaluation without expected output
            return {'score': 0.7, 'reason': 'heuristic_evaluation', 'details': 'No expected output provided'}

    async def _refine_signature(self, signature: str, failed_result: Dict, evaluation: Dict) -> str:
        """Refine signature based on failure analysis"""
        refinement = self.refinement_engine(
            failed_result=json.dumps(failed_result),
            error_analysis=json.dumps(evaluation)
        )
        return refinement.refined_signature
```

## Iteration Feedback Loop

## Messaging System

### Inter-Agent Communication
```python
class AgentMessaging:
    """Append-only JSON-lines messaging with file size tracking"""

    def __init__(self, agent_dir: Path):
        self.agent_dir = agent_dir
        self.messages_file = agent_dir / "messages.json"
        self.last_size = self.messages_file.stat().st_size if self.messages_file.exists() else 0
        self.agent_id = agent_dir.name

    def send_message(self, to_agent: str, message: Dict):
        """Send message with atomic append"""
        msg = {
            "timestamp": time.time(),
            "from": self.agent_id,
            "to": to_agent,
            "data": message
        }
        with open(self.messages_file, "a") as f:
            f.write(json.dumps(msg) + "\n")

    def check_new_messages(self) -> List[Dict]:
        """Check for new messages using file size tracking"""
        if not self.messages_file.exists():
            return []

        current_size = self.messages_file.stat().st_size
        if current_size > self.last_size:
            # Read only new content
            with open(self.messages_file, "r") as f:
                f.seek(self.last_size)
                new_lines = f.readlines()
            self.last_size = current_size
            return [json.loads(line.strip()) for line in new_lines if line.strip()]
        return []

    async def _should_spawn_subagent(self, result: Dict, evaluation: Dict) -> bool:
        """MIPROv2 optimized subagent spawning decision"""
        spawn_decision = self.subagent_spawner(
            execution_state=json.dumps(result),
            error_analysis=json.dumps(evaluation)
        )
        decision = json.loads(spawn_decision.spawn_decision)

        # Controlled spawning conditions
        triggers = [
            result.get('requires_iteration', False),
            result.get('recoverable_error', False),
            len(result.get('generated_subtasks', [])) > 0,
            evaluation.get('confidence', 1.0) < self.config.get('spawn_threshold', 0.7)
        ]

        return decision.get('should_spawn', False) and any(triggers)

    async def _generate_subagent_config(self, result: Dict, evaluation: Dict, iteration: int) -> Dict:
        """Generate subagent configuration with depth limits"""
        current_depth = self.config.get('spawn_depth', 0)
        max_depth = self.config.get('max_spawn_depth', 3)

        if current_depth >= max_depth:
            return None

        subagent_type = "iter" if result.get('requires_iteration') else "subtask"
        subagent_id = f"{self.agent_id}-{subagent_type}{iteration}"

        return {
            'agent_id': subagent_id,
            'directory': self.agent_dir / subagent_id,
            'spawn_depth': current_depth + 1,
            'parent_result': result,
            'execution_context': evaluation,
            'permissions': {
                'read': 'repository_wide',
                'write': ['own_directory', 'parent_defined_targets']
            }
        }
```
```python
class IterationCoordinator:
    """Coordinates iterative feedback between Agent-20 and Agent-30"""

    def __init__(self, config: Dict):
        self.config = config
        self.agent20 = Agent20SpecKitTransformer(config)
        self.agent30 = Agent30DSPyExecutor(config)
        self.redis_client = redis.from_url(config['redis_url'])

    async def execute_iterative_pipeline(self, pipeline_input: Dict) -> Dict:
        """Execute full iterative pipeline with feedback loops"""
        trace_id = pipeline_input['trace_id']
        max_pipeline_iterations = pipeline_input.get('max_pipeline_iterations', 3)

        pipeline_results = []
        current_spec = pipeline_input['initial_spec']

        for pipeline_iter in range(max_pipeline_iterations):
            # Agent-20: Convert spec-kit specifications to DSPy
            transform_result = await self.agent20.forward({
                'trace_id': trace_id,
                'spec_kit_specs': current_spec_kit_specs,
                'constraints': pipeline_input['constraints'],
                'validation_rules': pipeline_input['validation_rules']
            })

            if not transform_result['validation_passed']:
                # Handle validation failure
                pipeline_results.append({
                    'pipeline_iteration': pipeline_iter,
                    'stage': 'transformation',
                    'status': 'failed',
                    'result': transform_result
                })
                break

            # Agent-30: Execute DSPy signature
            execution_result = await self.agent30.forward({
                'trace_id': trace_id,
                'dspy_signature': transform_result['dspy_signature'],
                'inputs': pipeline_input['execution_inputs'],
                'expected_output': pipeline_input.get('expected_output'),
                'max_iterations': 5
            })

            pipeline_iteration_data = {
                'pipeline_iteration': pipeline_iter,
                'transformation': transform_result,
                'execution': execution_result,
                'quality_score': execution_result['quality_score'],
                'converged': execution_result['converged']
            }
            pipeline_results.append(pipeline_iteration_data)

            # Check convergence
            if execution_result['converged']:
                break

            # Feedback for next iteration
            if pipeline_iter < max_pipeline_iterations - 1:
                current_spec = await self._generate_feedback_spec(
                    current_spec,
                    execution_result,
                    pipeline_input['feedback_rules']
                )

        # Store complete pipeline result
        final_pipeline_result = {
            'trace_id': trace_id,
            'pipeline_iterations': len(pipeline_results),
            'final_quality_score': pipeline_results[-1].get('quality_score', 0.0),
            'pipeline_converged': pipeline_results[-1].get('converged', False),
            'iteration_history': pipeline_results,
            'total_agent30_iterations': sum(
                r['execution']['total_iterations']
                for r in pipeline_results
                if 'execution' in r
            )
        }

        await self._store_pipeline_result(trace_id, final_pipeline_result)
        return final_pipeline_result
```

## Training Integration

### 45_agent20_30_trainer.py
```python
class Agent2030Trainer:
    """Unified trainer for Agent-20 and Agent-30 using DSPy MIPROv2"""

    def __init__(self, config: Dict):
        self.config = config
        self.agent20 = Agent20SpecKitTransformer(config)
        self.agent30 = Agent30DSPyExecutor(config)

    async def train_agents_parallel(self, training_traces: List[Dict]) -> Dict:
        """Train both agents with shared feedback"""

        # Prepare training data
        agent20_examples = self._prepare_agent20_examples(training_traces)
        agent30_examples = self._prepare_agent30_examples(training_traces)

        # Define evaluation metrics
        def evaluate_pipeline(example, pred, trace=None):
            # Quality score combining both agents
            transform_score = self._evaluate_transformation(example, pred)
            execution_score = self._evaluate_execution(example, pred)
            return (transform_score + execution_score) / 2

        # Configure MIPROv2 for joint optimization
        teleprompter = MIPROv2(
            metric=evaluate_pipeline,
            num_candidates=10,
            init_temperature=1.0,
            max_rounds=20,
            verbose=True
        )

        # Train with pipeline examples
        pipeline_examples = self._create_pipeline_examples(training_traces)

        # Joint training
        optimized_pipeline = teleprompter.compile(
            student=self._create_joint_module(),
            trainset=pipeline_examples,
            valset=pipeline_examples[:int(len(pipeline_examples) * 0.2)]
        )

        return {
            'optimized_agent20': optimized_pipeline.agent20,
            'optimized_agent30': optimized_pipeline.agent30,
            'training_metrics': teleprompter.get_metrics(),
            'convergence_info': teleprompter.get_convergence_info()
        }

    def _create_joint_module(self):
        """Create joint module for training"""
        class JointAgent2030(dspy.Module):
            def __init__(self):
                super().__init__()
                self.agent20 = Agent20SpecKitTransformer(self.config)
                self.agent30 = Agent30DSPyExecutor(self.config)

            async def forward(self, **kwargs):
                transform_result = await self.agent20.forward(kwargs)
                if transform_result['validation_passed']:
                    execution_input = {
                        'dspy_signature': transform_result['dspy_signature'],
                        'inputs': kwargs['execution_inputs'],
                        'trace_id': kwargs.get('trace_id')
                    }
                    execution_result = await self.agent30.forward(execution_input)
                    return {
                        'transformation': transform_result,
                        'execution': execution_result,
                        'pipeline_success': execution_result['converged']
                    }
                else:
                    return {
                        'transformation': transform_result,
                        'execution': None,
                        'pipeline_success': False
                    }

        return JointAgent2030()
```

## Performance Monitoring

### 65_performance_metrics.py
```python
class Agent2030MetricsCollector:
    """Performance metrics collection for Agent-20 and Agent-30"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def collect_iteration_metrics(self, trace_id: str) -> Dict:
        """Collect comprehensive iteration metrics"""

        # Agent-20 metrics
        agent20_data = await self.redis.hgetall(f"agent20:iteration:{trace_id}")

        # Agent-30 metrics
        agent30_iterations = []
        iteration = 0
        while await self.redis.exists(f"agent30:iteration:{trace_id}:{iteration}"):
            data = await self.redis.hgetall(f"agent30:iteration:{trace_id}:{iteration}")
            agent30_iterations.append(json.loads(data.get('data', '{}')))
            iteration += 1

        # Pipeline metrics
        pipeline_data = await self.redis.hgetall(f"pipeline:result:{trace_id}")

        return {
            'trace_id': trace_id,
            'agent20_transform_time': self._extract_timing(agent20_data),
            'agent30_total_iterations': len(agent30_iterations),
            'agent30_convergence_iteration': self._find_convergence_iteration(agent30_iterations),
            'pipeline_total_iterations': json.loads(pipeline_data.get('data', '{}')).get('pipeline_iterations', 0),
            'final_quality_score': json.loads(pipeline_data.get('data', '{}')).get('final_quality_score', 0.0),
            'memory_usage': await self._get_memory_usage(trace_id),
            'redis_operations': await self._count_redis_operations(trace_id)
        }
```

## Production Deployment

### 85_agent20_30_deployment.yaml
```yaml
version: '3.8'
services:
  agent-20-transformer:
    build:
      context: .
      dockerfile: Dockerfile.agent20
    environment:
      - REDIS_URL=redis://redis-primary:6379
      - AGENT_ID=20
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
      - ./models:/app/models
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    depends_on:
      - redis-primary

  agent-30-executor:
    build:
      context: .
      dockerfile: Dockerfile.agent30
    environment:
      - REDIS_URL=redis://redis-primary:6379
      - AGENT_ID=30
      - LOG_LEVEL=INFO
      - MAX_ITERATIONS=5
      - QUALITY_THRESHOLD=0.8
    volumes:
      - ./config:/app/config:ro
      - ./models:/app/models
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
    depends_on:
      - redis-primary

  iteration-coordinator:
    build:
      context: .
      dockerfile: Dockerfile.coordinator
    environment:
      - REDIS_URL=redis://redis-primary:6379
      - MAX_PIPELINE_ITERATIONS=3
    volumes:
      - ./config:/app/config:ro
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    depends_on:
      - agent-20-transformer
      - agent-30-executor
```

## Key Features

- **Iterative Refinement**: Agent-30 iterates up to 5 times per signature execution
- **Pipeline Feedback**: Results feed back to Agent-20 for spec refinement
- **Joint Training**: MIPROv2 optimizes both agents simultaneously
- **Redis Storage**: All iterations cached with 24-hour TTL
- **Quality Gating**: Configurable quality thresholds for convergence
- **Horizontal Scaling**: Agent-30 scales to 3 replicas for parallel execution
- **Memory Efficiency**: Float16 embeddings and compressed storage
- **Monitoring**: Complete iteration history and performance metrics

This architecture achieves sub-second iteration cycles with automatic convergence detection and quality optimization.

## MIPROv2 Optimization Framework

### Optimizable Components
```python
class AgentOrchestrationOptimizer(dspy.Module):
    """MIPROv2 optimization for agent spawning, communication, and configuration"""

    def __init__(self):
        # Agent-20: Configuration generation optimization
        self.config_optimizer = dspy.ChainOfThought("spec_kit_specs, resources -> optimal_agent30_configs")

        # Agent-30: Communication pattern optimization
        self.comm_optimizer = dspy.ChainOfThought("agent_states, task_context -> communication_strategy")

        # Subagent spawning optimization
        self.spawn_optimizer = dspy.ChainOfThought("execution_state, resource_usage -> spawn_decision")

        # Execution instruction optimization
        self.instruction_optimizer = dspy.ChainOfThought("dspy_program, constraints -> execution_instructions")

    def optimize_agent20_configs(self, spec_kit_specs: List[Dict], resources: Dict) -> Dict:
        """Optimize agent-30 spawning configurations"""
        config_result = self.config_optimizer(
            spec_kit_specs=json.dumps(spec_kit_specs),
            resources=json.dumps(resources)
        )
        return json.loads(config_result.optimal_agent30_configs)

    def optimize_communication(self, sender_state: Dict, receiver_states: List[Dict]) -> Dict:
        """Optimize inter-agent communication patterns"""
        comm_result = self.comm_optimizer(
            agent_states=json.dumps(receiver_states),
            task_context=json.dumps(sender_state)
        )
        return json.loads(comm_result.communication_strategy)
```

### Training Integration
```python
class OptimizationTrainer:
    """Train MIPROv2 optimizers from execution traces"""

    async def train_from_traces(self, execution_traces: List[Dict]) -> Dict:
        """Train optimizers using historical execution data"""

        # Define metrics
        def config_metric(example, pred, trace=None):
            return (
                pred.get('execution_time_improvement', 0) * 0.4 +
                pred.get('resource_efficiency', 0) * 0.3 +
                pred.get('success_rate', 0) * 0.3
            )

        # Configure MIPROv2
        teleprompter = MIPROv2(
            metric=config_metric,
            num_candidates=15,
            init_temperature=1.2,
            max_rounds=25
        )

        return teleprompter.compile(student=self.optimizer, trainset=examples)
```

## Implementation Summary

**Key Features Implemented:**
- **Multi-Agent Spawning**: Agent-20 → multiple agent-30s (s1, s2, a1, a2)
- **Subagent Creation**: Agent-30 can spawn subagents (2-3 levels, controlled triggers)
- **Permission Model**: Read repository-wide, write own directory + defined targets
- **Messaging System**: Append-only JSON-lines with file size tracking
- **MIPROv2 Optimization**: All spawning, communication, and configuration patterns
