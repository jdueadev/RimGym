# **Advanced Engineering Framework for Integrating Ludeon Studio’s RimWorld with Gymnasium: A Technical Deep Dive**

## **1\. Introduction: The Grand Challenge of Complex Simulation Environments**

The advancement of Artificial General Intelligence (AGI) and Deep Reinforcement Learning (DRL) relies heavily on the quality and complexity of the environments in which agents are trained. While foundational benchmarks like the Arcade Learning Environment (Atari) and continuous control tasks (MuJoCo) have driven significant algorithmic progress, they lack the hierarchical depth, long-time horizons, and emergent complexity found in modern simulation games. Ludeon Studio’s *RimWorld*, a sophisticated sci-fi colony simulation driven by an intelligent AI storyteller, represents a frontier "Grand Challenge" for the research community. Unlike star-system strategy games or first-person shooters, RimWorld requires an agent to manage psychological states, intricate resource economies, tactical combat, and architectural planning simultaneously, all while navigating a procedural narrative that actively seeks to destabilize the player’s state.

This report details the exhaustive technical methodology required to bridge the proprietary, C\#-based architecture of RimWorld (built on the Unity Engine) with the Python-centric ecosystem of Gymnasium (formerly OpenAI Gym). This integration is not merely a matter of API hooking; it requires a fundamental re-engineering of the game’s execution flow, the implementation of thread-safe Inter-Process Communication (IPC) protocols, and the translation of high-dimensional, unstructured game states into tensor-ready formats suitable for Convolutional Neural Networks (CNNs) and Transformer architectures. By leveraging the Harmony patching library to intercept the Unity TickManager and constructing a custom TCP-based bridge, researchers can transform RimWorld into a steppable, observable, and deterministic Reinforcement Learning (RL) environment.1

### **1.1 Theoretical Justification for RimWorld as an RL Benchmark**

The utility of RimWorld as a research testbed lies in its "Storyteller" engine. Traditional RL environments possess static transition probabilities. In contrast, RimWorld’s AI Storyteller (e.g., Cassandra Classic or Randy Random) functions as an adversarial meta-agent, dynamically adjusting difficulty based on the colony’s wealth and population.4 This introduces a unique form of non-stationarity where the environment "learns" from the agent's success, punishing hoarding behavior with stronger raids.

Furthermore, the "Sim-to-Real" gap—often cited in robotics—has a parallel in procedural storytelling. Agents trained in RimWorld must learn generalizable heuristics (e.g., "fire spreads," "mood affects work speed") rather than memorizing map layouts, as the terrain and resources are procedurally generated for every episode.6 This forces the development of robust policies capable of transfer learning, a critical requirement for next-generation AI systems. The complexity of the state space, involving thousands of interactive objects (Things) and distinct biological needs (Needs) per agent, dwarfs the complexity of standard RTS benchmarks like StarCraft II minigames, offering a rich playground for Multi-Agent Reinforcement Learning (MARL) and Hierarchical Reinforcement Learning (HRL).

## ---

**2\. Analysis of the RimWorld Engine Architecture**

To effectively control RimWorld from an external Python process, one must first dissect its internal architecture. RimWorld is built on the Unity engine but relies heavily on a custom object-oriented framework contained within the Verse and RimWorld namespaces. Unlike typical Unity games that rely heavily on MonoBehaviour Update() loops for logic, RimWorld utilizes a centralized TickManager to handle simulation time.8

### **2.1 The Tick-Based Simulation Model**

The heartbeat of RimWorld is the "Tick." The game logic runs at a baseline of 60 ticks per real-time second (at 1x speed). Every interactive object, from a growing plant to a pawn’s hunger meter, acts based on these ticks.

* **Tick Types:**  
  * Tick(): Executed every frame (60 times/sec). Used for projectiles and combat.  
  * TickRare(): Executed every 250 ticks (\~4 seconds). Used for plant growth and temperature equalization.  
  * TickLong(): Executed every 2000 ticks (\~30 seconds). Used for long-term health tracking and trait development.

For an RL environment, the critical challenge is "Tick Determinism." Standard gameplay allows ticks to fluctuate based on frame rate (FPS). However, a Gymnasium environment requires lock-step execution: the simulation must freeze completely while the agent computes an action, and then advance by a precise number of ticks (e.g., exactly 60 ticks for a 1-second step).8 This necessitates injecting code directly into the Verse.TickManager.Ticker method to override the native time accumulation logic. Without this intervention, the game simulation would "drift," leading to non-deterministic behaviors where the agent’s reaction time depends on the CPU speed of the host machine rather than the policy’s output.

### **2.2 The Single-Threaded Constraint**

