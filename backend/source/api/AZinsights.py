import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor


logger=logging.getLogger("brand-guardian-telemetry")

def setup_telemetry():
    '''
    Initializes Azure monitor OpenTelemetry
    Tracks:errors,hhtp requests,database queries,performance metrics ,etc etc

    Auto captures every API request
    no need to manually log each end point
    '''

    #retrive the connection string
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        logger.warning("No Insights key Found............... ")
        return

    #Configure the azure monitor
    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="brand-guardian-tracer"
        )
        logger.info("Azure monitor tracking enabled")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Monitor: {e}")