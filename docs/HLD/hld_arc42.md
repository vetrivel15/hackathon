# **1. Introduction and Goals**

The **Robot Control System (RCS)** is a distributed, modular, extensible software platform designed to provide **real-time robot control**, **telemetry visualization**, and **multi-device operator access** for one or more humanoid robots.

The system is designed **local-first** for the initial deployment, but fully architected for **future migration to cloud-native, scalable, multi-robot environments** on Google Cloud Platform (GCP).

This section introduces the system, describes its purpose, highlights its major architectural goals, and defines the conditions under which future work should evolve.

---

## **1.1 Problem Statement**

Humanoid robots require a reliable and low-latency software platform that:

- Enables safe **remote teleoperation**
- Provides **real-time telemetry feedback**  
- Is **extensible to multi-robot fleets**  
- Can run on a **single local machine** for demos  
- Can migrate to **cloud infrastructure** for scalability  

The current local-only implementation must evolve into a **scalable, secure, multi-tenant architecture** suitable for cloud-hosted deployments.

---

## **1.2 Goals**

### **Primary Goals**
1. **Enable remote real-time control** of a humanoid robot through a browser-based UI.
2. **Stream and visualize telemetry** (pose, battery, joint data, operational status) at low latency.
3. **Provide multi-device access** (laptop, tablet, mobile).
4. **Support a “local-first” deployment model** with zero cloud dependency.
5. **Enable future cloud deployment**:  
   - Cloud Run  
   - WebSockets / MQTT over WebSockets  
   - Multi-robot scaling  
   - Authentication and access control  
   - Managed logging and observability  
   - Global operator access

### **Secondary Goals**
6. Provide a foundational architecture for future:
   - Robot autonomy
   - Path planning
   - Fleet orchestration
   - Logging dashboards (Grafana / Cloud Monitoring)
7. Maintain system simplicity for hackathon deployment while enabling enterprise evolution.
8. Use **only open-source technologies**.

---

## **1.3 Non-Goals**

The following are explicitly *not* part of the initial system scope:

- Autonomous behavior or decision-making
- Computer vision or ML inference pipeline
- Complex robotics simulations or SLAM
- Real-time distributed cloud control (<20 ms latency)
- Strong security compliance (will be added in cloud version)
- Production-grade HA/DR (high availability/disaster recovery)
- Hardware-level motor control implementation  
- Real-time OS constraints (RTOS not required)

Non-goals ensure the architecture remains focused on **remote control**, **telemetry**, and **operator experience**.

---

## **1.4 Stakeholders**

| Stakeholder | Role | Needs |
|------------|------|-------|
| **Developers** | Build, test, extend system | Clean architecture, modularity, simplicity |
| **Robot Operators / Users** | Control robot | Intuitive UI, reliable commands, real-time telemetry |
| **Robotics Engineers** | Integrate robot hardware | Predictable comms, structured data flow |
| **Future Cloud Ops Team** | Deploy and maintain | Cloud-ready architecture, logging, monitoring |
| **Security Reviewers** | Future stage | Auth model, secure comms, audit trails |

---

## **1.5 Quality Goals**

The four highest-priority quality attributes are:

### **1. Reliability**
- Robot must remain in safe states  
- No uncontrolled motion  
- Connectivity drops must trigger protective logic  

### **2. Performance**
- Telemetry latency < 200 ms locally  
- Command execution < 100 ms locally  
- Cloud latency target < 400 ms roundtrip  

### **3. Developer Experience**
- Simple to run locally  
- Clear module boundaries  
- Easy to extend with new robot types  

### **4. Scalability (Future Cloud)**
- Support multiple robots  
- Support multiple operators  
- Autoscale backend  
- Support multi-region deployments  

These quality goals directly influence design decisions (e.g., MQTT, WebSockets, local-first architecture, stateless backend).

---

## **1.6 Key Architectural Themes**

### **Local-first, Cloud-ready**
Architecture supports:
- Single-machine execution  
- Seamless deployment to GCP Cloud Run  

### **Message-driven**
MQTT chosen as:
- Low-latency  
- Lightweight  
- Perfect for robot telemetry  

### **Distributed and Decoupled**
Robot, backend, and UI communicate via:
- MQTT topics  
- WebSocket streams  
- REST (future expansion)

### **Modular, Extensible**
Future features include:
- Multi-robot routing  
- Role-based access control  
- Cloud-based robot registry  

---

## **1.7 Primary System Use Cases**

### **UC1: Remote Teleoperation**
Operator controls robot via UI → backend → MQTT → robot.

### **UC2: Telemetry Visualization**
Robot publishes data → broker → backend → WebSocket → UI.

### **UC3: Safe Startup**
System initializes backend, connects to broker, validates robot presence.

### **UC4: Multi-device Access**
Several devices concurrently view robot telemetry.

### **UC5: Cloud Migration (Future)**
Enable system components as microservices on Cloud Run.

---

## **1.8 Glossary**

| Term | Meaning |
|------|---------|
| **MQTT** | Pub/Sub message protocol for low-latency telemetry |
| **Telemetry** | Sensor and status information from robot |
| **WebSocket** | Real-time UI communication channel |
| **Broker** | MQTT message router |
| **Cloud Run** | Serverless container hosting on GCP |
| **Local-first** | Designed to run standalone without cloud |
| **Multi-robot support** | Ability to scale to many robots and UIs |

---

# **2. Architecture Constraints**

---

## **2.1 Technical Constraints**

### **2.1.1 Local-First Execution Requirement**

The system **must run entirely on a single local machine** during the early stages.
This drives key architectural decisions:

* Backend must run as a standalone Python service.
* MQTT broker must be local (Mosquitto or embedded).
* UI served locally via static server / development server.
* No cloud services required for minimal viable operation.
* Zero external dependencies to avoid network issues.

This constraint strongly influenced:

* The choice of **MQTT** (lightweight, embeddable, local-friendly).
* Minimal deployment complexity.
* Co-located components (backend, broker, UI).

---

### **2.1.2 Future Cloud Deployment Requirement**

Even though the system runs locally now, the architecture must support deployment to **GCP Cloud Run** and cloud-native MQTT brokers.

This requires:

* Stateless backend components
* Clear separation between UI, backend, robot
* Use of protocols suitable for cloud migration (MQTT, WebSockets, REST)
* Externalizing configuration & environment variables
* Cloud-ready architecture boundaries

This influences:

* Avoiding local-only protocols
* Designing with containerization in mind
* Layered architecture with well-defined interfaces

---

### **2.1.3 Use Only Open-Source Tools**

All components must use **free and open-source** technologies:

* Python (backend)
* JavaScript + HTML UI
* MQTT (Mosquitto broker)
* Optional: React/Vite/Tailwind (future UI enhancements)
* SQLite or JSON for local data persistence
* Docker (optional)
* No proprietary SDKs or paid libraries

This constraint excludes:

* AWS IoT Core
* Azure IoT Hub
* Proprietary robotics middleware
* Commercial MQTT brokers

It reinforces decision-making around:

* Using Mosquitto broker
* WebSocket communication
* Docker-based deployment options

---

### **2.1.4 Web Browser Interface Requirement**

The operator interacts exclusively through a **web browser** (Chrome, Safari, Firefox).
This requires:

* Cross-device compatibility (laptop, iPad, mobile)
* WebSocket support
* Responsive UI design
* Lightweight client-side logic

The UI must function without:

* Native apps
* Plugins
* Special runtime environments

---

### **2.1.5 Protocol Constraint: MQTT Instead of REST**

MQTT is mandatory for all robot-bound control & telemetry.

**Justification:**

| Requirement           | MQTT          | REST         |
| --------------------- | ------------- | ------------ |
| Low latency           | **Excellent** | Poor         |
| Real-time telemetry   | **Best fit**  | Not suitable |
| Pub/Sub               | **Built-in**  | No           |
| Bandwidth usage       | Low           | High         |
| Cloud/LAN flexibility | High          | Medium       |
| Multi-robot scaling   | High          | Medium       |
| Mobile connectivity   | High          | Medium       |

Thus MQTT is **non-negotiable** for:

* Robot telemetry ingestion
* Real-time robot control output
* Future multi-robot expansion

REST/WebSocket remains available for:

* Operator UI
* Management API
* Metadata

---

## **2.2 Organizational Constraints**

### **2.2.1 Small Team, Limited Development Time**

The system is being developed under **Rapid prototyping**.

This emphasizes:

* Simple architecture boundaries
* High reuse of open-source frameworks
* Avoiding heavy infrastructure setup

---

### **2.2.2 No Dedicated DevOps Team**

Deployment and infrastructure management must be:

* Simple
* Automated
* Minimal steps required
* Not dependent on specialized setups

Thus:

* GCP Cloud Run is chosen for future deployment (serverless, zero-ops)
* Local system uses Python scripts + Mosquitto → simplifies orchestration

---

## **2.3 Environmental Constraints**

### **2.3.1 Wi-Fi LAN Reliability**

Latency requirements (<200ms) mean the system depends on:

* Strong LAN connectivity
* Consistent Wi-Fi signal
* Minimal packet loss

Robot control safety must account for:

* Network jitter
* Operation in congested Wi-Fi environments

---

### **2.3.2 Hardware Device Limitations**

Robots may be constrained by:

* Battery life
* Limited compute resources
* Embedded Linux boards (Raspberry Pi, Jetson Nano)

The architecture must support:

* Lightweight message handling
* Minimal CPU overhead
* Efficient JSON payloads

---

## **2.4 Legal & Regulatory Constraints**

Although this is a prototype:

* No personally identifiable data (PII) may be stored
* Communication security must be considered for future cloud deployment
* Safety of robotic control is a critical concern
* For cloud deployment: TLS mandatory

For local deployment, this is relaxed due to:

* LAN isolation
* No external exposure

---

## **2.5 Future Scalability Constraints**

### **2.5.1 Multi-Robot Support**

The architecture must grow to support:

* 1 → many robots
* 1 → many operators
* Multi-session concurrency
* Robot identification and routing

This affects:

* MQTT topic naming conventions
* Backend routing logic
* UI selection of robot
* Cloud auto-scaling patterns

---

### **2.5.2 Cloud Observability Requirements**

The system must support future:

* Logging
* Metrics
* Distributed tracing
* Cloud Monitoring integration

Thus modules must be instrumentable.

---

## **2.6 Technology Stack Constraints**

* **Python backend only**
* **MQTT broker: Mosquitto**
* **Frontend: HTML/JS (React optional)**
* **GCP Cloud Run as future target**
* **Docker images must be buildable**
* **WebSockets for real-time UI updates**

These choices steer:

* Deployment strategies
* Component interfaces
* Bandwidth policies
* Failure modes

---

## **2.7 Summary of All Constraints**

