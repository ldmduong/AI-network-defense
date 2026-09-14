# AI-Driven Network Intrusion Detection & Autonomous Response

## 1. Tổng quan project

**Tên project:** AI-Driven Network Intrusion Detection & Autonomous Response

### Mục tiêu

Xây dựng một hệ thống phòng thủ mạng sử dụng Machine Learning để:

1. Phát hiện traffic bất thường.
2. Phân loại loại tấn công.
3. Đánh giá mức độ rủi ro.
4. Sử dụng Reinforcement Learning để tự động quyết định hành động phản ứng.
5. Expose toàn bộ pipeline qua REST API.
6. Theo dõi experiment/model bằng MLflow.
7. Monitoring hệ thống bằng Prometheus + Grafana.
8. Containerize và triển khai bằng Docker.
9. Tự động kiểm thử/build/deploy bằng GitHub Actions.
10. Quản lý toàn bộ source code bằng Git.

### Điểm khác biệt cốt lõi

Project không chỉ giải quyết:

> "Traffic này có phải attack không?"

mà giải quyết thêm:

> "Với traffic này và context hiện tại, hệ thống nên làm gì?"

Pipeline cốt lõi:

```text
Detect → Classify → Decide → Act → Feedback → Retrain
```

---

# 2. MUST-HAVE technologies

Project được chốt với 11 thành phần bắt buộc:

| Nhóm | Technology | Vai trò |
|---|---|---|
| Dataset | CICIDS2017 | Network traffic dataset |
| AI | Autoencoder | Anomaly detection |
| AI | XGBoost | Attack classification |
| AI | DQN | Autonomous response decision |
| Backend | FastAPI | REST API / model serving |
| MLOps | MLflow | Experiment & model tracking |
| Monitoring | Prometheus | Metrics collection |
| Monitoring | Grafana | Dashboard / visualization |
| DevOps | Docker | Containerization |
| DevOps | Git | Version control |
| DevOps | GitHub Actions | CI/CD |

Không cần thêm công nghệ khác để hoàn thành MVP. Các công nghệ như PPO, SHAP, DVC, Redis, Kubernetes, cloud deployment chỉ nên là stretch goals.

---

# 3. Kiến trúc tổng thể

```text
                         CICIDS2017
                             │
                             ▼
                ┌────────────────────────┐
                │ 
                └────────────┬───────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │ Detection Layer    │
                  └─────────┬──────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │   Autoencoder   │          │     XGBoost     │
     │                 │          │                 │
     │ Anomaly Score   │          │ Attack Type     │
     └────────┬────────┘          │ Probability     │
              │                   └────────┬────────┘
              │                            │
              └──────────────┬─────────────┘
                             ▼
                  ┌────────────────────┐
                  │ Row-ordered Window │
                  │ State              │
                  │                    │
                  │ Flow features      │
                  │ Anomaly score      │
                  │ Attack probability │
                  │ Previous action     │
                  │ Recent attack rate │
                  │ Traffic statistics │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │      DQN Agent     │
                  │                    │
                  │  Decision Making   │
                  └─────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
       ALLOW             MONITOR          RATE-LIMIT
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                     BLOCK / ESCALATE
                            │
                            ▼
                    Human Feedback
                            │
                            ▼
                      Retraining
```

DevOps/MLOps bao quanh hệ thống:

```text
                         Git
                          │
                          ▼
                   GitHub Repository
                          │
                          ▼
                    GitHub Actions
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
              Tests              Build
                                  │
                                  ▼
                                Docker
                                  │
                                  ▼
                            Deploy API
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
                Prometheus                   MLflow
                    │                           │
                    ▼                           ▼
                 Grafana                  Model / Experiment
```

---

# 4. Vai trò của từng thành phần

## 4.1 CICIDS2017

Dataset chính của project.

Network traffic được biểu diễn dưới dạng network flow với nhiều feature như:

```text
Flow Duration
Total Fwd Packets
Total Backward Packets
Total Length of Fwd Packets
Total Length of Bwd Packets
Fwd Packet Length Mean
Bwd Packet Length Mean
Flow Bytes/s
Flow Packets/s
SYN Flag Count
ACK Flag Count
...
```

Các class có thể bao gồm:

```text
BENIGN
DDoS
PortScan
Bot
FTP-Patator
SSH-Patator
DoS Hulk
DoS GoldenEye
...
```

Không nhất thiết phải sử dụng toàn bộ feature. Cần có bước feature selection và xử lý leakage/irrelevant features.

## Dataset snapshot used for the MVP

Phiên bản CSV hiện tại có khoảng **2,52 triệu flow**, gồm **52 numerical flow features** và một cột nhãn `Attack Type`. Dataset không có timestamp, source identity, destination identity hoặc protocol metadata.

Vì vậy MVP được giới hạn ở **flow-level detection/classification** và một **row-ordered offline simulator**. Các khái niệm như source blocklist, session tracking và attacker đổi IP không được xem là dữ liệu quan sát thật; nếu dùng trong simulator, chúng phải được ghi rõ là simulation assumptions.

