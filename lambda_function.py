"""
Este archivo servirá como punto de entrada para AWS Lambda
"""
from app.main import handler

def lambda_handler(event, context):
    """
    Punto de entrada para AWS Lambda.
    Delega la ejecución al handler de Mangum.
    """
    return handler(event, context)