| Category        | Constraints                                      |
| --------------- | ------------------------------------------------ |
| Technical       | Local-first, cloud-ready, MQTT, browser UI       |
| Organizational  | Small team, fast iteration, simple deployment    |
| Environmental   | LAN-based, Wi-Fi, embedded robot hardware        |
| Legal/Security  | No PII, TLS for cloud, safe teleoperation        |
| Future-proofing | Multi-robot, scalable, cloud observability       |
| Tooling         | 100% open-source, Python backend, GCP for future |

---

# **3. System Context**

The RCS is a distributed system designed to:

* Provide remote robot control
* Deliver real-time telemetry visualization
* Serve multiple operator devices
* Integrate with physical robot hardware
* Prepare for expansion to multi-robot, cloud-hosted orchestration

To support this, the system has two key interaction contexts:

1. **Business/Domain Context** — who uses the system, and why
2. **Technical Context** — what systems it interfaces with, and how

---

## **3.1 Business/Domain Context**

The **RCS** acts as the **control and monitoring gateway** between human operators and humanoid robots.

### **Primary Purpose**

* Provide safe, real-time remote control
* Provide live robot telemetry
* Enable multi-device access
* Support multiple robots (future)

---

### **3.1.1 Actors and Their Roles**

| Actor                                   | Type     | Role / Responsibility                              |
| --------------------------------------- | -------- | -------------------------------------------------- |
| **Robot Operator (User)**               | Human    | Controls robot, reads telemetry, triggers commands |
| **Developer**                           | Human    | Develops, extends, debugs system                   |
| **Robot/Robot Firmware**                | Machine  | Executes commands, publishes telemetry             |
| **System Administrator**                | Human    | Starts/stops system, configures environment        |
| **Future Cloud Infrastructure**         | Platform | Hosts system in large-scale setups                 |
| **Observers (reviewers)** | Human    | Watch system during demo                           |

---

### **3.1.2 Business Goals in Context**

The RCS must satisfy the following high-level goals:

1. Enable **remote robotic teleoperation** safely.
2. Provide **real-time telemetry feedback** for situational awareness.
3. Support **operator devices on the local network**.
4. Maintain **simple installation** and **open-source tooling**.
5. Enable future **cloud-scale remote control**.
6. Support **multi-robot orchestration** later.

---

### **3.1.3 Business Processes Supported**

The system primarily supports:

* **BP1: Robot Motion Control**
  Operators send movement, mode, and safety commands.

* **BP2: Telemetry Monitoring**
  Real-time data visualization (pose, joints, battery).

* **BP3: Health and Status Monitoring**
  Robot reports state; the system reflects faults.

* **BP4: Multi-device Viewing**
  Multiple browsers can observe telemetry simultaneously.

* **BP5: Cloud Management (Future)**
  Cloud operators can manage multiple robots across regions.

---

## **3.2 Technical Context**

The technical context describes the system’s boundaries and connections.
It identifies:

* Input/Output flows
* Protocols
* External systems
* Technology constraints

This section establishes **how** RCS interacts with the world.

---

### **3.2.1 System Boundary Diagram (Logical)**

```
+-------------------------------------------------------------+
|                      Robot  Control System (RCS)            |
|                                                             |
|-------------------------------------------------------------|
|                                                             |
|   Frontend UI (Browser)     Backend API      MQTT Messaging |
|       HTML/JS/WS        <-> Python FastAPI <->   Mosquitto  |
|                                                             |
+-------------------------------------------------------------+
                ^                           |
                |                           v
      Multi-device Operators         Physical Robot Hardware
          (Laptop/iPad)               (MQTT client, sensors)
```

You will receive polished architecture diagrams in Section 5 and Section 7.

---

### **3.2.2 Primary External Interfaces**

There are **three** major external systems:

---

## **A) Physical Humanoid Robot (external system)**

### Interface Type

* MQTT (primary)
* Optional REST in future for metadata

### Robot Responsibilities

* Publish telemetry
* Receive commands
* Execute movement
* Maintain internal watchdog

### RCS Responsibilities

* Forward commands
* Validate operator actions
* Display telemetry
* Ensure safe shutdown

---

## **B) Operator Devices (Browsers)**

### Devices Supported

* Mac/Windows laptops
* iPad/tablets
* Mobile phones (responsive UI)

### Interface Type

* HTTPS/HTTP (UI delivery)
* WebSocket (real-time telemetry)

### Constraints

* No app installation
* Must work behind LAN
* UI must be responsive

---

## **C) MQTT Infrastructure (Broker)**

### Current Mode (Local)

* Mosquitto broker running locally
* Broker endpoint accessible over LAN
* No TLS required due to network isolation

### Future Mode (Cloud)

* Mosquitto container in Cloud Run
* MQTT over WebSockets
* TLS enforced
* IAM/Identity Platform for operator authentication

---

### **3.2.3 Data Flow Summary**

| From                    | To             | Method           | Data |
| ----------------------- | -------------- | ---------------- | ---- |
| Robot → Broker          | MQTT           | Telemetry        |      |
| Backend → Broker        | MQTT           | Control commands |      |
| Backend → UI            | WebSocket      | Telemetry stream |      |
| UI → Backend            | HTTP/WebSocket | Commands         |      |
| Future: UI → Cloud Auth | OAuth2         | Credentials      |      |

---

## **3.3 Context Scenarios**

The context is best explained through scenarios:

---

### **Scenario 1 — Teleoperation**

1. Operator opens UI
2. UI opens WebSocket to backend
3. Operator sends command
4. Backend validates
5. MQTT publishes command to robot
6. Robot executes

---

### **Scenario 2 — Telemetry Visualization**

1. Robot publishes telemetry
2. MQTT broker receives
3. Backend subscribed & pushes updates to UI
4. UI updates charts, pose, diagnostics

---

### **Scenario 3 — Multi-device Access**

Multiple devices subscribe to backend WebSocket stream simultaneously.

---

### **Scenario 4 — Robot Offline State**

Backend & UI detect missing telemetry and switch to “disconnected” state.

---

## **3.4 In-Scope & Out-of-Scope Summary**

### **In Scope**

* Robot control
* Telemetry ingestion
* Real-time WebSockets
* UI on browser
* MQTT messaging
* Local deployment
* Cloud-native architectural design

### **Out of Scope**

* Full robotic autonomy
* Perception pipelines
* Security hardening (current local)
* Multi-factor authentication
* Persistent cloud storage
* Video streaming

---

## **3.5 Context Summary**

| Boundary     | Description                                  |
| ------------ | -------------------------------------------- |
| Internal     | UI, backend, MQTT adapter, routing logic     |
| External     | Robot, operator devices, network environment |
| Inputs       | Commands, configurations                     |
| Outputs      | Telemetry, status, logs                      |
| Dependencies | MQTT protocol, network stability             |

---

# **4. Solution Strategy**

The **Robot Control System (RCS)** follows a **local-first, cloud-ready, message-driven, modular architecture** that supports real-time remote robot control with future scalability to multi-robot cloud operations.

Solution strategy addresses:

* **How** the requirements will be met
* **Why** certain approaches were chosen
* **What** constraints shaped the architecture

---

## **4.1 Architectural Principles**

The architecture is guided by the following foundational principles:

---

### **4.1.1 Local-First Deployment (Phase 1)**

The system is initially designed to run fully on a **local machine**, with:

* Local MQTT broker
* Local backend
* Local UI running in browser
* Multi-device LAN access
* No internet dependencies

This guarantees:

* Predictability in demos
* Zero cloud setup time
* No billing risks
* Ultra-low latency communication
* Simplified debugging

This principle strongly influenced:

* Choice of Mosquitto broker
* Use of Python backend with minimal dependencies
* Static web UI accessible via LAN
* Simple, portable architecture

---

### **4.1.2 Cloud-Ready (Phase 2+)**

The software must be **effortlessly deployable to GCP** when needed.

This requires:

* Stateless backend design
* Containerization compatibility
* Environment-based configuration
* Web-ready protocols (MQTT over WebSockets)
* Cloud-friendly messaging patterns

The architecture supports future deployment on:

* **GCP Cloud Run** (backend)
* **GCP Cloud Run or VM running Mosquitto** (broker)
* **Firebase Hosting** (UI)

---

### **4.1.3 Message-Driven Architecture**

The system is built around:

**MQTT as the primary messaging backbone**

Why message-driven?

| Need                    | Reason                                         |
| ----------------------- | ---------------------------------------------- |
| Real-time updates       | MQTT is lightweight and low-latency            |
| Multi-robot scalability | Pub/Sub avoids point-to-point bottlenecks      |
| Cloud readiness         | MQTT over WebSockets enables global deployment |
| Multi-device UI         | Backend pushes updates to all UIs              |
| Network resilience      | MQTT supports QoS levels and retained messages |

MQTT substitutes more complex middleware like ROS2 in early stages but remains compatible if ROS2 is added later.

---

### **4.1.4 Modular, Layered Architecture**

The system enforces clean separations:

| Layer               | Responsibility                                |
| ------------------- | --------------------------------------------- |
| **UI Layer**        | Visualization, operator input                 |
| **Backend Layer**   | Business logic, validation, telemetry routing |
| **Messaging Layer** | MQTT broker, pub/sub                          |
| **Robot Layer**     | Actuators, sensors, firmware logic            |

This ensures:

* Replaceability of components
* Independent development
* Improved testability

---

### **4.1.5 Simplicity First**

The architecture follows:

* Minimal complexity
* Simple deployment
* Easy debugging
* Portable Python backend
* Lightweight frontend

This ensures the team can focus on **robot control**, not infrastructure.

---

## **4.2 Technology Decisions & Justifications**

This section explains the **key design choices** and the **architectural reasoning** behind them.

---

### **4.2.1 Python for Backend**

Chosen because:

* Very fast development speed
* Excellent abstraction for MQTT and WebSockets
* Portable across local and cloud environments
* Large open-source ecosystem
* Easy integration with robotics (ROS, pyserial, pyMQTT)

Alternatives considered:

* Go (faster but slower dev)
* Node.js (event-based but weaker in robotics ecosystem)

Final decision: **Python balances speed, simplicity, and maturity**.

---

### **4.2.2 HTML/JavaScript UI (Browser-first)**

Reasons:

* Zero installation
* Works on laptop, iPad, mobile
* Easy to serve locally
* Easy to deploy to Firebase/CloudFront later

Future enhancement:

* React/Vite/Tailwind for SPA
* Reuse existing components for robot dashboards

---

### **4.2.3 MQTT (Instead of REST/Webhooks)**

**Mandatory constraint** and **optimal choice**.

Justification:

#### **A) Telemetry Requires Low Latency**

Robots publish frequent updates (5–50Hz).
REST is too slow and heavy.

MQTT advantages:

