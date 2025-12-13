# **Technical Feasibility Study: Autonomous Agent Architecture for Ludeon Studios' *RimWorld***

## **1\. Introduction and Problem Definition**

The pursuit of Artificial General Intelligence (AGI) often utilizes complex video games as testbeds for reinforcement learning (RL) algorithms. While platforms like the Arcade Learning Environment (ALE) and simulators for *StarCraft II* or *Dota 2* have provided benchmarks for competitive zero-sum environments, the colony simulation genre represents a distinct and largely unexplored "Grand Challenge." This report assesses the technical feasibility, architectural requirements, and computational constraints of training an autonomous agent to play *RimWorld*, a sci-fi colony simulation developed by Ludeon Studios. Unlike competitive real-time strategy games where the objective is to destroy an opponent, *RimWorld* presents an open-ended, stochastic survival environment managed by an "AI Storyteller" that dynamically adjusts difficulty based on the player's success.

The primary objective of this study is to determine whether current Deep Reinforcement Learning (DRL) and Large Language Model (LLM) technologies can effectively interface with *RimWorld*'s closed-source engine to master its gameplay loop. This requires an agent to manage the psychological needs of semi-autonomous characters ("pawns"), optimize complex resource chains, navigate a technology tree, and survive procedural threats ranging from pirate raids to environmental catastrophes. The successful development of such an agent would necessitate a hybrid neuro-symbolic architecture, leveraging the game's existing behavior trees for low-level tasks while employing hierarchical policies for long-horizon strategic planning.

### **1.1 The RimWorld Environment as a Research Domain**

*RimWorld* creates a unique problem space for AI due to its integration of narrative generation with simulation. The game does not present a static optimization problem; rather, it is a non-stationary environment where the "opponent" (the Storyteller) actively monitors the agent's state—specifically its accumulated wealth—and generates threats proportional to that state.1 This mechanism, known as the "wealth trap," creates a paradoxical reward landscape where naive maximization of resources (a typical RL objective) increases the probability of terminal failure.

The environment is built upon the Unity engine but relies on a custom Entity-Component-System (ECS) implemented in C\#. It features a partially observable tile-based map, typically $250 \\times 250$ cells in size 3, where each cell contains multi-layered feature data including terrain, structures, items, filth, and temperature. This results in a state space dimensionality that far exceeds board games like Go or Chess. Furthermore, the action space is vast and hybrid, requiring discrete choices (e.g., "Build Wall"), continuous parameters (coordinates $x, y$), and context-sensitive configurations (material selection, rotation).

### **1.2 Defining "Victory" in an Open-Ended Simulation**

To train an agent, a clear objective function is required. While *RimWorld* is a sandbox, it contains a definitive "ending" condition: constructing or finding a starship to escape the planet. This objective provides a long-horizon goal (typically taking 10-60 in-game hours) that requires the agent to traverse the entire technology tree, secure advanced resources (Plasteel, Uranium, AI Persona Cores), and defend the ship during a 15-day reactor startup sequence that triggers continuous high-intensity raids.

However, survival alone is insufficient as a metric. The agent must also maintain the "Mood" of its colonists. Neglecting psychological needs leads to "Mental Breaks," where pawns become uncontrollable, attacking one another or destroying infrastructure.4 Thus, the agent must solve a multi-objective optimization problem: maximizing colony longevity and technological progress while minimizing the probability of mental breaks and catastrophic wealth accumulation.

## ---

**2\. Reverse Engineering the Game Engine**

To interface an RL agent with *RimWorld*, one must understand the internal architecture of the game's code, which is compiled into the Assembly-CSharp.dll library. Since Ludeon Studios does not provide an official API for external agent control 5, the development of a "RimGym" interface requires invasive memory manipulation and runtime patching of the C\# methods.

### **2.1 The Verse and RimWorld Namespaces**

The game's codebase is structured into two primary namespaces: Verse and RimWorld. Understanding the distinction is critical for state extraction and action injection.

