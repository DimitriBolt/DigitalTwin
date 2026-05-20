# Climate Control Quick Start Reference

**Use this guide to quickly recall the RainForest Digital Twin project.**

---

## PROJECT AT A GLANCE

| Aspect | Details |
|--------|---------|
| **Project Name** | RainForest Digital Twin for Climate Control Algorithm Competition |
| **User Keywords** | "Climate control" (2 words) → triggers this project |
| **Main Goal** | Build platform for students to develop & test climate control algorithms |
| **System** | LSTM surrogate model trained on 15 years of Biosphere 2 data |
| **Input Controls** | 64 programmable parameters (temperature, fan, valves) |
| **Output Sensors** | 36 monitoring channels (18 T + 18 RH across 4 towers) |
| **Data Volume** | ~500K timesteps (15 years × 15-min intervals) |

---

## QUICK REFERENCE: 64 INPUT CONTROLS

```
🌡️ Temperature setpoints:  15 parameters
🌬️ Supply fan commands:    7 parameters
🔧 Valve/damper commands:  42 parameters
   ├── Cooling valve         (included)
   ├── Heating valve         (included)
   ├── Economizer/damper     (included)
   ├── Valve position        (included)
   └── Occupancy/schedule    (included)
   ─────────────────────────────────────
TOTAL:                      64 parameters
```

---

## QUICK REFERENCE: 36 OUTPUT SENSORS

```
4 Vertical Measurement Towers:

Mountain Tower:      8 channels (4T + 4RH at 100, 300, 700, 1300 cm)
Northeast Tower:    10 channels (5T + 5RH, includes 2000 cm)
Northwest Tower:     8 channels (4T + 4RH at 100, 300, 700, 1300 cm)
South Tower:        10 channels (5T + 5RH, includes 2000 cm)
─────────────────────────────────────────────────────
Subtotal Temperature: 18 channels (9 per tower average)
Subtotal Humidity:    18 channels (9 per tower average)
─────────────────────────────────────────────────────
TOTAL:                36 monitoring sensors
```

---

## HOW THE CONTROL LOOP WORKS

The system operates as a **closed feedback loop** — analogous to QuantConnect LEAN for trading strategies, but for climate control:

```
┌─────────────────────────────────────────────────────────┐
│                  CONTROL LOOP (15-min steps)            │
│                                                         │
│  ┌──────────────┐    64 commands    ┌────────────────┐  │
│  │   ALGORITHM  │ ─────────────────>│  LSTM DIGITAL  │  │
│  │  (student or │                   │     TWIN       │  │
│  │  automated)  │ <─────────────────│  (environment  │  │
│  └──────────────┘  36 sensor values │   simulator)   │  │
│         ↑                           └────────────────┘  │
│   observe & decide                   ↑ temporal dynamics│
└─────────────────────────────────────────────────────────┘
```

**Key temporal properties the LSTM must capture:**
- **Delay** — outputs respond to inputs with a lag (thermal mass, air circulation time)
- **Autocorrelation** — current state depends on previous states (inertia)
- **Context window** — last 24 hours of history (96 × 15-min steps) needed for accurate prediction

**Framing as Reinforcement Learning environment:**

| RL Concept | In This System |
|---|---|
| State | 36 sensor readings + time of day/season |
| Action | 64 control parameter settings |
| Reward | Comfort score + energy efficiency + stability |
| Dynamics | LSTM model (simulates system response including delays) |
| Episode | e.g., 7-day simulation window |

**Algorithm types students can implement:**
- Classical: PID, rule-based bang-bang
- Predictive: MPC (Model Predictive Control)
- Learning: RL agents (train against the LSTM surrogate directly)

**Analogy:** LSTM surrogate = simulated market in QuantConnect; control algorithm = trading strategy.

---

## MODELING STRATEGY

**Primary Approach:** Hybrid LSTM + Physics-Informed Residuals

```
Input (64 params)
    ↓
LSTM Encoder (3 layers × 128 units)
    ↓
Physics Constraints (enforce physical limits)
    ↓
LSTM Decoder (3 layers × 128 units)
    ↓
Output (36 sensors)

Expected Performance:
  - RMSE: 10-15% (Phase 1 MVP)
  - Inference: ~50ms per 15-minute timestep
  - Training: 2-3 weeks on GPU
```

