import os, time
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from engine.fraud_pipeline import master_pipeline
from engine.mule_graph import mule_graph_instance
from engine.step_up import step_up_instance
from engine.db import record_transaction, get_metrics, get_user_by_email, create_user
from engine.ai_engine import generate_fraud_narrative, chat_with_fraud_advisor
from dataset.synthetic_generator import get_demo_scenarios
from auth.jwt_handler import create_access_token, get_current_user
from auth.password import hash_password, verify_password
from auth.models import SignupRequest, LoginRequest, GoogleSigninRequest, TokenResponse, UserResponse

app = FastAPI(
    title='RakshaPay API',
    description='Real-Time AI UPI Fraud Interception - Zero Trust Architecture',
    version='3.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8000', 'http://127.0.0.1:8000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ?? Auth Request Models ???????????????????????????????????????????????????????
class TransactionAnalysisRequest(BaseModel):
    sender_vpa: str = Field(default='user@upi', description='Sender UPI ID')
    recipient_vpa: str = Field(..., description='Recipient UPI ID')
    amount: float = Field(..., gt=0)
    note: str = Field(default='')
    transaction_type: str = Field(default='DIRECT_PAY')
    sender_baseline_avg: float = Field(default=1200.0)
    hour_of_day: Optional[int] = Field(default=None)
    call_active: bool = Field(default=False)
    screen_sharing: bool = Field(default=False)
    is_new_device: bool = Field(default=False)
    geo_distance_km: float = Field(default=15.0)

class StepUpVerifyRequest(BaseModel):
    challenge_type: str
    user_math_answer: Optional[str] = None
    expected_math_answer: Optional[str] = None
    acknowledged_checkbox: bool = False
    is_coerced_answer: Optional[bool] = None

class ReportVPARequest(BaseModel):
    vpa: str
    reason: str = 'Crowdsourced User Report'

class AIChatRequest(BaseModel):
    message: str
    history: list = []

# ?? Auth Routes (Public - No JWT Required) ?????????????????????????????????
@app.post('/auth/signup', response_model=TokenResponse)
async def signup(req: SignupRequest):
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered. Please login.')
    hashed = hash_password(req.password)
    user = create_user(email=req.email, name=req.name, hashed_pw=hashed, auth_provider='email')
    token = create_access_token({'sub': req.email, 'name': req.name, 'provider': 'email'})
    return TokenResponse(access_token=token, user_name=req.name, user_email=req.email)

@app.post('/auth/login', response_model=TokenResponse)
async def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail='No account found with this email. Please sign up.')
    if user.get('auth_provider') == 'google':
        raise HTTPException(status_code=400, detail='This account uses Google Sign-In. Please use that option.')
    if not verify_password(req.password, user.get('hashed_pw') or ''):
        raise HTTPException(status_code=401, detail='Incorrect password.')
    name = user.get('name', req.email.split('@')[0].capitalize())
    token = create_access_token({'sub': req.email, 'name': name, 'provider': 'email'})
    return TokenResponse(access_token=token, user_name=name, user_email=req.email)

@app.post('/auth/google-signin', response_model=TokenResponse)
async def google_signin(req: GoogleSigninRequest):
    existing = get_user_by_email(req.email)
    name = req.name or req.email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
    if not existing:
        create_user(email=req.email, name=name, google_id=req.google_id or 'demo', auth_provider='google')
    else:
        name = existing.get('name', name)
    token = create_access_token({'sub': req.email, 'name': name, 'provider': 'google'})
    return TokenResponse(access_token=token, user_name=name, user_email=req.email)

@app.get('/auth/me', response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        name=current_user.get('name', ''),
        email=current_user.get('sub', ''),
        auth_provider=current_user.get('provider', 'email')
    )

# ?? Protected API Endpoints (Zero Trust - JWT Required on ALL) ?????????????
@app.post('/api/analyze-transaction')
async def analyze_transaction(req: TransactionAnalysisRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = master_pipeline.evaluate_transaction(
            sender_vpa=req.sender_vpa, recipient_vpa=req.recipient_vpa,
            amount=req.amount, note=req.note, transaction_type=req.transaction_type,
            sender_baseline_avg=req.sender_baseline_avg, hour_of_day=req.hour_of_day,
            is_new_device=req.is_new_device, call_active=req.call_active,
            screen_sharing=req.screen_sharing, geo_distance_km=req.geo_distance_km
        )
        scam_cat = result.get('scam_category', '') or result.get('engine_breakdowns', {}).get('social_engineering', {}).get('scam_category', '')
        mule_graph_instance.record_transaction(
            sender_vpa=req.sender_vpa,
            receiver_vpa=req.recipient_vpa,
            amount=req.amount,
            remark=req.note or req.transaction_type,
            risk_score=result.get('risk_score', 0),
            risk_tier=result.get('risk_tier', 'LOW'),
            scam_category=scam_cat,
            action_code=result.get('action_code', 'ALLOW'),
            device_id=f"DEV-SIM-{abs(hash(req.recipient_vpa)) % 9000 + 1000}"
        )
        graph_data = result.get('engine_breakdowns', {}).get('mule_graph', {})
        is_zero_day = graph_data.get('is_zero_day', False)
        is_flagged = result.get('risk_score', 0) >= 50
        record_transaction(
            latency_ms=result.get('latency_ms', 0), risk_score=result.get('risk_score', 0),
            risk_tier=result.get('risk_tier', 'LOW'), threat_type=result.get('scam_category', ''),
            sender_vpa=req.sender_vpa, recipient_vpa=req.recipient_vpa, amount=req.amount,
            is_flagged=is_flagged, is_zero_day=is_zero_day, action=result.get('action_code', 'ALLOW')
        )
        # Enrich with Gemini AI narrative
        ai_data = {**result, 'recipient_vpa': req.recipient_vpa, 'amount': req.amount,
                   'scam_category': result.get('engine_breakdowns',{}).get('social_engineering',{}).get('scam_category','')}
        result['ai_narrative'] = generate_fraud_narrative(ai_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/ai-chat')
async def ai_chat(req: AIChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        reply = chat_with_fraud_advisor(req.message, req.history)
        return {'reply': reply, 'timestamp': time.time()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/scenarios')
async def get_scenarios(current_user: dict = Depends(get_current_user)):
    return {'scenarios': get_demo_scenarios()}

@app.get('/api/network-graph')
async def get_network_graph(current_user: dict = Depends(get_current_user)):
    return mule_graph_instance.get_full_graph_visualization_data()

@app.post('/api/verify-step-up')
async def verify_step_up(req: StepUpVerifyRequest, current_user: dict = Depends(get_current_user)):
    return step_up_instance.verify_challenge(
        challenge_type=req.challenge_type, user_math_answer=req.user_math_answer,
        expected_math_answer=req.expected_math_answer,
        acknowledged_checkbox=req.acknowledged_checkbox, is_coerced_answer=req.is_coerced_answer
    )

@app.get('/api/threat-feed')
async def get_threat_feed(current_user: dict = Depends(get_current_user)):
    metrics = get_metrics()
    return {
        'audit_feed': master_pipeline.get_audit_feed(),
        'stats': {
            'average_latency_ms': metrics['avg_latency_ms'],
            'accuracy_percent': metrics['detection_accuracy'],
            'false_positive_rate': metrics['false_positive_rate'],
            'blacklisted_vpas_count': len(mule_graph_instance.blacklist_vpas),
            'zero_day_accounts_flagged': metrics['zero_day_flagged'],
            'total_analyzed': metrics['total_analyzed'],
        }
    }

@app.get('/api/system-status')
async def get_system_status(current_user: dict = Depends(get_current_user)):
    t0 = time.time()
    metrics = get_metrics()
    check_latency = round((time.time() - t0) * 1000, 2)
    engine_checks = {}
    for name, mod in [('vpa_engine', 'engine.vpa_analyzer'), ('social_engine', 'engine.social_engineering'),
                      ('graph_engine', None), ('ml_engine', 'engine.ml_engine')]:
        try:
            if name == 'graph_engine':
                _ = mule_graph_instance.graph.number_of_nodes()
            else:
                __import__(mod)
            engine_checks[name] = True
        except:
            engine_checks[name] = False
    all_online = all(engine_checks.values())
    return {
        'status': 'online' if all_online else 'degraded',
        'all_engines_online': all_online,
        'check_latency_ms': check_latency,
        'avg_latency_ms': metrics['avg_latency_ms'],
        'detection_accuracy': metrics['detection_accuracy'],
        'false_positive_rate': metrics['false_positive_rate'],
        'zero_day_flagged': metrics['zero_day_flagged'],
        'total_analyzed': metrics['total_analyzed'],
        'recent_latencies': metrics['recent_latencies'],
        'engine_checks': engine_checks,
        'graph_nodes': mule_graph_instance.graph.number_of_nodes(),
        'graph_edges': mule_graph_instance.graph.number_of_edges(),
        'blacklisted_count': len(mule_graph_instance.blacklist_vpas),
        'ai_engine_active': bool(os.getenv('GEMINI_API_KEY', '') and os.getenv('GEMINI_API_KEY') != 'your-gemini-api-key-here'),
        'zero_trust_active': True,
        'database_type': 'PostgreSQL' if os.getenv('DATABASE_URL','').startswith('postgresql') else 'SQLite',
    }

@app.post('/api/report-vpa')
async def report_vpa(req: ReportVPARequest, current_user: dict = Depends(get_current_user)):
    mule_graph_instance.blacklist_vpa(req.vpa, req.reason)
    return {'success': True, 'message': f"VPA '{req.vpa}' added to real-time blacklist registry.", 'vpa': req.vpa}

# ?? Static Frontend Routing ????????????????????????????????????????????????
static_dir = os.path.join(os.path.dirname(__file__), 'static')
if os.path.exists(static_dir):
    app.mount('/static', StaticFiles(directory=static_dir), name='static')

    @app.get('/')
    async def serve_index():
        return FileResponse(os.path.join(static_dir, 'index.html'))

    @app.get('/signup')
    async def serve_signup():
        return FileResponse(os.path.join(static_dir, 'index.html'))

    @app.get('/logout')
    async def serve_logout():
        return FileResponse(os.path.join(static_dir, 'index.html'))

    @app.get('/dashboard')
    async def serve_dashboard():
        return FileResponse(os.path.join(static_dir, 'dashboard.html'))