* Persistent connections
* No polling overhead
* Extremely lightweight headers
* Optimized for IoT

---

#### **B) Commands Must Be Reliable**

MQTT provides 3 QoS levels:

| QoS | Reliability   | Use-case                 |
| --- | ------------- | ------------------------ |
| 0   | Best effort   | high-frequency telemetry |
| 1   | At least once | motor commands           |
| 2   | Exactly once  | OTA updates              |

REST has no equivalent.

---

#### **C) Multi-Robot Scalability**

MQTT is designed for many-to-many communication.

REST would scale poorly.

---

#### **D) Cloud Broker Friendly**

MQTT + WebSockets = native support in cloud environments.

REST APIs cannot push telemetry to multiple clients without heavy architecture overhead (WebSockets or SSE required).

---

### **4.2.4 Local Mosquitto Broker**

Why?

* Extremely small footprint
* Stable and battle tested
* Ideal for LAN demos
* Works with Python, JS, C++, embedded controllers

Future cloud upgrade path:

* Mosquitto on Cloud Run
* HiveMQ (OSS version)
* GCP Pub/Sub bridge

---

### **4.2.5 WebSockets for UI Telemetry**

Why not MQTT client in browser?

* Browser MQTT libraries exist but are less stable
* Simpler to control flow through backend
* Backend can transform/aggregate telemetry
* WebSockets give better control over security, throttling, filtering

---

## **4.3 Solution Strategy Summary**

### **Core Themes**

| Architectural Strategy | Description                        |
| ---------------------- | ---------------------------------- |
| **Local-first**        | Fully operable on one machine      |
| **Cloud-ready**        | Stateless backend, containerizable |
| **Message-driven**     | MQTT at the core                   |
| **Modular**            | Clear layers and responsibilities  |
| **Open-source only**   | Aligns with constraints            |
| **Low latency**        | Critical for robot control         |
| **Multi-device UI**    | Laptop + iPad support              |
| **Future multi-robot** | Scales using MQTT topics           |

---

## **4.4 Planned Evolution Roadmap**

### **Phase 1 (Current)** — Single Robot, Local Machine

* Local Mosquitto
* Python backend
* Browser UI
* No authentication

### **Phase 2** — Structured Backend & Cloud UI

* Backend deployed on Cloud Run
* UI deployed on Firebase
* MQTT broker still local

### **Phase 3** — Full Cloud System

* MQTT broker in Cloud Run
* TLS + OAuth2 + JWT security
* Multi-robot routing
* Persistent telemetry storage (BigQuery/InfluxDB)

### **Phase 4** — Fleet-Level Control System

* Robot registry
* Command orchestration
* Monitoring dashboards
* Autonomous fallback logic
* Alarming, notifications

---

## **4.5 How the Solution Meets Key Requirements**

### Requirement → Strategy Mapping

| Requirement        | Solution Strategy                       |
| ------------------ | --------------------------------------- |
| Local operation    | Local-first architecture                |
| Future cloud       | Stateless backend, MQTT over WebSockets |
| Open-source only   | Python, JS, Mosquitto                   |
| Scalable           | MQTT pub/sub model                      |
| Multi-device UI    | Browser-based WebSocket UI              |
| Multi-robot future | MQTT topic partitioning                 |
| Reliability        | Watchdog, backend validation            |
| Performance        | Message-driven, low overhead            |

---

# **5. Building Block View**

The building block view describes **what the system is made of**, how the parts are structured, and how they relate to each other.

It includes:

* The overall system decomposition
* Layered architecture
* Responsibilities of each building block
* Interfaces and communications between blocks
* Cross-platform, multi-device support
* Internal backend architecture
* MQTT topic organization for future multi-robot support

This is one of the largest and most important sections of arc42.

---

## **5.1 Top-Level System Decomposition (Level 1)**

The **Robot Control System (RCS)** is divided into **four major subsystems**:

```
+------------------------------------------------------------+
|                 Robot Control System                       |
+------------------------------------------------------------+
|  1. Operator UI Layer                                      |
|  2. Backend Control Layer                                  |
|  3. Messaging Layer (MQTT Broker)                          |
|  4. Robot Hardware Layer                                   |
+------------------------------------------------------------+
```

### **Subsystem Overview**

| Subsystem                 | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| **Operator UI Layer**     | Browser-based interface for robot control & telemetry   |
| **Backend Control Layer** | Logic, validation, telemetry routing, safety mechanisms |
| **Messaging Layer**       | MQTT pub/sub backbone                                   |
| **Robot Hardware Layer**  | Physical robot, sensors, firmware, actuator controllers |

---

## **5.2 Level 2 Decomposition (Container View)**

Each subsystem contains building blocks (similar to C4 "containers").

```
+-----------------------------------------------------------------+
|                             RCS                                 |
+-----------------------------------------------------------------+
|                                                                 |
|  +-------------------+            +--------------------------+  |
|  |  Operator UI      | <--WS-->   | Backend Control Service  |  |
|  |  HTML/JS/React    |   HTTP     | Python/WebSocket/MQTT    |  |
|  +-------------------+            +--------------------------+  |
|                         |              |                        |
|                         | MQTT Pub/Sub |                        |
|                         v              v                        |
|                    +--------------------------+                 |
|                    |      MQTT Broker         |                 |
|                    |   Mosquitto (Local)      |                 |
|                    +--------------------------+                 |
|                         |              |                        |
|                         |   Telemetry  |   Commands             |
|                         v              v                        |
|                   +---------------------------+                 |
|                   |   Robot Hardware Layer    |                 |
|                   |   Sensors, motors, FW     |                 |
|                   +---------------------------+                 |
+-----------------------------------------------------------------+
```

---

## **5.3 Detailed Description of Each Container**

---

### **5.3.1 Operator UI Layer (Browser Application)**

**Technology:**

* HTML, JavaScript
* Optional: React + Vite + Tailwind
* WebSocket for real-time telemetry
* HTTP for configuration or future API endpoints
* Fully responsive (desktop + tablet)

**Responsibilities:**

* Display telemetry (position, load, battery, status)
* Provide robot control interface (buttons, sliders, joystick)
* Maintain local UI state
* Sustain WebSocket connection to backend
* Render warnings and fault states
* Allow multiple devices to connect simultaneously

**Why browser UI?**

* Zero installation required
* Works on any device
* Easy to scale later (Firebase hosting)

**Inputs:**

* Telemetry stream (WebSocket)
* Configuration data
* Robot status messages

**Outputs:**

* Robot commands
* UI events
* Operator actions

---

### **5.3.2 Backend Control Layer (Python Backend)**

**Technology:**

* Python
* Websocket server
* MQTT client libraries
* Optional FastAPI/Falcon for REST endpoints
* Runs locally or in Cloud Run (cloud phase)

**Responsibilities:**

1. **Telemetry Router**

   * Subscribe to MQTT topics
   * Transform telemetry
   * Push updates to UI via WebSocket

2. **Command Validator**

   * Accept commands from UI
   * Validate safety rules (“safe control envelope”)
   * Publish sanitized commands to robot

3. **Robot State Monitor**

   * Track last-seen timestamps
   * Detect communication loss
   * Publish warnings or disconnect events

4. **Multi-device distributor**

   * Several UIs receive same telemetry feed
   * Keeps command source controlled

5. **Cloud-ready service**

   * Stateless
   * Configurable via env variables
   * Container-friendly

**Inputs:**

* Commands from UI
* Telemetry from MQTT

**Outputs:**

* Robot control commands
* Telemetry to UI
* System logs

---

### **5.3.3 Messaging Layer (MQTT Broker)**

**Technology:**

* Mosquitto (OSS)

Current mode: **Local broker**
Future mode: **Cloud Run container or VM**, supporting TLS

**Responsibilities:**

* Publish/subscribe routing
* Keep robot and backend decoupled
* Enable multi-robot topic separation
* Handle QoS levels
* Internal buffering (if configured)

**Why MQTT?**

* Lightweight
* Real-time streaming
* Network recoverability
* Multi-client scalability
* Perfect for robotics workloads

**Inputs:**

* Robot telemetry
* Backend commands

**Outputs:**

* Telemetry distribution
* Command distribution

---

### **5.3.4 Robot Hardware Layer**

**Technology:**

* Embedded controller (Raspberry Pi, ESP32, Jetson, etc.)
* Custom firmware for actuators
* MQTT client for telemetry & control
* Sensor fusion logic (IMU, joint encoders)

**Responsibilities:**

* Consume validated commands
* Execute joint movements
* Send sensor and status telemetry
* Implement watchdog & safety fallback
* Handle stop signals

**Inputs:**

* Commands (MQTT)
* Safety triggers

**Outputs:**

* Telemetry (position, power, temp)
* Status (faults, warnings)

---

## **5.4 Interfaces Between Building Blocks**

### **UI ↔ Backend**

| Protocol        | Purpose                      |
| --------------- | ---------------------------- |
| WebSocket       | Real-time telemetry          |
| HTTP (optional) | Configuration, health checks |

### **Backend ↔ MQTT Broker**

| Protocol | Purpose                      |
| -------- | ---------------------------- |
| MQTT     | Commands, telemetry exchange |

### **MQTT Broker ↔ Robot**

| Protocol | Purpose                    |
| -------- | -------------------------- |
| MQTT     | Robot commands & telemetry |

---

## **5.5 Internal Architecture of Backend Layer (Level 3)**

The backend decomposes into the following components:

```
Backend Control Layer
│
├── WebSocket Gateway
│   ├ Handles connections from UI
│   ├ Sends telemetry to UI
│   └ Receives operator commands
│
├── Command Processor
│   ├ Validates commands
│   ├ Enforces safety envelope
│   └ Publishes to MQTT
│
├── Telemetry Processor
│   ├ Parses MQTT payloads
│   ├ Normalizes telemetry
│   └ Forwards to WebSockets
│
├── Robot Presence Manager
│   ├ Tracks heartbeat
│   ├ Detects disconnections
│   └ Emits warnings
│
├── MQTT Client Adapter
│   ├ Connects to broker
│   ├ Subscribes/publishes topics
│   └ Manages reconnections
│
└── Config Manager
    ├ Handles environment variables
    ├ Contains cloud/local configs
    └ Standardizes deployment
```

---

## **5.6 MQTT Topic Architecture (Level 3+)**

### **Single Robot (Current)**

```
robot/telemetry
robot/commands
robot/status
robot/errors
```

### **Multi-Robot (Future)**

This scalable structure supports unlimited robots:

```
robots/<robot_id>/telemetry
robots/<robot_id>/commands
robots/<robot_id>/status
robots/<robot_id>/errors
```

Examples:

```
robots/alpha/telemetry
robots/beta/commands
robots/gamma/errors
```

This naming scheme supports:

* Cloud-scale multi-robot management
* Fine-grained ACLs
* Per-robot topic filtering
* Real-time dashboards

