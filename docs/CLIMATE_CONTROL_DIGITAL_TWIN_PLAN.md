# Climate Control Digital Twin Platform
## Comprehensive Implementation Plan for RainForest Algorithm Competition

**Last Updated:** May 5, 2026  
**Project Scope:** RainForest biome climate control optimization via student hackathon  
**Status:** Planning Phase  
**Key Stakeholder:** John Adams (Biosphere 2 Operations)

---

## Executive Summary

This document outlines the complete architecture for building a **Digital Twin of RainForest** to enable climate control algorithm competitions. The system will allow students to develop and test control algorithms against a machine-learning surrogate model trained on 15 years of historical operational data.

- **64 Input Control Parameters** (temperature setpoints, fan commands, valve positions)
- **36 Output Monitoring Sensors** (temperature & humidity across 4 vertical towers)
- **~500K timesteps** of historical data (15-year archive at 15-minute intervals)
- **Goal:** Safe, fair, scalable platform for algorithm validation before real deployment

---

## PART 1: SURROGATE MODEL SELECTION

### Recommended Approach: Hybrid LSTM + Physics-Informed Residuals

#### Architecture Overview
```
Input Layer (64 parameters)
    ↓
LSTM Encoder (3 layers, 128 units each)
    - Captures temporal dependencies
    - Context window: last 96 timesteps (24 hours)
    ↓
Physics Constraint Layer
    - Enforces known system dynamics
    - e.g., temperature changes limited by thermal mass
    - e.g., humidity lags temperature by ~2-4 timesteps
    ↓
LSTM Decoder (3 layers, 128 units each)
    - Generates multi-step predictions (optional: up to 96 steps ahead)
    ↓
Output Layer (36 sensors)
    - Linear activation for continuous values
    - Sigmoid/clipping for bounded outputs (T, RH within physical limits)
```

#### Why LSTM + Physics?

| Criterion | LSTM | Transformer | Prophet | XGBoost |
|-----------|------|-------------|---------|---------|
| Training Speed | ✅ Fast (2-3 weeks) | ❌ Slow (4-8 weeks) | ✅ Fast | ✅ Fast |
| Long-term Dependencies | ✅ Good | ✅✅ Excellent | ❌ Limited | ❌ No |
| Real-time Inference | ✅ ~50ms | ❌ ~200ms | ✅ <1ms | ✅ <1ms |
| Seasonal Patterns | ⚠️ Marginal | ✅ Good | ✅✅ Excellent | ⚠️ Needs preprocessing |
| Physics Integration | ✅✅ Natural | ✅ Possible | ❌ Difficult | ❌ Not applicable |
| **Recommendation** | **✅ PRIMARY** | ⚠️ Phase 2 | ✅ Ensemble component | ✅ Ensemble component |

#### Expected Performance
- **RMSE Target:** 10-15% for Phase 1 MVP
- **Training Data:** 350K timesteps (70%), 75K validation, 75K test
- **Temporal Split:** Respect causality—no data leakage
- **Environmental Constraints:** Temperature 18-32°C, Humidity 40-90%

#### Algorithm Selection Justification
1. **LSTM chosen because:**
   - 15 years of data is sufficient for training without overfitting
   - Natural handling of sequences and temporal correlations
   - Reasonable inference time for real-time competition scoring
   - Transfer learning possible if retraining on new seasons

2. **Physics constraints added because:**
   - Prevents unphysical predictions (e.g., infinite temperature ramps)
   - Improves generalization to unseen scenarios
   - Makes model interpretable to control engineers

3. **Ensemble backup (Prophet + XGBoost):**
   - Robust if primary model fails on edge cases
   - Prophet captures seasonal/trend patterns LSTM might miss
   - XGBoost provides fast baseline for comparison

---

## PART 2: DATA PREPARATION PIPELINE

