# **Project Aether: Architectural Roadmap for Real-Time Deep Reinforcement Learning in Stochastic Survival Simulations**

## **Executive Summary**

This report establishes the technical framework for **"Project Aether,"** an initiative to engineer autonomous AI agents capable of mastering *RimWorld*. Unlike previous iterations focused solely on step-locked training, this roadmap targets a **Real-Time Hybrid Architecture**. The objective is to develop an "Archotech" intelligence that operates under realistic time constraints, balancing long-term strategic planning with immediate tactical reflexes.

The architecture fuses low-level C\# systems engineering with high-level Pythonic deep learning. It addresses the critical challenge of **"Frame Slip"**—where the simulation advances while the agent "thinks"—by implementing a **Hierarchical Control System** and an **Intent-Based Action API**. Furthermore, it adopts an "Organ Transplant" development strategy, integrating high-fidelity data extraction logic from the *RIMAPI* project into a lightweight, high-performance TCP/Protobuf bridge.

## **1\. Theoretical Framework: The Real-Time Constraint**

### **1.1 The Challenge of Continuous Time**

Standard RL environments (Atari, AlphaGo) are "Stop-and-Go": the world freezes until the agent acts. *RimWorld*, however, is a continuous simulation. In a deployment (inference) scenario, the game runs at 60 FPS. If the agent takes 100ms to process a frame, the world has advanced by \~6 ticks.

* **The "Time Budget":** Computation time is a resource. A decision that takes too long to compute may be obsolete by the time it is issued.  
* **Stochastic Latency:** Raiders do not wait for the agent to finish its forward pass. The architecture must handle "noisy" or "outdated" observations.

### **1.2 The "Colony Executive" Persona**

To handle this, we reject the "Puppeteer" model (micromanaging every tick) in favor of the **"Colony Executive"** model.

