# **Project Aether: Architectural Roadmap for Deep Reinforcement Learning in Stochastic Survival Simulations**

## **Executive Summary**

This report establishes a comprehensive technical framework and development roadmap for "Project Aether," an initiative to engineer autonomous Artificial Intelligence (AI) agents capable of mastering *RimWorld*. Unlike finite board games or twitch-based shooters, *RimWorld* represents a class of "Deep Simulation" environments characterized by high-dimensional state spaces, emergent narrative mechanics, and extreme time horizons. The objective is to transcend simple automation, developing an agent capable of long-term strategic planning, colony management, and crisis mitigation in a stochastic environment.

The roadmap delineates a multidisciplinary approach, fusing low-level C\# systems engineering—required to instrument the Unity-based game engine—with high-level Pythonic deep learning architectures. It addresses critical technical hurdles, including the absence of a native machine learning API, the single-threaded constraints of the Unity engine, the complexity of the FloatMenu action interface, and the necessity of "Headless" rendering for scalable training.

By leveraging state-of-the-art techniques in Hierarchical Reinforcement Learning (HRL), Transformer-based entity processing, and Curriculum Learning derived from "Naked Brutality" survival protocols, Project Aether aims to create an "Archotech" intelligence: an AI that does not merely play the game but understands the causal tapestry of the simulation.

## ---

**1\. Theoretical Framework and Domain Analysis**

### **1.1 The Challenge of Deep Simulation**

*RimWorld* is not merely a game; it is a story generator powered by a complex, interlocking simulation of psychology, ecology, and physics. For a Reinforcement Learning (RL) agent, this presents a "Grand Challenge" distinct from standard benchmarks like Atari or StarCraft II.

In environments like *StarCraft II* (AlphaStar), the objective is zero-sum domination over a discrete duration (20–40 minutes).1 The reward signal (Win/Loss) is delayed but definitive. In *RimWorld*, the objective is indefinite survival. The time horizon stretches to tens of hours (hundreds of thousands of ticks), and failure is often the result of a "death spiral"—a cascading series of seemingly minor decisions made hours prior.3 A decision to neglect cleaning dirt in the kitchen (Day 1\) leads to food poisoning (Day 2), which causes a mental break during a raid (Day 3), resulting in colony collapse.

This "Credit Assignment Problem" is exacerbated by the "Storyteller" system (e.g., Cassandra Classic, Randy Random), which acts as an adversarial meta-agent injecting stochastic entropy (raids, solar flares, disease) into the environment.4 The agent must therefore learn robust generalizable policies rather than memorizing seed-specific sequences.

### **1.2 The "Persona" of the Agent**

The architecture described herein does not aim to mimic human mouse movements (which would require processing 1080p video streams). Instead, it adopts the persona of the **Colony Executive**. The agent interacts with the game at the semantic level: inspecting memory states directly and issuing high-level directives (JobDrivers and Designators) rather than raw inputs. This aligns with the "Overmind" architecture used in OpenAI Five, treating the colony as a distributed organism where the central policy dictates strategy while individual units (pawns) execute semi-autonomous pathfinding and interaction logic.5

### **1.3 Technical Constraints and Opportunities**

The primary constraint is the technical architecture of *RimWorld* itself. Built on the Unity Engine (version 2019/2020 era), it relies heavily on a main-thread loop for all logic and data manipulation. Accessing game state from external processes (like a Python training loop) requires a custom IPC (Inter-Process Communication) bridge. While projects like RIMAPI 7 provide REST endpoints, their HTTP-based nature is insufficient for the high-frequency (\~1000 TPS) throughput required for RL. Project Aether mandates a custom, high-performance TCP socket layer injected directly into the game assembly via Harmony patching (RimTCP).

## ---

**2\. The RimWorld Engine: A Technical Autopsy**

To control the simulation, one must first understand its internal physiology. *RimWorld*’s codebase is a hybrid of the Unity MonoBehaviour lifecycle and a custom simulation loop built on the Verse and RimWorld namespaces.9