### Step 1: Data Extraction from Oracle SensorDB
```sql
-- Extract 64 Input parameters (Control commands)
SELECT dv.LOCALDATETIME, s.SENSORNAME, dv.DATAVALUE
FROM BIOMS.DATAVALUES dv
JOIN BIOMS.SENSORS s ON dv.SENSORID = s.SENSORID
WHERE s.SENSORNAME IN ('u_AHUR1_SFCMD', 'u_AHUR1_CCVLVCMD', ...)  -- 64 sensor names
  AND dv.LOCALDATETIME >= '2011-01-01'
  AND dv.LOCALDATETIME < '2026-05-05'
ORDER BY dv.LOCALDATETIME;

-- Extract 36 Output sensors (Temperature & Humidity)
SELECT dv.LOCALDATETIME, s.SENSORNAME, dv.DATAVALUE
FROM BIOMS.DATAVALUES dv
JOIN BIOMS.SENSORS s ON dv.SENSORID = s.SENSORID
WHERE s.SENSORNAME IN ('TRF_MTN_100_HMP45', 'TRF_NE_300_HMP45', ...)  -- 36 sensor names
  AND dv.LOCALDATETIME >= '2011-01-01'
  AND dv.LOCALDATETIME < '2026-05-05'
ORDER BY dv.LOCALDATETIME;
```

### Step 2: Time-Series Alignment & Normalization
- Resample to exact 15-minute intervals (handle gaps with forward-fill)
- Remove obvious outliers (3-sigma rule)
- Normalize inputs (zero-mean, unit-variance across training set)
- Normalize outputs separately (preserve physical interpretability)

### Step 3: Train/Val/Test Split (Temporal Respect)
```
Temporal order (no leakage):
2011-01-01 ← 2019-12-31    |  2020-01-01 ← 2023-12-31   |  2024-01-01 ← 2026-05-05
  Training (70%)           |     Validation (15%)        |     Test (15%)
  ~350K timesteps          |      ~75K timesteps         |     ~75K timesteps
```

### Step 4: Feature Engineering
- **Lagged features:** Include previous 24, 48, 72-hour history for each input
- **Rolling statistics:** Mean/std of temperature over last 7 days (seasonal context)
- **Time-of-day encoding:** Sine/cosine encoding of hour, day-of-week
- **External features:** (optional) sunset time, outdoor temperature if available

---

## PART 3: SYSTEM ARCHITECTURE

### 3A: Microservices Deployment

```
┌────────────────────────────────────────────────────────────────┐
│                     STUDENT INTERFACE LAYER                    │
├────────────────────────────────────────────────────────────────┤
│  • GitHub Integration (student code submission)                │
│  • Docker Registry (algorithm container upload)                │
│  • Jupyter Notebook (optional: local testing)                  │
└────────┬─────────────────────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────────────────────────────┐
│                      API GATEWAY & ORCHESTRATION               │
├────────────────────────────────────────────────────────────────┤
│  FastAPI Server:                                               │
│  • POST /submit_algorithm (receive student code)               │
│  • GET /simulate (run simulation for N timesteps)              │
│  • GET /leaderboard (fetch current scores)                     │
│  • WS /stream_predictions (WebSocket for real-time viz)        │
└────────┬─────────────────────────────────────────────────────┘
         │
         ├─────────────────────┬──────────────────────┐
         │                     │                      │
         ↓                     ↓                      ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Worker Pool    │  │  LSTM Surrogate  │  │  Redis Cache     │
│  (Celery, 4-8    │  │  Model Service   │  │  (State mgmt,    │
│   containers)    │  │  (GPU-optimized) │  │   leaderboard)   │
│                  │  │  Inference:      │  │                  │
│  • Execute       │  │  ~50ms/timestep  │  │  • Cached        │
│    student code  │  │                  │  │    predictions   │
│ • Call environ   │  │  Pre-loaded:     │  │  • Submission    │
│   simulator      │  │  • PyTorch model │  │    metadata      │
│ • Log metrics    │  │  • ONNX format   │  │  • Leaderboard   │
│                  │  │    (cross-platform)  │    scores      │
└──────────┬───────┘  └──────┬───────────┘  └────────┬─────────┘
           │                 │                       │
           └─────────────────┼───────────────────────┘
                             │
                             ↓
                    ┌────────────────────┐
                    │  PostgreSQL Db     │
                    │  • Submissions     │
                    │  • Run history     │
                    │  • Leaderboard     │
                    │  • Audit logs      │
                    └────────────────────┘
```

### 3B: Component Specifications

#### LSTM Surrogate Model Service
- **Framework:** PyTorch 2.0+ or TensorFlow 2.13+
- **Model Size:** ~2-5M parameters
- **Memory:** 2-3 GB GPU VRAM
- **Inference:** 50-100ms per 15-minute timestep
- **Batch size:** 32 for evaluation
- **Retraining:** Quarterly on new 3-month data window

#### Student Algorithm Container (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /algorithm
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY algorithm.py .
ENTRYPOINT ["python", "algorithm.py"]
```

**Expected Interface:**
```python
def control_algorithm(sensors_dict: dict, config: dict) -> dict:
    """
    Input:
      sensors_dict: {
        'T_MTN_100': 24.5,      # Temperature at Mountain tower, 100cm
        'T_MTN_300': 23.8,
        'RH_MTN_100': 65.2,     # Relative Humidity
        'T_NE_100': 24.1,
        ...                      # 36 total sensor channels
      }
      config: {
        'target_temperature': 24.0,
        'target_humidity': 65.0,
        'energy_limit': 1000,    # kWh/day soft limit
      }
    
    Output:
      {
        'u_AHUR1_SFCMD': 50,          # Fan speed 0-100%
        'u_AHUR1_CCVLVCMD': 30,       # Cooling valve 0-100%
        'u_AHUR1_HCVLVCMD': 0,        # Heating valve 0-100%
        'u_AHUR1_MAXSATMPSP': 24.5,   # Max supply air temp setpoint
        ...                            # 61 additional parameters
      }
    """
    # Student implementation here
    pass
```

---

## PART 4: STUDENT SUBMISSION & EVALUATION SYSTEM

### 4A: Submission Workflow

```
1. DEVELOPMENT (Local)
   ├─ Student writes control_algorithm.py
   ├─ Tests locally with provided Docker image
   └─ Commits to GitHub or uploads container

2. CI/CD PIPELINE (Automated)
   ├─ GitHub Actions / GitLab CI triggers
   ├─ Syntax validation
   ├─ Unit tests (provided template)
   └─ Build Docker image

3. SUBMISSION (to Platform)
   ├─ POST to /submit_algorithm with Docker image URL
   ├─ Platform pulls container
   ├─ Stores version metadata (timestamp, git hash)
   └─ Queues for evaluation

4. EVALUATION (Celery Worker)
   ├─ Load pre-trained LSTM model
   ├─ Initialize student algorithm
   ├─ Simulate 7-day scenario (10,080 timesteps)
   ├─ Calculate metrics
   ├─ Store results in PostgreSQL
   └─ Update leaderboard

5. FEEDBACK (to Student)
   ├─ Return JSON with all metrics
   ├─ Dashboard shows real-time trajectory
   ├─ Email notification with ranking
   └─ Allow algorithm revision and resubmission
```

### 4B: Scoring Framework

```python
class RainForestScorer:
    """
    Comprehensive evaluation harness for RainForest climate control.
    Weights: Energy (40%) + Comfort (35%) + Stability (25%)
    """
    
    def __init__(self):
        self.w_energy = 0.40
        self.w_comfort = 0.35
        self.w_stability = 0.25
        
        # Hard constraints (violations = disqualification)
        self.constraints = {
            'T_min': 18,        # °C (damage risk)
            'T_max': 32,        # °C
            'RH_min': 40,       # % (desiccation)
            'RH_max': 90,       # % (fungal risk)
            'pressure_limit': 2.5,  # Pa
        }
    
    def energy_score(self, valve_positions, fan_speeds, dt=15*60):
        """
        Energy = integral of (valve position * time) + (fan speed * time)
        + penalty for rapid cycling (> 5 switches/hour per valve)
        
        Lower is better.
        Typical range: 300-2000 (arbitrary units)
        """
        # Base energy: sum of actuator duty cycles
        valve_energy = np.trapz(np.abs(valve_positions), dx=dt/3600)
        fan_energy = np.trapz(fan_speeds, dx=dt/3600)
        base_energy = valve_energy + fan_energy
        
        # Cycling penalty
        valve_switches = np.sum(np.abs(np.diff(valve_positions)) > 5)
        cycling_penalty = valve_switches * 50  # 50 points per switch
        
        return base_energy + cycling_penalty
    
    def comfort_score(self, T_observed, T_target, RH_observed, RH_target):
        """
        Comfort = MSE from setpoints
        
        Lower is better.
        Typical range: 0.1-5.0
        """
        T_error = np.mean((T_observed - T_target)**2)
        RH_error = np.mean((RH_observed - RH_target)**2)
        
        # Scale RH error to comparable magnitude
        return T_error + 0.5 * RH_error
    
    def stability_score(self, T_towers, RH_towers):
        """
        Stability = variance of climate across 4 towers
        
        Good controllers maintain uniform conditions.
        Lower is better.
        Typical range: 0.1-2.0
        """
        T_variance = np.var(np.mean(T_towers, axis=1))  # Avg per tower
        RH_variance = np.var(np.mean(RH_towers, axis=1))
        
        return T_variance + RH_variance
    
    def check_constraints(self, T_all, RH_all):
        """
        Return True if all hard constraints satisfied, False otherwise.
        """
        violations = (
            np.any(T_all < self.constraints['T_min']) or
            np.any(T_all > self.constraints['T_max']) or
            np.any(RH_all < self.constraints['RH_min']) or
            np.any(RH_all > self.constraints['RH_max'])
        )
        return not violations
    
    def total_score(self, energy, comfort, stability, constraints_met):
        """
        Final score (lower is better, so higher negative = worst).
        If constraints violated: return worst possible score.
        """
        if not constraints_met:
            return float('inf')  # Disqualified
        
        return (self.w_energy * energy + 
                self.w_comfort * comfort + 
                self.w_stability * stability)
