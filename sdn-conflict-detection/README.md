# OpenFlow Rule Conflict Detection in SDN

This repository implements an SDN testbed for detecting and classifying OpenFlow rule conflicts using machine learning, based on the IEEE Access paper **“Detection and Classification of Conflict Flows in SDN Using Machine Learning Algorithms” (Khairi et al., 2021, IEEE Access, IEEE Xplore ID 9433563)**. The project emulates an OpenFlow‑based SDN network, generates normal and conflicting flows, and evaluates multiple ML models for both conflict detection and conflict‑type classification across datasets from 1,000 to 100,000 flows.

---

## Project Overview

The goal of this project is to automatically detect and classify OpenFlow rule conflicts in Software‑Defined Networking (SDN) environments using machine learning. The system generates normal and seven types of conflicting rules in a Mininet topology controlled by Ryu, exports them as labeled datasets, and trains ML models to distinguish between normal and conflicting flows and to classify conflict types.

**Key features:**

- Emulated SDN network using Mininet and Ryu
- Automatic generation of normal and conflicting flows
- Labeled datasets from 1K to 100K flows
- Two‑phase ML pipeline:
  - Phase 1: Binary conflict detection (normal vs conflict)
  - Phase 2: Conflict‑type classification (7 classes)
- HTML report generation for visual analysis

---

## System Architecture

The system follows a **4‑layer architecture**:

1. **Network Emulation Layer**
   - Uses **Mininet** to create a simple tree topology:
     - 3 OpenFlow switches (s1, s2, s3)
     - 4 hosts (h1–h4)
   - s1 is the root switch connected to s2 and s3; h1–h2 connect to s2, h3–h4 connect to s3.
   - All switches run OpenFlow 1.3 and connect to a remote controller on port 6633.

2. **Control Layer**
   - **Ryu** SDN controller (OpenFlow 1.3).
   - Custom Ryu apps:
     - Flow generator for normal flows.
     - Flow collector for conflict generation and statistics.

3. **Data Generation Layer**
   - Python scripts generate:
     - Normal flows (about 70% of each dataset).
     - Seven types of conflicting flows:
       - Redundancy
       - Shadowing
       - Overlapping
       - Correlation A
       - Correlation B
       - Generalization
       - Imbrication
   - Export labeled flows to CSV for ML processing.

4. **Machine Learning Layer**
   - Scikit‑learn‑based ML pipeline.
   - Phase 1: Binary classification (normal vs conflict).
   - Phase 2: Multi‑class classification (7 conflict types).
   - Algorithms:
     - Decision Tree (DT)
     - Support Vector Machine (SVM)
     - Extremely Fast Decision Tree (EFDT)
     - Hybrid DT‑SVM
   - Metrics: accuracy, precision, recall, F1‑score, execution time.

---
## Repository Structure

```text
sdn-conflict-detection/
│
├── README.md
├── requirements.txt
│
├── src/
│   ├── simple_tree_topo.py       # Mininet topology
│   ├── flow_generator_v3.py      # Ryu flow generator (normal flows)
│   ├── simple_flow_collector.py  # Conflict flow generator + CLI
│   ├── ml_detector.py            # ML pipeline (Phase 1 & 2)
│   └── html_report.py            # HTML report generator
│
├── results/
│   ├── ml_results_ds1000.json
│   ├── ml_results_ds10000.json
│   ├── ml_results_ds20000.json
│   ├── ml_results_ds50000.json
│   └── ml_results_ds100000.json
│
├── reports/
│   └── Security_of_SDN_Project_Report.pdf
│
└── docs/
    └── architecture.png          # optional: system diagram
```

## What Not to Commit

Do not commit third‑party tools and large generated artefacts:

   - Third‑party directories (reference in README instead):
     - `oflops/`
     - `oftest/`
     - `pox/`
     - `openflow/`
     - `mininet/`

   - Generated data:
     - Large CSVs
     - `Output Files/` or similar export directories

Add a `.gitignore` including, for example:

```text
# Data / exports
*.csv
Output Files/

# Third‑party tools (install separately)
oflops/
oftest/
pox/
openflow/
mininet/
```

## What Not to Commit

