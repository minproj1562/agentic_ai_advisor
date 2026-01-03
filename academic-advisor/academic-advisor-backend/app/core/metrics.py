"""
Metrics and monitoring
Track API performance and ML model metrics
"""

import time
from functools import wraps
from typing import Dict, Any
import asyncio
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from app.core.logging import get_logger

logger = get_logger(__name__)

# Prometheus metrics
api_request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

ml_inference_count = Counter(
    'ml_inference_total',
    'Total ML model inferences',
    ['model', 'status']
)

ml_inference_duration = Histogram(
    'ml_inference_duration_seconds',
    'ML inference duration',
    ['model']
)

active_connections = Gauge(
    'websocket_active_connections',
    'Active WebSocket connections'
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# Decorators for tracking
def track_api_call(func):
    """
    Track API call metrics
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
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
            
            # Extract endpoint from function
            endpoint = func.__name__
            method = kwargs.get('request', {}).method if 'request' in kwargs else 'GET'
            
            api_request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            api_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            if duration > 1.0:  # Log slow requests
                logger.warning(f"Slow API call: {endpoint} took {duration:.2f}s")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        status = 'success'
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start_time
            
            endpoint = func.__name__
            method = 'GET'
            
            api_request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            api_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def track_ml_inference(func):
    """
    Track ML model inference metrics
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        status = 'success'
        model_name = kwargs.get('model', 'unknown')
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = 'error'
            logger.error(f"ML inference error in {model_name}: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            
            ml_inference_count.labels(
                model=model_name,
                status=status
            ).inc()
            
            ml_inference_duration.labels(
                model=model_name
            ).observe(duration)
            
            if duration > 0.5:  # Log slow inferences
                logger.warning(f"Slow ML inference: {model_name} took {duration:.2f}s")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        status = 'success'
        model_name = func.__name__
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start_time
            
            ml_inference_count.labels(
                model=model_name,
                status=status
            ).inc()
            
            ml_inference_duration.labels(
                model=model_name
            ).observe(duration)
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def track_service_call(func):
    """
    Track service layer calls
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            service_name = func.__qualname__.split('.')[0] if '.' in func.__qualname__ else 'unknown'
            
            if duration > 2.0:
                logger.warning(f"Slow service call: {func.__name__} in {service_name} took {duration:.2f}s")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            
            if duration > 2.0:
                logger.warning(f"Slow service call: {func.__name__} took {duration:.2f}s")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

# Metrics endpoint for Prometheus
def get_metrics():
    """
    Generate metrics in Prometheus format
    """
    return generate_latest()

# Custom metrics collection
class MetricsCollector:
    """
    Collect and aggregate custom metrics
    """
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Record a custom metric
        """
        key = f"{name}:{tags}" if tags else name
        
        if key not in self.metrics:
            self.metrics[key] = []
        
        self.metrics[key].append({
            'value': value,
            'timestamp': time.time(),
            'tags': tags or {}
        })
        
        # Keep only last 1000 data points
        if len(self.metrics[key]) > 1000:
            self.metrics[key] = self.metrics[key][-1000:]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary
        """
        summary = {
            'uptime_seconds': time.time() - self.start_time,
            'metrics': {}
        }
        
        for key, values in self.metrics.items():
            if values:
                metric_values = [v['value'] for v in values]
                summary['metrics'][key] = {
                    'count': len(values),
                    'mean': sum(metric_values) / len(metric_values),
                    'min': min(metric_values),
                    'max': max(metric_values),
                    'latest': values[-1]['value']
                }
        
        return summary

# Global metrics collector
metrics_collector = MetricsCollector()