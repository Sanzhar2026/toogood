# backend/twilio_service.py
import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID')
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

# Basic authentication for Twilio
auth_string = f"{ACCOUNT_SID}:{AUTH_TOKEN}"
auth_bytes = auth_string.encode('ascii')
base64_auth = base64.b64encode(auth_bytes).decode('ascii')

async def send_verification_code(phone_number: str):
    """
    Send verification code via SMS to any phone number
    Supports international numbers including Kazakhstan (+7)
    """
    
    # DEMO MODE: No actual SMS sending, just print code
    if DEMO_MODE:
        print(f"📱 [DEMO MODE] Verification code for {phone_number}: 123456")
        print(f"💡 In production, this would send an actual SMS")
        return {
            'success': True, 
            'demo': True, 
            'message': 'Demo mode: Use code 123456',
            'channel': 'sms'
        }
    
    # Check if Twilio credentials are configured
    if not ACCOUNT_SID or not AUTH_TOKEN or not VERIFY_SERVICE_SID:
        print("❌ Twilio credentials missing! Check your .env file")
        return {
            'success': False,
            'error': 'SMS service not configured. Please check .env file',
            'demo': True,
            'fallback_code': '123456'
        }
    
    async with httpx.AsyncClient() as client:
        # Format phone number (add + if missing)
        formatted_number = phone_number
        if not formatted_number.startswith('+'):
            formatted_number = '+' + formatted_number
        
        print(f"📤 Sending SMS verification to: {formatted_number}")
        print(f"🔧 Using Verify Service: {VERIFY_SERVICE_SID}")
        
        try:
            response = await client.post(
                f'https://verify.twilio.com/v2/Services/{VERIFY_SERVICE_SID}/Verifications',
                data={
                    'To': formatted_number,
                    'Channel': 'sms'  # Changed from 'whatsapp' to 'sms'
                },
                headers={
                    'Authorization': f'Basic {base64_auth}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=30.0  # 30 second timeout
            )
            
            result = response.json()
            print(f"📥 Twilio response status: {response.status_code}")
            print(f"📥 Response body: {result}")
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'demo': False,
                    'status': result.get('status'),
                    'channel': 'sms',
                    'to': formatted_number,
                    'message': 'Verification code sent via SMS! Check your phone.',
                    'sid': result.get('sid')
                }
            else:
                # Handle specific Twilio errors
                error_code = result.get('code')
                error_message = result.get('message', 'Failed to send SMS')
                
                # User-friendly error messages
                if error_code == 21610:
                    user_message = "Too many requests. Please wait a minute and try again."
                elif error_code == 21211:
                    user_message = "Invalid phone number format. Please use international format (+7XXXXXXXXXX)"
                elif error_code == 21408:
                    user_message = "Cannot send SMS to this number. Please check the number."
                else:
                    user_message = error_message
                
                print(f"❌ Twilio error {error_code}: {error_message}")
                
                return {
                    'success': False,
                    'error': user_message,
                    'code': error_code,
                    'demo': False
                }
                
        except httpx.TimeoutException:
            print("❌ Request timeout")
            return {
                'success': False,
                'error': 'Request timed out. Please try again.',
                'demo': False
            }
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'demo': False
            }


async def verify_code(phone_number: str, code: str):
    """
    Verify the 6-digit code entered by user
    """
    
    # DEMO MODE: Accept 123456 as valid code
    if DEMO_MODE:
        is_valid = (code == "123456")
        print(f"🔐 [DEMO MODE] Code verification for {phone_number}: {code} -> {is_valid}")
        return {
            'success': is_valid,
            'demo': True,
            'message': 'Phone verified successfully!' if is_valid else 'Invalid code. Try 123456',
            'status': 'approved' if is_valid else 'pending'
        }
    
    # Check credentials
    if not ACCOUNT_SID or not AUTH_TOKEN or not VERIFY_SERVICE_SID:
        print("❌ Twilio credentials missing!")
        return {
            'success': False,
            'error': 'SMS service not configured',
            'fallback_valid': (code == "123456")  # Fallback for testing
        }
    
    async with httpx.AsyncClient() as client:
        # Format phone number
        formatted_number = phone_number
        if not formatted_number.startswith('+'):
            formatted_number = '+' + formatted_number
        
        print(f"🔐 Verifying code {code} for {formatted_number}")
        
        try:
            response = await client.post(
                f'https://verify.twilio.com/v2/Services/{VERIFY_SERVICE_SID}/VerificationCheck',
                data={
                    'To': formatted_number,
                    'Code': code
                },
                headers={
                    'Authorization': f'Basic {base64_auth}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=30.0
            )
            
            result = response.json()
            print(f"📥 Verification response: {result}")
            
            if response.status_code == 200 and result.get('status') == 'approved':
                return {
                    'success': True,
                    'message': 'Phone verified successfully!',
                    'status': result.get('status'),
                    'demo': False
                }
            else:
                error_msg = result.get('message', 'Invalid verification code')
                return {
                    'success': False,
                    'error': error_msg,
                    'status': result.get('status'),
                    'demo': False
                }
                
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timed out. Please try again.',
                'demo': False
            }
        except Exception as e:
            print(f"❌ Verification error: {str(e)}")
            return {
                'success': False,
                'error': f'Verification failed: {str(e)}',
                'demo': False
            }


async def check_verification_status(phone_number: str):
    """
    Check if a phone number is already verified (optional)
    """
    if DEMO_MODE:
        return {
            'success': True,
            'status': 'pending',
            'demo': True
        }
    
    async with httpx.AsyncClient() as client:
        formatted_number = phone_number
        if not formatted_number.startswith('+'):
            formatted_number = '+' + formatted_number
        
        try:
            response = await client.get(
                f'https://verify.twilio.com/v2/Services/{VERIFY_SERVICE_SID}/Verifications',
                params={'To': formatted_number},
                headers={'Authorization': f'Basic {base64_auth}'}
            )
            
            result = response.json()
            return {
                'success': True,
                'status': result.get('status', 'unknown')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }