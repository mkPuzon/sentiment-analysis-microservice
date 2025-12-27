**SENTIMENT ANALYSIS MICROSERVICE: PRODUCTION DEPLOYMENT ROADMAP**

---

## **PHASE 1: TESTING INFRASTRUCTURE**

### Task 1.1: Set Up Testing Framework
**Time estimate:** 1 hour

**Technologies:**
- `pytest` - industry standard Python testing framework
- `pytest-cov` - code coverage reporting
- `httpx` - async HTTP client for testing FastAPI

**Steps:**
1. Install dependencies: `pip install pytest pytest-cov httpx`
2. Create `tests/` directory in project root
3. Create `tests/conftest.py` for shared test fixtures
4. Create `tests/test_api.py` for API tests

**Self-check questions:**
- Can I run `pytest` and see test discovery working?
- Do I understand what a "fixture" is and why we use them?
- Can I explain what code coverage measures?

---

### Task 1.2: Write API Endpoint Tests
**Time estimate:** 2 hours

**What to test:**
```python
# tests/test_api.py structure
# 1. Test successful sentiment analysis
# 2. Test empty text input (should fail)
# 3. Test extremely long text (should fail)
# 4. Test special characters/emojis
# 5. Test response schema matches expected format
```

**Resources:**
- FastAPI Testing Docs: https://fastapi.tiangolo.com/tutorial/testing/
- Use `TestClient` from `fastapi.testclient`

**Self-check questions:**
- Do all my tests pass?
- Can I explain what each test is validating?
- What happens if I intentionally break the code - do tests catch it?
- Am I testing both success AND failure cases?

---

### Task 1.3: Write Database Tests
**Time estimate:** 1.5 hours

**What to test:**
```python
# Test database logging functionality
# 1. Verify query gets logged to database
# 2. Verify correct fields are stored
# 3. Test database connection failure handling
# 4. Test duplicate query handling
```

**Technologies:**
- Use in-memory SQLite for tests (faster than spinning up Postgres)
- `pytest` fixtures for database setup/teardown

**Self-check questions:**
- Are my tests isolated (don't depend on each other)?
- Do tests clean up after themselves?
- Can I run tests multiple times and get same results?

---

### Task 1.4: Achieve 70%+ Code Coverage
**Time estimate:** 1 hour

**Commands:**
```bash
pytest --cov=app tests/
pytest --cov=app --cov-report=html tests/
```

**Self-check questions:**
- Which parts of my code aren't tested?
- Are those untested parts actually important?
- Can I open `htmlcov/index.html` and understand the coverage report?

---

## **PHASE 2: OBSERVABILITY & ERROR HANDLING**

### Task 2.1: Add Structured Logging
**Time estimate:** 1 hour

**Technologies:**
- Python's built-in `logging` module
- Consider `structlog` for better formatting (optional)

**What to add:**
```python
# In main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log at different levels:
# - logger.info() for normal operations
# - logger.warning() for concerning but non-breaking issues
# - logger.error() for failures
# - logger.debug() for detailed debugging info
```

**Where to add logs:**
- Start of each API request
- Before/after model inference
- Database operations
- Any exception handlers

**Self-check questions:**
- Can I tell what the API is doing by reading logs alone?
- Are my log messages descriptive without being verbose?
- Do I log sensitive data? (DON'T - no user text in logs for privacy)

---

### Task 2.2: Create Health Check Endpoint
**Time estimate:** 45 minutes

**What to build:**
```python
# Add to main.py
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    Returns: status of API and database connection
    """
    return {
        "status": "healthy",
        "database": check_db_connection(),  # you implement this
        "model_loaded": model is not None
    }
```

**Self-check questions:**
- Does `/health` return 200 when everything works?
- Does it return 503 when database is down?
- Can I use this endpoint to know if service is truly ready?

---

### Task 2.3: Add Input Validation
**Time estimate:** 1 hour

**Technologies:**
- Pydantic (already used by FastAPI)
- FastAPI's built-in validators

**What to add:**
```python
from pydantic import BaseModel, Field, validator

class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace')
        return v
```

**Self-check questions:**
- What happens if I send text longer than 5000 chars?
- What HTTP status code do I get for invalid input?
- Do I return helpful error messages to users?

---

### Task 2.4: Implement Error Handling
**Time estimate:** 1.5 hours

**What to add:**
```python
# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Specific handlers for:
# - Database connection errors (503)
# - Model inference errors (500)
# - Invalid input (400)
# - Rate limiting (429)
```

**Self-check questions:**
- If the database crashes, does my API return a useful error?
- Do I expose stack traces to users? (DON'T - security risk)
- Can I test error paths in my test suite?

---

## **PHASE 3: PERFORMANCE & CACHING**

### Task 3.1: Add Redis Caching Layer
**Time estimate:** 2 hours

**Technologies:**
- Redis (in-memory cache)
- `redis-py` or `aioredis` for async support

**What to add:**
```yaml
# Add to compose.yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data

volumes:
  postgres_data:
  redis_data:  # Add this
```

**Caching logic:**
```python
# Before running model inference:
# 1. Hash the input text
# 2. Check if hash exists in Redis
# 3. If yes, return cached result
# 4. If no, run inference, cache result with TTL (e.g., 1 hour)
```

**Self-check questions:**
- Can I measure cache hit rate?
- Does caching actually speed up repeated queries?
- What's a reasonable TTL (time-to-live) for sentiment results?

---

### Task 3.2: Add Request Latency Tracking
**Time estimate:** 45 minutes

**What to add:**
```python
import time
from fastapi import Request

@app.middleware("http")
async def add_latency_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    response.headers["X-Process-Time"] = str(latency)
    logger.info(f"Request to {request.url.path} took {latency:.4f}s")
    return response
```

**Self-check questions:**
- What's my average response time?
- Which requests are slowest?
- Does caching improve latency measurably?

---

## **PHASE 4: INTERACTIVE DASHBOARD UPDATE**

### Task 4.1: Add User Input to Streamlit Dashboard
**Time estimate:** 1 hour

**What to modify in `dashboard/app.py`:**
```python
st.title("Sentiment Analysis Dashboard")

# Add interactive section at top
st.header("🎯 Try It Yourself")
user_input = st.text_area(
    "Enter text to analyze:",
    placeholder="Type something...",
    height=100
)

if st.button("Analyze Sentiment"):
    if user_input.strip():
        response = requests.post(
            "http://api:8000/query",
            json={"text": user_input}
        )
        result = response.json()
        
        # Display results nicely
        col1, col2 = st.columns(2)
        col1.metric("Sentiment", result["sentiment_label"])
        col2.metric("Confidence", f"{result['sentiment_score']:.2%}")
    else:
        st.warning("Please enter some text")

st.divider()
st.header("📊 Historical Analytics")
# ... existing dashboard code ...
```

**Self-check questions:**
- Can I analyze custom text without using curl?
- Does the dashboard show my new query in the analytics?
- Is the UI intuitive for someone who's never seen it?

---

## **PHASE 5: DEPLOYMENT PREPARATION**

### Task 5.1: Environment Configuration Cleanup
**Time estimate:** 1 hour

**What to do:**
1. Create `.env.example` with placeholder values:
```ini
POSTGRES_USER=your_user_here
POSTGRES_PASSWORD=your_password_here
# ... etc
```

2. Add to `.gitignore`:
```
.env
__pycache__/
*.pyc
.pytest_cache/
htmlcov/
.coverage
```

3. Create `docker-compose.prod.yaml` (production version):
```yaml
# Same as compose.yaml but:
# - Remove volume mounts for live-reloading
# - Remove exposed database port
# - Add restart policies
```

**Self-check questions:**
- Is my `.env` file in `.gitignore`?
- Can someone clone my repo and run it with just `.env.example`?
- Are there any hardcoded secrets in my code?

---

### Task 5.2: Add Dockerfile Optimizations
**Time estimate:** 45 minutes

**What to optimize:**
```dockerfile
# Current Dockerfile probably copies everything
# Optimize by:
# 1. Using multi-stage builds
# 2. Copying requirements.txt first (better caching)
# 3. Running as non-root user

FROM python:3.12-slim as base

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Self-check questions:**
- Do my containers build faster on second run?
- Am I running as root? (bad practice)
- Is my image size reasonable? (check with `docker images`)

---

### Task 5.3: Add Health Checks to Compose
**Time estimate:** 30 minutes

**Update compose.yaml:**
```yaml
api:
  # ... existing config ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s

dashboard:
  # ... existing config ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Self-check questions:**
- Does `docker-compose ps` show services as "healthy"?
- If I kill the database, does API show as unhealthy?

---

## **PHASE 6: CLOUD DEPLOYMENT**

### Task 6.1: Sign Up for Render and Initial Setup
**Time estimate:** 30 minutes

**Steps:**
1. Go to render.com, sign up with GitHub
2. Grant Render access to your repository
3. Familiarize yourself with dashboard

**Self-check questions:**
- Can I see my GitHub repos in Render?
- Do I understand the difference between "Web Service" and "Database"?

---

### Task 6.2: Deploy PostgreSQL Database
**Time estimate:** 30 minutes

**Steps:**
1. Create new PostgreSQL instance (free tier)
2. Note the "Internal Database URL" (services use this)
3. Note the "External Database URL" (you use this for testing)

**Self-check questions:**
- Can I connect to the database from my local machine using the external URL?
- Do I understand internal vs external URLs?

---

### Task 6.3: Deploy API Service
**Time estimate:** 1 hour

**Steps:**
1. Create new "Web Service"
2. Connect to your GitHub repo
3. Set build command: `docker build -t api .`
4. Set start command: (Docker handles this)
5. Add environment variables from Render dashboard
6. Set `DATABASE_URL` to your Render Postgres internal URL
7. Deploy and monitor logs

**Common issues:**
- Port binding: Render assigns `$PORT`, ensure your app uses it
- Database connection: Use internal URL, not localhost
- Model download: First deploy is slow (~5 min) due to model download

**Self-check questions:**
- Can I access my API at the Render-provided URL?
- Does `/health` endpoint return healthy?
- Can I see logs in real-time?

---

### Task 6.4: Deploy Dashboard Service
**Time estimate:** 45 minutes

**Steps:**
1. Create second "Web Service" for dashboard
2. Point to `dashboard/` directory or use separate Dockerfile
3. Set environment variables
4. Update dashboard code to use Render API URL (not localhost)
5. Deploy

**Self-check questions:**
- Does dashboard load at its Render URL?
- Can dashboard communicate with API?
- Can I analyze text and see it appear in analytics?

---

### Task 6.5: Configure Custom Domains (Optional)
**Time estimate:** 30 minutes

**Steps:**
1. Render provides default URLs like `yourapp.onrender.com`
2. Can set up custom domains if you own one
3. For now, use default URLs

**Self-check questions:**
- Are my URLs descriptive (not random strings)?
- Can I access both services from a browser?

---

## **PHASE 7: DOCUMENTATION & POLISH**

### Task 7.1: Update README with Live Demo
**Time estimate:** 45 minutes

**What to add at the top of README:**
```markdown
## 🚀 Live Demo

**Try it now:** [Sentiment Analysis Dashboard](https://your-dashboard.onrender.com)
**API Documentation:** [Swagger UI](https://your-api.onrender.com/docs)

> ⏱️ **Note:** Services may take 30-60 seconds to wake from sleep on the free tier.

---
```

**Also update:**
- Architecture diagram to show cloud deployment
- "Getting Started" section to include live demo option
- Environment variables section

**Self-check questions:**
- Can a recruiter click links and use the app immediately?
- Is the wake-up time warning prominent?
- Are instructions clear for both cloud and local usage?

---

### Task 7.2: Add Known Limitations Section
**Time estimate:** 30 minutes

**What to include:**
```markdown
## Known Limitations & Future Improvements

### Current Limitations
- **Model**: DistilBERT is optimized for English only
- **Scale**: Single-instance deployment (no horizontal scaling)
- **Rate Limiting**: Not implemented (would add Redis-based rate limiting)
- **Authentication**: Public API (would add API keys for production)

### Planned Improvements
- [ ] Add batch processing endpoint
- [ ] Implement model versioning
- [ ] Add A/B testing between different sentiment models
- [ ] Create alerting for model drift
- [ ] Add comprehensive monitoring dashboard
```

**Self-check questions:**
- Am I honest about limitations without underselling?
- Do my "future improvements" show I understand production systems?
- Would these improvements actually be useful?

---

### Task 7.3: Add Screenshots and Visuals
**Time estimate:** 30 minutes

**What to add:**
1. Screenshot of Streamlit dashboard with data
2. Screenshot of Swagger API docs
3. GIF of someone using the interactive feature (use LICEcap or similar)
4. Update architecture diagram with actual URLs

**Self-check questions:**
- Do my screenshots show real data (not empty states)?
- Are images compressed (use TinyPNG) to load fast on GitHub?
- Does my README look professional when scrolling?

---

### Task 7.4: Code Documentation & Comments
**Time estimate:** 1 hour

**What to add:**
```python
# Add docstrings to every function
def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of input text using DistilBERT model.
    
    Args:
        text (str): Input text to analyze (1-5000 characters)
        
    Returns:
        dict: Contains sentiment_label (POSITIVE/NEGATIVE) and 
              sentiment_score (confidence 0-1)
              
    Raises:
        ValueError: If text is empty or exceeds max length
        ModelError: If inference fails
    """
    # Implementation...
```

**Add inline comments for:**
- Non-obvious logic
- Why you chose specific values (e.g., cache TTL)
- TODO items if any

**Self-check questions:**
- Can someone understand my code without running it?
- Are my docstrings following a consistent format (Google/NumPy style)?
- Did I over-comment obvious things? (if yes, remove them)

---

### Task 7.5: Create Demo Video (Optional but Recommended)
**Time estimate:** 1 hour

**Tools:**
- Loom (free screen recorder)
- OBS Studio (more advanced, free)

**What to show (keep under 3 minutes):**
1. Visit live dashboard (15s)
2. Analyze custom text (30s)
3. Show results appearing in analytics (20s)
4. Open API docs, show Swagger UI (30s)
5. Quick code walkthrough (60s)
6. Mention tests, monitoring, deployment (30s)

**Self-check questions:**
- Is my audio clear?
- Did I rehearse before recording?
- Is the video under 3 minutes? (recruiters won't watch longer)

---

## **PHASE 8: FINAL VALIDATION**

### Task 8.1: End-to-End Testing in Production
**Time estimate:** 1 hour

**Checklist:**
- [ ] Visit dashboard URL - loads within 60s
- [ ] Analyze 5 different texts - all work correctly
- [ ] Check if results appear in analytics
- [ ] Visit `/docs` - Swagger UI loads
- [ ] Try API directly with curl/Postman
- [ ] Check `/health` endpoint - returns healthy
- [ ] Kill and restart services - everything recovers
- [ ] Test from different devices/browsers
- [ ] Test from mobile device

**Self-check questions:**
- Did I find any bugs testing as a user would?
- Is the experience smooth enough for a demo?
- Would I be confident showing this in an interview?

---

### Task 8.2: Performance Benchmarking
**Time estimate:** 45 minutes

**Tools:**
- Apache Bench: `ab -n 100 -c 10 https://your-api.onrender.com/query`
- Or write simple Python script

**What to measure:**
- Average response time
- Cache hit rate (if you added Redis)
- Database query performance
- Cold start time (first request after sleep)

**Self-check questions:**
- What's my 95th percentile latency?
- Is performance acceptable for a demo?
- Do I understand what's slowing down requests?

---

### Task 8.3: Security Check
**Time estimate:** 30 minutes

**What to verify:**
- [ ] No API keys/secrets in GitHub repo
- [ ] No exposed database ports in production
- [ ] Error messages don't leak sensitive info
- [ ] Input validation prevents injection attacks
- [ ] CORS configured properly (if needed)
- [ ] Running as non-root user in containers

**Tools:**
- `git log -p | grep -i password` (check history for leaks)
- Render dashboard environment variables

**Self-check questions:**
- If my repo went public tomorrow, would I be embarrassed?
- Are there any obvious security holes?
- Did I commit secrets in early commits? (if yes, rewrite history)

---

### Task 8.4: Create Interview Talking Points
**Time estimate:** 45 minutes

**Write down answers to:**
1. "Walk me through your architecture"
2. "Why did you choose DistilBERT over other models?"
3. "How would you scale this to 10,000 requests/second?"
4. "What was the hardest bug you encountered?"
5. "If you had another week, what would you add?"
6. "How do you ensure model quality over time?"

**Self-check questions:**
- Can I explain technical decisions confidently?
- Do I admit what I don't know instead of bullshitting?
- Are my answers concise (under 2 minutes each)?

---

## **WHY EACH PHASE MATTERS**

### **Phase 1: Testing - The Foundation**

**For the project:**
- Catches bugs before deployment
- Enables confident refactoring
- Documents expected behavior
- Prevents regressions when adding features

**For your skills:**
- **Most important skill gap for new grads.** Everyone can write code; few can write testable code.
- Shows you understand software quality beyond "it works on my machine"
- Demonstrates you can work in team environments (tests are documentation)
- **Interview goldmine:** "I have 70% test coverage including edge cases" impresses immediately

**Reality check:** Companies won't hire new grads who can't write tests. Period. This is the #1 thing that separates student projects from professional work.

---

### **Phase 2: Observability - Production Readiness**

**For the project:**
- Makes debugging 10x easier
- Shows the app is working even when you're not looking at it
- Enables monitoring and alerting in real deployments
- Demonstrates you think beyond happy paths

**For your skills:**
- Most new grads never think about observability
- Shows you understand prod systems fail in ways you can't predict
- Health checks are table stakes for any deployed service
- **Interview signal:** "I added logging and health checks" shows maturity

**Reality check:** Your app WILL break in production. Logging is how you'll figure out why. This phase teaches you to think defensively.

---

### **Phase 3: Performance - Optimization Mindset**

**For the project:**
- Makes the demo actually usable (fast response times)
- Shows you understand system bottlenecks
- Caching is a universal pattern - you'll use it everywhere
- Demonstrates awareness of resource costs

**For your skills:**
- Teaches you to measure before optimizing (latency tracking)
- Redis caching is industry standard - you'll see it at every job
- Understanding performance trade-offs (memory vs speed)
- **Interview question:** "How would you improve performance?" - you have real answers

**Reality check:** Nobody cares about elegant code if it's too slow to use. This phase teaches you that working software must also be performant software.

---

### **Phase 4: Dashboard UX - User-Centric Thinking**

**For the project:**
- Makes it actually demo-able to recruiters
- Shows you think about end users, not just APIs
- Demonstrates full-stack capability (backend + frontend)

**For your skills:**
- Forces you to think from user perspective
- Simple UX is harder than complex UX - this teaches that
- Makes you comfortable with frontend frameworks
- **Recruiter impact:** They can actually TRY your project without setup

**Reality check:** Beautiful code nobody can interact with is worthless. This phase makes your work accessible.

---

### **Phase 5: Deployment Prep - Professional Standards**

**For the project:**
- Makes it reproducible (anyone can run it)
- Security best practices (no leaked secrets)
- Optimizes for deployment constraints

**For your skills:**
- **Critical gap:** Most students never deploy anything real
- Learning environment variables is essential professional knowledge
- Docker optimization will save you hours in every future project
- **Interview credibility:** "I deployed to production" > "I built locally"

**Reality check:** Code that only runs on your laptop isn't production code. This phase bridges the gap between student work and professional work.

---

### **Phase 6: Cloud Deployment - Proof of Competency**

**For the project:**
- Makes it real - not just a school project anymore
- Available 24/7 for recruiters to see
- Tests if your architecture actually works

**For your skills:**
- **Most impressive thing on your resume:** "Deployed ML service to production"
- Teaches you cloud platforms (Render is simpler than AWS, but same concepts)
- Debugging production issues is different from local - you learn this here
- **Interview storytelling:** Real deployments = real problems solved = good stories

**Reality check:** Saying "I built X" is theory. Showing "Here's X running live" is proof. Recruiters trust proof.

---

### **Phase 7: Documentation - Selling Your Work**

**For the project:**
- 90% of recruiter evaluation happens here
- Good README = they explore further
- Bad README = they close tab and move on
- Shows communication skills (critical for engineering)

**For your skills:**
- Writing clear docs is 30% of engineering work
- Learning to explain technical decisions simply
- Visual communication (diagrams, screenshots)
- **Reality check:** Your code doesn't speak for itself. You must speak for your code.

**Harsh truth:** A mediocre project with great documentation beats a great project with poor documentation in job searches. Always.

---

### **Phase 8: Validation - Professional Polish**

**For the project:**
- Catches embarrassing bugs before interviews
- Ensures consistent behavior
- Proves security hygiene
- Prepares you for technical questions

**For your skills:**
- Teaches QA mindset (test like an adversary)
- Performance benchmarking is how you prove scale claims
- Security awareness (companies care deeply about this)
- **Interview preparation:** You can confidently discuss every decision

**Reality check:** The difference between 90% done and 100% done is where most projects fail. This phase forces you to finish properly.

---

## **THE META-LESSON**

Each phase teaches you something beyond the technical task:

- **Testing:** Quality over speed
- **Observability:** Defensive programming
- **Performance:** Measure, don't guess
- **UX:** Build for users, not yourself
- **Deployment prep:** Professional standards matter
- **Cloud deployment:** Proof beats promises
- **Documentation:** Communication is half the job
- **Validation:** Finish what you start

**Combined, these phases transform you from:**
- "I can code" → "I can ship production systems"
- "It works for me" → "It works reliably for everyone"
- "Here's my project" → "Here's my deployed, tested, documented service"

---
