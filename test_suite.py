import time
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)
print("Starting RakshaPay Verification Suite...")

# 1. Test index page (login)
r = client.get('/')
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
assert 'Sign In' in r.text, "Login page missing 'Sign In'"
print("1. GET / status: 200 - OK (Login page loaded)")

# 2. Test dashboard page
r = client.get('/dashboard')
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
assert 'RakshaPay' in r.text, "Dashboard missing brand"
print("2. GET /dashboard status: 200 - OK (Dashboard loaded)")

# 3. Test signup with unique email
unique_email = f"user_{int(time.time())}@example.com"
r = client.post('/auth/signup', json={'name': 'Gayatri Tester', 'email': unique_email, 'password': 'password123'})
print("3. POST /auth/signup status:", r.status_code, "User:", r.json().get('user_name'))
assert r.status_code == 200
token = r.json().get('access_token')
assert token is not None

# 4. Test login with newly created user
r = client.post('/auth/login', json={'email': unique_email, 'password': 'password123'})
print("4. POST /auth/login status:", r.status_code, "Token received:", bool(r.json().get('access_token')))
assert r.status_code == 200

# 5. Test Google sign-in (creates or retrieves Google user)
r = client.post('/auth/google-signin', json={'email': 'gayatri@gmail.com', 'name': 'Gayatri'})
print("5. POST /auth/google-signin status:", r.status_code, "User:", r.json().get('user_name'))
assert r.status_code == 200
g_token = r.json().get('access_token')

# 6. Test auth/me with JWT
r = client.get('/auth/me', headers={'Authorization': f'Bearer {g_token}'})
print("6. GET /auth/me status:", r.status_code, "Email:", r.json().get('email'))
assert r.status_code == 200

# 7. Test protected /api/scenarios with JWT
r = client.get('/api/scenarios', headers={'Authorization': f'Bearer {g_token}'})
print("7. GET /api/scenarios (WITH JWT) status:", r.status_code, "Scenarios loaded:", len(r.json()))
assert r.status_code == 200

# 8. Test protected /api/scenarios WITHOUT JWT (Zero Trust enforcement)
r = client.get('/api/scenarios')
print("8. GET /api/scenarios (NO JWT) status:", r.status_code, "Zero Trust Blocked:", r.status_code == 401)
assert r.status_code == 401

# 9. Test transaction analysis with AI narrative injection
tx_payload = {
    'sender_vpa': 'gayatri@okaxis',
    'recipient_vpa': 'refund.claim@fakebank',
    'amount': 15000.0,
    'device_id': 'DEV-9988',
    'ip_address': '192.168.1.50',
    'location_city': 'Bengaluru',
    'scenario_name': 'Fake Customer Care Refund'
}
r = client.post('/api/analyze-transaction', headers={'Authorization': f'Bearer {g_token}'}, json=tx_payload)
print("9. POST /api/analyze-transaction status:", r.status_code)
assert r.status_code == 200
tx_res = r.json()
print("   Risk Score:", tx_res.get('risk_score'), "Tier:", tx_res.get('risk_tier'))
print("   AI Narrative:", str(tx_res.get('ai_narrative'))[:80] + "...")

# 10. Test AI Chat Assistant
chat_payload = {'message': 'Explain why refund.claim@fakebank is dangerous', 'history': []}
r = client.post('/api/ai-chat', headers={'Authorization': f'Bearer {g_token}'}, json=chat_payload)
print("10. POST /api/ai-chat status:", r.status_code)
assert r.status_code == 200
print("    AI Reply preview:", str(r.json().get('reply'))[:80] + "...")

print("\n=======================================================")
print("  >>> ALL 10 INTEGRATION TESTS PASSED WITH FLYING COLORS! <<<")
print("=======================================================")