```

### 4C: Leaderboard Display

```
┌─────────────────────────────────────────────────────────────────────────┐
│              RAINFOREST CLIMATE CONTROL ALGORITHM COMPETITION            │
│                        Leaderboard (Live Updated)                       │
├────┬──────────────────┬──────────────────┬────────┬─────────┬──────────┤
│Rank│  Team Name       │  Algorithm       │Energy  │ Comfort │Stability│
├────┼──────────────────┼──────────────────┼────────┼─────────┼──────────┤
│ 1  │ Alice ML Lab     │ RL_PPO_Adaptive  │ 450.2  │  0.82   │  0.15   │
│    │                  │ v3.1             │        │         │         │
├────┼──────────────────┼──────────────────┼────────┼─────────┼──────────┤
│ 2  │ Bob's Control Sys│ MPC_ModelPred_v2 │ 520.1  │  0.65   │  0.22   │
├────┼──────────────────┼──────────────────┼────────┼─────────┼──────────┤
│ 3  │ Charlie Inc      │ PID_Classic      │ 600.5  │  1.20   │  0.30   │
├────┼──────────────────┼──────────────────┼────────┼─────────┼──────────┤
│ 4  │ Diana's RL Team  │ DQN_Discrete     │ 890.0  │  2.15   │  0.45   │
└────┴──────────────────┴──────────────────┴────────┴─────────┴──────────┘

