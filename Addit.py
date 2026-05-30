from twilio.rest import Client

account_sid = 'ACd396c383470f2ea4d9a402d6f1a953d9'
auth_token = 'bfe0278462b2bffc0cb8832a6b0e76cc'
client = Client(account_sid, auth_token)

# Теперь должно работать (номер подтвержден)
verification = client.verify.v2.services('VAa9ec4ff236ba4b5a2380b3248fcf47cd').verifications.create(
    to='+77089249375',
    channel='sms'  # или 'whatsapp'
)

print(f"Status: {verification.status}")