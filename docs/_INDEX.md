# Climate Control Project Documentation Index

## Overview

This folder (`docs/`) contains all planning, architecture, and reference materials for the **RainForest Digital Twin & Climate Control Algorithm Competition** project.

**Key Trigger:** When you see "Climate control" (2 words) in a user message, navigate to this folder.

---

## 📚 Document Guide

### 1. **CLIMATE_CONTROL_QUICK_START.md** ← START HERE
**Purpose:** Rapid context refresh and project overview  
**Read Time:** 5-10 minutes  
**Best for:** Refreshing memory, understanding scope at a glance  
**Contains:**
- Project summary (64 inputs, 36 outputs)
- Quick reference tables
- Modeling strategy overview
- Implementation timeline
- File locations

---

### 2. **CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md** ← DETAILED REFERENCE
**Purpose:** Comprehensive implementation plan  
**Read Time:** 30-45 minutes (first read); 5-10 min (specific sections)  
**Best for:** Making implementation decisions, understanding architecture  
**Contains:**
- Part 1: Surrogate Model Selection (LSTM + Physics)
- Part 2: Data Preparation Pipeline
- Part 3: System Architecture (microservices diagram)
- Part 4: Student Submission & Evaluation System
- Part 5: Implementation Roadmap (Phase 1/2/3)
- Part 6: Technology Stack
- Part 7: Hard Constraints & Operational Limits
- Part 8: Future Research Directions

---

## 🎯 Quick Navigation by Task

| User Intent | Read This | Time |
|------------|-----------|------|
| "Remind me of the project scope" | QUICK_START | 5 min |
| "What algorithms should we use?" | PLAN, Part 1 | 15 min |
| "How should students submit?" | PLAN, Part 4A | 10 min |
| "What are the scoring metrics?" | PLAN, Part 4B | 10 min |
| "When do we need to start Phase 1?" | PLAN, Part 5 | 10 min |
| "What technology stack?" | PLAN, Part 6 | 5 min |
| "What are hard constraints?" | PLAN, Part 7 | 10 min |

---

## 📊 System at a Glance

The system is a **closed-loop control simulator** (similar to QuantConnect LEAN, but for climate):

```
                  ┌──────────────────────────────┐
                  │     CONTROL LOOP (step=15min) │
                  │                               │
  ┌─────────────┐ │  64 commands (action)         │
  │  ALGORITHM  │─┼──────────────────────────>    │
  │  (student)  │ │                               │
  │             │ │       LSTM DIGITAL TWIN        │
  │  observe &  │ │    (environment simulator)     │
  │  decide     │ │    - temporal delays           │
  │             │ │    - autocorrelation           │
  │             │<┼─────────────────────────────  │
  └─────────────┘ │  36 sensor values (state)     │
                  └──────────────────────────────┘
                              │
                              ↓
              EVALUATION (after N-day episode)
         Score = Energy (40%) + Comfort (35%) + Stability (25%)

INPUT LAYER (64 control parameters)
  ├── Temperature setpoints: 15
  ├── Supply fan commands: 7
  └── Valve/damper commands: 42

LSTM MODEL trained on 500K historical timesteps
  └── Captures: delays, autocorrelation, seasonal patterns

OUTPUT LAYER (36 monitoring sensors)
  ├── Mountain Tower: 8 channels
  ├── Northeast Tower: 10 channels
  ├── Northwest Tower: 8 channels
  └── South Tower: 10 channels
```

---

## 🔧 Key Implementation Decisions

### Surrogate Model Choice: LSTM + Physics-Informed Residuals
- **Why?** Fast inference (~50ms), captures temporal dependencies, integrates physics naturally
- **Alternative:** Transformer (more accurate but slower), Prophet (for seasonality), XGBoost (baseline)
- **Ensemble approach:** Use all three as backup/validation

### Student Submission Method: REST API + Docker
- **Why?** Scalable, fair (all students use same model), secure sandboxing
- **Alternative:** Jupyter notebooks (more educational, less secure)

### Scoring Weights: 40% Energy, 35% Comfort, 25% Stability
- **Rationale:** Balance operational efficiency with environmental integrity
- **Hard constraints:** Temperature 18-32°C, Humidity 40-90% (violation = disqualification)