**Why LSTM?**
- ✅ Captures long-term dependencies
- ✅ Fast inference (~50ms)
- ✅ Natural physics integration
- ✅ 15 years of data sufficient for training

**Backup Ensemble:** Prophet (seasonal) + XGBoost (fast baseline)

---

## STUDENT SUBMISSION WORKFLOW

```
1. WRITE code locally
   └─ Implement control_algorithm(sensors, config) → commands

2. TEST with provided Docker image
   └─ Simulate locally against surrogate model

3. SUBMIT via GitHub or Docker registry
   └─ Platform CI/CD automatically validates

4. EVALUATE (automated)
   └─ 7-day simulation, compute 3 metrics

5. LEADERBOARD update
   └─ Real-time ranking visible to all students
```

**Student Algorithm Template:**
```python
def control_algorithm(sensors_dict, config):
    """
    Input: 36 sensor channels + target setpoints
    Output: 64 control commands
    """
    # PID, MPC, RL, or any approach...
    pass
```

---

## SCORING SYSTEM

**Total Score = Energy (40%) + Comfort (35%) + Stability (25%)**

| Metric | Lower Better? | Typical Range | Description |
|--------|---------------|---------------|---|
| Energy | ✅ Yes | 300-2000 | Sum of valve/fan duty cycles + cycling penalty |
| Comfort | ✅ Yes | 0.1-5.0 | MSE from temperature/humidity setpoints |
| Stability | ✅ Yes | 0.1-2.0 | Variance of climate across 4 towers |

**Hard Constraints (Violation = Disqualification):**
- Temperature: 18-32°C
- Humidity: 40-90%
- Pressure: ±2.5 Pa

---

## IMPLEMENTATION TIMELINE

**Phase 1 (Weeks 1-12): MVP**
1. Data extraction & normalization (Weeks 1-2)
2. LSTM training & validation (Weeks 3-5)
3. API & infrastructure (Weeks 6-8)
4. Evaluation framework & CI/CD (Weeks 9-10)
5. Documentation & student onboarding (Weeks 11-12)

**Phase 2 (Weeks 13-24): Improvements**
- Ensemble models, uncertainty quantification, scenario challenges

**Phase 3 (Weeks 25+): Production**
- Live integration, historical replay, long-running experiments

---

## KEY FILES & LOCATIONS

```
Project Root: /home/dimitri/PycharmProjects/CO2Flux

docs/
  └─ CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md  ← MAIN REFERENCE
  └─ CLIMATE_CONTROL_QUICK_START.md        ← THIS FILE

Sensors_Description/
  └─ variables_schema.xlsx  (64 inputs, 36 outputs defined)

scripts/
  └─ analyze_rainforest_scope.py  (confirm 64 & 36 counts)
  └─ filter_input_climate_controls.py  (list all 64 inputs)

Project_description/
  └─ Response_to_John_Adams_Climate_Control_RainForest.txt
```

---

## DECISION POINTS FOR NEXT PHASE

When continuing this project, you will need to decide:

1. **LSTM Framework?**
   - PyTorch (recommended) vs TensorFlow

2. **Data Extraction?**
   - Use existing scripts to query Oracle, or build new pipeline?

3. **Student Interface?**
   - REST API + Docker (recommended) vs Jupyter notebooks?

4. **Leaderboard?**
   - GitHub-based vs custom web dashboard?

5. **Deployment?**
   - Local development vs AWS/Cloud infrastructure?

---

## STAKEHOLDERS & NEXT CONTACT

- **John Adams** (jadamsb2@arizona.edu)
  - Biosphere 2 Operations Director
  - Key constraint requirements (equipment cycling, energy limits)
  
- **Professor Gabitov**
  - Academic supervisor
  
- **Dimitri Bolt** (dimitribolt@arizona.edu)
  - Project lead

---

**This document should be consulted whenever "Climate control" is mentioned.**  
Last Updated: May 5, 2026