---

## **5.7 Cross-Layer Interactions**

### **Telemetry Pipeline**

Robot → MQTT Broker → Backend → WebSocket → UI

### **Command Pipeline**

UI → WebSocket → Backend → MQTT Broker → Robot

### **Fault/Disconnect Handling**

Robot stops posting → Backend timeout → UI alert

---

## **5.8 Building Block Summary Table**

| Layer     | Building Blocks                                    | Purpose            |
| --------- | -------------------------------------------------- | ------------------ |
| UI        | Dashboard, WebSocket client, Control widgets       | User interaction   |
| Backend   | WS gateway, validators, transformers, MQTT adapter | Core logic         |
| Messaging | Mosquitto broker                                   | Pub/Sub routing    |
| Robot     | Firmware, actuators, sensors                       | Physical execution |

---

## **5.9 Why This Decomposition Works**

### ✔ Highly modular

Each layer can be replaced or upgraded independently.

### ✔ Future cloud compatibility

Backend and MQTT broker are container-ready.

### ✔ Multi-robot scalable

Topic partitioning and stateless backend supports fleet expansion.

### ✔ Safe and predictable

Backend validation ensures command safety.

### ✔ Multi-UI support

WebSocket fan-out enables many observers.

### ✔ Low latency

MQTT + WebSocket is extremely efficient.

---
# **6. Runtime View**

---

## **6.1 Runtime Scenario 1 — System Startup Sequence**

This describes how the system initializes from power-on to full operational readiness.

### **6.1.1 Purpose**

Ensure all subsystems—MQTT broker, backend, UI, and robot—start in a correct order and become fully operational.

### **6.1.2 Actors**

* Backend Control Service
* MQTT Broker
* Robot Hardware
* Operator UI

---

### **6.1.3 Preconditions**

* All components are installed locally
* Robot has network access
* Mosquitto broker running
* Backend script executable
* UI reachable via browser

---

# **6.1.4 Sequence Flow (Textual Diagram)**

```
Operator/Dev
   |
   | Start MQTT broker
   v
[Mosquitto Broker] --------------------------------------------+
                                                              |
Backend                                                       |
   | Connect to MQTT broker                                   |
   |--------------------------------------------------------->|
   | Subscribe to telemetry/status topics                     |
   |<---------------------------------------------------------|
   | Initialize WebSocket server                              |
   |
   |
Robot                                                           |
   | Power on                                                  |
   | Firmware boots                                            |
   | Connects to MQTT broker                                  |
   |---------------------------------------------------------->|
   | Publishes "robot/status: ONLINE"                         |
   |
Backend                                                        |
   | Receives status                                           |
   | Notifies all connected UIs (if any)                      |
   |
Operator UI                                                    |
   | Loads webpage                                             |
   | Establishes WebSocket connection to Backend              |
   |--------------------------------------------------------->|
   | Requests robot status & initial telemetry                |
   |
Backend                                                        |
   | Sends initial robot state                                |
   | Subscribes UI session to telemetry stream                |
   |
UI                                                              |
   | Renders dashboard and controls                           |
```

---

### **6.1.5 Outcome**

* All connections initialized
* Robot online
* UI synchronized
* System in “Ready” operational state

---

### **6.1.6 Failure/Exception Paths**

| Failure                          | Cause             | Recovery                       |
| -------------------------------- | ----------------- | ------------------------------ |
| Backend fails to connect to MQTT | Broker offline    | Retry with exponential backoff |
| Robot fails to connect to MQTT   | Network/firmware  | Backend shows “Robot Offline”  |
| UI fails WebSocket connection    | Wrong backend URL | UI retries or shows banner     |
| MQTT drops connection            | LAN glitch        | Automatic reconnect            |

---

---

## **6.2 Runtime Scenario 2 — Robot Command Flow**

This describes how the operator issues a command that the robot executes.

### **6.2.1 Purpose**

Ensure safe, validated command handling with proper backend control.

### **6.2.2 Actors**

* Operator UI
* Backend Control Layer
* MQTT Broker
* Robot

---

### **6.2.3 Preconditions**

* UI connected via WebSocket
* Backend connected to MQTT
* Robot online and subscribed to command topics

---

# **6.2.4 Sequence Flow (Textual Diagram)**

```
Operator UI
   | Issue command (ex: 'move_forward', 'turn_left')
   v
[WebSocket] Send command to Backend
   |
Backend
   | Validate command (safety checks)
   | Throttle or transform if needed
   v
   Publish MQTT command topic
             |
             v
    [MQTT Broker]
             |
Robot Firmware
   | Receives command
   | Executes motion
   | Publishes acknowledgment (optional)
             |
Backend
   | Receives ack
   | Forwards state update to UI
   |
UI
   | Updates display to reflect new state
```

---

### **6.2.5 Safety Considerations**

Backend enforces:

* Allowed command whitelist
* Maximum velocity limits
* Joint limit check (future)
* Command rate limiting
* Emergency stop priority

---

### **6.2.6 Failure/Exception Paths**

| Failure                        | Effect          | Mitigation            |
| ------------------------------ | --------------- | --------------------- |
| UI sends malformed command     | Backend rejects | UI notified           |
| Backend cannot publish MQTT    | Command lost    | Visible error message |
| Robot firmware rejects command | No motion       | Robot sends status    |
| Network drop during command    | Robot may stop  | Watchdog timeout      |

---

---

## **6.3 Runtime Scenario 3 — Telemetry Update Flow**

Describes how telemetry flows continuously from robot → UI.

### **6.3.1 Purpose**

Enable real-time visualization of robot’s state.

### **6.3.2 Actors**

* Robot
* MQTT Broker
* Backend
* UI

---

### **6.3.3 Preconditions**

* Robot publishing telemetry
* Backend subscribed to telemetry
* UI connected to WebSocket

---

# **6.3.4 Sequence Flow (Textual Diagram)**

```
Robot
   | Publish telemetry (pose, battery, load, joint angles)
   v
[MQTT Broker]
   |
Backend
   | MQTT handler receives telemetry
   | Parse & normalize data
   | Broadcast to all connected UI WebSockets
   v
Operator UI
   | Receive telemetry packet
   | Update dashboard charts & indicators
```

---

### **6.3.5 Telemetry Characteristics**

| Parameter       | Expected Behavior      |
| --------------- | ---------------------- |
| Frequency       | 5–50 Hz                |
| Latency         | <200ms local           |
| Size per packet | <1KB typical           |
| Format          | JSON payloads          |
| Loss tolerance  | Small drops acceptable |

---

### **6.3.6 Alternative Flows**

* UI joins late → backend sends last-known state
* Multiple UI clients subscribe → backend fans out telemetry
* Robot stops sending → backend detects offline

---

### **6.3.7 Failure/Exception Paths**

| Issue                 | Behavior             | Mitigation                        |
| --------------------- | -------------------- | --------------------------------- |
| Robot telemetry stops | UI “Robot Offline”   | Backend uses timestamp monitoring |
| MQTT broker lag       | No real-time updates | Increase broker buffer            |
| Backend overload      | Telemetry delayed    | Use async processing              |

---

---

## **6.4 Runtime Scenario 4 — Robot Disconnect Detection**

### Sequence:

1. Robot stops publishing telemetry
2. Backend MQTT client detects timeout
3. Backend sends `robot/offline` message to UI
4. UI disables controls & shows alert
5. Once robot reconnects, system resumes

---

## **6.5 Runtime Scenario 5 — Multi-Device UI Access**

The system supports multiple UIs viewing telemetry simultaneously.

### Flow:

* Multiple WebSocket clients connect
* Backend distributes telemetry to all
* Backend permits only one “control master” (future)

---

## **6.6 Runtime Scenario 6 — System Shutdown**

Orderly shutdown:

1. UI closes WebSocket
2. Backend disconnects MQTT client
3. Backend stops WebSocket server
4. Broker stops (optional)

---

## **6.7 Summary of Runtime Behaviors**

| Scenario     | Key Behavior                               |
| ------------ | ------------------------------------------ |
| Startup      | Safe connection sequencing, initialization |
| Command      | Validation → MQTT publish → robot executes |
| Telemetry    | Robot → Broker → Backend → UI              |
| Disconnect   | Heartbeat detection, state update          |
| Multi-device | Broadcast telemetry, manage concurrency    |
| Shutdown     | Clean disconnects                          |

---
# **7. Deployment View**

---

## **7.1 Deployment Environment Overview**

### **Two Core Modes**

| Mode                       | Description                                                                   |
| -------------------------- | ----------------------------------------------------------------------------- |
| **Local Deployment**       | Everything runs on a single laptop or local machine. Zero cloud dependencies. |
| **Cloud Deployment (GCP)** | Backend runs on Cloud Run, UI on Firebase Hosting, MQTT on Cloud Run or VM.   |
| **Multi-Robot/Fleet Mode** | Cloud-native scaling for multiple robots, multiple operators, global access.  |

---

## **7.2 Deployment Model (Phase 1 — Local Deployment)**

### *As used for hackathon and initial development.*

All components run on a single machine connected to a **local Wi-Fi LAN**.
The robot is on the same LAN.

---

### **7.2.1 Local Deployment Diagram**

```
                +-------------------------------+
                |      Operator Laptop/PC       |
                |-------------------------------|
                |  Web Browser (UI)             |
                |  WebSocket Client             |
                +-------------------------------+
                          |
                    (HTTP / WS)
                          |
                +-------------------------------+
                |   Backend Control Service     |
                |   Python WebSocket + MQTT     |
                +-------------------------------+
                          |
                      (MQTT)
                          |
                +-------------------------------+
                |       Mosquitto Broker        |
                |  (Local MQTT on same machine) |
                +-------------------------------+
                          |
                      (Wi-Fi LAN)
                          |
                +-------------------------------+
                |      Humanoid Robot Device    |
                |  MQTT Client + Motor Control  |
                +-------------------------------+
```

---

### **7.2.2 Local Deployment Characteristics**

| Area             | Description                                         |
| ---------------- | --------------------------------------------------- |
| **Topology**     | Single machine for backend + broker; robot separate |
| **Network**      | Local LAN (Wi-Fi or Ethernet)                       |
| **Security**     | No TLS required (isolated)                          |
| **Performance**  | Very low latency (<20ms local MQTT)                 |
| **Installation** | Python script + Mosquitto broker                    |
| **Scalability**  | 1–2 robots max (local limits)                       |

---

### **7.2.3 Local Deployment Advantages**

* Simple setup
* Best possible latency
* Perfect for demos/hackathons
* No cloud billing
* Reproducible and offline-capable

---

### **7.2.4 Local Deployment Limitations**

* Single point of failure
* No global access
* No persistence
* No authentication/security
* Not scalable to multiple robots or operators