---

# 5. Data Processing Pipeline

Pipeline:

```text
Raw CICIDS2017
       ↓
Remove invalid values
       ↓
Handle NaN / Inf
       ↓
Remove leakage / irrelevant columns
       ↓
Feature selection
       ↓
Scaling
       ↓
Train / Validation / Test
```

## Row-ordered train / validation / test split

Phiên bản CSV hiện tại không có `Timestamp`, `Source IP`, `Destination IP` hoặc `Protocol`. Vì vậy không thể tuyên bố đây là temporal split thực sự theo thời gian mạng.

Trong MVP, dữ liệu được chia theo thứ tự dòng của file và phải được mô tả chính xác là **row-ordered split** hoặc **pseudo-temporal split**:

```text
Earlier rows
      │
      ▼
   TRAIN

Middle rows
      │
      ▼
 VALIDATION

Later rows
      │
      ▼
    TEST
```

Ví dụ:

```text
First 70%  → TRAIN
Next 15%   → VALIDATION
Last 15%   → TEST
```

Mục tiêu là giữ nguyên thứ tự replay trong simulator và hạn chế việc trộn ngẫu nhiên toàn bộ dataset. Tuy nhiên, vì file không chứa timestamp, kết quả không được gọi là đánh giá trên traffic tương lai thật.

Nếu cần temporal split thực sự, phải sử dụng PCAP hoặc phiên bản dữ liệu có timestamp và metadata mạng tương ứng.

---

# 6. Detection Layer

Detection Layer gồm hai model:

```text
                 Network Flow
                     │
            ┌────────┴────────┐
            ▼                 ▼
      Autoencoder          XGBoost
            │                 │
            ▼                 ▼
      Anomaly Score      Attack Type
                          Probability
```

Hai model có hai nhiệm vụ khác nhau:

### Autoencoder

> What looks unusual?

### XGBoost

> What kind of attack is this?

Sau đó DQN trả lời:

> What should I do?

Pipeline:

```text
Detect → Classify → Decide
```

---

# 7. Autoencoder

## Mục tiêu

Autoencoder được train chủ yếu trên:

```text
BENIGN traffic
```

Architecture cơ bản:

```text
Input
  │
  ▼
Encoder
  │
  ▼
Latent Representation
  │
  ▼
Decoder
  │
  ▼
Reconstructed Input
```

Ví dụ:

```text
78 features
    ↓
64
    ↓
32
    ↓
16
    ↓
32
    ↓
64
    ↓
78
```

Model học representation của traffic bình thường.

Sau đó tính:

```text
Reconstruction Error
        ↓
Anomaly Score
```

Ví dụ:

```text
Normal traffic
reconstruction error = 0.03

Suspicious traffic
reconstruction error = 0.71
```

Traffic thứ hai có khả năng bất thường cao.

---

# 8. Anomaly threshold

Không nên hard-code:

```python
if anomaly_score > 0.5:
    attack
```

mà cần xác định threshold từ validation data.

Quy trình:

```text
Training normal traffic
        ↓
Autoencoder
        ↓
Validation normal traffic
        ↓
Distribution of reconstruction errors
        ↓
Choose threshold
```

Có thể lựa chọn dựa trên:

- Percentile.
- False Positive Rate mục tiêu.
- Operational cost.

Ví dụ:

```text
Threshold = 99th percentile
```

hoặc tối ưu theo:

```text
Expected Operational Cost
```

---

# 9. XGBoost

Autoencoder cho biết traffic có bất thường hay không.

XGBoost giúp xác định loại attack.

Ví dụ:

```text
Input
 │
 ▼
XGBoost
 │
 ├── BENIGN       0.02
 ├── DDoS         0.11
 ├── PortScan     0.81
 ├── Bot          0.04
 └── BruteForce   0.02
```

Kết quả:

```text
attack_type = PortScan
confidence = 0.81
```

XGBoost được ưu tiên làm supervised classifier chính vì:

- Hiệu quả tốt trên tabular network-flow data.
- Training tương đối nhanh.
- Dễ tune.
- Dễ giải thích hơn nhiều deep learning architecture.
- Giảm scope so với việc đồng thời dùng CNN + LSTM + Transformer.

---

# 10. Vì sao Autoencoder + XGBoost?

Đây là thiết kế hai tầng:

```text
Autoencoder
     ↓
Anomaly detection
     +
XGBoost
     ↓
Attack classification
```

Ví dụ:

```text
Traffic
   ↓
Autoencoder
   ↓
Anomaly Score = 0.91
   ↓
XGBoost
   ↓
PortScan = 0.94
   ↓
DQN
   ↓
RATE-LIMIT
```

Điều này tốt hơn việc chỉ có một classifier vì hệ thống vừa có anomaly signal vừa có attack-class signal.

---