* **Verse:** This namespace handles the low-level engine functionality. It defines the fundamental data structures for the map (Map, IntVec3), the base entity class (Thing), and the ticking mechanism (TickManager).6 The Verse layer is responsible for the simulation physics, pathfinding, and the basic update loops that drive the game forward.  
* **RimWorld:** This namespace contains the gameplay-specific logic. It defines the AI behaviors (JobDriver, ThinkTree), the Storyteller logic (IncidentWorker), and the rules for colony management (zones, bills, policies).

Decompilation tools such as ILSpy or dnSpy are essential for analyzing these libraries.7 Analysis reveals that the game uses a "tick-based" system where 60 ticks correspond to one real-time second at normal speed, and 20,000 ticks constitute an in-game day. The simulation is largely single-threaded, a significant constraint that will be discussed in the performance engineering section.8

### **2.2 The Job System and Pawn Behavior**

At the core of pawn behavior is the **Job System**. Pawns do not simply "move" or "act" frame-by-frame; they execute high-level Jobs which are decomposed into atomic Toils.

#### **2.2.1 JobDrivers and Toils**

A Job (e.g., JobDefOf.Hunt) is assigned to a pawn by a WorkGiver or ThinkNode. The pawn then executes the corresponding JobDriver (e.g., JobDriver\_Hunt). This driver defines a sequence of Toils, which are discrete states in a finite state machine.

* **Example:** A JobDriver\_Ingest might consist of:  
  1. Toil\_Goto: Move to the food source.  
  2. Toil\_Take: Pick up the food.  
  3. Toil\_Ingest: Play eating animation and modify hunger need.

Snippet 6 reveals the structure of the JobDriver class, showing properties like pawn, job, curToilIndex, and ticksLeftThisToil. For an RL agent to control a pawn effectively, it must interfere with this system. A "Tactical" agent (e.g., for combat) might need to override the current job with a Job\_WaitCombat or Job\_Goto to position the pawn behind cover, interrupting the default behavior flow.

#### **2.2.2 The ThinkTree**

Pawns select their jobs by traversing a **ThinkTree**, a hierarchical decision tree defined in XML and parsed at runtime into C\# objects.9 The ThinkNode\_Priority class iterates through child nodes (e.g., "Emergency," "Health," "Work") and executes the first one that returns a valid job.11

* **Implication for AI:** A key insight for feasibility is that an RL agent does not need to learn pathfinding or basic interaction logic from scratch. By manipulating the *priorities* within the ThinkTree—or by injecting a custom, high-priority ThinkNode that queries the RL policy—the agent can direct pawn behavior while relying on the robust, native pathfinding code for execution. This is similar to the approach taken by the "Free Will" mod, which overrides priorities based on an internal logic system.10

### **2.3 The Needs Tracker and Mood System**

The Pawn\_NeedsTracker class manages the psychological and physical state of every entity.12 This tracker updates needs such as Food, Rest, and Recreation every tick (or at defined intervals).

* **Mood Calculation:** The Need\_Mood class aggregates "Thoughts" (memories of events) to calculate a current mood level. Snippets 13 show stack traces involving RimWorld.ThoughtHandler.GetAllMoodThoughts, indicating that accessing this data requires iterating through a list of active thought objects.  
* **State Observation:** For the RL agent, the state vector must include normalized values from Pawn\_NeedsTracker. Specifically, the "Mood" value serves as a dense reward signal (auxiliary reward), while critical needs like "Food" serve as survival constraints. Accessing this data via Reflection is computationally expensive if done every tick for every pawn, necessitating optimized data gathering strategies.

## ---

**3\. The "RimGym" Interface Architecture**

To train an agent using modern frameworks like PyTorch or TensorFlow, a bridge must be built between the *RimWorld* process (running on Mono/.NET) and the training process (typically running in Python). This requires a custom mod that functions as the Gym Environment server.

### **3.1 Harmony Patching Strategy**

The standard method for modifying *RimWorld* behavior is **Harmony**, a library that allows injecting code (Prefixes, Postfixes, and Transpilers) into compiled C\# methods at runtime.14

#### **3.1.1 Hooking the Game Loop**

To synchronize the agent with the game, we must hook into the main update loop. The Verse.Root\_Play.Update method 16 or Verse.TickManager.DoSingleTick are ideal candidates.