---

---

## **7.3 Deployment Model (Phase 2 — Hybrid Cloud Deployment)**

### *Backend and UI in Cloud; MQTT still local.*

Operators access cloud-hosted services, but the robot remains on the LAN with a local MQTT broker.

---

### **7.3.1 Hybrid Cloud Deployment Diagram**

```
                        +---------------------------+
                        |    Firebase Hosting       |
                        |  (UI served from cloud)   |
                        +-------------+-------------+
                                      |
                                 (HTTPS)
                                      |
                        +-------------v-------------+
                        |       Cloud Run           |
                        |  Backend Control Service  |
                        +-------------+-------------+
                                      |
                              (Secure MQTT/WS)
                                      |
                 +-----------------------------------------+
                 |         Local Environment (LAN)         |
                 |-----------------------------------------|
                 |    +-----------------------------+       |
                 |    |     Local Mosquitto Broker  |       |
                 |    +--------------+--------------+       |
                 |                   |                      |
                 |                 (MQTT)                  |
                 |                   |                      |
                 |    +--------------v--------------+       |
                 |    |      Humanoid Robot         |       |
                 |    +-----------------------------+       |
                 +-----------------------------------------+
```

---

### **7.3.2 Hybrid Cloud Characteristics**

| Area         | Description                                                   |
| ------------ | ------------------------------------------------------------- |
| UI           | Cloud hosted                                                  |
| Backend      | Hosted on GCP Cloud Run                                       |
| Broker       | Still local                                                   |
| Connectivity | Backend connects to LAN broker via secure tunnel or public IP |
| Latency      | Slightly increased                                            |
| Security     | JWT-based authentication possible                             |
| Scalability  | Backend/UI scale globally; robot stays local                  |

---

### **7.3.3 Hybrid Cloud Benefits**

* Cloud-hosted UI accessible anywhere
* Backend auto-scales
* Robot stays on local network for safety
* No need to move MQTT to cloud yet
* Future-proof migration path

---

### **7.3.4 Hybrid Cloud Challenges**

* Cloud Run must reach local MQTT broker
* Requires port forwarding or secure tunnel
* More complex networking

---

---

## **7.4 Deployment Model (Phase 3 — Fully Cloud-Native Deployment)**

### *All components cloud-hosted, supporting multi-robot global fleet.*

This is the **future target architecture**.

---

### **7.4.1 Cloud-Native Deployment Diagram**

```
+--------------------------------------------------------------+
|                     Google Cloud Platform                    |
|--------------------------------------------------------------|
| +------------------+      +-------------------------------+ |
| | Firebase Hosting |      |       Cloud Run Backend       | |
| | (UI SPA/React)   |<---->|  API + WebSocket Gateway      | |
| +------------------+      +-------------------------------+ |
|                                   |                          |
|                                   | MQTT over WebSockets     |
|                                   v                          |
|                       +-----------------------------+        |
|                       |  MQTT Broker on Cloud Run   |        |
|                       |  or Managed MQTT Container   |        |
|                       +--------------+--------------+        |
|                                      |                       |
+--------------------------------------------------------------+
                                       |
                                Global Internet
                                       |
                           +------------------------+
                           |   Humanoid Robots      |
                           |   (Anywhere)           |
                           +------------------------+
```

---

### **7.4.2 Cloud-Native Characteristics**

| Area               | Description                       |
| ------------------ | --------------------------------- |
| UI                 | Global SPA hosting                |
| Backend            | Stateless, auto-scaling Cloud Run |
| MQTT Broker        | Container with TLS + MQTT-over-WS |
| Robot Connectivity | Secure MQTT endpoint              |
| Authentication     | Google Identity Platform          |
| Observability      | Cloud Logging + Monitoring        |
| Scalability        | Virtually unlimited               |

---

### **7.4.3 Cloud Deployment Advantages**

* Global access
* Infinite operator scaling
* Multi-robot fleet support
* Fully secure with TLS
* Centralized monitoring/logging
* Container-based reproducibility

---

### **7.4.4 Cloud Deployment Challenges**

| Challenge               | Description                                     |
| ----------------------- | ----------------------------------------------- |
| Robot NAT traversal     | Robots behind routers need MQTT-over-WebSockets |
| Cloud Run statelessness | Must store state externally if needed           |
| WebSocket load limits   | Many client fanouts require horizontal scaling  |
| MQTT broker scaling     | Must support many simultaneous connections      |

---

---

## **7.5 Deployment Requirements**

### **Minimal Local Deployment Requirements**

* Python 3.10+
* Mosquitto broker
* Node/Vite dev server (optional)
* Local Wi-Fi network
* Browser (Chrome/Safari etc.)

---

### **Cloud Deployment Requirements**

* GCP project
* Cloud Run enabled
* Firebase Hosting enabled
* Containerized backend
* TLS certificates

---

## **7.6 Deployment View Summary**

| Deployment Phase     | Key Attributes                               |
| -------------------- | -------------------------------------------- |
| **Phase 1 (Local)**  | Simple, LAN-based, no cloud, hackathon-ready |
| **Phase 2 (Hybrid)** | Cloud UI + backend, robot local              |
| **Phase 3 (Cloud)**  | Fully cloud-native, global multi-robot       |
| **Future Expansion** | Fleet management, dashboards, IAM, logs      |

---
# **8. Cross-Cutting Concepts**

The major categories covered:

1. **Domain model & data model**
2. **Communication patterns**
3. **Error handling & safety rules**
4. **Logging & observability**
5. **Security & authentication**
6. **Configuration management**
7. **Performance considerations**
8. **Concurrency & event flow**
9. **Deployment/DevOps concerns**
10. **Monitoring & health checks**
11. **Testing approach**

Let’s dive into each one.

---

## **8.1 Domain Concepts (Robot Control Domain Model)**

The RCS revolves around a set of core domain concepts:

### **Entities**

* **Robot**

  * ID, type, capabilities
* **Telemetry Frame**

  * Pose, joint angles, battery, temperature
* **Command**

  * Motion, posture, E-stop, reset
* **Operator Session**

  * UI session connected via WebSocket
* **System State**

  * Robot online/offline
  * Backend health
* **Fault/Event Messages**

---

### **Robot State Machine (conceptual)**

```
OFFLINE → INITIALIZING → READY → EXECUTING → ERROR → OFFLINE
```

Backend enforces transitions with validation.

---

## **8.2 Data Model and Data Formats**

### **Telemetry Format (JSON)**

Example fields:

```
{
  "timestamp": 1672838893,
  "battery": 82,
  "pose": { "x": 0.2, "y": 1.0, "yaw": 15 },
  "joints": { "head": 12, "arm_left": 30, ... },
  "temperature": 48,
  "status": "OK"
}
```

### **Command Format (JSON)**

```
{
  "command": "move_forward",
  "value": 0.3,
  "speed": 0.5
}
```

### **MQTT Topic Naming Schema**

Current:

```
robot/telemetry
robot/commands
robot/status
robot/errors
```

Future scalable:

```
robots/<robot_id>/telemetry
robots/<robot_id>/commands
robots/<robot_id>/status
robots/<robot_id>/errors
```

This schema is foundational for multi-robot cloud operations.

---

## **8.3 Communication Patterns**

### **Pattern: Event-driven Messaging (MQTT)**

Used for:

* Telemetry (robot → backend)
* Commands (backend → robot)
* Status updates (robot → backend)

Why MQTT?

* Low latency
* Reliable QoS
* Auto-reconnect
* Perfect for robotics

---

### **Pattern: Publish/Subscribe**

* Robot publishes telemetry
* Backend and other services subscribe
* UIs subscribe indirectly via backend WebSocket fan-out

---

### **Pattern: Request-Response** (for some UI/backend interactions)

Used via WebSocket or REST for:

* Fetching initial robot state
* Asking for config

---

### **Pattern: WebSocket Push**

Used for:

* UI real-time updates
* Multi-device distribution
* Disconnect detection

---

## **8.4 Error Handling & Safety Concepts**

Robot control requires *strict safety rules*.

### **8.4.1 Command Validation Rules**

Backend ensures:

* Whitelisted commands only
* Velocity/joint limits
* Emergency-stop is prioritised
* Rate limiting (avoid command flooding)
* No invalid states (e.g., torque too high)

---

### **8.4.2 Watchdog & Heartbeat**

Robot publishes periodic heartbeat:

* Backend tracks last-seen timestamp
* If expired → robot considered offline
* UI is notified immediately

---

### **8.4.3 Safe Fallback States**

If telemetry stops:

* UI disables controls
* Robot enters safe-stop (firmware responsibility)

---

### **8.4.4 Error Reporting Model**

Robot reports errors via:

```
robots/<id>/errors
```

Backend forwards critical errors to UI.

---

## **8.5 Logging and Observability**

### **8.5.1 Local Mode**

* Python logging to stdout
* Optional local file logs
* Simple console-based monitoring

---

### **8.5.2 Cloud Mode (GCP)**

Backend logs go to:

* Cloud Logging
* Structured JSON logs
* Robot activity logs aggregated by topic

---

### **8.5.3 Log Categories**

* INFO: Connection events, start/stop
* WARN: Late telemetry, dropping frames
* ERROR: Broken WebSocket, MQTT disconnect
* CRITICAL: Robot error events

---

### **8.5.4 Tracing**

Future extension:

* OpenTelemetry instrumentation
* Request correlation IDs
* Tracing robot commands through pipeline

---

## **8.6 Security Concepts**

(Security is minimal in local mode, but fully planned for cloud.)

---

### **8.6.1 Phase 1: Local**

* No authentication
* No encryption
* LAN isolation trusted
* Local MQTT broker without password

---

### **8.6.2 Phase 2: Hybrid**

Backend on Cloud Run:

* HTTPS forced
* Token-based UI auth
* MQTT broker local → secure tunnel required

---

### **8.6.3 Phase 3: Cloud**

Full security architecture:

* OAuth2 (Google Identity Platform)
* JWT sessions for UI
* TLS mandatory for MQTT (port 8883)
* Service accounts control robot→cloud access
* Topic-level ACLs for multi-robot separation

---

### **8.6.4 Robot Authentication (future)**

Robots identified by:

* x509 certificates
* Robot ID embedded in cert
* MQTT ACLs enforce which topics each robot can publish/subscribe

---

## **8.7 Configuration Management**

### **Config Layers**

| Layer                             | Examples                  |
| --------------------------------- | ------------------------- |
| **Backend environment variables** | MQTT URL, ports, robot ID |
| **Robot firmware configs**        | MQTT endpoint, frequency  |
| **UI configuration**              | Backend WebSocket URL     |

---

### **Configuration Sources**

* `.env` files (local)
* Cloud Run environment variables
* Firebase hosting config (future)
* Robot YAML file or JSON

---

