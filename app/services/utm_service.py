"""
UTM Parameter Tracking Service.

Lightweight, privacy-conscious attribution service for educational/project analytics.
Captures standard UTM parameters in the user's session without external transmission
or tracking of sensitive authentication data.
"""

import re
from flask import request, session

VALID_UTM_PARAMS = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content')
MAX_PARAM_LENGTH = 100
SAFE_PARAM_REGEX = re.compile(r'^[a-zA-Z0-9_\-\.\+ ]+$')


def sanitize_utm_value(value):
    """Sanitize and validate a UTM parameter value to prevent unsafe inputs."""
    if not value or not isinstance(value, str):
        return None
    val = value.strip()[:MAX_PARAM_LENGTH]
    if SAFE_PARAM_REGEX.match(val):
        return val
    return None


def capture_utm_parameters():
    """
    Extracts UTM parameters from the current request query string
    and stores them in the session if valid.
    Respects user privacy: only stores attribution metadata.
    """
    if not request.args:
        return

    incoming_utm = {}
    for param in VALID_UTM_PARAMS:
        raw_val = request.args.get(param)
        if raw_val:
            sanitized = sanitize_utm_value(raw_val)
            if sanitized:
                incoming_utm[param] = sanitized

    if incoming_utm:
        # Retrieve existing or initialize
        current_utm = session.get('utm_data', {})
        current_utm.update(incoming_utm)
        session['utm_data'] = current_utm