# 11. DQN Decision Layer

Đây là phần khác biệt quan trọng nhất của project.

DQN không trực tiếp phát hiện attack.

Nó sử dụng thông tin từ detection layer để quyết định hành động.

```text
Autoencoder
     │
     └── Anomaly Score
              │
XGBoost       │
     │        │
     └── Attack Probability
              │
              ▼
        Row-ordered Window State
              │
              ▼
             DQN
              │
              ▼
          Action
```

---

# 12. Vì sao phải có Window Context?

Nếu mỗi flow hoàn toàn độc lập thì interviewer có thể hỏi:

> Why do you need Reinforcement Learning instead of a cost-sensitive classifier?

Do đó state phải chứa context của các dòng replay gần nhất. Đây là window context, không phải temporal context có timestamp thật.

Ví dụ:

```text
State_t =
[
    flow_duration,
    packet_rate,
    byte_rate,
    fin_flag_count,
    psh_flag_count,
    ack_flag_count,
    ...

    anomaly_score,

    P(BENIGN),
    P(DDoS),
    P(PortScan),
    P(Bot),
    P(BruteForce),

    previous_action,

    recent_attack_count,
    recent_flow_count,
    recent_bytes,
    recent_packets,
    attack_density_in_window,
    destination_port,
    port_diversity,
    action_cooldown
]
```

Các giá trị `recent_*` được tính trên một cửa sổ gồm các dòng replay trước đó. Đây là context theo thứ tự dữ liệu, không phải temporal context có timestamp hoặc session identity thật.

---

# 13. Ví dụ row-ordered window decision

## Scenario A

```text
1 suspicious flow
```

DQN có thể chọn:

```text
MONITOR
```

## Scenario B

```text
100 suspicious flows trong một cửa sổ replay
        ↓
cùng destination port
        ↓
high packet rate
        ↓
attack density tăng
```

DQN có thể chọn:

```text
BLOCK
```

Hai flow riêng lẻ có thể tương tự nhau, nhưng context khác nhau.

Đây là lý do để mô hình hóa bài toán như sequential decision-making.

---

# 14. Action Space

DQN có 5 actions:

```text
0 → ALLOW
1 → MONITOR
2 → RATE-LIMIT
3 → BLOCK
4 → ESCALATE
```

## ALLOW

Cho traffic đi qua.

## MONITOR

Cho traffic đi qua nhưng tăng giám sát.

## RATE-LIMIT

Giới hạn traffic.

## BLOCK

Chặn traffic.

## ESCALATE

Đưa case cho security analyst/human.

ESCALATE không phải action "mạnh hơn BLOCK".

Nó đại diện cho:

```text
AI uncertain / high-impact case
              ↓
       Human decision
```

---

# 15. Reward Function

Đây là phần quan trọng nhất của RL.

Không nên chỉ dùng:

```text
Correct = +1
Wrong = -1
```

Thay vào đó sử dụng cost-sensitive reward.

Ví dụ ban đầu:

## Normal traffic

| Action | Reward |
|---|---:|
| ALLOW | +5 |
| MONITOR | +3 |
| RATE-LIMIT | -5 |
| BLOCK | -30 |
| ESCALATE | -8 |

Block normal traffic gây service disruption nên chi phí cao.

## Low-risk attack

| Action | Reward |
|---|---:|
| ALLOW | -8 |
| MONITOR | +3 |
| RATE-LIMIT | +6 |
| BLOCK | +4 |
| ESCALATE | +5 |

## High-risk attack

| Action | Reward |
|---|---:|
| ALLOW | -30 |
| MONITOR | -5 |
| RATE-LIMIT | +5 |
| BLOCK | +15 |
| ESCALATE | +12 |

Các con số trên chỉ là initial configuration.

Cần calibration/tuning dựa trên validation scenarios.

---

# 16. Không ép DQN phải thắng bằng mọi giá

Không nên đặt mục tiêu:

> DQN phải có accuracy cao hơn XGBoost.

XGBoost và DQN giải quyết hai bài toán khác nhau.

Nên so sánh:

```text
Rule-based Policy
        VS
DQN Policy
```

Ví dụ rule baseline:

```python
if anomaly_score > 0.8:
    BLOCK
elif attack_probability > 0.7:
    RATE_LIMIT
else:
    ALLOW
```

DQN:

```text
State
 ↓
DQN
 ↓
Action
```

So sánh bằng:

```text
Expected Operational Cost
False Positive Cost
Missed Attack Cost
Block Rate
Service Disruption
Average Reward
```

Câu hỏi nghiên cứu chính:

> Does DQN reduce expected operational cost compared with a rule-based baseline?

---

# 17. Flow-Level Offline Network Defense Simulator

Với CICIDS2017, project nên được mô tả chính xác là:

> Cost-Sensitive Row-Ordered Offline Flow Simulator

Không nên claim:

> AI trực tiếp chống tấn công trên production network.

Flow được replay:

