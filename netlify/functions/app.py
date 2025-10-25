import json
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import app

def handler(event, context):
    """Netlify function handler for Flask app"""
    try:
        # Parse the event
        path = event.get('path', '/')
        http_method = event.get('httpMethod', 'GET')
        headers = event.get('headers', {})
        query_string = event.get('queryStringParameters', {}) or {}
        body = event.get('body', '')
        
        # Create a mock WSGI environment
        environ = {
            'REQUEST_METHOD': http_method,
            'PATH_INFO': path,
            'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in query_string.items()]),
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': str(len(body)),
            'wsgi.input': body,
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Add headers to environ
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            environ[key] = value
        
        # Call the Flask app
        response_data = []
        
        def start_response(status, response_headers, exc_info=None):
            response_data.append(status)
            response_data.append(response_headers)
        
        response_body = app(environ, start_response)
        
        # Convert response to Netlify format
        status_code = int(response_data[0].split()[0])
        headers = dict(response_data[1])
        
        # Join response body
        if isinstance(response_body, list):
            body = ''.join([chunk.decode() if isinstance(chunk, bytes) else str(chunk) for chunk in response_body])
        else:
            body = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': body
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'Internal Server Error: {str(e)}'
        }
