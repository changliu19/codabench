import os
import ssl

broker_url = os.environ.get('BROKER_URL')
if os.environ.get('BROKER_USE_SSL', False):
    broker_use_ssl = {
        "cert_reqs": ssl.CERT_NONE,
    }
worker_concurrency = 1
worker_prefetch_multiplier = 1
task_acks_late = True

# AMQP connection timeout settings
broker_connection_timeout = float(os.environ.get('BROKER_CONNECTION_TIMEOUT', 30.0))
broker_connection_retry = os.environ.get('BROKER_CONNECTION_RETRY', 'True').lower() == 'true'
broker_connection_retry_on_startup = os.environ.get(
    'BROKER_CONNECTION_RETRY_ON_STARTUP', 'True'
).lower() == 'true'
broker_connection_max_retries = int(os.environ.get('BROKER_CONNECTION_MAX_RETRIES', 10))