```text
CICIDS2017
    ↓
Candidate Flow 1
    ↓
Agent Action
    ↓
Environment Transition
    ↓
Candidate Flow 2
    ↓
Agent Action
    ↓
Environment Transition
    ↓
...
```

## 17.1. Vì sao replay đơn thuần chưa đủ cho DQN?

Nếu chỉ đọc tuần tự các flow trong file, action của agent không làm thay đổi flow kế tiếp:

```text
Flow 1 → Flow 2 → Flow 3 → Flow 4
```

Trong trường hợp đó, dù agent chọn `BLOCK` ở Flow 1 thì Flow 2 vẫn được đưa vào như thể chưa có firewall. Khi state kế tiếp không phụ thuộc vào action trước đó, bài toán gần với **cost-sensitive contextual bandit** hơn là Reinforcement Learning đầy đủ.

Vì vậy, environment phải mô phỏng tác động của action lên trạng thái hệ thống:

```text
State_t + Action_t
        ↓
Firewall / Rate-limit / Alert state
        ↓
State_(t+1)
        ↓
Reward_t
```

Dataset hiện tại chỉ cung cấp flow-level features và không có identity của source/destination. State không được chứa nhãn thật của flow. Nhãn chỉ được environment dùng nội bộ để tính reward trong offline simulator.

Ví dụ state có thể gồm:

```text
[
    anomaly_score,
    attack_probabilities,
    recent_attack_rate,
    recent_packet_rate,
    recent_flow_count,
    recent_bytes,
    attack_density_in_window,
    destination_port,
    port_diversity,
    alert_queue_size,
    previous_action,
    action_cooldown
]
```

Các action tác động ở mức flow/window, không đại diện cho firewall đang chặn một source IP thật:

| Action | Tác động ngay | Ảnh hưởng lên state kế tiếp |
|---|---|---|
| `ALLOW` | Chấp nhận flow hiện tại | Cập nhật các bộ đếm flow/byte/packet trong cửa sổ replay |
| `MONITOR` | Chấp nhận flow và tăng alert counter | Tăng context quan sát cho các flow tiếp theo |
| `RATE-LIMIT` | Giới hạn số flow hoặc bytes được chấp nhận trong window | Cập nhật `action_cooldown` và throughput giả lập |
| `BLOCK` | Loại bỏ flow hiện tại hoặc flow có cùng signature trong vài bước | Cập nhật trạng thái block giả lập; không được gọi là block source IP thật |
| `ESCALATE` | Đưa flow vào alert queue | Tạo độ trễ và pending-case counter trong các bước sau |

Ví dụ transition giả lập cho `BLOCK`:

```python
if action == BLOCK:
    blocked_until[current_signature] = current_step + block_duration

next_candidate = replay.next_flow()

if signature(next_candidate) in blocked_until:
    next_state = build_blocked_event_state(next_candidate)
else:
    next_state = build_processed_flow_state(next_candidate)
```

Ở đây `current_signature` chỉ là signature mô phỏng được tạo từ các feature có sẵn, chẳng hạn `Destination Port` và các thống kê flow. Nó không phải source identity thật. Với CICIDS2017, attacker cũng không thực sự phản ứng trong dữ liệu lịch sử; mọi quy tắc giảm throughput, block signature hoặc thay đổi attack density đều phải được ghi rõ là **simulation assumptions**.

Do đó project nên được gọi là **cost-sensitive row-ordered offline flow simulator** hoặc **semi-synthetic offline simulator**, không phải bản sao production network.

Nếu chưa xây được transition có tác động của action, nên triển khai rule-based policy hoặc contextual bandit trước, thay vì tuyên bố rằng DQN đã học sequential decision-making.

Có thể triển khai environment:

```python
class NetworkDefenseEnv(gym.Env):
    ...
```

Công cụ RL:

```text
Gymnasium
Stable-Baselines3
DQN
```

Gymnasium/Stable-Baselines3 là implementation dependencies hỗ trợ DQN; không phải các MUST-HAVE technologies cần quảng bá ở tiêu đề project.

---

# 18. FastAPI

FastAPI là MUST-HAVE và là lớp serving/backend.

Kiến trúc:

```text
Client
  │
  │ HTTP
  ▼
FastAPI
  │
  ├── Autoencoder
  │
  ├── XGBoost
  │
  └── DQN
       │
       ▼
     Action
```

FastAPI biến project từ một ML notebook thành một hệ thống có thể gọi qua API.

---

# 19. API endpoints

## POST /api/v1/analyze

Input:

```json
{
  "features": {
    "flow_duration": 120,
    "total_fwd_packets": 15,
    "total_bwd_packets": 8,
    "flow_bytes": 5420
  }
}
```

Output:

```json
{
  "anomaly_score": 0.91,
  "attack_type": "PortScan",
  "confidence": 0.94,
  "risk_score": 0.87,
  "recommended_action": "RATE_LIMIT"
}
```

---