### **Configuration Characteristics**

* No hard-coded URLs
* Cloud/local mode selection
* Safe fallback defaults
* Secrets stored in Secret Manager (cloud mode)

---

## **8.8 Performance Concepts**

Performance is critical for teleoperation.

---

### **8.8.1 Latency Targets**

| Mode         | Target            |
| ------------ | ----------------- |
| Local        | <100ms end-to-end |
| Cloud hybrid | <300ms            |
| Fully cloud  | <400ms            |

---

### **8.8.2 Telemetry Processing**

Backend may implement:

* Frame skipping if lagging
* Telemetry grouping
* Compression (future)

---

### **8.8.3 Command Throughput Limiting**

Prevent:

* Command flooding
* Device overload

Rate limit example:

```
max 20 commands/second
```

---

## **8.9 Concurrency & Event Flow Concepts**

The system is **event-driven**, with asynchronous concurrency.

Backend must support:

* Multiple UI WebSocket connections
* Continuous telemetry processing
* MQTT client callbacks
* Non-blocking operations

Technologies:

* Python asyncio (recommended)
* WebSocket async tasks
* Independent MQTT threads

---

## **8.10 DevOps & Deployment Concepts**

### **Local Mode**

* Start broker
* Start Python backend
* Serve UI via local server

### **Cloud Mode**

* Docker images for backend
* Deploy to Cloud Run
* Deploy UI via Firebase hosting
* Container for MQTT broker

---

### **Zero-Downtime Deployment**

Cloud Run handles:

* Rolling upgrades
* Auto-scaling
* Health checks
* Instance isolation

---

## **8.11 Monitoring & Health Checks**

### **Backend**

* `/health` endpoint
* WebSocket ping/pong
* MQTT connection health

### **Robot**

* Heartbeat timestamp
* Missing telemetry alerts

### **Cloud**

* Cloud Monitoring dashboards
* Alerting on robot offline
* API error rates

---

## **8.12 Testing Concepts**

### **Unit Tests**

* Command validation
* Payload parsing
* Safety logic

### **Integration Tests**

* MQTT broker + backend
* WebSocket telemetry flow

### **System Tests**

* End-to-end teleoperation
* Multi-device access

### **Cloud Tests (future)**

* Load tests for scaling
* Failover tests

---

## **8.13 Summary**

Cross-cutting concepts ensure:

* **Safety**
* **Reliability**
* **Performance**
* **Scalability**
* **Future cloud readiness**
* **Consistent quality**

---

# **9. Architecture Decisions**

Below are the major decisions made for the system. Each is documented using a simplified ADR structure:

* **Context**
* **Decision**
* **Status**
* **Rationale**
* **Alternatives considered**
* **Consequences**

---

## **ADR-001: Use MQTT as the Primary Communication Protocol**

### **Context**

The system needs low-latency, high-frequency, bidirectional communication between robot ↔ backend ↔ UI, running locally now and in cloud later.

### **Decision**

MQTT is selected as the primary communication protocol for **robot telemetry** and **control commands**.

### **Status**

**Accepted**, mandatory constraint.

### **Rationale**

* Built for IoT and robotics
* Extremely lightweight
* Low-latency pub/sub
* Handles disconnects well
* QoS levels ensure reliability
* Cloud-friendly (MQTT over WebSockets)
* Enables multi-robot scaling via topic namespaces

### **Alternatives Considered**

| Alternative     | Reason Rejected                                     |
| --------------- | --------------------------------------------------- |
| REST            | Too slow, polling required, no streaming            |
| WebSockets only | No pub/sub, no QoS, manual message routing          |
| ROS2 DDS        | Too heavy for browser, complex setup                |
| gRPC            | Not ideal for streaming telemetry at high frequency |

### **Consequences**

✔ Perfect for robotics
✔ Cloud-ready
✔ Supports multi-robot
✖ Requires MQTT broker
✖ More complexity than simple HTTP

---

## **ADR-002: Use Python for Backend**

### **Context**

Backend must validate commands, route telemetry, handle WebSockets, and be cloud-ready.

### **Decision**

Backend is implemented in **Python**.

### **Status**

**Accepted.**

### **Rationale**

* Fast developer productivity
* Abundant libraries (paho-mqtt, websockets, FastAPI)
* Excellent for robotics integration
* Easy for hackathon teams to iterate
* Portable and container-friendly

### **Alternatives Considered**

| Alt     | Reason Rejected                                  |
| ------- | ------------------------------------------------ |
| Node.js | Weaker robotics tooling, less stability for MQTT |
| Go      | High performance but slower development speed    |
| C++     | Too heavy for backend; complexity too high       |
| Rust    | Overkill for hackathon; steep learning curve     |

### **Consequences**

✔ Rapid development
✔ Easy debugging
✔ Excellent for prototype & cloud migration
✖ Lower performance under extreme load (can scale horizontally)

---

## **ADR-003: Use Browser-Based UI (HTML/JS)**

### **Context**

Operators must control the robot from laptop or tablet without installing software.

### **Decision**

Use **Web-based UI** delivered over HTTP.

### **Status**

**Accepted.**

### **Rationale**

* Zero installation
* Works across iPad, Windows, Mac, mobile
* Easy cloud deployment (Firebase Hosting)
* Fast UI iteration
* Rich libraries for UI/visualization

### **Alternatives Considered**

| Alt                | Reason Rejected                       |
| ------------------ | ------------------------------------- |
| Native apps        | Too slow to build, not cross-platform |
| Electron           | Heavyweight, unnecessary              |
| Command-line tools | Not user-friendly                     |

### **Consequences**

✔ Multi-device access
✔ Easy deployment
✔ Easy UI/UX development
✖ Browser-based UI depends on WebSocket connection stability

---

## **ADR-004: Use WebSockets for UI Telemetry Distribution**

### **Context**

Telemetry needs to reach many UIs in real time.

### **Decision**

Use **WebSocket** push from backend → UI.

### **Status**

**Accepted.**

### **Rationale**

* Real-time streaming
* Simple client implementation
* Backend can fan-out to multiple UIs
* Browser-compatible
* Works in both local + cloud modes

### **Alternatives**

| Alt                | Reject Reason                |
| ------------------ | ---------------------------- |
| MQTT in browser    | Less reliable, complex setup |
| Server-sent events | One-way only                 |
| Polling            | Too slow, high overhead      |

### **Consequences**

✔ Real-time updates
✔ Easy multi-device broadcasting
✖ Requires persistent backend connections
✖ Cloud scaling requires load-balanced WebSockets

---

## **ADR-005: Local-First Architecture**

### **Context**

Hackathon requirement: system must run entirely on one machine.

### **Decision**

Architecture supports **complete local execution** with no cloud dependencies.

### **Status**

**Accepted**.

### **Rationale**

* Reliability during demos
* No internet required
* Zero cloud billing
* Simplifies development
* Easier debugging

### **Alternatives**

| Alternative | Reason rejected                              |
| ----------- | -------------------------------------------- |
| Cloud-first | Requires billing, auth setup, risk of outage |

### **Consequences**

✔ Robust offline capability
✔ Very fast iteration
✖ Local broker limits multi-robot scaling
✖ Extra work needed when migrating to cloud

---

## **ADR-006: Cloud-Ready Stateless Backend**

### **Context**

Backend must migrate to GCP Cloud Run later.

### **Decision**

Backend is designed to be **stateless**, using:

* No local file state
* No session storage
* All state external (MQTT, memory only)

### **Status**

**Accepted**.

### **Rationale**

* Cloud Run instances restart anytime
* Statelessness = auto-scaling
* Multiple backend instances share work

### **Alternatives**

| Alt              | Reason rejected                         |
| ---------------- | --------------------------------------- |
| Stateful backend | Cannot auto-scale; error-prone in cloud |

### **Consequences**

✔ Easy GCP deployment
✔ Horizontal scaling support
✖ Stateful features need external storage if added later

---

## **ADR-007: Open-Source Only Technology Stack**

### **Context**

Your requirement: use only free/open-source technologies.

### **Decision**

All components are OSS:

* Python
* Mosquitto MQTT
* Node.js / Vite
* WebSocket
* React (?) optionally

### **Alternatives rejected**

Any commercial/paid solutions.

### **Consequences**

✔ No licensing issues
✔ Highly portable
✖ No enterprise features out-of-box
✖ Some manual operations required when scaling

---

## **ADR-008: MQTT Topic Namespace for Multi-Robot Future**

### **Context**

Future version requires multiple robots.

### **Decision**

Use hierarchical topic namespace:

```
robots/<id>/telemetry
robots/<id>/commands
robots/<id>/status
robots/<id>/errors
```

### **Status**

**Accepted.**

### **Rationale**

* Cloud-ready
* Scalable
* Allows isolation and routing
* Simple ACLs and permissions

### **Alternatives**

A flat namespace like:

```
telemetry/robot1
```

Rejected due to lower scalability.

### **Consequences**

✔ Clean multi-robot separation
✔ Fine-grained access control
✖ Slightly more complex backend logic

---

## **ADR-009: Use Mosquitto Broker (Local)**

### **Context**

Needs local MQTT broker for hackathon.

### **Decision**

Use **Mosquitto OSS**, locally installed.

### **Status**

**Accepted.**

### **Rationale**

* Lightweight
* Highly stable
* Zero-cost
* Easy to configure
* Perfect for local demos

### **Alternatives**

* HiveMQ CE
* EMQX
* GCP IoT Core (deprecated)

All rejected due to complexity or not fully open-source.

---

## **ADR-010: Use Containerization for Cloud Migration**

### **Context**

Backend must run on Cloud Run.

### **Decision**

Package backend as a **Docker container**.

### **Status**

**Accepted (future).**

### **Rationale**

* Cloud Run only accepts containers
* Standardized builds
* Easy reproduction
* Multi-environment consistency

### **Alternatives**

| Alt                   | Reject Reason                 |
| --------------------- | ----------------------------- |
| Running backend on VM | Requires DevOps; more complex |

---

## **ADR-011: Keep UI Stateless and Client-Heavy**

### **Context**

UI must work across many devices and scale globally.

### **Decision**

UI is purely static, served as HTML/JS/React bundle.

### **Benefits**

* Easy hosting (Firebase Hosting)
* Cached by CDN
* No server-side state
* Ultra-fast cold start

---

## **ADR-012: Use WebSocket Ping/Pong for Disconnect Detection**

### **Context**

Robot control must alert UI if backend or robot disconnects.

### **Decision**

WebSocket ping/pong frames used to maintain connection health.

### **Consequences**

✔ UI knows immediately if backend drops
✔ Real-time fault awareness

---

## **ADR-013: Use Heartbeat Monitoring for Robot Presence**

### **Context**

Robot safety requires detecting unexpected disconnects.

### **Decision**

