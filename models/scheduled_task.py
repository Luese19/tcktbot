"""Scheduled task data model for admin task scheduling"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class TaskType(str, Enum):
    """Types of tasks that can be scheduled"""
    SEND_MESSAGE = "send_message"
    ESCALATE_TICKET = "escalate_ticket"
    RUN_CLEANUP = "run_cleanup"
    SEND_REMINDER = "send_reminder"
    GENERATE_REPORT = "generate_report"
    CREATE_TICKET = "create_ticket"


class ScheduleType(str, Enum):
    """Types of schedules"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CRON = "cron"


class TaskStatus(str, Enum):
    """Task status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


@dataclass
class ExecutionLog:
    """Log entry for a task execution"""
    executed_at: datetime
    status: str  # success, failed
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'executed_at': self.executed_at.isoformat(),
            'status': self.status,
            'error': self.error,
            'result': self.result
        }

    @staticmethod
    def from_dict(data: dict) -> 'ExecutionLog':
        """Create from dictionary"""
        return ExecutionLog(
            executed_at=datetime.fromisoformat(data['executed_at']),
            status=data['status'],
            error=data.get('error'),
            result=data.get('result')
        )


@dataclass
class ScheduledTask:
    """Represents an admin-scheduled task"""
    task_id: str
    task_type: TaskType
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]  # Contains time info (once: {datetime}, daily: {time}, cron: {expression}, etc.)
    action_params: Dict[str, Any]  # Task-specific parameters
    status: TaskStatus = TaskStatus.ACTIVE
    created_by: int = 0  # Admin user_id
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    next_run: Optional[datetime] = None
    execution_logs: list = field(default_factory=list)  # List of ExecutionLog objects

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.value,
            'schedule_type': self.schedule_type.value,
            'schedule_config': self.schedule_config,
            'action_params': self.action_params,
            'status': self.status.value,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'execution_logs': [log.to_dict() if hasattr(log, 'to_dict') else log for log in self.execution_logs]
        }

    @staticmethod
    def from_dict(data: dict) -> 'ScheduledTask':
        """Create from dictionary"""
        # Parse execution logs
        logs = []
        for log_data in data.get('execution_logs', []):
            if isinstance(log_data, dict):
                logs.append(ExecutionLog.from_dict(log_data))
            else:
                logs.append(log_data)

        return ScheduledTask(
            task_id=data['task_id'],
            task_type=TaskType(data['task_type']),
            schedule_type=ScheduleType(data['schedule_type']),
            schedule_config=data['schedule_config'],
            action_params=data['action_params'],
            status=TaskStatus(data.get('status', 'active')),
            created_by=data.get('created_by', 0),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data.get('updated_at', data['created_at'])),
            last_triggered=datetime.fromisoformat(data['last_triggered']) if data.get('last_triggered') else None,
            next_run=datetime.fromisoformat(data['next_run']) if data.get('next_run') else None,
            execution_logs=logs
        )

    def add_execution_log(self, status: str, error: Optional[str] = None, result: Optional[Dict] = None):
        """Add an execution log entry"""
        log = ExecutionLog(
            executed_at=datetime.now(),
            status=status,
            error=error,
            result=result
        )
        self.execution_logs.append(log)
        # Keep only last 20 logs
        if len(self.execution_logs) > 20:
            self.execution_logs = self.execution_logs[-20:]
        self.last_triggered = datetime.now()
        self.updated_at = datetime.now()