A pervasive misconception in Unity modding is the availability of multi-threading for logic. RimWorld’s gameplay logic is almost entirely single-threaded. The Verse API, which controls map generation, pawn pathfinding, and job assignments, is **not thread-safe**.10 Accessing game data (e.g., reading Pawn.health) or modifying state (e.g., Pawn.jobs.TryTakeOrderedJob) from a background thread—such as one handling a TCP network socket—will inevitably cause race conditions, data corruption, and immediate application crashes.12

This architectural reality dictates the design of the "Bridge." We cannot simply expose an API endpoint that modifies the game state asynchronously. Instead, we must implement a **Dispatcher Pattern**. The network listener must reside on a background thread to prevent blocking the UI, but it must only *queue* commands. The actual execution of these commands must be deferred to the main Unity thread, injected via a Harmony patch into the Verse.Root.Update() loop.10 This ensures that all memory modifications occur within the safe context of the game's primary execution cycle.

### **2.3 Decompilation and Reflection**

Since RimWorld is closed-source, understanding the specific classes requires decompilation. Tools like ILSpy or DotPeek allow researchers to inspect the Assembly-CSharp.dll found in the game’s installation folder.14 Key namespaces identified for control include:

* Verse: The base engine handling low-level math, map grids (Map.thingGrid), and entity definitions (Def).  
* RimWorld: The gameplay layer handling specific mechanics like JobDriver\_AttackStatic, WealthWatcher, and Storyteller.  
* RimWorld.Planet: Handles the world map and macro-simulation, relevant for long-term strategic agents.

## ---

**3\. The Inter-Process Communication (IPC) Bridge**

The gulf between the C\#/.NET environment of RimWorld and the Python/PyTorch environment of Gymnasium must be bridged by a robust communication layer. While Unity ML-Agents provides a native solution 15, its rigid "Academy" structure often lacks the flexibility required for the deep, granular state extraction needed for RimWorld. A custom TCP socket solution allows for full control over the serialization protocol and the "Step" logic.

### **3.1 Socket Topology: The Server-Client Model**

The architecture operates on a Client-Server model where the RimWorld application acts as the Server.

1. **Initialization:** Upon game launch, the custom mod utilizes the StaticConstructorOnStartup attribute to initialize a TcpListener on a configurable port (default 5000).17  
2. **Listening:** The server spins up a background thread dedicated to listening for incoming connections from the Python client.  
3. **Handshake:** When env.reset() is called in Python, a socket connection is established. The C\# server validates the connection and prepares the game instance (e.g., loading a specific save or generating a scenario).

### **3.2 Protocol Design: JSON vs. Binary**

For the data payload, there is a trade-off between human readability and performance.

* **JSON (Newtonsoft.Json):** Easy to debug and flexible. However, serializing a 250x250 map grid (62,500 tiles) with multiple layers (terrain, items, pawns) creates massive string objects that trigger frequent Garbage Collection (GC) spikes in Unity, causing "stutter" that slows down training.19  
* **Binary (Protobuf/FlatBuffers):** Highly efficient. We recommend a hybrid approach: use JSON for control messages (e.g., {"type": "RESET", "seed": 12345}) and binary byte arrays for the high-bandwidth observation tensors (map grids). This reduces CPU overhead on the C\# side significantly.20

### **3.3 The "Stop-and-Wait" Synchronization Protocol**

To enforce the Markov Property required by RL (where the next state depends only on the current state and action), the communication must be synchronous.

1. **Python sends STEP(action):** The Python process blocks, waiting for a response.  
2. **C\# Receives Action:** The background thread enqueues the action.  
3. **C\# Main Thread Executes:** The Harmony patch detects the queued action, executes it (e.g., assigns a job to a pawn), and then **unpauses** the TickManager for a specific duration (e.g., 60 ticks).  
4. **Simulation Advances:** The game runs for 1 second of in-game time. The UI is updated, physics are calculated, and AI logic runs.  
5. **C\# Pauses and Observes:** After 60 ticks, the game is forced to pause. The Main Thread scrapes the state (wealth, map grid, health), serializes it, and sends it back to Python.  
6. **Python Returns obs, reward, done:** The RL agent processes the new state.

This "Stop-and-Wait" cycle ensures that the agent never acts on stale data and that the game never advances without the agent's permission.

## ---

**4\. Harmony Patching and Mod Development**

Implementing the architecture described above requires "Modding" the game logic at runtime. The standard tool for this in the RimWorld community is **Harmony**.3 Harmony allows developers to write "Patches"—code that runs before (Prefix) or after (Postfix) existing game methods.

### **4.1 Setting Up the Development Environment**

Development requires a C\# IDE (Visual Studio/Rider) targeting.NET Framework 4.7.2 (standard for Unity 2019/2020 era games). The project must reference:

* Assembly-CSharp.dll (RimWorld logic)  
* UnityEngine.dll (Unity engine)  
* 0Harmony.dll (The patching library)