Do **not** commit third‑party tools and large generated artefacts:

- Third‑party directories (install separately):
  - `oflops/`
  - `oftest/`
  - `pox/`
  - `openflow/`
  - `mininet/`
- Generated data:
  - Large CSVs
  - `Output Files/` or similar export directories

Example `.gitignore`:

```gitignore
# Data / exports
*.csv
Output Files/

# Third‑party tools (install separately)
oflops/
oftest/
pox/
openflow/
mininet/
```

## Installation

### Prerequisites

- Ubuntu 22.04 LTS  
- Mininet 2.3.1b4  
- Ryu 4.34  
- Open vSwitch (OVS) 2.17.9  
- Python 3.10.x and `pip`

### Python Dependencies

Install Python packages via:

```bash
pip install -r requirements.txt
```

(Requirements should include at least: `ryu`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`.)


## Execution Workflow
### 1. Start the Ryu Controller with Flow Generator

In terminal 1:

```bash
source ryu-env/bin/activate

ryu-manager --ofp-tcp-listen-port 6633 --observe-links src/flow_generator_v3.py --verbose
```

### 2. Launch the Mininet Topology

In terminal 2:

```bash
sudo mn --custom src/simple_tree_topo.py --topo simpletree \
    --controller remote,ip=127.0.0.1,port=6633 \
    --switch ovsk,protocols=OpenFlow13 --mac
```

Optional connectivity check:

```bash
mininet> pingall
```
### 3. Start the Flow Collector

In terminal 3:

```bash
source ryu-env/bin/activate

ryu-manager --ofp-tcp-listen-port 6633 src/simple_flow_collector.py --verbose
```
### 4. Generate Flows and Export Dataset

From the flow collector CLI (example commands):

```text
flowcollector stats
flowcollector generate dataset
flowcollector export
This generates normal and conflicting flows and exports a labeled CSV such as:
```

```text
flows135720251115125845.csv
flows1344220251115131706.csv
...
```

### 5. Run the ML Pipeline (Phase 1 & 2)

Use ml_detector.py on a CSV:

```bash
python3 src/ml_detector.py path/to/flowsXXXXX.csv
```
This will:

- Load and preprocess the data
- Split into training (70%) and test (30%)
- Run DT, SVM, EFDT, Hybrid DT‑SVM for Phase 1
- Run multi‑class classification for Phase 2
- Save a JSON summary such as:

```text
results/ml_results_ds1000.json
results/ml_results_ds10000.json
...
```

### 6. Generate HTML Reports

```bash
python3 src/html_report.py results/ml_results_ds1000.json
```
This produces:

```text
mlresultsds1000report.html
mlresultsds10000report.html
...
```
Open in a browser, for example:

```bash
firefox mlresultsds1000report.html
```

## Results Summary (Headline)

### Phase 1: Binary Conflict Detection

Across all dataset sizes (1K–100K), Decision Tree (DT) and Extremely Fast Decision Tree (EFDT) achieve **>99% accuracy** in distinguishing normal flows from conflict flows.

Example headline numbers:

| Dataset size | Best algorithm | Accuracy |
|--------------|----------------|----------|
| 1K           | DT             | 99.02%   |
| 10K          | DT             | 99.63%   |
| 20K          | EFDT           | 99.65%   |
| 50K          | EFDT           | 99.68%   |
| 100K         | EFDT           | 99.74%   |

EFDT combines very high accuracy with very low execution time, making it suitable for real‑time SDN deployments.

### Phase 2: Conflict‑Type Classification

Phase 2 performs multi‑class classification over seven conflict types:

- Overall accuracy ≈ **56–60%** on larger datasets  
- **Generalization** and **Shadowing** are classified with very high precision and recall (close to 100%)  
- **Correlation A**, **Correlation B**, and **Overlapping** are harder to distinguish due to similar feature patterns  

## How to Extend
- Modify `simple_tree_topo.py` to change the network topology.
- Tune generation logic in `flow_generator_v3.py` and `simple_flow_collector.py`.
- Extend `ml_detector.py` with new algorithms or feature engineering.
- Customize `html_report.py` to add more plots and summaries.

