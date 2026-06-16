#!/usr/bin/env python3
"""
Cisco Security Cloud Control AI Assistant API Client

⚠️  WIP - WORK IN PROGRESS ⚠️
The AI Assistant API endpoint (/v1/ai-assistant/conversations) is currently
returning 400 errors and appears to not be fully deployed in production yet.
This script is ready to use once the endpoint becomes available.

For now, use the FMC agent (@FMC) or direct API calls to query device information.

This script provides a complete example for interacting with the SCC AI Assistant API.
It demonstrates how to send questions and retrieve AI-generated responses for
security management tasks.

Prerequisites:
    1. Set up hosts.sh with required credentials
    2. Load environment: set -a; source hosts.sh; set +a
    3. Install dependencies: pip install requests

Environment Variables (from hosts.sh):
    - SCC_FMC_API_KEY: Your SCC Firewall Manager API token
    - SCC_EDGE_URL: SCC Firewall API endpoint

Usage:
    python scc_ai_assistant.py "How to create VLAN on remote FTD?"
    
    Or run interactively:
    python scc_ai_assistant.py
"""

import requests
import json
import os
import sys
import time
from typing import Optional, Dict, Any

# Configuration from hosts.sh
SCC_FMC_API_KEY = os.getenv('SCC_FMC_API_KEY')
SCC_EDGE_URL = os.getenv('SCC_EDGE_URL')
SCC_ORG_UUID = os.getenv('SCC_ORG_UUID')
SCC_USERNAME = os.getenv('SCC_USERNAME')

# API Configuration
MAX_RETRIES = 60
RETRY_DELAY = 2  # seconds
API_TIMEOUT = 30  # seconds


class SCCAIAssistant:
    """Client for Cisco Security Cloud Control AI Assistant API"""
    
    def __init__(self, api_key: str, base_url: str, org_uuid: str = None, username: str = None):
        """
        Initialize the AI Assistant client.
        
        Args:
            api_key: SCC API token (Bearer token)
            base_url: Regional SCC API base URL
            org_uuid: Organization UUID
            username: SCC username
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add optional AI Assistant headers
        if org_uuid:
            headers['x-aiassistant-orgid'] = org_uuid
            headers['x-aiassistant-tenant-id'] = org_uuid
        if username:
            headers['x-aiassistant-username'] = username
            
        self.session.headers.update(headers)
    
    def send_request(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Send a request to the AI Assistant and create a new conversation.
        
        Args:
            content: The question or prompt to send to the AI Assistant
            
        Returns:
            Response dictionary containing conversation UID and metadata,
            or None if the request failed
        """
        url = f"{self.base_url}/v1/ai-assistant/conversations"
        payload = {"content": content}
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"✓ Request sent successfully")
            print(f"  Conversation ID: {data.get('uid', 'N/A')}")
            return data
            
        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Request Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON response: {e}")
            return None
    
    def get_response(self, conversation_uid: str) -> Optional[str]:
        """
        Poll for the AI Assistant response with retry logic.
        
        Args:
            conversation_uid: The unique identifier of the conversation
            
        Returns:
            The AI Assistant's response content, or None if retrieval failed
        """
        url = f"{self.base_url}/v1/ai-assistant/conversations/{conversation_uid}/messages"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=API_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                # Check response status
                status = data.get('status', 'unknown')
                
                if status == 'completed':
                    return data.get('content', data.get('response', ''))
                    
                elif status == 'failed':
                    error_msg = data.get('error', 'Unknown error')
                    print(f"✗ AI Assistant request failed: {error_msg}")
                    return None
                    
                elif status in ['pending', 'processing']:
                    # Still processing, wait and retry
                    print(f"⏳ Processing... (attempt {attempt + 1}/{MAX_RETRIES})", end='\r')
                    time.sleep(RETRY_DELAY)
                    
                else:
                    # Unknown status, continue polling
                    print(f"⏳ Status: {status} (attempt {attempt + 1}/{MAX_RETRIES})", end='\r')
                    time.sleep(RETRY_DELAY)
                    
            except requests.exceptions.HTTPError as e:
                print(f"\n✗ HTTP Error: {e.response.status_code}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"\n✗ Request Error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return None
        
        print(f"\n✗ Timeout: No response after {MAX_RETRIES * RETRY_DELAY} seconds")
        return None
    
    def ask(self, question: str) -> Optional[str]:
        """
        Complete workflow: send a question and get the AI Assistant's response.
        
        Args:
            question: The question to ask the AI Assistant
            
        Returns:
            The AI Assistant's response, or None if the operation failed
        """
        print(f"\n{'=' * 80}")
        print(f"📝 Question: {question}")
        print(f"{'=' * 80}\n")
        
        # Step 1: Send the request
        result = self.send_request(question)
        if not result or 'uid' not in result:
            return None
        
        conversation_uid = result['uid']
        
        # Step 2: Poll for response
        print("⏳ Waiting for AI Assistant response...")
        response = self.get_response(conversation_uid)
        
        if response:
            print(f"\n{'=' * 80}")
            print(f"💬 AI Assistant Response:")
            print(f"{'=' * 80}")
            print(response)
            print(f"{'=' * 80}\n")
            return response
        else:
            print("\n✗ Failed to get response from AI Assistant")
            return None


def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if environment is properly configured, False otherwise
    """
    if not SCC_FMC_API_KEY:
        print("✗ Error: SCC_FMC_API_KEY not set")
        print("  Please load environment: set -a; source hosts.sh; set +a")
        return False
    
    if not SCC_EDGE_URL:
        print("✗ Error: SCC_EDGE_URL not set")
        print("  Please configure hosts.sh with the SCC Firewall API endpoint")
        return False
    
    print(f"✓ Environment configured")
    print(f"  Endpoint: {SCC_EDGE_URL}")
    print(f"  Token: {SCC_FMC_API_KEY[:10]}...{SCC_FMC_API_KEY[-4:] if len(SCC_FMC_API_KEY) > 14 else ''}")
    
    return True


def interactive_mode(assistant: SCCAIAssistant):
    """
    Run the AI Assistant client in interactive mode.
    
    Args:
        assistant: The SCCAIAssistant instance
    """
    print("\n" + "=" * 80)
    print("  Cisco Security Cloud Control AI Assistant - Interactive Mode")
    print("=" * 80)
    print("\nType your questions below (or 'quit' to exit):\n")
    
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            assistant.ask(question)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except EOFError:
            print("\n\nEnd of input. Goodbye!")
            break


def main():
    """Main entry point for the script."""
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Initialize AI Assistant client
    assistant = SCCAIAssistant(SCC_FMC_API_KEY, SCC_EDGE_URL, SCC_ORG_UUID, SCC_USERNAME)
    
    # Check if question provided as command-line argument
    if len(sys.argv) > 1:
        # Single question mode
        question = ' '.join(sys.argv[1:])
        response = assistant.ask(question)
        sys.exit(0 if response else 1)
    else:
        # Interactive mode
        interactive_mode(assistant)


if __name__ == "__main__":
    main()