Dependencies are critical. The About.xml file of the mod must declare a dependency on brrainz.harmony (Harmony ID) to ensure the library is loaded before our code executes.23

### **4.2 Critical Harmony Patches**

To achieve the control required for RL, three specific areas of the code must be patched:

#### **4.2.1 The Tick Interceptor**

We target Verse.TickManager.Ticker. A Prefix patch is used to short-circuit the game loop.

C\#

public static class TickPatch {  
    public static bool Prefix() {  
        if (Bridge.IsWaitingForAgent) {  
            return false; // Skip the original Ticker method, effectively freezing the game  
        }  
        return true; // Run the tick normally  
    }  
}

This patch effectively puts the game in a coma, waking up only when Bridge.IsWaitingForAgent is set to false by the network listener.8

#### **4.2.2 The Main Thread Dispatcher**

We target Verse.Root.Update. This method runs every frame, regardless of whether the game is paused. This is the ideal location to check the ConcurrentQueue for incoming network commands.

C\#

public static class UpdatePatch {  
    public static void Postfix() {  
        Bridge.ProcessCommandQueue(); // Execute queued actions on the main thread  
    }  
}

By placing this in Root.Update, we ensure that even if the simulation is paused, the mod can still spawn items, manipulate the camera, or reset the map.18

#### **4.2.3 GUI Rendering Suppression (Headless Mode)**

Training RL agents is computationally expensive. Rendering the game at 60 FPS is a waste of resources, especially when training 8+ environments in parallel. While Unity doesn't support true "Headless" mode for RimWorld easily (as some logic is tied to graphical assets), we can suppress the rendering of the "World" layer.  
A patch on Verse.MapDrawer.MapMeshDrawerUpdate can simply return immediately, skipping the expensive mesh regeneration steps. Additionally, the standard RL environment setup should force Find.TickManager.CurTimeSpeed to Ultrafast during the execution phase to minimize wall-clock time per step.20

## ---

**5\. Designing the Observation Space**

The "Observation Space" defines what the agent sees. In a game as visually and systematically dense as RimWorld, raw pixel input is inefficient. A feature-based extraction method, yielding semantic maps and vector statistics, is far superior for training efficiency.

### **5.1 The Spatial Tensor (The Grid)**

RimWorld maps are tile grids. We can represent the map as a 3D tensor of shape $(C, H, W)$, where $H$ and $W$ are map dimensions (e.g., 200x200) and $C$ represents feature channels.  
Using Verse.Map.thingGrid and Verse.Map.terrainGrid, we iterate through the map to populate these channels 6:

| Channel Index | Feature Description | Data Source (C\#) |
| :---- | :---- | :---- |
| 0 | **Terrain Passability** | cell.GetTerrain(map).passability (Walkable vs. Impassable) |
| 1 | **Terrain Fertility** | cell.GetTerrain(map).fertility (Important for farming) |
| 2 | **Edifices** | Walls, Doors, Workbenches. Encoded by ThingDef.index. |
| 3 | **Items** | Resources on floor (Wood, Steel, Weapons). |
| 4 | **Friendlies** | Pawn positions (Player faction). |
| 5 | **Hostiles** | Raiders/Mechanoids positions. |
| 6 | **Fire/Danger** | Active fire or extreme temperature zones. |

**Optimization:** Iterating 40,000+ tiles every step is slow. We optimize this by maintaining a "Dirty Rect" system—only updating the tensor for chunks of the map that actually changed during the last tick, or by using Unity's Unsafe memory copying to blast the grid array directly to the output buffer.21

### **5.2 The Vector Observation (Global State)**

Global variables that don't fit on the grid are passed as a separate vector (MLP input).

* **Colony Wealth:** RimWorld.WealthWatcher.WealthTotal. A primary indicator of success and raid difficulty.4  
* **Resource Counts:** Total food, medicine, and building materials available in stockpiles (Map.resourceCounter).  
* **Time:** Current Season, Day, and Hour (critical for preparing for winter).  
* **Pawn Aggregates:** Average Mood, Average Health.

### **5.3 Agent-Specific Observations (Egocentric)**

For Multi-Agent setups, each pawn needs its own view.

* **Health:** Pawn.health.summaryHealth.SummaryHealthPercent.30  
* **Mood:** Pawn.needs.mood.CurLevel.  
* **Skills:** Shooting, Melee, Medical, Construction.  
* **Equipment:** Current weapon and apparel.

### **5.4 Curriculum Generation via Map Design**

To prevent the agent from being overwhelmed, we must control the environment's initial complexity. Leveraging the **MapDesigner** mod 6, we can programmatically adjust map parameters via the interface.

* *Stage 1:* 50x50 map, flat terrain, no enemies. Goal: Learn to gather berries.  
* *Stage 2:* 100x100 map, simple ruins. Goal: Build a room.  
* Stage 3: 200x200 map, mountainous. Goal: Defend against a single raider.  
  This procedural curriculum is vital for converging on complex tasks like base defense.

## ---

**6\. Action Space and Semantics**

Mapping the continuous/discrete decisions of an RL agent to RimWorld’s Job system is the most conceptually difficult task. RimWorld pawns do not just "move"; they "Take Jobs." A Job consists of a JobDef (e.g., HaulToCell) and a Target.

### **6.1 The JobDriver System**

Internally, RimWorld breaks high-level jobs into "Toils" (atomic actions).

* *Job:* JobDefOf.Ingest (Eat a meal).  
* *Toils:*  
  1. Goto(Meal).  
  2. Pickup(Meal).  
  3. Goto(Table).  
  4. Chew(Duration).  
  5. Swallow.

The RL agent should ideally operate at the **Job** level, not the **Toil** level. Operating at the Toil level (micro-managing every step) creates an excessively long time horizon.

### **6.2 Hierarchical Action Space Design**

We propose a Gymnasium.spaces.MultiDiscrete action space.31  
Action Tuple: \`\`

| Action Type ID | RimWorld JobDef | Description |
| :---- | :---- | :---- |
| 0 | Wait | Idle for next duration. |
| 1 | Goto | Move to (X, Y). |
| 2 | AttackStatic | Attack thing at (X, Y). Requires drafting. |
| 3 | HaulToCell | Pick up item at (X, Y) (Logic must infer destination or use separate param). |
| 4 | Harvest | Cut plant at (X, Y). |
| 5 | Construct | Build selected blueprint at (X, Y). |

### **6.3 Implementing "Drafting" and Force-Jobs**

To make a pawn obey these commands instantly, bypassing their internal AI priorities, they must often be "Drafted" (Combat Mode).

* **Drafting:** Set Pawn.drafter.Drafted \= true.33 This gives the player (and thus the RL agent) direct control over movement and combat.  
* **Forcing Jobs:** Use the API Pawn.jobs.TryTakeOrderedJob(Job job, JobTag tag). The JobTag.Misc or JobTag.DraftedOrder ensures the job interrupts current activities immediately.35

### **6.4 Handling Invalid Actions (Action Masking)**

An agent might try to "Harvest" a rock or "Attack" empty space. The environment must handle this:

1. **Masking:** The observation space should include an "Action Mask" boolean array indicating valid actions for the current state (e.g., Attack is only valid if an enemy is in range).  
2. **No-Op:** If an invalid action is chosen, the C\# mod should detect the failure (e.g., JobMaker fails validation), return a small negative reward, and the pawn should Wait instead of crashing.38

## ---

**7\. Reward Engineering: Defining "Success" in a Sandbox**

RimWorld has no explicit "Win" condition other than launching a spaceship, which takes huge amounts of time. For RL, we must construct a dense reward function composed of several weighted terms.

### **7.1 The Survival Component (Sparse)**

The most basic reward is $R\_t \= \+1$ for every tick the colony survives. If the "Game Over" screen is triggered (Population \= 0), the episode ends with a penalty $R\_T \= \-100$.

### **7.2 The Mood Component (Dense)**

Mood is a proxy for all biological needs. If a pawn is hungry, tired, or in pain, their mood drops.

$$R\_{mood} \= \\frac{1}{N} \\sum\_{i=1}^{N} (\\text{Mood}\_i \- 0.5)$$

Targeting a mood above 50% yields positive rewards; below yields negative. This encourages the agent to feed, entertain, and protect pawns naturally without hard-coding specific "Eat" rewards.39

### **7.3 The Wealth Paradox**

Increasing wealth ($R\_{wealth} \= \\Delta \\text{WealthTotal}$) rewards building and gathering. However, RimWorld’s Storyteller scales raid strength based on wealth. A naive agent maximizing wealth will trigger impossible raids and die.

* Insight: The reward function must balance Wealth and Defense.

  $$R \= w\_1 \\cdot \\Delta \\text{Wealth} \+ w\_2 \\cdot \\Delta \\text{Mood} \- w\_3 \\cdot \\text{DamageTaken}$$

  .4

### **7.4 Handling the Storyteller**

To isolate the agent's skill from RNG (Random Number Generation), we should initially use a custom "Training Storyteller" via XML modification. This Storyteller should be deterministic (e.g., "Raid every 5 days with strength X") rather than random. This stabilizes the learning curve. Later, the standard "Cassandra" storyteller can be reintroduced to test robustness.41

## ---

**8\. Integration with Gymnasium and RL Baselines**

The Python side of the equation involves subclassing gymnasium.Env.

### **8.1 The Environment Wrapper**

The RimWorldEnv class manages the socket connection and data formatting.

Python

import gymnasium as gym  
from gymnasium import spaces  
import socket  
import json  
import numpy as np

class RimWorldEnv(gym.Env):  
    def \_\_init\_\_(self, host='127.0.0.1', port=5000):  
        self.sock \= socket.socket(socket.AF\_INET, socket.SOCK\_STREAM)  
        self.sock.connect((host, port))  
          
        \# Define Spaces  
        self.observation\_space \= spaces.Dict({  
            "grid": spaces.Box(low=0, high=255, shape=(6, 100, 100), dtype=np.uint8),  
            "global": spaces.Box(low=0, high=float('inf'), shape=(10,), dtype=np.float32)  
        })  
        self.action\_space \= spaces.MultiDiscrete() \# Type, X, Y

    def step(self, action):  
        \# Serialize Action  
        payload \= json.dumps({"type": "STEP", "data": action.tolist()}).encode()  
        self.sock.sendall(payload)  
          
        \# Wait for Response (Blocking)  
        data \= self.sock.recv(1024 \* 1024) \# Large buffer for maps  
        state \= json.loads(data)  
          
        obs \= self.\_process\_obs(state)  
        reward \= self.\_calculate\_reward(state)  
        done \= state\['game\_over'\]  
          
        return obs, reward, done, False, {}

    def reset(self, seed=None, options=None):  
        self.sock.sendall(json.dumps({"type": "RESET", "seed": seed}).encode())  
        \#... receive initial state...  
        return obs, {}

31

### **8.2 Parallel Training (Vectorization)**

RimWorld is a heavy application. Running it efficiently requires the SubprocVecEnv from StableBaselines3. We can launch multiple instances of the RimWorld executable, each passing a different port number command-line argument \-port 500X. The C\# mod reads Environment.GetCommandLineArgs() to bind to the correct port. This allows a single PPO algorithm to collect experience from 8 games simultaneously, significantly speeding up the "Wall-clock time to convergence".32

### **8.3 Neuro-Symbolic Hybrid Agents**

Given the difficulty of learning low-level pathfinding via RL, a hybrid approach is promising. We can use the **Rimworld\_AI\_Framework** (which integrates LLMs) to make high-level strategic decisions (e.g., "We are low on food, prioritize farming") and feed this "Intent" as a context vector to the RL agent, or use the RL agent to execute the specific moves required to fulfill the LLM's plan. This decomposes the problem: LLM handles the "Story" and "Strategy," while RL handles the "Tactics" and "Control".19

## ---

**9\. Optimization and Performance Tuning**

Training a decent agent requires millions of timesteps. Optimizing the "Ticks Per Second" (TPS) in training mode is non-negotiable.

### **9.1 Minimizing Overhead**

* **Disable Audio:** Audio processing consumes CPU. Disable via command line \-nosaudio.  
* **Texture Atlas Management:** RimWorld builds texture atlases for pawns. In training, we don't need visuals. Patches should disable PortraitsCache and PawnRenderer to save massive amounts of RAM and CPU.44  
* **Garbage Collection:** C\#’s GC is a killer. The interface mod must avoid new allocations in the update loop. Re-use buffers for the map grid arrays instead of allocating new ones every step.

### **9.2 The "RimSort" and "RimPy" Ecosystem**

Managing the interface mod and its dependencies (Harmony, Hugslib, MapDesigner) requires a robust mod manager. **RimSort** 45 is an open-source alternative to RimPy that supports CLI operations. This is crucial for "Headless" training on Linux servers, allowing us to programmatically sort the load order (Harmony first \-\> Core \-\> Interface Mod) before launching the game instances. Without correct load ordering, the Harmony patches will fail to apply, and the environment will not bind.45

## ---

**10\. Conclusion and Future Outlook**

Creating a Gymnasium environment for RimWorld is a significant software engineering undertaking that goes beyond simple API wrapping. It requires a deep understanding of the Unity engine’s execution model, the discipline to implement thread-safe dispatchers, and the creativity to map complex emergent gameplay mechanics into structured RL concepts.

By following the roadmap defined in this report—specifically the **Harmony-based Tick interception**, the **Synchronous TCP Bridge**, and the **Hierarchical Action Space**—researchers can unlock a testbed of unparalleled depth. RimWorld offers the unique opportunity to study agents that must balance immediate survival (eating, fighting) with long-term prosperity (building, researching) against an adversary (the Storyteller) that actively adapts to their strategies. This moves the field of Game AI away from the "perfect information, fixed rule" paradigm of Chess and Go, and towards the messy, chaotic, and human-centric challenges of general intelligence.

### **Table 1: Comparative Analysis of RimWorld Control Approaches**

| Feature | Low-Level (WASD Mod) | Mid-Level (Drafted Command) | High-Level (Work Priorities) |
| :---- | :---- | :---- | :---- |
| **Control Granularity** | Pixel-perfect movement | Cell-based positioning | Abstract task assignment |
| **Action Space Size** | Continuous / Small Discrete | Multi-Discrete (Large) | Small Discrete |
| **Pathfinding** | RL Learned (Hard) | Engine Native (Easy) | Engine Native (Easy) |
| **Strategic Depth** | Low (Tactical only) | **High (RTS Style)** | Medium (Management only) |
| **Suitability for RL** | Poor (Sparse rewards) | **Optimal (Balanced)** | Good (Sim-to-Real tasks) |

50

The path forward involves not just building this environment, but populating it with agents capable of "beating" the Storyteller—a feat that would mark a significant milestone in the history of AI in Games.

#### **Works cited**

1. reinforcement-learning-environment · GitHub Topics, accessed December 13, 2025, [https://github.com/topics/reinforcement-learning-environment](https://github.com/topics/reinforcement-learning-environment)  
2. EmmanuelMess/SimplifiedRimWorldRL: Very simple ... \- GitHub, accessed December 13, 2025, [https://github.com/EmmanuelMess/SimplifiedRimWorldRL](https://github.com/EmmanuelMess/SimplifiedRimWorldRL)  
3. pardeike/HarmonyRimWorld: A RimWorld mod that installs Harmony for all other mods \- GitHub, accessed December 13, 2025, [https://github.com/pardeike/HarmonyRimWorld](https://github.com/pardeike/HarmonyRimWorld)  
4. Colony wealth calculation question :: RimWorld General Discussions \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/5087338135409864127/](https://steamcommunity.com/app/294100/discussions/0/5087338135409864127/)  
5. Wealth and Wealth Management: What is Wealth, what counts, and more. : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/s39vkb/wealth\_and\_wealth\_management\_what\_is\_wealth\_what/](https://www.reddit.com/r/RimWorld/comments/s39vkb/wealth_and_wealth_management_what_is_wealth_what/)  
6. Map Designer Mod Showcase / Guide / Tutorial for Rimworld \- YouTube, accessed December 13, 2025, [https://www.youtube.com/watch?v=DTydAEaiCWQ](https://www.youtube.com/watch?v=DTydAEaiCWQ)  
7. Is there a way to create a map grid with the conditions I want? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/a6aoxo/is\_there\_a\_way\_to\_create\_a\_map\_grid\_with\_the/](https://www.reddit.com/r/RimWorld/comments/a6aoxo/is_there_a_way_to_create_a_map_grid_with_the/)  
8. Get Started with ML-Agents in Unity \- Part 3: Creating the 'Turtle Agent' Project \- YouTube, accessed December 13, 2025, [https://www.youtube.com/watch?v=rMZi1nt0pBw](https://www.youtube.com/watch?v=rMZi1nt0pBw)  
9. Need help. The game pauses automatically, any way to check what is causing this ?No errors while startup , No error logs .Just pauses automatically. Completely unplayable .I need to unpause every time .Anyone facing the same issue ?(Promise not using keyboard to Pause/Unpause) : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/pbam3r/need\_help\_the\_game\_pauses\_automatically\_any\_way/](https://www.reddit.com/r/RimWorld/comments/pbam3r/need_help_the_game_pauses_automatically_any_way/)  
10. I wanted to share this about MODDING in Rimworld \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/707749927473930642/](https://steamcommunity.com/app/294100/discussions/0/707749927473930642/)  
11. Design choice for not multithreading. :: RimWorld General Discussions \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/600774299444372854/](https://steamcommunity.com/app/294100/discussions/0/600774299444372854/)  
12. All resources must be loaded in the main thread error : r/rimworldmodding \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/rimworldmodding/comments/1jwiqpz/all\_resources\_must\_be\_loaded\_in\_the\_main\_thread/](https://www.reddit.com/r/rimworldmodding/comments/1jwiqpz/all_resources_must_be_loaded_in_the_main_thread/)  
13. Running code in main thread from another thread \- Stack Overflow, accessed December 13, 2025, [https://stackoverflow.com/questions/11123621/running-code-in-main-thread-from-another-thread](https://stackoverflow.com/questions/11123621/running-code-in-main-thread-from-another-thread)  
14. After weeks of development and learning CSharp from scratch, the Pawn Tracker mod is finally live\! : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/17t850j/after\_weeks\_of\_development\_and\_learning\_csharp/](https://www.reddit.com/r/RimWorld/comments/17t850j/after_weeks_of_development_and_learning_csharp/)  
15. ML-Agents Overview \- Unity \- Manual, accessed December 13, 2025, [https://docs.unity3d.com/Packages/com.unity.ml-agents%403.0/manual/index.html](https://docs.unity3d.com/Packages/com.unity.ml-agents%403.0/manual/index.html)  
16. Making a New Learning Environment \- Unity ML-Agents Toolkit, accessed December 13, 2025, [https://unity-technologies.github.io/ml-agents/Learning-Environment-Create-New/](https://unity-technologies.github.io/ml-agents/Learning-Environment-Create-New/)  
17. Use TcpClient and TcpListener \- .NET \- Microsoft Learn, accessed December 13, 2025, [https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/sockets/tcp-classes](https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/sockets/tcp-classes)  
18. Getting started with RimWorld modding on Linux \- arp242.net, accessed December 13, 2025, [https://www.arp242.net/rimworld-mod-linux.html](https://www.arp242.net/rimworld-mod-linux.html)  
19. oidahdsah0/Rimworld\_AI\_Framework: A revolutionary AI ... \- GitHub, accessed December 13, 2025, [https://github.com/oidahdsah0/Rimworld\_AI\_Framework](https://github.com/oidahdsah0/Rimworld_AI_Framework)  
20. Is there a way to reduce the performance degradation of large maps without compromising the size itself? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/10b3umb/is\_there\_a\_way\_to\_reduce\_the\_performance/](https://www.reddit.com/r/RimWorld/comments/10b3umb/is_there_a_way_to_reduce_the_performance/)  
21. Map size influence on performance. Please advise. Thank you. :: RimWorld General Discussions \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/1646544348825497125/](https://steamcommunity.com/app/294100/discussions/0/1646544348825497125/)  
22. Harmony Setup Guide for Rimworld Mod Creation \- YouTube, accessed December 13, 2025, [https://www.youtube.com/watch?v=g70QGY8fJ0k](https://www.youtube.com/watch?v=g70QGY8fJ0k)  
23. How to update your Mod from RimWorld from 1.0 to 1.1 and Harmony 1.2.0.1 to 2.0 · GitHub, accessed December 13, 2025, [https://gist.github.com/pardeike/08ff826bf40ee60452f02d85e59f32ff](https://gist.github.com/pardeike/08ff826bf40ee60452f02d85e59f32ff)  
24. Harmony patching : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/8mfx9p/harmony\_patching/](https://www.reddit.com/r/RimWorld/comments/8mfx9p/harmony_patching/)  
25. Sudden performance issues : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1ox1jpe/sudden\_performance\_issues/](https://www.reddit.com/r/RimWorld/comments/1ox1jpe/sudden_performance_issues/)  
26. Walk The World \- mod to explore every map tile manually \- is out\! : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1mn85no/walk\_the\_world\_mod\_to\_explore\_every\_map\_tile/](https://www.reddit.com/r/RimWorld/comments/1mn85no/walk_the_world_mod_to_explore_every_map_tile/)  
27. Steam Workshop::Map Preview \- RimWorld, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=2800857642](https://steamcommunity.com/sharedfiles/filedetails/?id=2800857642)  
28. Why exactly do large maps have worse performance? :: RimWorld General Discussions, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/4758704179141623089/?l=english](https://steamcommunity.com/app/294100/discussions/0/4758704179141623089/?l=english)  
29. How do I find the wealth of my colony? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/7fs50k/how\_do\_i\_find\_the\_wealth\_of\_my\_colony/](https://www.reddit.com/r/RimWorld/comments/7fs50k/how_do_i_find_the_wealth_of_my_colony/)  
30. check if pawn has thought (C\#) : r/rimworldmodding \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/rimworldmodding/comments/1augenh/check\_if\_pawn\_has\_thought\_c/](https://www.reddit.com/r/rimworldmodding/comments/1augenh/check_if_pawn_has_thought_c/)  
31. Reinforcement Learning with Gymnasium: A Practical Guide \- DataCamp, accessed December 13, 2025, [https://www.datacamp.com/tutorial/reinforcement-learning-with-gymnasium](https://www.datacamp.com/tutorial/reinforcement-learning-with-gymnasium)  
32. how do i design the action space for this in gym? : r/reinforcementlearning \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/reinforcementlearning/comments/17rdn16/how\_do\_i\_design\_the\_action\_space\_for\_this\_in\_gym/](https://www.reddit.com/r/reinforcementlearning/comments/17rdn16/how_do_i_design_the_action_space_for_this_in_gym/)  
33. Non-humanlike Pawn Control \- Workshop \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=3465881088](https://steamcommunity.com/sharedfiles/filedetails/?id=3465881088)  
34. New "AI Control" mode in Drafted Auto-Combat : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1o24klv/new\_ai\_control\_mode\_in\_drafted\_autocombat/](https://www.reddit.com/r/RimWorld/comments/1o24klv/new_ai_control_mode_in_drafted_autocombat/)  
35. Steam Workshop::\[KV\] Force Do Job \- RimWorld, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=1180719500](https://steamcommunity.com/sharedfiles/filedetails/?id=1180719500)  
36. lmgginspace\] Force Do Job \- Workshop \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/sharedfiles/filedetails/?id=3226046759](https://steamcommunity.com/sharedfiles/filedetails/?id=3226046759)  
37. Has anyone made a force job queue mod?? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/jl1w6x/has\_anyone\_made\_a\_force\_job\_queue\_mod/](https://www.reddit.com/r/RimWorld/comments/jl1w6x/has_anyone_made_a_force_job_queue_mod/)  
38. Building a Gymnasium Environment for the Startups Card Game | by Jeremy Kneebone, accessed December 13, 2025, [https://medium.com/@jeremykneebone/building-a-gymnasium-environment-for-the-startups-card-game-2a29914fbad7](https://medium.com/@jeremykneebone/building-a-gymnasium-environment-for-the-startups-card-game-2a29914fbad7)  
39. Why is target mood so low when the only bad thing is eating w/o a table? : r/RimWorld, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/118jzbz/why\_is\_target\_mood\_so\_low\_when\_the\_only\_bad\_thing/](https://www.reddit.com/r/RimWorld/comments/118jzbz/why_is_target_mood_so_low_when_the_only_bad_thing/)  
40. How to keep pawn's mood up? :: RimWorld Általános témák \- Steam Community, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/3471730015112071148/?l=hungarian](https://steamcommunity.com/app/294100/discussions/0/3471730015112071148/?l=hungarian)  
41. Rimnarrator is a local-only AI narrator mod for Rimworld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1p4uf5d/rimnarrator\_is\_a\_localonly\_ai\_narrator\_mod\_for/](https://www.reddit.com/r/RimWorld/comments/1p4uf5d/rimnarrator_is_a_localonly_ai_narrator_mod_for/)  
42. I Asked an AI to Design a Modpack | Rimworld: Android Utopia \#1 \- YouTube, accessed December 13, 2025, [https://www.youtube.com/watch?v=kSG\_6YGx6q0](https://www.youtube.com/watch?v=kSG_6YGx6q0)  
43. Spaces \- Gymnasium Documentation, accessed December 13, 2025, [https://gymnasium.farama.org/api/spaces/](https://gymnasium.farama.org/api/spaces/)  
44. My rimworld keeps giving me the error message when trying to load my modded world, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/126igk5/my\_rimworld\_keeps\_giving\_me\_the\_error\_message/](https://www.reddit.com/r/RimWorld/comments/126igk5/my_rimworld_keeps_giving_me_the_error_message/)  
45. RimSort is an open source mod manager for the video game RimWorld. There is support for Linux, Mac, and Windows, built from the ground up to be a reliable, community-managed alternative to RimPy Mod Manager. \- GitHub, accessed December 13, 2025, [https://github.com/RimSort/RimSort](https://github.com/RimSort/RimSort)  
46. RimSort \- GitHub, accessed December 13, 2025, [https://github.com/RimSort](https://github.com/RimSort)  
47. RimWorld Mod Menu 2025: Best Mods, Installation Guide & Top Features for Enhanced Gameplay \- GitHub, accessed December 13, 2025, [https://github.com/gordyr/RimWorld-mod-menu](https://github.com/gordyr/RimWorld-mod-menu)  
48. Deep Dive: RimPy a powerful external mod tool. : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/tzd90w/deep\_dive\_rimpy\_a\_powerful\_external\_mod\_tool/](https://www.reddit.com/r/RimWorld/comments/tzd90w/deep_dive_rimpy_a_powerful_external_mod_tool/)  
49. \[TOOL\] RimPy \- Rimworld Mod Manager and Sorter, accessed December 13, 2025, [https://steamcommunity.com/app/294100/discussions/0/1643171537292525456/](https://steamcommunity.com/app/294100/discussions/0/1643171537292525456/)  
50. I've made WASDControl for single pawn (top-down shooters alike) : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/1k6p59e/ive\_made\_wasdcontrol\_for\_single\_pawn\_topdown/](https://www.reddit.com/r/RimWorld/comments/1k6p59e/ive_made_wasdcontrol_for_single_pawn_topdown/)  
51. Curious self resolving issue: All work types set to max priority \[1.2\] : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/l37898/curious\_self\_resolving\_issue\_all\_work\_types\_set/](https://www.reddit.com/r/RimWorld/comments/l37898/curious_self_resolving_issue_all_work_types_set/)  
52. Is there a mod to force fabricors to prioritize work? : r/RimWorld \- Reddit, accessed December 13, 2025, [https://www.reddit.com/r/RimWorld/comments/14l4kqs/is\_there\_a\_mod\_to\_force\_fabricors\_to\_prioritize/](https://www.reddit.com/r/RimWorld/comments/14l4kqs/is_there_a_mod_to_force_fabricors_to_prioritize/)