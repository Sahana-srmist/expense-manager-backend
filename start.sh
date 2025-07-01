#!/bin/bash
echo "? Running Uvicorn..."
uvicorn main:app --host 0.0.0.0 --port $PORT
