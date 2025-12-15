"""
Error tracking with Sentry
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from app.config import settings

def init_sentry():
    """
    Initialize Sentry for error tracking
    """
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration()
            ],
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            environment=settings.ENVIRONMENT,
            release=f"academic-advisor@{settings.APP_VERSION}",
            attach_stacktrace=True,
            send_default_pii=False,
            before_send=before_send_filter,
            before_send_transaction=before_send_transaction_filter
        )

def before_send_filter(event, hint):
    """
    Filter sensitive data before sending to Sentry
    """
    # Remove sensitive data
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        
        # Remove authorization headers
        headers.pop('authorization', None)
        headers.pop('cookie', None)
        
    # Remove passwords from data
    if 'extra' in event:
        for key in list(event['extra'].keys()):
            if 'password' in key.lower():
                del event['extra'][key]
    
    return event

def before_send_transaction_filter(event, hint):
    """
    Filter transactions before sending
    """
    # Don't send health check transactions
    if event.get('transaction') == '/health':
        return None
    
    return event

def capture_exception(error: Exception, **kwargs):
    """
    Capture exception with additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_exception(error)

def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture message with context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_message(message, level=level)