## POST /api/v1/feedback

Security analyst gửi feedback:

```json
{
  "event_id": "abc123",
  "true_label": "BENIGN",
  "actual_action": "BLOCK",
  "correct_action": "ALLOW"
}
```

Pipeline:

```text
Human Feedback
      ↓
Store
      ↓
Future Retraining
```

---

## GET /api/v1/health

Ví dụ:

```json
{
  "status": "healthy",
  "detector": "loaded",
  "classifier": "loaded",
  "rl_agent": "loaded"
}
```

---

## GET /api/v1/metrics

Expose metrics cho Prometheus.

---

## GET /docs

FastAPI tự cung cấp Swagger UI/OpenAPI documentation.

Demo:

```text
Swagger UI
   ↓
POST /analyze
   ↓
Network Flow
   ↓
AI Detection
   ↓
DQN Decision
```

---

# 20. MLflow

MLflow dùng cho:

- Experiment tracking.
- Parameter tracking.
- Metric tracking.
- Artifact tracking.
- Model versioning/registry.

## Autoencoder

Track:

```text
learning_rate
batch_size
latent_dim
epochs
threshold
reconstruction_error
```

Metrics:

```text
Validation FPR
Validation Recall
PR-AUC
```

## XGBoost

Track:

```text
max_depth
learning_rate
n_estimators
subsample
```

Metrics:

```text
Accuracy
Precision
Recall
F1
ROC-AUC
PR-AUC
```

## DQN

Track:

```text
learning_rate
gamma
epsilon
batch_size
buffer_size
target_update
```

Metrics:

```text
Episode Reward
Average Reward
Expected Cost
Action Distribution
```

MLflow giúp trả lời:

> Production model hiện tại được train bằng configuration nào và có kết quả ra sao?

---

# 21. Prometheus

Prometheus tập trung vào runtime/system metrics.

Ví dụ:

```text
http_requests_total
prediction_latency_seconds
prediction_errors_total

allow_actions_total
monitor_actions_total
rate_limit_actions_total
block_actions_total
escalate_actions_total
```

Có thể theo dõi:

```text
API Requests
API Latency
Error Rate
Prediction Count
Action Count
```

---

# 22. Grafana

Grafana sử dụng dữ liệu từ Prometheus.

Dashboard đề xuất:

```text
┌─────────────────────────────────────────────┐
│         NETWORK DEFENSE DASHBOARD           │
├───────────────┬───────────────┬─────────────┤
│ Requests/sec  │ Avg Latency   │ Error Rate  │
│               │               │             │
├───────────────┴───────────────┴─────────────┤
│                                             │
│           Attack Detection Rate             │
│                                             │
├──────────────────────┬──────────────────────┤
│ Action Distribution  │ Attack Types         │
│                      │                      │
│ ALLOW                │ PortScan             │
│ MONITOR              │ DDoS                 │
│ RATE-LIMIT           │ Bot                  │
│ BLOCK                │ Other                │
│ ESCALATE             │                      │
└──────────────────────┴──────────────────────┘
```

Nên bổ sung:

```text
Anomaly Score Distribution
Action Distribution Over Time
API Latency
Requests/sec
Error Rate
```

Ví dụ:

```text
09:00 → normal
09:10 → PortScan increase
09:20 → DDoS spike
09:21 → BLOCK actions increase
```

---

# 23. Docker

Nên tách training và serving environment.

```text
docker/
├── Dockerfile.train
└── Dockerfile.api
```

## Training image

Có thể sử dụng:

```text
Python 3.12
PyTorch
XGBoost
MLflow
Gymnasium
Stable-Baselines3
```

## Serving image

Có thể sử dụng:

```text
Python 3.14
FastAPI
Uvicorn
XGBoost
PyTorch
```

Mục tiêu:

```text
Development
      ↓
Docker
      ↓
Reproducible Environment
```

---

# 24. Docker Compose

Development stack:

```text
docker-compose.yml
```

Kiến trúc:

```text
┌──────────────┐
│   FastAPI    │
└──────┬───────┘
       │
       ├──────────────┐
       ▼              ▼
 ┌──────────┐   ┌───────────┐
 │ MLflow   │   │Prometheus │
 └──────────┘   └─────┬─────┘
                      │
                      ▼
                 ┌─────────┐
                 │ Grafana │
                 └─────────┘
```

Mục tiêu:

```bash
docker compose up
```

có thể khởi động toàn bộ development stack.

---

# 25. Git

Git dùng để quản lý source code và development workflow.

Branch structure:

```text
main
 │
 ├── develop
 │
 ├── feature/autoencoder
 ├── feature/xgboost
 ├── feature/dqn
 ├── feature/api
 └── feature/monitoring
```

Commit convention:

```text
feat: add xgboost classifier
feat: implement dqn environment
fix: handle nan network features
test: add api integration tests
docs: update architecture
```

Có thể sử dụng Pull Request và branch protection cho main.

---