* **Implementation:** A Postfix patch on DoSingleTick checks if a decision interval has passed (e.g., every 200 ticks). If so, it pauses the game thread, serializes the current state, and waits for an action command from the Python client. This "lock-step" mechanism ensures that the simulation does not advance while the neural network is performing inference.

#### **3.1.2 Handling Wealth and Difficulty**

The RimWorld.WealthWatcher class tracks colony wealth, which drives raid difficulty.1 Snippets 16 and 2 highlight that ForceRecount can be computationally expensive and prone to IndexOutOfRangeException if map objects are in an invalid state.

* **Feasibility Note:** The agent must be able to query wealth *without* triggering a full recount every step, which would kill performance. The interface should read the cached WealthTotal property and only force a recount continuously if the "adaptive difficulty" reward signal requires high-precision wealth deltas.

### **3.2 Inter-Process Communication (IPC) Mechanisms**

The choice of IPC determines the throughput of the training loop. We compare three primary methods identified in the research material.

#### **Table 3.1: IPC Mechanism Comparison**

| Mechanism | Implementation Complexity | Latency | Data Throughput | Suitability for RimGym |
| :---- | :---- | :---- | :---- | :---- |
| **TCP Sockets** 17 | Low (Standard.NET lib) | Medium (Network stack overhead) | Medium | **High** for distributed training (Docker clusters). |
| **Memory Mapped Files** 18 | Medium (Requires P/Invoke) | Very Low (Zero-copy RAM) | Very High | **High** for local training with large image observations. |
| **HTTP/REST** | Very Low | High | Low | **Low** (Too slow for RL steps). |

**Recommendation:** A hybrid approach is optimal.

1. **Observation Data (MMF):** The heavy $250 \\times 250$ map feature tensor should be written to a **Memory Mapped File**.19 This allows the Python process to wrap the memory block as a NumPy array without serialization overhead, essential for handling the visual complexity of the map.20  
2. **Control Signals (Sockets/Protobuf):** Action commands and scalar data (rewards, done flags) should be sent via **TCP Sockets** using **Protocol Buffers (Protobuf)** serialization.22 Protobuf is significantly faster and more compact than JSON 23, reducing the serialization bottleneck that often plagues Unity-Python bridges.

### **3.3 State Representation and Feature Extraction**

The state representation must capture both the global map state and the local entity states.

#### **3.3.1 The Grid Tensor**

The map should be represented as a multi-channel image.

* **Channels:** Terrain (Walkability), Things (Wall, Sandbag, Door), Items (Weapon, Food), Filth/Fire, Pawn Presence (Friend/Foe), Zoning.  
* **Optimization:** Creating this tensor from scratch every frame is too slow. The interface must implement a "Dirty Flag" system, hooking into Map.mapDrawer.MapMeshDirty to only update the tensor cells that have changed graphically 25, or simply tracking updates to the ThingGrid.

#### **3.3.2 Entity Lists**

Detailed stats for each pawn (Health tree, Needs, Skills) cannot be easily encoded into the grid. These should be serialized as a list of feature vectors.

