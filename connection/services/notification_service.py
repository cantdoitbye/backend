import os
import aiohttp
import asyncio
from typing import List
from settings.base import NOTIFICATION_SERVICE_URL

class NotificationService:
    def __init__(self):
        self.notification_service_url = NOTIFICATION_SERVICE_URL

  
    async def notifyConnectionRequest(self, sender_name: str, receiver_device_id: str, connection_id: str):
        """
        Send notification to receiver about new connection request
        """
        print("Starting connection request notification...")
        print("Notification URL:", self.notification_service_url)
        print("Sender:", sender_name)
        print("Receiver device ID:", receiver_device_id)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"New connection request from {sender_name}",
            "body": "Someone wants to connect with you!",
            "token": receiver_device_id,
            "priority": "high",
            "click_action": f"/connection/{connection_id}",
            "data": {
                "connection_id": connection_id,
                "type": "connection_request"
            }
        }
        
        print("Sending connection request notification...")
        print("Notification data:", notification_data)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.notification_service_url}/notifications",
                    json=notification_data,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    print(f"Response status: {response.status}")
                    print(f"Response body: {response_text}")
                    if response.status != 200:
                        print(f"Error response: {response_text}")
            except Exception as e:
                print(f"Error sending connection request notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifyConnectionAccepted(self, receiver_name: str, sender_device_id: str, connection_id: str):
        """
        Send notification to sender about accepted connection
        """
        print("Starting connection accepted notification...")
        print("Notification URL:", self.notification_service_url)
        print("Receiver:", receiver_name)
        print("Sender device ID:", sender_device_id)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"{receiver_name} accepted your connection request",
            "body": "You are now connected!",
            "token": sender_device_id,
            "priority": "high",
            "click_action": f"/connection/{connection_id}",
            "data": {
                "connection_id": connection_id,
                "type": "connection_accepted"
            }
        }
        
        print("Sending connection accepted notification...")
        print("Notification data:", notification_data)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.notification_service_url}/notifications",
                    json=notification_data,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    print(f"Response status: {response.status}")
                    print(f"Response body: {response_text}")
                    if response.status != 200:
                        print(f"Error response: {response_text}")
            except Exception as e:
                print(f"Error sending connection accepted notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}")

    async def notifyConnectionRejected(self, receiver_name: str, sender_device_id: str, connection_id: str):
        """
        Send notification to sender about rejected connection
        """
        print("Starting connection rejected notification...")
        print("Notification URL:", self.notification_service_url)
        print("Receiver:", receiver_name)
        print("Sender device ID:", sender_device_id)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        notification_data = {
            "title": f"{receiver_name} declined your connection request",
            "body": "Your connection request was not accepted",
            "token": sender_device_id,
            "priority": "high",
            "click_action": f"/connection/{connection_id}",
            "data": {
                "connection_id": connection_id,
                "type": "connection_rejected"
            }
        }
        
        print("Sending connection rejected notification...")
        print("Notification data:", notification_data)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.notification_service_url}/notifications",
                    json=notification_data,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    print(f"Response status: {response.status}")
                    print(f"Response body: {response_text}")
                    if response.status != 200:
                        print(f"Error response: {response_text}")
            except Exception as e:
                print(f"Error sending connection rejected notification: {str(e)}")
                print(f"Full error details: {type(e).__name__}: {str(e)}") 