# 26. GitHub Actions

CI pipeline:

```text
Push / Pull Request
        ↓
GitHub Actions
        ↓
Install dependencies
        ↓
Lint
        ↓
Unit Tests
        ↓
Integration Tests
        ↓
Docker Build
```

CD pipeline:

```text
GitHub Actions
      ↓
Docker Build
      ↓
Container Registry
      ↓
Deployment
```

Với project sinh viên, Docker + GitHub Actions là đủ để thể hiện kiến thức CI/CD. Kubernetes không bắt buộc.

---

# 27. MLOps Lifecycle

Toàn bộ lifecycle:

```text
                 CICIDS2017
                     │
                     ▼
                Train Models
                     │
                     ▼
                   MLflow
                     │
                     ▼
               Model Registry
                     │
                     ▼
                 FastAPI
                     │
                     ▼
                Production
                     │
            ┌────────┴────────┐
            ▼                 ▼
       Prometheus          Feedback
            │                 │
            ▼                 ▼
         Grafana          New Dataset
                              │
                              ▼
                          Retraining
```

Project trở thành một hệ thống:

```text
Cybersecurity
     +
Machine Learning
     +
Reinforcement Learning
     +
MLOps
     +
DevOps
```

---

# 28. Evaluation

Evaluation chia thành 3 tầng.

## 28.1 Detection evaluation

Autoencoder:

```text
Precision
Recall
F1
FPR
FNR
PR-AUC
```

Đặc biệt quan tâm:

```text
False Positive Rate
```

vì IDS thực tế dễ gặp false alarms.

---

## 28.2 Classification evaluation

XGBoost:

```text
Accuracy
Precision
Recall
F1
ROC-AUC
PR-AUC
Confusion Matrix
```

Nên báo cáo:

```text
Macro F1
Weighted F1
Per-class F1
```

---

## 28.3 Autonomous Response evaluation

So sánh:

```text
Rule-based Policy
        VS
DQN Policy
```

Metrics:

```text
Expected Operational Cost
Average Reward
Missed Attack Rate
False Mitigation Rate
Block Rate
Escalation Rate
```

Evaluation phải dùng cùng một row-ordered test set và cùng cost matrix cho cả hai policy. Các metrics của DQN chỉ phản ánh simulator và simulation assumptions; không được diễn giải là hiệu quả chặn source IP trong production.

Ví dụ format báo cáo:

| Metric | Rule-based | DQN |
|---|---:|---:|
| Expected Cost | TBD | TBD |
| Missed Attack | TBD | TBD |
| False Mitigation | TBD | TBD |
| Block Rate | TBD | TBD |
| Average Reward | TBD | TBD |

Không được điền số giả. Các giá trị phải được lấy từ experiment thực tế.

---

# 29. Demo Scenarios

## Scenario 1 — Normal traffic

```text
Traffic
 ↓
Autoencoder
 ↓
Normal
 ↓
XGBoost
 ↓
BENIGN
 ↓
DQN
 ↓
ALLOW
```

## Scenario 2 — PortScan

```text
Traffic
 ↓
High Anomaly Score
 ↓
XGBoost = PortScan
 ↓
DQN
 ↓
RATE-LIMIT
```

## Scenario 3 — DDoS

```text
High packet rate
        ↓
High anomaly score
        ↓
XGBoost = DDoS
        ↓
Row-ordered window context
        ↓
DQN
        ↓
BLOCK
```

## Scenario 4 — Uncertain case

```text
Anomaly = high
XGBoost confidence = low
        ↓
DQN
        ↓
ESCALATE
        ↓
Security Analyst
        ↓
Feedback
```

Scenario 4 thể hiện human-in-the-loop và tránh giả định rằng AI luôn phải tự động xử lý mọi trường hợp.

---

# 30. End-to-End Demo

Một demo hoàn chỉnh có thể chạy như sau:

```text
1. Start Docker Compose
        ↓
2. FastAPI
        ↓
3. Swagger /docs
        ↓
4. POST /api/v1/analyze
        ↓
5. Autoencoder
        ↓
6. XGBoost
        ↓
7. DQN
        ↓
8. Response
        ↓
9. Prometheus collects metrics
        ↓
10. Grafana displays metrics
        ↓
11. MLflow displays model/experiment
```

Ví dụ response:

```json
{
  "anomaly_score": 0.97,
  "attack_type": "DDoS",
  "confidence": 0.96,
  "risk_score": 0.95,
  "recommended_action": "BLOCK"
}
```

---

# 31. Repository Structure