Filters: [Show All] [Constraints Met] [Top 10] [Recent Submissions]
Timeline: 7-day simulation  |  Last Updated: 2026-05-05 14:23:15 UTC
```

---

## PART 5: IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-12)

**Week 1-2: Data Preparation**
- Extract 500K timesteps from Oracle (64 inputs + 36 outputs)
- Exploratory analysis: seasonal patterns, anomalies, missing data
- Create normalized train/val/test splits

**Week 3-5: LSTM Training**
- Implement PyTorch LSTM encoder-decoder
- Add physics constraints layer
- Train on GPU (estimate 40-80 GPU-hours)
- Validate RMSE < 15%

**Week 6-8: API & Infrastructure**
- FastAPI server with /predict, /submit_algorithm endpoints
- Redis for caching predictions
- PostgreSQL schema for submissions/leaderboard
- Docker compose for local development

**Week 9-10: Evaluation Framework**
- Implement RainForestScorer class
- Test on reference baselines (PID controller, random)
- GitHub Actions CI/CD for automatic submission evaluation

**Week 11-12: Documentation & Student Onboarding**
- OpenAPI Swagger docs
- Example algorithms (PID, simple RL, random controller)
- Docker template repository
- Tutorial notebook

### Phase 2: Improvements (Weeks 13-24)

- Ensemble models (add Prophet, XGBoost backups)
- Uncertainty quantification (prediction confidence intervals)
- Scenario-based challenges (cold winter, hot summer cases)
- Multi-step predictions (lookahead 4, 24, 96 timesteps)
- Leaderboard versioning (track algorithm evolution)

### Phase 3: Production (Weeks 25+)

- Live connection to actual Biosphere 2 equipment (read-only validation)
- Historical replay mode (test algorithms against real outcomes)
- Student teams' long-running experiments
- Optional: real deployment with safety guards

---

## PART 6: TECHNOLOGY STACK

| Layer | Technology | Justification |
|-------|-----------|---|
| **Data Storage** | PostgreSQL | Reliable, ACID for leaderboard |
| **Cache** | Redis | Fast leaderboard queries, session state |
| **API** | FastAPI | Modern, fast, auto-docs |
| **Task Queue** | Celery | Parallel evaluation of submissions |
| **LSTM Framework** | PyTorch | Research-friendly, good performance |
| **Containerization** | Docker | Reproducibility, student sandboxing |
| **CI/CD** | GitHub Actions | Free, git-integrated |
| **Monitoring** | Prometheus + Grafana | Track API/worker health |
| **Visualization** | Plotly / D3.js | Real-time leaderboard, metrics dashboards |

---

## PART 7: HARD CONSTRAINTS & OPERATIONAL LIMITS

From Biosphere 2 operational requirements:

```python
BIOSPHERE2_CONSTRAINTS = {
    'temperature': {
        'min': 18,      # °C (equipment damage below this)
        'max': 32,      # °C (comfort/safety above this)
        'rate_limit': 2,  # °C/hour (prevent thermal shock)
    },
    'humidity': {
        'min': 40,      # % (desiccation risk)
        'max': 90,      # % (fungal/mold risk)
        'rate_limit': 10,  # %/hour
    },
    'pressure': {
        'limit': 2.5,   # Pa (target ±2.5 Pa vs outside)
    },
    'equipment': {
        'chiller_cycles': {
            'max_per_day': 12,        # Avoid excessive wear
            'min_runtime': 15*60,     # 15 minutes per cycle
            'cooldown': 5*60,         # 5 min between starts
        },
        'fan_duty_cycle': {
            'target': 0.4,  # Avg 40% utilization for longevity
            'max_continuous': 95,  # % (thermal protection)
        },
    },
    'energy': {
        'daily_budget_kwh': 500,     # Soft limit (advisory)
        'peak_power_kw': 150,        # Hard limit (circuit breaker)
    },
}
```

---

## PART 8: FUTURE ENHANCEMENTS & RESEARCH DIRECTIONS

1. **Reinforcement Learning Integration**
   - Train RL agents directly on surrogate model
   - PPO, DQN, A3C algorithms
   - Curriculum learning (start in stable conditions, progress to edge cases)

2. **Multi-Objective Optimization**
   - Pareto frontier of energy vs comfort
   - Interactive visualization for trade-off exploration

3. **Uncertainty Quantification**
   - Bayesian Neural Networks
   - Monte Carlo dropout
   - Confidence intervals on predictions

4. **Transfer Learning**
   - Pre-train on historical data
   - Fine-tune on season-specific variations
   - Adapt to equipment degradation over time

5. **Hardware-in-the-Loop Simulation**
   - Optional: connect to actual RainForest sensors for read-only validation
   - Shadow mode: run student algorithm in parallel, compare to production controller

---

## PART 9: REFERENCES & RESOURCES

- **LSTM Tutorial:** http://colah.github.io/posts/2015-08-Understanding-LSTMs/
- **PyTorch Time Series:** https://pytorch.org/tutorials/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Reinforcement Learning:** OpenAI Spinning Up, Stable-Baselines3
- **Biosphere 2:** https://biosphere2.org (operational data & constraints)

---

## KEY CONTACTS & DECISION MAKERS

- **Dimitri Bolt** (dimitribolt@arizona.edu) - Project Lead
- **John Adams** (jadamsb2@arizona.edu) - Biosphere 2 Operations Director
- **Professor Gabitov** - Academic Advisor

---

**Document Control:**
- Version: 1.0
- Status: Planning Phase (Ready for Implementation)
- Next Review: When development begins (Phase 1, Week 1)