* **Macro-Decisions (Python):** The external agent issues high-level directives ("Prioritize: Defense," "Blueprint: Killbox A") every 0.5s – 2.0s.  
* **Micro-Execution (C\#):** The game's native AI (JobDrivers) handles the immediate execution (pathfinding, shooting, eating) frame-by-frame.

## **2\. The RimWorld Engine: A Technical Autopsy**

### **2.1 The "Hybrid Valve" Tick Lifecycle**

To support both accelerated training and realistic inference, the C\# Bridge (TickPatch.cs) must implement a **Dual-Mode Valve**:

1. **Training Mode (Synchronous):** The TickManager is strictly hijacked. The game pauses every $N$ ticks and waits for a STEP command. This ensures data purity and perfect reproducibility for RL training.  
2. **Inference Mode (Asynchronous):** The TickManager runs freely. The Bridge serves QUERY\_STATE requests on demand without blocking the game. This tests the agent's ability to survive in a chaotic, real-time environment.

### **2.2 The Main Thread Dispatcher**

Unity forbids background threads from touching game objects.

* **The Bottleneck:** The TCP Listener runs on a background thread.  
* **The Solution:** A thread-safe **Action Queue**. Incoming commands are pushed to a ConcurrentQueue\<Action\>. A Harmony patch on Verse.Root.Update() consumes this queue once per frame, executing valid actions and discarding invalid ones (e.g., target died while agent was thinking).

## **3\. The Bridge Architecture: System Integration**

### **3.1 The "Organ Transplant" Strategy**

Instead of reinventing data extraction, we integrate the robust memory-reading logic from the *RIMAPI* project into our lightweight RimworldMLBridge.

* **Source:** *RIMAPI* Services/ (e.g., ColonistService.cs, MapService.cs).  
* **Refactoring:** We strip the HTTP/JSON layers. The services will return raw C\# DTOs (Data Transfer Objects).  
* **Translation:** A new ProtobufAdapter class maps these C\# DTOs directly to our binary StateMessage, ensuring $\<1$ms serialization time.

### **3.2 Protocol Design (TCP \+ UDP)**

We utilize a dual-socket approach to separate logic from bandwidth-heavy visuals.

**Socket A: Control & Logic (TCP Port 50051\)**

* **Format:** Google Protocol Buffers (Protobuf).  
* **Traffic:** State Tensors, Entity Lists, Semantic Actions.  
* **Latency:** Critical (Nagle's Algorithm Disabled).

**Socket B: Visual Stream (UDP Port 5007\)** (Optional)

* **Format:** Raw JPEG chunks (Ported from *RIMAPI* UdpCameraStreamer).  
* **Traffic:** Rendered frames for human spectators or CNN-based visual analysis.  
* **Reliability:** Fire-and-forget (packet loss is acceptable).

## **4\. State Space Engineering: The "Streamed" World**

### **4.1 The Semantic Tensor**

The map is represented as a $C \\times H \\times W$ tensor (Terrain, Buildings, Items) constructed via the ported MapService.

* **Optimization:** In Real-Time mode, we cannot resend the full grid every tick. We implement **Delta Compression**, sending only cells that changed (e.g., walls destroyed, items spawned) since the last frame ID.

### **4.2 Handling Latency "Blind Spots"**

Since the agent's observation $O\_t$ is always slightly older than the current game state $S\_{t+\\Delta}$, the State Vector includes a **Timestamp** and **Velocity Vectors** for all moving entities. This allows the Python agent to "extrapolate" where a raider might be when the command arrives.

## **5\. Action Space: Intent Over Coordinates**

### **5.1 Semantic Intents**

In a real-time environment, coordinate-based actions (Click at 10,15) are fragile. By the time the click registers, the target might have moved.  
The Solution: Intent-Based Actions.

* *Fragile:* Action: Attack(10, 15\)  
* *Robust:* Action: ExecuteJob(Type=Attack, TargetThingID=402)

### **5.2 Server-Side Validation & Auto-Correction**

The C\# Bridge performs a "Sanity Check" before executing any queued action:

* *Is the pawn still drafted?*  
* *Is the target still alive?*  
* Is the path reachable?  
  Failure Handling: If an action is invalid due to lag, the Bridge sends a FAILURE\_SIGNAL event, prompting the agent to replan immediately, rather than crashing the simulation.

### **5.3 Interrupt Events (Red Alerts)**

Long-term planning (e.g., "Build Base") must be interruptible. The Bridge pushes **High-Priority Events** (Raid, Fire, Mental Break) immediately. The Agent architecture must support "Preemption," discarding the current plan to enter a "Combat Mode."

## **6\. Agent Architecture: The Triple-Threaded Client**

To decouple inference time from game speed, the Python client (SpectatorClient.py) adopts a parallel architecture:

1. **Listener Thread (60Hz):**  
   * Polls QUERY\_STATE constantly.  
   * Updates a local "World Model" (latest known state).  
   * Buffers "Reward Signals."  
2. **Inference Thread (Variable Hz):**  
   * Samples the World Model.  
   * Runs the Transformer/LSTM Policy.  
   * This thread can take 50ms or 500ms without freezing the game.  
3. **Actor Thread:**  
   * Receives intents from the Inference Thread.  
   * Pushes EXECUTE\_ACTION commands to the TCP socket.

## **7\. Curriculum & Operations**

### **7.1 The Training vs. Inference Split**

* **Training:** Uses **Synchronous Mode** (Tick Hijacking). We prioritize sample efficiency. The agent learns "perfect" strategy without lag noise.  
* **Fine-Tuning:** Uses **Asynchronous Mode** (Real-Time). We introduce artificial lag and frame slip to robustify the policy against timing errors.

### **7.2 Infrastructure**

* **Docker:** Containerized *RimWorld* instances.  
* **Ray RLLib:** Distributed training.  
* **Version Control:** "Frozen" Game Version to prevent mod breakage.

## **8\. Strategic Roadmap Steps**

1. **Phase I: The Skeleton (Complete)**  
   * TCP/Protobuf Server operational.  
   * Basic Tick Hijacking operational.  
2. **Phase II: The Organ Transplant (Current Priority)**  
   * Port Services/ from *RIMAPI* to *RimworldMLBridge*.  
   * Implement ProtobufAdapter to serialize complex DTOs.  
   * Implement "Intent-Based" Action definition in Protobuf.  
3. **Phase III: The Hybrid Valve**  
   * Implement AsyncMode toggle in C\#.  
   * Implement the Thread-Safe ActionQueue in Harmony Update patch.  
4. **Phase IV: The Triple-Threaded Brain**  
   * Develop SpectatorClient.py for asynchronous inference.  
   * Train initial hierarchical policy (Executive/Reflex).

## **9\. Conclusion**

This updated roadmap acknowledges that *RimWorld* is a living, breathing system. By moving from a rigid, step-locked architecture to a flexible, intent-based real-time architecture, Project Aether aims to create AI that doesn't just "solve" a puzzle, but dynamically survives in a chaotic, unfolding story.