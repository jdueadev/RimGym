# **Implementation Handoff Plan: Project "RimGym"**

Target Actor: Autonomous Coding Agent / Dev  
Objective: Establish a Reinforcement Learning interface ("RimGym") for RimWorld by bridging the C\# game engine with a Python training loop.  
Tech Stack: \* Game/Mod: C\# (.NET Framework 4.7.2), Harmony Library, Unity Engine.

* **ML/Client:** Python 3.11+, PyTorch, Stable Baselines 3, uv (dependency management).  
* **Infrastructure:** Docker, Xvfb (Headless Display).

## **Phase 1: C\# Mod Development (The "Server")**

**Goal:** Inject code into the RimWorld Assembly-CSharp.dll to pause execution, export state, and await actions.

### **Task 1.1: Solution Scaffolding**

* **Action:** Create a .NET Framework 4.7.2 Class Library project in /src-mod/.  
* **References:** Add references to Assembly-CSharp.dll, UnityEngine.dll, and 0Harmony.dll (assume local paths in /resources/ for build).

### **Task 1.2: State Serialization (MemoryMappedFiles)**

Implement StateWriter.cs.

* **Logic:**  
  1. Initialize a MemoryMappedFile named RimWorld\_State\_Shm of size 10MB (approximate for 250x250 map tensors).  
  2. Define a byte structure: \[Header: Tick(int), Wealth(float), Mood(float)\] \[Body: MapTensor(byte\[\])\].  
  3. Implement WriteState(Map map): Serialize the current map's terrain and thing grids into the byte array.

### **Task 1.3: The Harmony Patch (Game Loop Hook)**

Implement GameLoopPatch.cs.

* **Target Method:** Verse.TickManager.DoSingleTick  
* **Logic:**  
  1. Use a Postfix patch.  
  2. Check GenTicks.TicksGame % STEP\_INTERVAL \== 0 (e.g., every 60 ticks).  
  3. If true:  
     * Call StateWriter.WriteState().  
     * **Blocking Call:** Open a TCP Socket listener on port 5000\.  
     * Wait for an incoming byte (Action ID) from the Python client.  
     * Decode Action ID and execute ActionExecutor.Execute(actionId).  
     * Resume game execution.

### **Task 1.4: Action Execution**

Implement ActionExecutor.cs.

* **Logic:**  
  * Map integer IDs to game functions.  
  * *Example:*  
    * Action 0: Do nothing.  
    * Action 1: Change game speed to Speed 3\.  
    * Action 2: Designate "Hunt" on nearest animal.  
  * Use Verse.AI.JobMaker and Pawn.jobs.TryTakeOrderedJob to force execution.

## **Phase 2: Python Client Development (The "Client")**

**Goal:** Create a Gym-compliant wrapper that treats the running game as an environment.

### **Task 2.1: The Gym Wrapper**

Create file /src-python/rimgym/env.py.

* **Class:** RimWorldEnv(gym.Env)  
* **\_\_init\_\_**:  
  * Connect to MemoryMappedFile RimWorld\_State\_Shm.  
  * Define self.observation\_space (Box shape matching the map tensor).  
  * Define self.action\_space (Discrete or MultiDiscrete).  
* **reset()**:  
  * Send TCP signal to "Reload Save" or "Restart Scenario".  
  * Read initial state from SHM.  
* **step(action)**:  
  * Send action via TCP socket to port 5000\.  
  * Wait for acknowledgement (handled by blocking socket).  
  * Read new state from SHM.  
  * Calculate Reward: R \= (CurrentTick \- StartTick) \+ (DeltaWealth \* 0.1).  
  * Check Done: if Mood \< Threshold or ColonyIsDead.

## **Phase 3: Infrastructure & Headless Execution**

**Goal:** Run the game inside a container without a GPU/Monitor to scale training.

### **Task 3.1: Dockerfile**

Create /docker/Dockerfile.

* **Base:** ubuntu:22.04  
* **Dependencies:**  
  * xvfb (X Virtual Framebuffer).  
  * wine (compatibility layer) or native dependencies if using Linux native build.  
  * python3, uv.  
* **Command:**  
  CMD xvfb-run \--auto-servernum \--server-args='-screen 0 1024x768x24' \\  
      ./RimWorldLinux \-batchmode \-nographics \-quicktest \-mod:RimGym

### **Task 3.2: Launch Script**

Create train.py in /src-python/training/.

* **Logic:**  
  1. Subprocess: Launch Docker container (or local game executable).  
  2. Wait for TCP handshake (Game loaded).  
  3. Initialize RimWorldEnv.  
  4. Initialize PPO model from Stable Baselines 3\.  
  5. model.learn(total\_timesteps=1\_000\_000).

## **Phase 4: Validation Criteria (Definition of Done)**

1. **Handshake Test:** Python script launches game, connects to socket, and receives "Ready" signal.  
2. **State Test:** Python script reads SHM and successfully reconstructs a numpy array representing the map terrain.  
3. **Action Test:** Python script sends "Pause" command, and game execution halts visibly.  
4. **Loop Test:** Agent runs for 1000 steps selecting random actions without crashing the C\# thread.