```text
ai-network-defense/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
│
├── configs/
│   ├── training.yaml
│   ├── model.yaml
│   └── rl.yaml
│
├── src/
│   │
│   ├── data/
│   │   ├── ingest.py
│   │   ├── clean.py
│   │   └── features.py
│   │
│   ├── detection/
│   │   ├── autoencoder.py
│   │   ├── classifier.py
│   │   ├── threshold.py
│   │   └── inference.py
│   │
│   ├── rl/
│   │   ├── env.py
│   │   ├── state.py
│   │   ├── reward.py
│   │   └── agent.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── dependencies.py
│   │
│   └── monitoring/
│       └── metrics.py
│
├── training/
│   ├── train_autoencoder.py
│   ├── train_xgboost.py
│   └── train_dqn.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_autoencoder.ipynb
│   ├── 03_xgboost.ipynb
│   └── 04_dqn.ipynb
│
├── models/
│
├── docker/
│   ├── Dockerfile.train
│   └── Dockerfile.api
│
├── prometheus/
│   └── prometheus.yml
│
├── grafana/
│   └── dashboards/
│
├── mlruns/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── cd.yml
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
│
├── docs/
│   ├── architecture.md
│   ├── reward_design.md
│   ├── experiments.md
│   └── api.md
│
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── LICENSE
```

---

# 32. Roadmap 12 tuần

## Weeks 1–2 — Data & baseline

```text
CICIDS2017
 ↓
EDA
 ↓
Cleaning
 ↓
Feature Engineering
 ↓
Row-ordered Split
 ↓
RF/XGBoost Baseline
 ↓
Git Repository
```

Deliverables:

- Dataset pipeline.
- EDA.
- Baseline classifier.
- Git workflow.

---

## Weeks 3–4 — Detection

```text
Autoencoder
 ↓
Anomaly Score
 ↓
Threshold
```

và:

```text
XGBoost
 ↓
Attack Classification
```

MLflow được tích hợp ngay từ giai đoạn này.

Deliverables:

- Autoencoder.
- XGBoost.
- Evaluation.
- MLflow tracking.

---

## Weeks 5–7 — RL

```text
Gymnasium Environment
 ↓
Row-ordered Window State
 ↓
Cost Matrix
 ↓
DQN
 ↓
Rule-based Baseline
```

Deliverables:

- Network defense environment.
- Row-ordered window state representation.
- Reward design.
- Explicit simulation assumptions.
- DQN agent.
- Baseline comparison.

---

## Week 8 — Evaluation

Tập trung:

```text
Expected Operational Cost
False Positive
False Negative
Missed Attack
False Mitigation
Average Reward
```

Deliverables:

- Benchmark.
- Charts.
- Tables.
- Analysis.

---

## Weeks 9–10 — Serving

```text
FastAPI
 ↓
Docker
 ↓
Integration Tests
 ↓
Docker Compose
```

Endpoints:

```text
POST /api/v1/analyze
POST /api/v1/feedback
GET  /api/v1/health
GET  /api/v1/metrics
GET  /docs
```

---

## Week 11 — MLOps / DevOps

```text
GitHub Actions
 ↓
CI
 ↓
Docker Build
 ↓
CD
```

Monitoring:

```text
FastAPI
 ↓
Prometheus
 ↓
Grafana
```

ML:

```text
Training
 ↓
MLflow
```

---

## Week 12 — Finalization

```text
Architecture
 ↓
Documentation
 ↓
Benchmarks
 ↓
Demo
 ↓
README
 ↓
CV
```

Deliverables:

- Architecture diagram.
- Experiment report.
- API documentation.
- Grafana dashboard.
- MLflow screenshots.
- CI/CD pipeline.
- End-to-end demo.
- CV description.

---

# 33. Stretch Goals

Không bắt buộc cho MVP.

Có thể bổ sung sau khi core system ổn định:

```text
PPO
SHAP
DVC
Human-in-the-loop retraining
Automatic drift detection
Automatic retraining
Cloud deployment
```

Không nên thêm các thành phần này trước khi:

```text
Autoencoder
+
XGBoost
+
DQN
+
FastAPI
+
MLflow
+
Prometheus
+
Grafana
+
Docker
+
GitHub Actions
```

đã hoạt động ổn định.

---

# 34. Final Architecture

Phiên bản cuối cùng:

```text
┌──────────────────────────────────────────────────────────────┐
│                 AI NETWORK DEFENSE SYSTEM                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CICIDS2017                                                 │
│       │                                                      │
│       ▼                                                      │
│  Data Processing                                             │
│       │                                                      │
│       ├───────────────┐                                      │
│       ▼               ▼                                      │
│  Autoencoder       XGBoost                                  │
│       │               │                                      │
│       │               │                                      │
│  Anomaly Score    Attack Probability                         │
│       │               │                                      │
│       └───────┬───────┘                                      │
│               ▼                                              │
│        Row-ordered Window State                              │
│               │                                              │
│               ▼                                              │
│             DQN                                              │
│               │                                              │
│       ┌───────┼──────────────┐                               │
│       ▼       ▼       ▼      ▼       ▼                       │
│     ALLOW  MONITOR RATE-LIMIT BLOCK ESCALATE                │
│               │                                              │
│               ▼                                              │
│         Human Feedback                                        │
│               │                                              │
│               ▼                                              │
│           Retraining                                          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                       SERVING                                │
│                                                              │
│                       FastAPI                                │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                       MLOps                                  │
│                                                              │
│                       MLflow                                 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                     MONITORING                               │
│                                                              │
│                Prometheus → Grafana                          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                     DEVOPS                                   │
│                                                              │
│           Git → GitHub Actions → Docker                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

# 35. CV Positioning

Không nên mô tả project đơn giản là:

> Built an intrusion detection system using machine learning.

Nên định vị:

> **AI-Driven Network Intrusion Detection & Autonomous Response** — Built a flow-level offline network-defense simulator using CICIDS2017, combining an Autoencoder for anomaly detection, XGBoost for attack classification, and a cost-sensitive DQN policy for row-ordered response decisions. Exposed inference through FastAPI and implemented experiment/model tracking with MLflow, containerization with Docker, CI/CD using GitHub Actions, and runtime monitoring with Prometheus/Grafana.

Cách mô tả ngắn hơn:

> Developed a flow-level AI network-defense simulator combining anomaly detection, attack classification, and cost-sensitive reinforcement learning under explicit offline simulation assumptions, with FastAPI serving, MLflow experiment tracking, Docker containerization, GitHub Actions CI/CD, and Prometheus/Grafana monitoring.

---

# 36. Cách mô tả project trong interview

Câu trả lời ngắn:

> "The project is a flow-level offline network-defense simulator based on CICIDS2017. I use an Autoencoder to detect anomalous traffic and XGBoost to classify attacks. Their outputs are combined with row-ordered window context and passed to a DQN agent. Instead of simply predicting whether traffic is malicious, the agent learns a cost-sensitive policy to choose between allow, monitor, rate-limit, block, and escalate under explicit simulation assumptions. The system is served through FastAPI and containerized with Docker, while MLflow handles experiment/model tracking and Prometheus/Grafana handle runtime monitoring. GitHub Actions provides CI/CD."

---

# 37. Core Research Question

Project có thể được xoay quanh một câu hỏi chính:

> **Can a cost-sensitive DQN policy reduce the operational cost of a row-ordered offline flow-defense simulator compared with a conventional rule-based response policy?**

Các câu hỏi phụ:

1. Autoencoder có phát hiện được traffic bất thường tốt không?
2. XGBoost phân loại attack tốt đến mức nào?
3. Row-ordered window context có cải thiện quyết định của DQN không?
4. DQN có giảm false mitigation không?
5. DQN có giảm expected operational cost so với rule-based policy không?
6. Hệ thống có đáp ứng được latency yêu cầu khi serving qua FastAPI không?

---

# 38. Project Identity

Project cuối cùng nên được nhìn nhận là:

```text
                    AI
                     │
        ┌────────────┴────────────┐
        │                         │
  Autoencoder                 XGBoost
        │                         │
  Anomaly Detection       Attack Classification
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
                    DQN
                     │
             Autonomous Response
                     │
                     ▼
                  FastAPI
                     │
          ┌──────────┴──────────┐
          │                     │
      MLflow              Monitoring
                            │
                     Prometheus/Grafana
                            │
                         Docker
                            │
                     GitHub Actions
                            │
                           Git
```

**Core identity:**

> **AI-driven, cost-sensitive, flow-level offline network-defense simulator with reproducible MLOps/DevOps infrastructure.**

---

# 39. MUST-HAVE Checklist

- [ ] CICIDS2017
- [ ] Data preprocessing pipeline
- [ ] Row-ordered train/validation/test split with documented limitation
- [ ] Autoencoder
- [ ] Anomaly threshold
- [ ] XGBoost classifier
- [ ] Row-ordered window state representation
- [ ] Flow-level DQN environment
- [ ] Explicit simulation assumptions
- [ ] Cost-sensitive reward
- [ ] Rule-based baseline
- [ ] DQN evaluation
- [ ] FastAPI
- [ ] `/analyze`
- [ ] `/feedback`
- [ ] `/health`
- [ ] `/metrics`
- [ ] Swagger `/docs`
- [ ] MLflow
- [ ] Prometheus
- [ ] Grafana
- [ ] Docker
- [ ] Docker Compose
- [ ] Git
- [ ] GitHub Actions CI
- [ ] GitHub Actions CD
- [ ] Unit tests
- [ ] Integration tests
- [ ] End-to-end demo
- [ ] Documentation
- [ ] Final benchmark

---

# 40. Final project statement

> **AI-Driven Network Intrusion Detection & Autonomous Response** is a flow-level, row-ordered offline network-defense platform that combines Autoencoder-based anomaly detection, XGBoost attack classification, and a cost-sensitive DQN agent for sequential response decisions under explicit simulation assumptions. The system exposes AI inference through FastAPI, tracks experiments and models using MLflow, monitors runtime behavior with Prometheus and Grafana, and provides reproducible deployment and CI/CD through Docker, Git, and GitHub Actions.