Robot publishes periodic heartbeat.
Backend runs a timeout thread.

### **Consequences**

✔ Robot offline detection
✔ UI notified instantly
✔ Backbone for future alarm system

---

## **ADR-014: Cloud Identity Platform for Authentication (Future)**

### **Context**

Cloud version needs operator login.

### **Decision**

Use Google Identity Platform + Firebase Auth.

### **Consequences**

✔ Secure OAuth2 flows
✔ Easy integration
✔ Role-based access (future)

---

## **ADR-015: Minimal Dependencies for Hackathon Robustness**

### **Context**

Hackathon demos can break if environment too complex.

### **Decision**

Minimize dependencies:

* No DB
* No heavy frameworks
* No complex networking
* No external APIs

### **Consequences**

✔ Fast setup
✔ Robust in offline scenarios
✖ Limited functionality short-term

---

## **ADR Summary Table**

| ADR # | Decision                   | Status   |
| ----- | -------------------------- | -------- |
| 001   | MQTT protocol              | Accepted |
| 002   | Python backend             | Accepted |
| 003   | Browser UI                 | Accepted |
| 004   | WebSocket telemetry        | Accepted |
| 005   | Local-first                | Accepted |
| 006   | Stateless backend          | Accepted |
| 007   | Open-source only           | Accepted |
| 008   | Multi-robot MQTT namespace | Accepted |
| 009   | Mosquitto broker           | Accepted |
| 010   | Docker + Cloud Run         | Future   |
| 011   | Stateless UI               | Accepted |
| 012   | WS Ping/Pong               | Accepted |
| 013   | Robot heartbeat            | Accepted |
| 014   | Cloud Authentication       | Future   |
| 015   | Minimal dependencies       | Accepted |

---
# **10. Quality Requirements**

---

## **10.1 The Quality Tree**

The Quality Tree organizes major quality attributes into categories.

```
Quality Attributes
│
├── Reliability
│    ├── Connectivity stability
│    ├── Telemetry consistency
│    └── Safe command handling
│
├── Performance
│    ├── Low-latency control
│    ├── High-frequency telemetry
│    └── Efficient event-driven backend
│
├── Scalability
│    ├── Multi-robot support
│    ├── Multi-operator support
│    └── Cloud auto-scaling
│
├── Security (Future priority)
│    ├── Authentication
│    ├── TLS MQTT
│    └── Access control
│
├── Developer Experience
│    ├── Easy to setup locally
│    ├── Clear architecture
│    └── Rapid debugging
│
├── Maintainability
│    ├── Modular components
│    ├── Stateless backend
│    └── Configuration management
│
└── Portability / Cloud-readiness
     ├── Runs locally
     ├── Docker container support
     └── Seamless migration to GCP
```

---

## **10.2 Quality Goals (Top Priorities)**

From your input, the system’s top 4 quality goals are:

### **1. Reliability (Highest Priority)**

The robot must behave predictably; errors or disconnects must be detected in real time.

### **2. Performance**

Low latency and real-time responsiveness are crucial for safe teleoperation.

### **3. Developer Experience**

Easy setup, readable code, simple debugging, modular architecture.

### **4. Scalability**

Support for multiple robots, multiple operators, and future cloud deployment.

---

## **10.3 Detailed Quality Goal Descriptions**

### **10.3.1 Reliability**

Robots must remain in safe operating conditions at all times.

**Key requirements:**

* Backend detects robot disconnects < 2 seconds
* Commands validated before sending
* Watchdog must ensure robot enters safe stop state
* MQTT reconnect must be automatic

---

### **10.3.2 Performance**

System must feel “real-time”.

**Targets:**

| Layer                  | Target Latency |
| ---------------------- | -------------- |
| UI → Backend           | <50ms          |
| Backend → MQTT → Robot | <100ms         |
| Telemetry roundtrip    | <150ms         |
| Local mode             | <20ms typical  |
| Cloud mode             | <300–400ms     |

**Telemetry throughput:**

* 5–50 Hz
* <1 KB per message

---

### **10.3.3 Developer Experience**

For rapid development and hackathon setup:

* System runs in <2 minutes
* Minimal dependencies
* No cloud required
* Clean modular layout
* Clear building blocks
* Easy logging/debugging
* Readable error messages

---

### **10.3.4 Scalability**

Future target: **multi-robot, multi-user cloud platform**.

Requirements:

* Topic namespace partitioning
* Stateless backend suitable for Cloud Run
* MQTT broker scalable to thousands of topics
* Horizontal scaling of backend workers
* WebSocket load-balancing
* Multi-device telemetry delivery

---

## **10.4 Quality Scenarios**

Quality scenarios describe **measurable**, **observable** behaviors under specific conditions.

---

### **10.4.1 Reliability Scenarios**

#### **Scenario R1 — Robot Disconnect Detection**

**Stimulus:** Robot suddenly loses network connection.
**Response:** Backend detects missing heartbeats within **2 seconds**.
**Measures:** UI switches to “Offline” state instantly.

---

#### **Scenario R2 — Corrupt Command Rejection**

**Stimulus:** UI sends malformed or unsafe command.
**Response:** Backend rejects command, UI notified.
**Measures:** Robot never receives invalid data.

---

#### **Scenario R3 — MQTT Reconnect**

**Stimulus:** MQTT broker temporarily drops.
**Response:** Backend auto-reconnects in < 3 seconds.
**Measures:** UI continues running; telemetry resumes.

---

### **10.4.2 Performance Scenarios**

#### **Scenario P1 — Telemetry Throughput**

**Stimulus:** Robot sends 20 telemetry messages per second.
**Response:** Backend and UI process all messages without lag.
**Measures:** <150ms end-to-end latency.

---

#### **Scenario P2 — Command Responsiveness**

**Stimulus:** Operator sends movement command.
**Response:** Robot receives command within 100 ms.
**Measures:** Motion begins within human-perceived real-time.

---

#### **Scenario P3 — Cloud Mode Latency**

**Stimulus:** UI → Cloud Run → Cloud MQTT → Robot.
**Response:** Roundtrip remains ≤400ms.
**Measures:** Teleoperation remains usable.

---

### **10.4.3 Scalability Scenarios**

#### **Scenario S1 — Multi-Robot Environment**

**Stimulus:** 10 robots connect to cloud MQTT broker.
**Response:** Backend routes telemetry based on robot_id.
**Measures:** No cross-robot data leakage.

---

#### **Scenario S2 — Multi-Operator UI**

**Stimulus:** 20 UIs open telemetry dashboard.
**Response:** Backend fans out WebSocket telemetry to all.
**Measures:** CPU <70% per instance.

---

#### **Scenario S3 — Cloud Run Auto-Scaling**

**Stimulus:** Spike in traffic.
**Response:** Cloud Run spins up more backend instances.
**Measures:** No loss of telemetry messages.

---

### **10.4.4 Developer Experience Scenarios**

#### **Scenario D1 — Local Setup**

**Stimulus:** Developer clones repo.
**Response:** System fully operational in <2 minutes.
**Measures:** Backend starts, UI loads, robot or simulator connects.

---

#### **Scenario D2 — Code Modification**

**Stimulus:** Developer updates backend logic.
**Response:** Hot reload or fast restart <1 second.

---

#### **Scenario D3 — Logging Clarity**

**Stimulus:** Error occurs in MQTT connection.
**Response:** Log shows human-readable message and recommended fix.

---

## **10.5 Quality Requirements Summary Table**

| Quality Attribute    | Requirement                                     |
| -------------------- | ----------------------------------------------- |
| Reliability          | Detect disconnects <2s, safe fallbacks          |
| Performance          | Latency <100ms local, <400ms cloud              |
| Developer Experience | Simple setup, modular architecture              |
| Scalability          | Multi-robot, multi-operator, cloud auto-scaling |
| Security (future)    | OAuth2, TLS, role-based control                 |

---

## **10.6 Mapping Quality to Architecture Strategy**

| Quality Goal   | Supported By                                         |
| -------------- | ---------------------------------------------------- |
| Reliability    | MQTT QoS, heartbeats, validation, watchdog           |
| Performance    | MQTT, WebSockets, async backend                      |
| Dev Experience | Python backend, simple architecture, logs            |
| Scalability    | Topic namespace, stateless backend, cloud deployment |
| Security       | OAuth2 (future), TLS, ACLs                           |

---

## **10.7 Quality Summary**

The system meets its quality goals through:

* Event-driven architecture
* Stateless backend design
* Lightweight real-time protocols
* Modular building blocks
* Clear separation of concerns
* Future-ready cloud strategy

---
# **11. Risks & Technical Debt**

We break risks into:

1. **Technical Risks**
2. **Operational Risks**
3. **Security Risks**
4. **Cloud & Deployment Risks**
5. **Technical Debt Items**
6. **Risk Matrix** (Probability × Impact)
7. **FMEA Table** (Failure Mode & Effects Analysis)

---

## **11.1 Technical Risks**

### **T1 — MQTT Broker Single Point of Failure (Local Mode)**

**Description:** Local Mosquitto broker fails → entire robot control system stops.
**Impact:** Very high
**Likelihood:** Medium

**Mitigation:**

* Run broker as system service
* Health checks and auto-restart
* Move to cloud MQTT in future
* Redundant broker instances for fleet mode

---

### **T2 — Robot Firmware or Connectivity Failure**

**Description:** Robot loses connectivity or fails to publish telemetry.
**Impact:** High
**Likelihood:** Medium

**Mitigation:**

* Heartbeat monitoring
* Watchdog in firmware
* Safe-stop mechanism

---

### **T3 — Backend Overload or Event Loop Blockage**

**Description:** Python backend overloaded or blocking on synchronous operations.
**Impact:** Medium
**Likelihood:** Medium

**Mitigation:**

* Use asyncio
* Avoid heavy synchronous I/O
* Cloud auto-scaling in future

---

### **T4 — WebSocket Fan-out Performance Limit**

**Description:** Multiple operator clients may overload backend WebSocket.
**Impact:** Medium
**Likelihood:** Medium

**Mitigation:**

* Introduce message bus (Redis Pub/Sub)
* Horizontal Cloud Run scaling
* Sharded WebSocket endpoints

---

### **T5 — Telemetry Dropping under High Load**

**Description:** Telemetry may overflow backend if robot publishes at high frequency.
**Impact:** Medium
**Likelihood:** Medium

**Mitigation:**

* Frame skipping
* Fixed max telemetry bandwidth
* Async queues

---

---

## **11.2 Operational Risks**

### **O1 — Network Instability in Hackathon Venue**

**Description:** Wi-Fi congestion impacts control communication.
**Impact:** High
**Likelihood:** High

**Mitigation:**

* Local-only mode
* Dedicated hotspot/router
* Reduce message frequencies

---

### **O2 — Multi-device Access Mismanagement**

