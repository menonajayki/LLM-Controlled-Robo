# Robot Control with Groq API

## Overview
- The robot operates via Groq API.
- A Finite State Machine (FSM) ensures safety.
- Additional FSM states can be added to perform more complex tasks.
- Uses MQTT for communication and ROS 1 as a listener for triggers.

## Setup
1. Add `.env` file with necessary keys.
2. Configure the input prompt to define FSM states.
3. Run: `docker-compose up -d`

## ⚠ Warning  
This is a test script. Ensure safety measures before deploying.