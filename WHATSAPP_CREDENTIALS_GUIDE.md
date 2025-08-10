# WhatsApp Credentials Setup Guide

## Updated Integration: Baileys-Mod with JSON Credentials

### Changes Made
- **Switched to baileys-mod** from @whiskeysockets/baileys for better stability
- **JSON credentials support** instead of pairing codes
- **Environment variable loading** of session data
- **Enhanced connection handling** with better error reporting

### Required Environment Variable

**Variable Name**: `WHATSAPP_CREDS`
**Format**: JSON string containing WhatsApp session data

### Example Credentials Format
```json
{
  "noiseKey": {
    "private": {"type":"Buffer","data":"cBs5BvN8OLIyjtfqXDtr9YIEXKacvgZyjYJuwRr/G3Q="},
    "public": {"type":"Buffer","data":"rnEhLD+fk0HqLbEEW2w5JIdKQx4zjyFSVguyYOgkRW0="}
  },
  "pairingEphemeralKeyPair": {
    "private": {"type":"Buffer","data":"CLoUzs1hiQlnrsVUiCkvkXrUQNdeZZTen72yS3OnomI="},
    "public": {"type":"Buffer","data":"PaIDP3g4SUsrcSk34k3tvVEywQZqXcrOpfnCcB7cInc="}
  },
  "signedIdentityKey": {
    "private": {"type":"Buffer","data":"iAaytrgcHpxhDFo8n6CYM7SbSxYlrechTxG7k82L1VQ="},
    "public": {"type":"Buffer","data":"D1nNKmCd9kbog0u0lOqjm6eZPuanC/N2oG3516NGgxQ="}
  },
  "signedPreKey": {
    "keyPair": {
      "private": {"type":"Buffer","data":"EAsBQOjA3xE2RxRbgB2D9/6O8OViMlu3+b/0EcU9jU4="},
      "public": {"type":"Buffer","data":"odY0ONX+t/2a0H3KCr3p9iKKLu21Hqg+w3vZ0cCQMWU="}
    },
    "signature": {"type":"Buffer","data":"MlVJN52nLQRtGAVYkkl5y8mTZ4YpcwIyLIeIVaylTfWcrlgruP3LOKBnjrArULz1leJ+PurBwvuzjJePffVCgA=="},
    "keyId": 1
  },
  "registrationId": 191,
  "advSecretKey": "y7h/zcMJDWd2OADrEwUHPj1TWSI/XoPAMTqqQ2NI1d8=",
  "processedHistoryMessages": [],
  "nextPreKeyId": 31,
  "firstUnuploadedPreKeyId": 31,
  "accountSyncCounter": 0,
  "accountSettings": {"unarchiveChats": false},
  "deviceId": "ODs4GhpmQJ2t7YJfSITdfA",
  "phoneId": "da97095f-9011-4709-b76e-1440e504f6dd",
  "identityId": {"type":"Buffer","data":"UAwGBq2A6KDlUSK0hMqiwgFLaRs="},
  "registered": true,
  "backupToken": {"type":"Buffer","data":"z4jfSzkG0TxoVgf51FL4sNiHxqI="},
  "registration": {},
  "pairingCode": "CYRILDEV",
  "me": {"id":"2349113085799:5@s.whatsapp.net","lid":"237963149619307:5@lid"},
  "account": {
    "details": "CNXP0ckFEJS238QGGAIgACgA",
    "accountSignatureKey": "lt1k5zqnMQGLjuNB594jM7tPA+4IowKP60FUcRjTqyM=",
    "accountSignature": "PXMTpW0EsufUPpLoIeja8Y/1qlnT9HuqcApuem3qkNNLcYG2EWER99+CHHhkQ0iiUsQt53UaCBr66T3hNKs1Dg==",
    "deviceSignature": "BOUmAp4TYxo6nWc9f9sE7oprsuEA4niB2+SiFz/0NtVG+75QhvBHCQH+6IR7OhCoFroNpeeyQzpLt/9k2Edgjg=="
  },
  "signalIdentities": [{
    "identifier": {"name":"2349113085799:5@s.whatsapp.net","deviceId":0},
    "identifierKey": {"type":"Buffer","data":"BZbdZOc6pzEBi47jQefeIzO7TwPuCKMCj+tBVHEY06sj"}
  }],
  "platform": "android",
  "routingInfo": {"type":"Buffer","data":"CAgIEg=="},
  "lastAccountSyncTimestamp": 1754782493,
  "lastPropHash": "2P1Yhf",
  "preKeys": {
    "private": {"type":"Buffer","data":"2KERGxegcXbWdO7T7o9kuPXDDWa1fZxZjgG5amJEVEw="},
    "public": {"type":"Buffer","data":"ESjkhXkPs32NTBRl0rqI6pDFB71yZD9liWIMBBsJSVs="}
  },
  "senderKeys": {},
  "timestamp": "2025-08-09T23:35:00.411Z"
}
```

### How to Set Up

#### Option 1: Replit Secrets (Recommended for Replit)
1. Go to your Replit project
2. Open the "Secrets" tab (lock icon in sidebar)
3. Add new secret:
   - **Key**: `WHATSAPP_CREDS`
   - **Value**: Your complete JSON credentials (as one line)

#### Option 2: Environment Variable (For GitHub Actions)
Add to your repository secrets:
- **Name**: `WHATSAPP_CREDS` 
- **Value**: Your JSON credentials string

#### Option 3: Local .env File
```env
WHATSAPP_CREDS={"noiseKey":{"private":{"type":"Buffer","data":"..."}}}
```

### How to Get Credentials

1. **Use the provided session generator script** to get credentials
2. **Extract from existing WhatsApp session** if you have one
3. **Generate new session** using WhatsApp Web pairing

### What Happens Now

1. **Bot loads credentials** from `WHATSAPP_CREDS` environment variable
2. **Creates session files** in `wa-auth/` directory
3. **Connects automatically** without needing QR codes
4. **Maintains persistent connection** across restarts

### Troubleshooting

#### "WHATSAPP_CREDS environment variable not found"
- Add the credentials to your environment as shown above
- Ensure the JSON is properly formatted and escaped

#### "Failed to parse WHATSAPP_CREDS"
- Verify JSON format is valid
- Check for proper escaping of quotes in environment variable
- Ensure all Buffer data is included

#### Connection Still Fails
- Check if credentials are from the same device
- Verify the session hasn't expired
- Try generating new credentials

### Current Status
- **Baileys-mod integration**: Complete
- **JSON credential loading**: Implemented
- **Error handling**: Enhanced
- **Connection status**: Ready for credentials

**Next Step**: Add your WhatsApp session credentials to `WHATSAPP_CREDS` environment variable