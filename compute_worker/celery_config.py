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
# Connection timeout in seconds (default: 4.0)
broker_connection_timeout = float(os.environ.get('BROKER_CONNECTION_TIMEOUT', 30.0))
# Whether to retry connection on connection failure
broker_connection_retry = os.environ.get('BROKER_CONNECTION_RETRY', 'True').lower() == 'true'
# Whether to retry connection on startup
broker_connection_retry_on_startup = os.environ.get('BROKER_CONNECTION_RETRY_ON_STARTUP', 'True').lower() == 'true'
# Maximum number of connection retries
broker_connection_max_retries = int(os.environ.get('BROKER_CONNECTION_MAX_RETRIES', 10))
