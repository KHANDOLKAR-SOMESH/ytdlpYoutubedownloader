#!/bin/bash
chmod +x start.sh
gunicorn --bind 0.0.0.0:10000 app:app