### **2.1 The Data Hierarchy: Defs and Things**

The game splits data into two primary categories: **Definitions (Defs)** and **Things**.

* **Defs (Immutable):** Loaded at startup from XML, Defs define the templates for everything in the universe—ThingDef (items), TerrainDef (floors), JobDef (actions). An RL agent must index these Defs to understand the semantic meaning of objects (e.g., knowing that ID \#402 corresponds to "Rice," which is edible).9  
* **Things (Mutable):** Instances of Defs existing in the game world. A Pawn is a Thing with complex components (Pawn\_HealthTracker, Pawn\_MindState, Pawn\_JobTracker). The agent’s observation space is essentially a serialization of these Thing objects.

### **2.2 The Tick Lifecycle**

Time in *RimWorld* is discrete, measured in Ticks (60 ticks \= 1 real-time second at 1x speed). The TickManager controls the flow of time.

* **TickManager.DoSingleTick():** This method advances the simulation by one quantum. It iterates through all active maps, ticking MapComponents, Things (pawns, plants), and WorldObjects.  
* **Implication for RL:** We cannot rely on the game’s internal "Play/Pause" buttons. To ensure deterministic training, the C\# Bridge must **hijack the Tick Loop**. The game must be strictly paused (TickManager.paused \= true), and only advanced when the RL agent sends a Step command. The Bridge then forces a specific number of ticks (e.g., 60 ticks) via DoSingleTick() before freezing the state again and returning observations. This ensures the agent experiences a consistent flow of time regardless of the host machine's computational load.10

### **2.3 The Single-Threaded Bottleneck**

Unity prohibits accessing UnityEngine objects (transforms, meshes) from background threads.11 *RimWorld* follows this pattern; modification of the Game object or Map data must occur on the main thread.

* **The Danger:** A naive socket server running on a background thread attempting to read Pawn.Position will cause a race condition or immediate crash.  
* **The Solution:** We must implement a **Main Thread Dispatcher**. The socket listener (background thread) receives the Action Packet, validates it, and pushes it to a thread-safe ConcurrentQueue. A Harmony patch on Verse.Root.Update() checks this queue every frame. If an action is pending, the main thread consumes it, executes the logic, and pushes the resulting state back to the socket writer.13

### **2.4 The LongEventHandler**

Loading maps, generating worlds, and spawning colonies are asynchronous operations managed by Verse.LongEventHandler.15

* **Requirement:** The RL agent must wait for LongEventHandler.ShouldWaitForEvent to be false before attempting to interact with the world. Attempting to read the map state while a LongEvent is processing (e.g., "Generating Map...") will result in null reference exceptions or partial state data.16 The Bridge must expose a Status flag indicating whether the game is Ready, Loading, or Generating.

## ---

**3\. The Bridge Architecture: C\# Systems Engineering**

The "Bridge" is the middleware connecting the compiled.NET assemblies of *RimWorld* to the Python-based training environment (PyTorch/Ray).

### **3.1 Network Protocol Design**

JSON is too verbose and CPU-intensive for the required throughput. We will utilize **Protocol Buffers (Protobuf)**, which offers a strongly-typed, binary serialization format that is compact and fast to parse.

**Table 1: Proposed Protocol Buffer Schema**

| Packet Type | Field | Data Type | Description |
| :---- | :---- | :---- | :---- |
| **Command** | type | Enum | RESET, STEP, QUERY\_STATE, NO\_OP |
|  | ticks\_to\_run | int32 | Number of ticks to advance (e.g., 60). |
|  | actions | repeated Action | List of actions for specific pawns. |
| **Action** | agent\_id | int32 | The thingID of the pawn. |
|  | verb | Enum | DRAFT, GOTO, ATTACK, BUILD, JOB\_PRIORITY |
|  | target | int32 | thingID of target entity (enemy, item). |
|  | cell | Vector3 | Target map coordinates $(x, y, z)$. |
| **State** | frame\_id | int64 | Current game tick. |
|  | global | GlobalState | Wealth, Weather, Date, Research progress. |
|  | map\_layers | repeated Bytes | RLE-compressed byte arrays for terrain grids. |
|  | entities | repeated Entity | List of pawns, items, and buildings. |

### **3.2 The Socket Server Implementation**

The Bridge Mod initiates a TcpListener on port 5000 upon game startup.

* **Connection Handling:** The server accepts a single persistent connection from the Python client. Re-connection logic must be robust to handle Python process crashes without crashing the game.18  
* **Non-Blocking I/O:** The listener runs on a Task.Run() background thread to avoid freezing the Unity window (which would trigger OS "Application Not Responding" warnings).  
* **Performance:** TcpNoDelay (Nagle's Algorithm disabled) must be set to true to minimize latency for small packets.20

### **3.3 Harmony Patching Strategy**

We utilize Harmony (v2.x) to inject the Bridge hooks into the game lifecycle.21

1. **Verse.Root\_Play.Update**: This is the main game loop. We postfix this method to check the ConcurrentQueue for incoming actions from the socket thread.  
   C\#  
   public static class UpdatePatch {  
       public static void Postfix() {  
           Dispatcher.ExecutePendingActions();  
       }  
   }

2. **Verse.TickManager.DoSingleTick**: We utilize a **Prefix** patch here. If the RL agent has not requested a step, we return false to skip the original method, effectively pausing the game logic without pausing the UI thread (which keeps the socket listener alive).10  
3. **Verse.Log.Error**: We patch the logging system to intercept errors. In vanilla *RimWorld*, an error might pause the game or open a debug window. For RL training, errors must be captured, logged to a text file, and the simulation must continue (or terminate the episode if critical) without UI interruption.23

### **3.4 Headless Rendering Optimization**

Training performance is bound by the render loop. Even if we don't look at the screen, Unity prepares frames.

* **Batchmode:** Launching with \-batchmode \-nographics is the standard Unity approach.24 However, *RimWorld* may crash if it attempts to load shader assets in this mode.  
* **Phantom Display Issue:** On certain server hardware (especially without GPUs), Unity might fail to initialize a graphics context or create a "phantom display" that consumes resources.26  
* **The "Null Renderer" Patch:** A more robust solution is to patch UIRoot.UIRootUpdate and Verse.MapInterface.MapInterfaceUpdate to simply return immediately. This bypasses the code that generates draw calls, effectively creating a logic-only simulation loop. We can also patch FogGrid to skip mesh regeneration, as the agent accesses the data array directly.27

## ---

**4\. State Space Engineering: From Pixels to Tensors**

The *RimWorld* map is a grid (typically 200x200 to 250x250 cells). Passing this as raw pixels is inefficient and loses semantic clarity. We construct a **Semantic Tensor** representation.

### **4.1 The Map Tensor**

The map is represented as a $C \\times H \\times W$ tensor, where $C$ is the number of channels.

* **Channel 0 (Terrain):** Categorical ID of the TerrainDef (e.g., Soil=1, Water=2, Stone=3).  
* **Channel 1 (Edifice):** Categorical ID of the building/structure on the tile (Wall=1, Door=2, Turret=3).  
* **Channel 2 (Items):** Categorical ID of loose items (Wood=1, Meal=2, Weapon=3).  
* **Channel 3 (Filth/Beauty):** Continuous value $\[-1, 1\]$ representing the tile's beauty. (Critical for pawn mood).  
* **Channel 4 (Passability):** Boolean mask (0=Blocked, 1=Walkable).  
* **Channel 5 (Fog):** Boolean mask (0=Visible, 1=Fogged/Unexplored).28

**Compression Strategy:** Since most of the map is static (terrain doesn't change often), we can optimize bandwidth by only sending *deltas* (changes) or by using heavy compression (Zlib) on the serialized byte arrays.29

### **4.2 Entity Embeddings**

Pawns are too complex to be represented solely on the grid. They require a separate feature vector, processed by a Transformer or fully connected network.31

* **Identity:** FactionID (Colony vs Enemy), PawnID.  
* **Vitals:** Health (0-1), Pain, BleedRate.  
* **Needs:** Mood, Food, Rest, Recreation, Comfort, Outdoors.  
* **Skills:** Vector of 12 integers (Shooting, Melee, Construction, Cooking, etc.).  
* **Gear:** WeaponDefID, ApparelScore.  
* **Social:** A small adjacency matrix or embedding representing relationships (Spouse, Rival, Parent) which impacts social fighting logic.32

### **4.3 Handling Hidden Information**

*RimWorld* features a "Fog of War" (unrevealed areas, hidden raids). The RL agent should respect this to learn exploration. The C\# Bridge must query the FogGrid.27 If FogGrid.IsFogged(cell) is true, the corresponding data in the Terrain/Edifice channels must be masked (set to 0 or a specialized "Unknown" token). This forces the agent to perform actions that reveal the map (mining, moving).

## ---

**5\. Action Space Engineering: The Interface of Agency**

Defining how the agent interacts with the world is the most complex design decision. We move away from mouse emulation toward **Function Calling**.

### **5.1 The FloatMenu Dilemma**

In *RimWorld*, players interact by right-clicking a target. The game generates a FloatMenu containing context-sensitive options (e.g., "Prioritize Refueling Generator").

* **The Challenge:** The list of options is generated dynamically based on the pawn's capabilities, the target's state, and current reservations.  
* **The Engineering Solution:** We must reverse-engineer FloatMenuMakerMap.ChoicesAtFor.33  
  * The Bridge mod will programmatically call FloatMenuMakerMap.ChoicesAtFor(Vector3 clickPos, Pawn pawn) on the main thread.  
  * Instead of drawing the UI, we capture the list of FloatMenuOption objects.  
  * We extract the label (e.g., "Strip Corpse") and the underlying Action delegate.  
  * We expose these "Potential Actions" to the RL agent as a discrete list.  
  * *Note:* This approach is computationally expensive. A more optimized approach is to implement specific JobDrivers directly.

### **5.2 Direct Job Instantiation**

A more robust method is to bypass the menu and instantiate Jobs directly.

* **Job System:** *RimWorld* pawns execute Jobs. A Job consists of a JobDef (e.g., AttackMelee) and a TargetA (and optional TargetB).10  
* **Implementation:**  
  C\#  
  // C\# Bridge Code  
  public void ExecuteJob(Pawn pawn, string jobDefName, Thing target) {  
      JobDef def \= DefDatabase\<JobDef\>.GetNamed(jobDefName);  
      Job job \= JobMaker.MakeJob(def, target);  
      pawn.jobs.TryTakeOrderedJob(job, JobTag.Misc);  
  }

* **RL Output:** The agent outputs a Tuple: (PawnIndex, JobType, TargetIndex).  
  * JobType: Categorical (Wait, Goto, Attack, Haul, Clean, Build).  
  * TargetIndex: The ThingID from the Entity list.

### **5.3 Hierarchical Action Space**

To manage the combinatorial explosion of actions, we employ a hierarchical structure:

1. **Macro-Controller:** Selects the "Mode" for the pawn (Combat, Labor, Rest, Schedule).  
2. **Micro-Controller:**  
   * *If Combat:* Outputs (MoveToCell, AttackTarget).  
   * *If Labor:* Outputs (WorkType, Priority).  
   * *If Build:* Outputs (BuildDef, CellLocation).

This splits the learning problem. The "Combat Net" learns cover usage and kiting. The "Labor Net" learns optimal work priorities (Cooking \> Cleaning).31

---

## **6\. Agent Architecture: The "Archotech"**

We propose a **Transformer-based Actor-Critic** architecture, inspired by AlphaStar and OpenAI Five, to handle the variable number of entities and long-term dependencies.

### **6.1 Network Topology**

**Table 2: Neural Network Architecture Specifications**

| Component | Input Dimensions | Architecture | Output |
| :---- | :---- | :---- | :---- |
| **Map Encoder** | $250 \\times 250 \\times 6$ | ResNet-18 (Custom Stride) | $16 \\times 16 \\times 256$ Spatial Embeddings |
| **Entity Encoder** | $N\_{pawns} \\times 128$ | Shared MLP (3 layers) | $N\_{pawns} \\times 64$ Entity Embeddings |
| **Memory Core** | $1024$ (Fused Features) | LSTM or Transformer-XL | $512$ Context Vector (Hidden State) |
| **Policy Head** | Context Vector | Multi-Head Attention | Probability dist. over Actions |
| **Value Head** | Context Vector | MLP (2 layers) | Scalar Value Estimate $V(s)$ |

### **6.2 The Attention Mechanism**

The core innovation is using **Self-Attention** to process the Entity List.

* **Problem:** The number of raiders, colonists, and items changes constantly.  
* **Solution:** A Transformer encoder processes the list of all entities (pawns \+ enemies). It computes attention weights determining which entities are relevant to each other (e.g., a "Doctor" pawn pays high attention to a "Bleeding" pawn). This makes the policy invariant to the number of units.1

### **6.3 Memory and LSTM**

*RimWorld* requires long-term memory. A raid might be triggered by high wealth accumulation days prior. An LSTM (Long Short-Term Memory) layer maintains a history of the colony's state, allowing the agent to infer hidden variables (e.g., "The Storyteller hasn't sent a raid in 10 days, one is likely imminent").1

## ---

**7\. The Curriculum of Survival: Learning to Live**

Training from scratch on a full game is impossible due to the sparsity of rewards. We utilize **Curriculum Learning**, structured around the "Naked Brutality" survival guide.38

### **Stage 1: The Maslow Foundation (Survival)**

* **Scenario:** Single pawn, Naked Brutality, Small Map, No Raids, Permanent Summer.  
* **Objective:** Maintain Food and Rest bars \> 0\.  
* **Action Set:** Harvest(Berry), Eat, Sleep, ChopWood, Build(Wall/Door/Bed).  
* **Reward Shaping:**  
  * $+1$ for eating when hungry.  
  * $+1$ for sleeping in a bed (vs on floor).  
  * $-10$ for Malnutrition hediff.  
  * $-100$ for Death.  
* **Success Metric:** Survive 10 Days without Malnutrition.

### **Stage 2: The Engineer (Construction & Production)**

* **Scenario:** Add Winter season.  
* **Objective:** Build a heated room and cook food.  
* **Action Set:** Add Build(Campfire), Cook(Stove), Sow(Rice).  
* **Reward Shaping:**  
  * $+5$ for maintaining room temperature $21^\\circ C$.  
  * $+2$ for eating *Cooked* meals (requires successfully building stove \+ cooking job).  
  * Penalty for "Ate Raw Food" mood debuff.  
* **Success Metric:** Survive Winter.

### **Stage 3: The Warlord (Combat & Defense)**

* **Scenario:** Enable "Raids" (1 enemy with club).  
* **Objective:** Defeat raider without taking damage.  
* **Action Set:** Draft, Attack, Move (Kiting mechanics).  
* **Reward Shaping:**  
  * $+10$ for reducing enemy health.  
  * $-10$ for taking damage.  
  * $+100$ for RaidDefeated event.40  
* **Success Metric:** 95% Win Rate against single raider.

### **Stage 4: The Colony Manager (Multi-Agent)**

* **Scenario:** Crashlanded (3 pawns).  
* **Objective:** Optimization of labor.  
* **Complexity:** The agent controls 3 pawns. It must assign the best shooter to hunt, the best builder to construct.  
* **Reward Shaping:**  
  * Global Colony Mood Average.  
  * Total Wealth Accumulation.  
  * Novelty Search: Reward for triggering new HistoryEvents (e.g., first Sculpture made).41

## ---

**8\. Infrastructure and Operations**

### **8.1 Dockerized Training Environment**

To scale, we must containerize *RimWorld*.

* **Base Image:** ubuntu:20.04 with wine (since the Linux version of RimWorld exists but Wine often offers better mod compatibility/performance for certain DLLs). Ideally, use the native Linux binary if possible.  
* **Dependencies:** xvfb (X Virtual Framebuffer) is required even for "headless" mode to satisfy Unity's display initialization check, preventing the phantom display crash.26  
* **Volume Mounting:** Mount the Mods directory and Config directory to ensure consistent settings across containers.

### **8.2 Parallelization with Ray RLLib**

We utilize **Ray** for distributed training.

* **Worker Nodes:** CPU-heavy instances (e.g., AWS c5.24xlarge). Each node runs 20-40 Docker containers.  
* **Learner Node:** GPU instance (e.g., AWS p3.8xlarge). Receives batches of trajectories from workers and updates the policy.  
* **Throughput Target:** With the C\# Bridge \+ Headless optimization, we target **1000 TPS per instance**. With 100 instances, we achieve 100,000 TPS, allowing for millions of training steps per hour.

## ---

**9\. Modding and Performance Optimization**

The vanilla game is unoptimized for the scale of RL training. We must integrate specific performance mods and patches.

### **9.1 Required Utility Mods**

* **Harmony:** The backbone for all logic patching.21  
* **HugsLib:** Provides library functions for log handling and mod interoperability.32  
* **Prepatcher:** Allows for field addition to existing classes without recompilation, useful for tagging "Agent Data" onto Pawn objects.

### **9.2 Performance Mods**

* **RocketMan:** A state-of-the-art optimization mod that caches tick data (StatPart caching) and throttles low-priority ticks (e.g., animals off-screen). This is critical for maintaining high TPS in late-game scenarios.43  
* **Performance Optimizer:** Disables UI elements and optimizes gizmo drawing code. Even in headless mode, some UI logic runs in the background; this mod strips it.43  
* **Clean Pathfinding:** Optimizes the A\* pathfinding algorithms, reducing the CPU spike when agents issue movement commands.45

### **9.3 Custom "Stripping" Patches**

To further reduce overhead, the Bridge Mod should apply aggressive Harmony patches to disable:

* **AudioSystem:** Complete disablement of sound engine.  
* **MusicManager:** Disable music track selection.  
* **Effecter:** Disable particle effects (fire, smoke) which consume CPU cycles calculating trajectories, even if not rendered.46

## ---

**10\. Strategic Outlook and Risk Assessment**

### **10.1 The Versioning Risk**

*RimWorld* updates (e.g., 1.4 \-\> 1.5) notoriously break mod assemblies.47

* **Mitigation:** Project Aether must "freeze" the game version. The Docker image will contain a specific hash of the *RimWorld* assembly. We will not update the environment mid-training.

### **10.2 The Sparse Reward Trap**

There is a high risk the agent learns to "hibernate"—doing nothing to conserve energy—rather than progressing.

* **Mitigation:** The **Novelty Search** reward 41 is crucial. We track a set of "Achieved States" (e.g., "Has Built Freezer", "Has Recruited Prisoner"). The agent receives high intrinsic rewards for unlocking new states, driving it up the tech tree.

### **10.3 Conclusion**

Project Aether moves beyond the paradigm of "playing a game" to "managing a complex system." By instrumenting *RimWorld* with a high-fidelity TCP bridge, engineering a semantic tensor state space, and applying a rigorous survival curriculum, we pave the way for General AI that can plan, adapt, and survive in open-ended, chaotic environments. This roadmap provides the necessary blueprints—from the low-level C\# byte-streams to the high-level Transformer attention heads—to realize this ambition.