**Description:** Multiple UIs sending commands simultaneously.
**Impact:** High
**Likelihood:** Medium

**Mitigation:**

* Role-based UI access ("Master Operator")
* Command mutex
* UI feedback enforcing operator control

---

### **O3 — Human Error Causes Unsafe Robot Behavior**

**Description:** Wrong command or rapid sequence of commands causes instability.
**Impact:** Very high
**Likelihood:** Medium

**Mitigation:**

* Rate limiting
* Command validation
* Safety boundaries in robot firmware

---

---

## **11.3 Security Risks**

(*Mostly future-focused since current deployment is local.*)

### **S1 — No Authentication (Local Mode)**

**Description:** Anyone on LAN can access UI.
**Impact:** Medium
**Likelihood:** Low

**Mitigation:**

* Move to authenticated mode when cloud-ready
* Protect local network

---

### **S2 — Unencrypted MQTT (Local)**

**Description:** MQTT traffic readable on LAN.
**Impact:** Medium
**Likelihood:** Low

**Mitigation:**

* TLS MQTT when cloud deployed
* Secure Wi-Fi network today

---

### **S3 — Robot Spoofing (Future Cloud Mode)**

**Description:** Unauthorized client spoofing robot identity in cloud.
**Impact:** Very high
**Likelihood:** Low

**Mitigation:**

* Robot certificates
* MQTT ACLs
* IAM-controlled topic permissions

---

---

## **11.4 Cloud & Deployment Risks (Future)**

### **C1 — Cloud Run Cold Starts**

**Description:** First request is slow.
**Impact:** Medium
**Likelihood:** Medium

**Mitigation:**

* Minimum instance count = 1
* Warmup routines

---

### **C2 — WebSocket Load Balancing Challenges**

**Description:** Stateless Cloud Run scaling can break WebSocket stickiness.
**Impact:** High
**Likelihood:** Medium

**Mitigation:**

* Use Cloud Run session affinity
* Or move to a managed WebSocket gateway in future

---

### **C3 — Global Latency Issues for R/C**

**Description:** Long physical distances increase roundtrip time.
**Impact:** High
**Likelihood:** Medium

**Mitigation:**

* Regional deployments
* Robot → nearest edge region
* Operator → region selection

---

## **11.5 Technical Debt Items**

### **D1 — No Authentication**

Current local mode intentionally omits auth.

**Impact:** Low (local), high (cloud).
**Must fix before cloud launch.**

---

### **D2 — Backend Not Yet Using Asyncio Everywhere**

Some parts may use threaded MQTT rather than full async.

**Impact:** Medium.
**Mitigation:** Migrate to full async architecture.**

---

### **D3 — No Automated Test Suite**

Currently relies on manual testing.

**Impact:** Medium.
**Mitigation:** Add unit + integration tests.

---

### **D4 — Robot Simulator Missing**

A simulator would help developers without robot hardware.

**Impact:** Medium.
**Mitigation:** Build a software simulator.

---

### **D5 — No persistent logs**

Local logs mostly console-based.

**Impact:** Low today; high for cloud ops.
**Mitigation:** Cloud Logging integration.

---

## **11.6 Risk Matrix (Probability × Impact)**

Scale:

* Probability: Low = 1, Medium = 2, High = 3
* Impact: Low = 1, Medium = 2, High = 3

| Risk ID | Description              | Probability | Impact | Risk Score |
| ------- | ------------------------ | ----------- | ------ | ---------- |
| T1      | MQTT SPOF                | 2           | 3      | **6**      |
| O1      | Wi-Fi instability        | 3           | 3      | **9**      |
| O3      | Unsafe commands          | 2           | 3      | **6**      |
| S3      | Robot spoofing (future)  | 1           | 3      | **3**      |
| C2      | WebSocket scaling issues | 2           | 3      | **6**      |
| D2      | Non-async backend code   | 2           | 2      | 4          |
| D3      | Missing tests            | 2           | 2      | 4          |

**Highest priority risks:**

* **Wi-Fi instability (9)**
* **MQTT broker SPOF (6)**
* **Unsafe human commands (6)**
* **WebSocket scaling (6)**

---

## **11.7 FMEA (Failure Mode & Effects Analysis)**

| Failure Mode         | Effect                | Severity | Cause                   | Detection          | Mitigation                       |
| -------------------- | --------------------- | -------- | ----------------------- | ------------------ | -------------------------------- |
| MQTT broker crash    | Full system down      | 9        | CPU spike, config error | Broker logs        | System service with auto-restart |
| Robot heartbeat lost | Robot unresponsive    | 8        | Wi-Fi drop              | Backend timeout    | Heartbeat, alerts, safe stop     |
| Invalid command sent | Unsafe robot behavior | 10       | UI bug, operator error  | Command validation | Safety limits + whitelist        |
| WebSocket disconnect | UI stops updating     | 6        | Network drop            | Ping/pong          | Auto reconnect                   |
| Cloud Run cold start | Initial lag           | 4        | Instance scaling down   | Logs, metrics      | Keep-min-instances=1             |
| Telemetry spam       | Backend overload      | 7        | Robot bug               | Monitoring         | Rate limiting                    |

Severity scored from 1–10.

---

## **11.8 Summary of Section 11**

The RCS system faces typical real-time robotics risks:

* Unstable networks
* MQTT broker reliance
* Operator safety concerns
* Scaling challenges
* Future security needs

Mitigation strategies are built directly into the architecture:

* Heartbeat + watchdog
* MQTT QoS
* Local-first architecture
* Stateless backend
* WebSockets + validation
* Future TLS and OAuth2

---
# **12. Glossary**

---

## **A**

### **ADR (Architecture Decision Record)**

A structured document capturing a major architectural decision, alternatives, and rationale.

### **API (Application Programming Interface)**

Defined interface allowing communication between software modules.

### **Async / Asynchronous**

A programming model where operations run concurrently without blocking. Essential for real-time robot control.

---

## **B**

### **Backend**

Server-side component responsible for command validation, telemetry routing, and UI communication.

### **Broker (MQTT Broker)**

A messaging server that handles publish/subscribe communication between robot, backend, and services.

### **Build Artifact**

Compiled output (e.g., UI build bundle, Docker image) used in deployment.

---

## **C**

### **Cloud Run**

Google Cloud service for running stateless containers with auto-scaling.

### **Command (Robot Command)**

Instruction sent from backend to robot for motion, posture, or system control.

### **Configuration Management**

Approach for handling environment variables, endpoints, and dynamic system settings.

### **Container**

A packaged runtime environment (e.g., Docker) used for cloud deployment.

### **CQRS (Command Query Responsibility Segregation)**

(Not implemented but useful) pattern separating read and write operations for scalability.

---

## **D**

### **Dashboard**

The UI page used by operators to view telemetry and control the robot.

### **DevOps**

Practices involving continuous integration, deployment, and monitoring of the system.

### **DNS (Domain Name System)**

Resolves hostnames to IPs; relevant when UI and backend run in cloud.

---

## **E**

### **Event-driven Architecture**

System design where actions are triggered by incoming data/telemetry events.

### **E-stop (Emergency Stop)**

A safety command that stops the robot instantly. Highest priority command.

---

## **F**

### **FMEA (Failure Mode & Effects Analysis)**

Structured method for identifying system failures, causes, and mitigations.

### **Firebase Hosting**

Google service used to host static web applications.

### **Fleet Management**

Future capability for managing and monitoring multiple robots at scale.

---

## **G**

### **GCP (Google Cloud Platform)**

Cloud provider used for future backend and UI deployment.

### **Git**

Version control system used for tracking changes to code.

### **Graceful Disconnect**

When a client intentionally closes WebSocket or MQTT connections.

---

## **H**

### **Heartbeat**

Periodic message sent by robot to indicate active connection.

### **Hybrid Cloud**

Architecture where UI and backend run in cloud but robot/MQTT remain local.

---

## **I**

### **IAM (Identity and Access Management)**

Google Cloud's authentication and permission system.

### **IoT (Internet of Things)**

Devices like robots interacting over networks.

---

## **J**

### **Joint Angle**

Position of robot joints (arms, legs, head) used in telemetry.

---

## **K**

### **Kinematics**

Mathematical model describing robot motion and positions.

---

## **L**

### **Latency**

Delay between sending a command and observing robot response.

### **Local Deployment**

Mode where everything runs on a single machine (no cloud dependency).

---

## **M**

### **MQTT (Message Queuing Telemetry Transport)**

Lightweight publish/subscribe protocol used for telemetry and robot commands.

### **Mosquitto**

Open-source MQTT broker used in local deployment.

### **Multi-robot Architecture**

Future design supporting multiple robots with unique topics and IDs.

---

## **N**

### **Namespace (MQTT Topic Namespace)**

Hierarchical structure of topics to support multi-robot architecture.
Example:

```
robots/<robot_id>/telemetry
```

### **NAT Traversal**

Process required for robots behind routers to connect to cloud services.

---

## **O**

### **Operator**

Human user controlling the robot through the dashboard.

### **Open Source**

Technologies freely available without licensing costs (Python, Mosquitto, etc.).

---

## **P**

### **Performance Envelope**

Set of limits under which robot operates safely (speed, torque, frequency).

### **Pub/Sub (Publish/Subscribe)**

Messaging pattern used by MQTT.

---

## **Q**

### **QoS (Quality of Service)**

MQTT feature defining message delivery guarantees:

* QoS0: At most once
* QoS1: At least once
* QoS2: Exactly once

---

## **R**

### **Real-time Control**

Capability of controlling robot with minimal latency.

### **REST**

HTTP-based API style (not used for robot communication).

### **Runtime View**

arc42 section describing dynamic behavior of the system.

---

## **S**

### **Safety Boundaries**

Limits that prevent unsafe robot behaviors (max speed, max angles, etc.)

### **Scalability**

Ability to support more robots, users, or cloud instances without degradation.

### **Stateless Backend**

Backend that holds no persistent session data, enabling cloud scaling.

---

## **T**

### **Telemetry**

Sensor and status data sent from robot to backend/UI.

### **Topic**

MQTT channel used for message routing.

### **Technical Debt**

Known limitations or shortcuts that must be addressed in future.

---

## **U**

### **UI (User Interface)**

Frontend application for monitoring and controlling the robot.

### **UDP**

Not used, but relevant in other robotics systems (low-latency networking).

---

## **V**

### **Vite**

Frontend build tool used for rapid development.

### **Virtual Robot Simulator**

Future tool for testing without physical robot hardware.

---

## **W**

### **WebSocket**

Protocol for real-time client/server communication used by UI/backend.

### **Watchdog**

Mechanism ensuring system detects failures or timeouts quickly.

---

## **X, Y, Z**

### *(None currently relevant, placeholders reserved for future domain terms)*

---