* **Vector Content:** \`\`  
* **Handling Variable Counts:** Since the number of pawns changes (death, recruitment), the neural network architecture must support variable-length inputs (e.g., using Transformer encoders or Deep Sets), or the interface must pad the list to a maximum fixed size.

## ---

**4\. Agent Architecture and Hierarchical Control**

Given the complexity of *RimWorld*, an end-to-end "pixels-to-actions" model is unlikely to succeed. The action space is too vast, and the planning horizon is too long. A **Hierarchical Reinforcement Learning (HRL)** approach is required, decomposing the problem into strategic and tactical layers.

### **4.1 The Executive Agent (Strategic Layer)**

The Executive Agent operates on a slow clock (e.g., once every in-game hour). Its role is to set high-level goals and policies.

* **Action Space:**  
  * **Work Priorities:** Adjusting the "Work Tab" priorities (0-4) for each pawn.26  
  * **Policy Management:** Setting drug policies, outfit restrictions 28, and food restrictions.  
  * **Construction:** Designating blueprints (Designator\_Build). This requires a generative output (What to build, Where to build).  
* **Integration:** This layer can be augmented with **Large Language Models (LLMs)**. As demonstrated by the OpenRimWorldAI mod 29 and RimGPT 30, LLMs can ingest textual summaries of the colony status (e.g., "Food is low," "Raid incoming") and output high-level commands. While LLMs are too slow for real-time control, they excel at "common sense" reasoning (e.g., "Build a heater because it is winter").

### **4.2 The Manager Agent (Operational Layer)**

This layer bridges the gap between high-level strategy and low-level execution. It functions similarly to the "Free Will" mod 10, which algorithmically assigns priorities based on pawn skills and interests.

* **Mechanism:** Instead of manually setting every priority, the RL agent can output a "Focus Vector" (e.g., \`\`). The Manager Agent then translates this vector into specific WorkGiver priorities, effectively biasing the ThinkTree search to prefer jobs related to defense.10

### **4.3 The Tactical Agent (Micro-Control Layer)**

During critical events like combat, the "Executive" passes control of specific pawns to the Tactical Agent. This agent operates on a fast clock (every few ticks) and controls "Drafted" pawns.

* **State:** Local grid (e.g., $20 \\times 20$ around the pawn) \+ Line of Sight info.  
* **Action:** Move to cover, Attack Target, Use Ability (Psycasts).  
* **Precedent:** The SimplifiedRimWorldRL project 31 demonstrates a basic Q-learning agent for killing enemies. This needs to be scaled up to handle cover mechanics (CoverUtility.CalculateOverallBlockChance) and friendly fire avoidance.32

### **4.4 The "Wealth Trap" and Reward Shaping**

A critical challenge in *RimWorld* RL is the **Wealth Trap**. The Storyteller scales raid difficulty based on WealthTotal.1

* **Naive Reward:** If $R \= \\Delta Wealth$, the agent will mine gold and build statues. The Storyteller will respond with a massive Mechanoid raid that destroys the colony.  
* Curriculum Reward: The reward function must penalize undefended wealth or prioritize defense relative to wealth.

  $$R \= \\alpha \\cdot (\\text{Wealth}) \- \\beta \\cdot (\\text{ThreatPoints}) \+ \\gamma \\cdot (\\text{AvgMood})$$  
* **Survival Constraint:** The ultimate reward is longevity. However, sparse rewards (survival time) make learning slow. Dense auxiliary rewards (Mood, Hunger) are necessary but must be carefully balanced to prevent "reward hacking" (e.g., eating lavish meals constantly to maximize mood, leading to food shortages).

## ---

**5\. Simulation and Performance Engineering**

Training RL agents requires millions of interaction steps. *RimWorld* is a performance-heavy simulation, making this the primary bottleneck for feasibility.

### **5.1 The Ticks Per Second (TPS) Bottleneck**

In a vanilla game, 1x speed is 60 TPS. "Speed 3" attempts to reach higher rates but is capped by the CPU's single-core performance. Late-game colonies often struggle to maintain even 60 TPS due to the complexity of Pawn\_NeedsTracker, pathfinding, and social interactions.33

* **Training Requirement:** To train in a reasonable timeframe, we need effective speeds of 500+ TPS, or massive parallelization.  
* **Unlocking Speed:** Developer Mode allows a "Speed 4" (Smart Speed) which removes the frame-rate cap.35 The interface mod must permanently enable this mode and strip out thread.sleep calls to run as fast as the hardware allows.

### **5.2 Headless Execution and Dockerization**

To scale training, we must run multiple instances of *RimWorld* in parallel on a server cluster or cloud GPU instances. This requires running the game in "headless" mode (no GUI).

* **Unity Batchmode:** The command line arguments \-batchmode and \-nographics are standard for Unity.37 However, user reports indicate that *RimWorld* specifically crashes with \-nographics because certain UI initialization routines (loading textures for icons) are not null-checked.38  
* **Workaround:** We must use a virtual display.  
  * **Linux/Docker:** Using xvfb (X virtual framebuffer) allows the game to "render" to a virtual screen in memory, satisfying the engine's requirement for a graphics device without physical output.39  
  * **Containerization:** The "Open World" multiplayer mod community has successfully containerized *RimWorld* servers using Docker.40 While these servers primarily sync state rather than run the full simulation, the container structure provides a template: FROM mono or FROM ubuntu with wine (since the Linux version of RimWorld is native but sometimes less stable with mods).

### **5.3 Optimization Mods**

To maximize TPS, the training environment should incorporate performance-enhancing mods.

* **RocketMan:** Optimizes the ticking of world pawns and caches stat calculations.42  
* **Fishery:** A modding library that provides framework-level optimizations.44  
* **Slower Pawn Tick Rate:** Mods that reduce the tick frequency of non-critical components (e.g., ticking needs every 20 ticks instead of 10\) can significantly boost performance with minimal impact on agent decision quality.33

### **5.4 GPU Compute Shaders and Rendering**

Even in headless mode, Unity may attempt to use GPU resources for compute shaders. Snippets 37 suggest using the flag \-disable-compute-shaders to prevent crashes on server hardware that lacks a dedicated GPU or has incompatible drivers. This is crucial for cost-effective cloud training on CPU-only instances.

## ---

**6\. Implementation Roadmap**

Based on the analysis, a phased implementation plan is recommended.

### **Phase 1: The "RimGym" Prototype (Months 1-3)**

**Objective:** Establish the Python-C\# bridge and achieve stable headless execution.

1. **Mod Development:** Create a C\# solution using the RimWorld Dotnet Template.46 Implement Harmony patches to serialize the map tensor to a Memory Mapped File.  
2. **Docker Harness:** configure a Dockerfile using xvfb to run the Linux version of RimWorld with the mod loaded.  
3. **Benchmarking:** Measure TPS in headless mode on a standard cloud instance (e.g., AWS c5.large). Target \>500 TPS.

### **Phase 2: Micro-Agent Training (Months 4-6)**

**Objective:** Train sub-policies for specific tasks (HRL components).

1. **Combat Sandbox:** Create a custom ScenarioDef that spawns a pawn and a raider in a small arena. Train a PPO agent to win the duel using cover.31  
2. **Economy Sandbox:** Create a "Peaceful" scenario. Train an agent to manage food production and cooking to keep hunger/mood above a threshold.

### **Phase 3: Integration and The Executive (Months 7-12)**

**Objective:** Combine sub-policies under a hierarchical controller.

1. **Action Abstraction:** Implement the "Executive" action space (Setting priorities, Designating zones).  
2. **LLM Integration:** Connect the "Letter" system (events) to a local LLM (e.g., Llama 3\) to handle complex events (e.g., "Peace Talks," "Refugee Requests") via text-based decision making.29  
3. **Full Loop:** Train the integrated agent on a "Cassandra Classic" difficulty curve, utilizing the "Wealth Trap" aware reward function.

## ---

**7\. Feasibility Verdict and Conclusion**

### **7.1 Technical Feasibility**

Training an agent to play *RimWorld* is **Technically Feasibility** but represents a significant engineering undertaking. The primary barriers are not theoretical but infrastructural:

1. **No Native API:** Requires building a custom Gym wrapper using invasive Harmony patching.  
2. **Simulation Speed:** Single-threaded CPU limits require aggressive optimization and headless containerization to achieve sufficient training sample efficiency.  
3. **State Complexity:** Requires sophisticated Hybrid/Hierarchical RL architectures to manage the vast action space.

### **7.2 Comparison to Other Game AI**

Compared to *StarCraft II*, *RimWorld* is **less computationally demanding regarding APM** (micro-management) but **more demanding regarding long-term causal reasoning** and state variance. The solution lies not in brute-force RL, but in a Neuro-Symbolic approach: utilizing the game's existing pathfinding and job systems (Symbolic) steered by a high-level policy (Neural).

### **7.3 Final Recommendation**

For a research team or dedicated engineer, the "RimGym" project is a viable path to advancing the state of the art in MARL and HRL. The recommended architecture is a **Hierarchical PPO** model interacting with a **Dockerized, headless RimWorld instance** via **Memory Mapped Files**, leveraging **LLMs** for high-level semantic reasoning. This hybrid approach circumvents the limitations of pure RL in infinite-horizon, open-ended games.

## **8\. Summary of Mod/Tool Recommendations**

#### **Table 8.1: Recommended Tool Stack**

| Component | Tool/Mod | Purpose |
| :---- | :---- | :---- |
| **Hooking/Patching** | **Harmony** 14 | Injecting code into C\# methods (Update, Tick). |
| **Decompilation** | **ILSpy / dnSpy** 7 | Analyzing RimWorld and Verse namespaces. |
| **Performance** | **RocketMan** 42 | Optimizing tick rate for faster training. |
| **Performance** | **Fishery** 44 | Modding framework for optimization. |
| **IPC** | **Protobuf** 22 | Fast serialization of control signals. |
| **Behavior Ref.** | **Free Will** 10 | Reference for overriding ThinkTree priorities. |
| **LLM Integration** | **OpenRimWorldAI** 29 | Reference for serializing game state to text. |
| **Headless Env** | **Docker \+ xvfb** 39 | Running the game without a physical display. |

This roadmap provides a clear, technically grounded path to creating the first autonomous *RimWorld* agent, turning a complex entertainment product into a robust AI research environment.

#### **Works cited**

1. RimWorld \- Vanilla Factions Expanded \- Empire \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/workshop/filedetails/discussion/2938820380/3776868552319024412/](https://steamcommunity.com/workshop/filedetails/discussion/2938820380/3776868552319024412/)  
2. Need help debugging "Exception while recalculating" : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1968k5x/need\_help\_debugging\_exception\_while\_recalculating/](https://www.reddit.com/r/RimWorld/comments/1968k5x/need_help_debugging_exception_while_recalculating/)  
3. Increase the size of the map. 256х256 \- Editor Discussion \- SC2 Forums, accessed December 13, 2025, [https://us.forums.blizzard.com/en/sc2/t/increase-the-size-of-the-map-256%D1%85256/20070](https://us.forums.blizzard.com/en/sc2/t/increase-the-size-of-the-map-256%D1%85256/20070)  
4. 400+ mods, just realized that pawns can't have mental breaks for some reason... More info in the comments. : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/16cwag3/400\_mods\_just\_realized\_that\_pawns\_cant\_have/](https://www.reddit.com/r/RimWorld/comments/16cwag3/400_mods_just_realized_that_pawns_cant_have/)  
5. Where are the modding APIs? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1j6qgfj/where\_are\_the\_modding\_apis/](https://www.reddit.com/r/RimWorld/comments/1j6qgfj/where_are_the_modding_apis/)  
6. RW-Decompile/Verse.AI/JobDriver.cs at master · josh-m/RW-Decompile · GitHub, accessed December 13, 2025, [https://github.com/josh-m/RW-Decompile/blob/master/Verse.AI/JobDriver.cs](https://github.com/josh-m/RW-Decompile/blob/master/Verse.AI/JobDriver.cs)  
7. RimWorld Modding Resources \- spdskatr, accessed December 13, 2025, [https://spdskatr.github.io/RWModdingResources/](https://spdskatr.github.io/RWModdingResources/)  
8. Maximum TPS : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1iuque2/maximum\_tps/](https://www.reddit.com/r/RimWorld/comments/1iuque2/maximum_tps/)  
9. Disabling Vanilla Content? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/ovlt7m/disabling\_vanilla\_content/](https://www.reddit.com/r/RimWorld/comments/ovlt7m/disabling_vanilla_content/)  
10. Steam Workshop::Free Will \- RimWorld, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=2580837227](https://steamcommunity.com/sharedfiles/filedetails/?id=2580837227)  
11. How to find which mod is causing an error? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/9kq7ep/how\_to\_find\_which\_mod\_is\_causing\_an\_error/](https://www.reddit.com/r/RimWorld/comments/9kq7ep/how_to_find_which_mod_is_causing_an_error/)  
12. How to make a Simple Rick/Yunners : Rimworld Tutorial Nuggets \- YouTube, accessed December 13, 2025, [https://www.youtube.com/watch?v=alShZCbhgB4](https://www.youtube.com/watch?v=alShZCbhgB4)  
13. I need help with a bug (pls) :: RimWorld General Discussions \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/600784181506638370/](https://steamcommunity.com/app/294100/discussions/0/600784181506638370/)  
14. Mod Orders; a Beginner's Guide \- RimWorld \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=2017183144](https://steamcommunity.com/sharedfiles/filedetails/?id=2017183144)  
15. Harmony patching : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/8mfx9p/harmony\_patching/](https://www.reddit.com/r/RimWorld/comments/8mfx9p/harmony_patching/)  
16. can anyone help? i keep getting errors like this in debug log, and what does it even do? (i do have a lot of mods : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/yccj3w/can\_anyone\_help\_i\_keep\_getting\_errors\_like\_this/](https://www.reddit.com/r/RimWorld/comments/yccj3w/can_anyone_help_i_keep_getting_errors_like_this/)  
17. Use Sockets to send and receive data over TCP \- .NET | Microsoft Learn, accessed December 13, 2025, [https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/sockets/socket-services](https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/sockets/socket-services)  
18. Memory-Mapped Files \- .NET \- Microsoft Learn, accessed December 13, 2025, [https://learn.microsoft.com/en-us/dotnet/standard/io/memory-mapped-files](https://learn.microsoft.com/en-us/dotnet/standard/io/memory-mapped-files)  
19. Optimizing Memory Usage of Unity Game by Using Memory Mapped File | by Alan Liu, accessed December 13, 2025, [https://medium.com/@alanliu90/optimizing-memory-usage-of-unity-game-by-using-memory-mapped-file-2c0d7afb9a8e](https://medium.com/@alanliu90/optimizing-memory-usage-of-unity-game-by-using-memory-mapped-file-2c0d7afb9a8e)  
20. Accessing MemoryMappedFiles in Unity \- Stack Overflow, accessed December 13, 2025, [https://stackoverflow.com/questions/25506132/accessing-memorymappedfiles-in-unity](https://stackoverflow.com/questions/25506132/accessing-memorymappedfiles-in-unity)  
21. c\# \- .NET 4.0 Memory Mapped Files Performance \- Stack Overflow, accessed December 13, 2025, [https://stackoverflow.com/questions/2333075/net-4-0-memory-mapped-files-performance](https://stackoverflow.com/questions/2333075/net-4-0-memory-mapped-files-performance)  
22. Performance Test – Binary serializers Part II \- theburningmonk.com, accessed December 13, 2025, [https://theburningmonk.com/2011/12/performance-test-binary-serializers-part-ii/](https://theburningmonk.com/2011/12/performance-test-binary-serializers-part-ii/)  
23. Protocol Buffers — Just how fast are they | by David Turner | Medium, accessed December 13, 2025, [https://medium.com/@david\_turner/protocol-buffers-just-how-fast-are-they-9ec19ea580db](https://medium.com/@david_turner/protocol-buffers-just-how-fast-are-they-9ec19ea580db)  
24. How are protocol-buffers faster than XML and JSON? \- Stack Overflow, accessed December 13, 2025, [https://stackoverflow.com/questions/52146721/how-are-protocol-buffers-faster-than-xml-and-json](https://stackoverflow.com/questions/52146721/how-are-protocol-buffers-faster-than-xml-and-json)  
25. Guide :: Rimworld optimization. In an adult way. \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=3150465850](https://steamcommunity.com/sharedfiles/filedetails/?id=3150465850)  
26. Steam Workshop::Automated Work Assignment, accessed December 13, 2025, [https://steamcommunity.com/workshop/filedetails/?id=3453406362](https://steamcommunity.com/workshop/filedetails/?id=3453406362)  
27. So... job assignments and priorities.... manual or auto? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1h166tl/so\_job\_assignments\_and\_priorities\_manual\_or\_auto/](https://www.reddit.com/r/RimWorld/comments/1h166tl/so_job_assignments_and_priorities_manual_or_auto/)  
28. Batch Commands :: RimWorld General Discussions \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/3120424524431534905/](https://steamcommunity.com/app/294100/discussions/0/3120424524431534905/)  
29. Steam Workshop::OpenRimWorldAI, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=3411917876](https://steamcommunity.com/sharedfiles/filedetails/?id=3411917876)  
30. RimWorldAI Core \- Steam Workshop, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=3269938006](https://steamcommunity.com/sharedfiles/filedetails/?id=3269938006)  
31. EmmanuelMess/SimplifiedRimWorldRL: Very simple ... \- GitHub, accessed December 13, 2025, [https://github.com/EmmanuelMess/SimplifiedRimWorldRL](https://github.com/EmmanuelMess/SimplifiedRimWorldRL)  
32. Steam Workshop::Rimworld Private Server, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=2038900738](https://steamcommunity.com/sharedfiles/filedetails/?id=2038900738)  
33. Steam Workshop::Performance \- Slower Pawn Tick Rate, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=3524116050](https://steamcommunity.com/sharedfiles/filedetails/?id=3524116050)  
34. Your lowest , Average and highest TPS : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1hl87rl/your\_lowest\_average\_and\_highest\_tps/](https://www.reddit.com/r/RimWorld/comments/1hl87rl/your_lowest_average_and_highest_tps/)  
35. PSA: Development mode enables "ultra fast" speed. : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/6akyzi/psa\_development\_mode\_enables\_ultra\_fast\_speed/](https://www.reddit.com/r/RimWorld/comments/6akyzi/psa_development_mode_enables_ultra_fast_speed/)  
36. There's a FOURTH (hidden) speed option\!?\!? I just discovered this after crossing 700 hours the other day. : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1g5cnsm/theres\_a\_fourth\_hidden\_speed\_option\_i\_just/](https://www.reddit.com/r/RimWorld/comments/1g5cnsm/theres_a_fourth_hidden_speed_option_i_just/)  
37. There are still errors even without MOD installed :: RimWorld General Discussions \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/664963445168344904/](https://steamcommunity.com/app/294100/discussions/0/664963445168344904/)  
38. Stuck on initializing. 1.6(stable), all dlc : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1lxo6rt/stuck\_on\_initializing\_16stable\_all\_dlc/](https://www.reddit.com/r/RimWorld/comments/1lxo6rt/stuck_on_initializing_16stable_all_dlc/)  
39. Vlli/docker-phi-server: RimWorlds popular multiplayer mod server in a container \- GitHub, accessed December 13, 2025, [https://github.com/Vlli/docker-phi-server](https://github.com/Vlli/docker-phi-server)  
40. f0rkz/docker-openworld: Open World mod server for docker \- GitHub, accessed December 13, 2025, [https://github.com/f0rkz/docker-openworld](https://github.com/f0rkz/docker-openworld)  
41. Docker container for headless server · NebulaModTeam nebula · Discussion \#591 \- GitHub, accessed December 13, 2025, [https://github.com/NebulaModTeam/nebula/discussions/591](https://github.com/NebulaModTeam/nebula/discussions/591)  
42. I Tested The Top 3 Rimworld Performance Mods To See Which is the Best \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/q8fwtb/i\_tested\_the\_top\_3\_rimworld\_performance\_mods\_to/](https://www.reddit.com/r/RimWorld/comments/q8fwtb/i_tested_the_top_3_rimworld_performance_mods_to/)  
43. If you are the "I do not play with mods" type of person, at least download the performance mods, literally download more TPS, here they are: : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1jfz8q0/if\_you\_are\_the\_i\_do\_not\_play\_with\_mods\_type\_of/](https://www.reddit.com/r/RimWorld/comments/1jfz8q0/if_you_are_the_i_do_not_play_with_mods_type_of/)  
44. rimworld-mod · GitHub Topics, accessed December 13, 2025, [https://github.com/topics/rimworld-mod?o=desc\&s=forks](https://github.com/topics/rimworld-mod?o=desc&s=forks)  
45. What's the best way to increase performance in 1.6? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1p0y2pu/whats\_the\_best\_way\_to\_increase\_performance\_in\_16/](https://www.reddit.com/r/RimWorld/comments/1p0y2pu/whats_the_best_way_to_increase_performance_in_16/)  
46. rimworld-mod · GitHub Topics, accessed December 13, 2025, [https://github.com/topics/rimworld-mod](https://github.com/topics/rimworld-mod)