### Deployment Architecture: Microservices (FastAPI + Celery)
- **Why?** Parallel evaluation, scalable to many students
- **Components:** Student API, LSTM service, Worker pool, Redis cache, PostgreSQL

---

## 📈 Project Timeline

```
Phase 1: MVP (Weeks 1-12)
├─ Data prep (Weeks 1-2)
├─ LSTM training (Weeks 3-5)
├─ API & infrastructure (Weeks 6-8)
├─ Evaluation framework (Weeks 9-10)
└─ Student docs (Weeks 11-12)

Phase 2: Refinements (Weeks 13-24)
├─ Ensemble models
├─ Uncertainty quantification
└─ Scenario challenges

Phase 3: Production (Weeks 25+)
├─ Live integration
├─ Historical replay
└─ Extended competitions
```

---

## 📍 File Locations (Project Root)

```
/home/dimitri/PycharmProjects/CO2Flux/

docs/                           ← YOU ARE HERE
  ├─ CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md
  ├─ CLIMATE_CONTROL_QUICK_START.md
  └─ _INDEX.md                  (this file)

Sensors_Description/
  └─ variables_schema.xlsx      (64 inputs, 36 outputs defined)

scripts/
  ├─ analyze_rainforest_scope.py
  ├─ filter_input_climate_controls.py
  ├─ update_input_sheet.py
  └─ update_rainforest_output_sheet.py

Project_description/
  └─ Response_to_John_Adams_Climate_Control_RainForest.txt

AGENTS.md                       (update with Climate control memory)
```

---

## 🎓 Next Steps (When Implementation Begins)

1. **Data Pipeline**
   - Run `analyze_rainforest_scope.py` to confirm 500K timesteps
   - Extract 64 inputs + 36 outputs from Oracle SensorDB
   - Normalize and split into train/val/test (70/15/15 temporal)

2. **LSTM Training**
   - Set up PyTorch environment (GPU recommended)
   - Implement encoder-decoder architecture
   - Train and validate (target: RMSE < 15%)

3. **REST API**
   - Implement FastAPI server with `/predict` endpoint
   - Create submission pipeline
   - Set up CI/CD (GitHub Actions)

4. **Evaluation Framework**
   - Implement `RainForestScorer` class (energy, comfort, stability)
   - Create leaderboard visualization
   - Test on reference baselines (PID controller)

5. **Student Documentation**
   - Write API docs (OpenAPI/Swagger)
   - Create example algorithms
   - Build Docker template repository

---

## ❓ FAQ & Decision Points

**Q: Why LSTM instead of Transformer?**  
A: LSTM trains faster (2-3 weeks) with our data volume. Transformer could be Phase 2 enhancement.

**Q: How accurate should the surrogate be?**  
A: Phase 1 targets 10-15% RMSE. Good enough for algorithm comparison. Phase 2 can refine to <5%.

**Q: Should we connect to real equipment?**  
A: Not in Phase 1. Phase 3 allows optional read-only validation. Safety-first approach.

**Q: What if student algorithm violates constraints?**  
A: Automatic disqualification from leaderboard. Algorithm stored for debugging.

**Q: Can students use reinforcement learning?**  
A: Yes! RL agents can train on the surrogate model directly.

---

## 👥 Stakeholders & Communication

- **John Adams** (jadamsb2@arizona.edu)
  - Requires: hard constraints, equipment cycling limits
  - Feedback cycle: Weekly during Phase 1

- **Professor Gabitov** 
  - Academic supervisor
  - Reviews architecture & research methodology

- **Dimitri Bolt** (dimitribolt@arizona.edu)
  - Project lead
  - Day-to-day implementation

---

## 📝 Document Maintenance

**Last Updated:** May 5, 2026  
**Next Review:** When Phase 1 development begins (Week 1, estimated June 2026)  
**Maintainer:** Dimitri Bolt

---

## 🔗 Related Files & Contexts

- `../AGENTS.md` - Project instructions for AI agents
- `../README.md` - Overall project overview
- `Response_to_John_Adams_Climate_Control_RainForest.txt` - Official correspondence with stakeholder

---

**Remember:** When the user mentions "Climate control" (2 words), navigate here and reference these documents!

