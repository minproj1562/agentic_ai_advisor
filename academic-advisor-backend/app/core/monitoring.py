"""
Application monitoring and metrics
"""

import time
from functools import wraps
from typing import Any, Callable, Dict

import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Metrics
request_count = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'app_active_users',
    'Active users'
)

system_cpu = Gauge(
    'system_cpu_percent',
    'System CPU usage'
)

system_memory = Gauge(
    'system_memory_percent',
    'System memory usage'
)

ml_predictions = Counter(
    'ml_predictions_total',
    'Total ML predictions',
    ['model', 'status']
)

class MetricsCollector:
    """
    Collect and expose metrics
    """
    
    def __init__(self):
        self.start_time = time.time()
        
    def collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application metrics"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'system': self.collect_system_metrics(),
            'timestamp': time.time()
        }

# Global metrics collector
metrics_collector = MetricsCollector()

def track_request(endpoint: str):
    """Decorator to track requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                
                request_count.labels(
                    method='GET',
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                request_duration.labels(
                    method='GET',
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator

async def get_metrics():
    """Get Prometheus metrics"""
    return generate_latest()

async def get_application_metrics():
    """Get custom application metrics"""
    return metrics_collector.get_application_metrics()