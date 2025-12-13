using System;
using System.Collections.Concurrent;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Google.Protobuf;
using RimTCP.Adapters;
using RimTCP.Protos;
using RimTCP.Services;
using RimWorld;
using Verse;

namespace RimTCP
{
    /// <summary>
    /// High-performance TCP server using Protocol Buffers for serialization.
    /// Handles communication with Python RL agent without requiring native gRPC libraries.
    /// Phase II: Uses RichStateMessage with high-fidelity ColonistState extraction.
    /// Phase III: Supports Hybrid Valve with velocity tracking and delta compression.
    /// </summary>
    public class TcpProtobufServer
    {
        private TcpListener _listener;
        private TcpClient _client;
        private NetworkStream _stream;
        private Thread _serverThread;
        private bool _isRunning;
        private readonly int _port;

        // Thread-safe queue for commands from client (background thread) to game (main thread)
        private readonly ConcurrentQueue<CommandMessage> _commandQueue =
            new ConcurrentQueue<CommandMessage>();

        // Thread-safe queue for responses from game (main thread) to client (background thread)
        private readonly ConcurrentQueue<RichStateMessage> _responseQueue =
            new ConcurrentQueue<RichStateMessage>();

        // Game state management
        private static long _currentTick = 0;
        private static readonly object _tickLock = new object();

        // Phase III: Velocity and timing tracking
        private long _lastFrameTimestamp = 0; // Timestamp of last frame in milliseconds
        private readonly ConcurrentDictionary<int, Vector3> _lastPositions =
            new ConcurrentDictionary<int, Vector3>();
        private readonly ConcurrentDictionary<int, long> _lastPositionTimes =
            new ConcurrentDictionary<int, long>();

        // Diagnostics: Connection and message counters for structured logging
        private long _totalConnectionsAccepted = 0;
        private long _totalMessagesReceived = 0;
        private long _totalMessagesSent = 0;
        private long _totalErrors = 0;
        private DateTime _serverStartTime;
        private DateTime _lastClientConnectTime;
        private DateTime _lastHeartbeatTime;
        private const int HeartbeatIntervalSeconds = 30;

        // Phase VI: RESET (save-load cycle) tracking
        private volatile bool _resetInProgress;
        private volatile string _resetSaveName;
        private volatile bool _resetObservedLongEvent;
        private volatile bool _resetObservedNotReady;
        private volatile string _lastResetError;

        public bool IsConnected => _client != null && _client.Connected;
        public bool IsRunning => _isRunning;

        // Expose stats for external monitoring
        public long TotalConnectionsAccepted => _totalConnectionsAccepted;
        public long TotalMessagesReceived => _totalMessagesReceived;
        public long TotalMessagesSent => _totalMessagesSent;
        public long TotalErrors => _totalErrors;

        public TcpProtobufServer(int port = 50051)
        {
            _port = port;
        }

        public void Start()
        {
            if (_isRunning)
            {
                Log.Warning($"{Constants.LogPrefix} Server is already running");
                return;
            }

            _isRunning = true;
            _serverStartTime = DateTime.UtcNow;
            _serverThread = new Thread(ServerLoop)
            {
                IsBackground = true,
                Name = "RimTCP-TCP-Server",
            };
            _serverThread.Start();

            Log.Message(
                $"{Constants.LogPrefix} TCP Protobuf server started on port {_port} at {_serverStartTime:yyyy-MM-dd HH:mm:ss} UTC"
            );
        }

        public void Stop()
        {
            _isRunning = false;
            var uptime = DateTime.UtcNow - _serverStartTime;

            try
            {
                _stream?.Close();
                _client?.Close();
                _listener?.Stop();
            }
            catch (Exception e)
            {
                Log.Warning($"{Constants.LogPrefix} Error during shutdown: {e.Message}");
            }

            Log.Message(
                $"{Constants.LogPrefix} TCP server stopped. Stats: uptime={uptime.TotalSeconds:F1}s, connections={_totalConnectionsAccepted}, msgs_rx={_totalMessagesReceived}, msgs_tx={_totalMessagesSent}, errors={_totalErrors}"
            );
        }

        private void ServerLoop()
        {
            try
            {
                const int ListenerPollIntervalMs = 100;
                var bindAddress = GetBindAddress();
                _listener = new TcpListener(bindAddress, _port);
                _listener.Start();
                Log.Message(
                    $"{Constants.LogPrefix} Waiting for Python client connection on {FormatBindAddress(bindAddress)}:{_port}..."
                );

                while (_isRunning)
                {
                    // Accept connection (blocking call)
                    if (_listener.Pending())
                    {
                        _client = _listener.AcceptTcpClient();
                        _client.NoDelay = true; // Disable Nagle's algorithm for low latency
                        _stream = _client.GetStream();

                        _totalConnectionsAccepted++;
                        _lastClientConnectTime = DateTime.UtcNow;
                        Log.Message(
                            $"{Constants.LogPrefix} Client connected! connection_id={_totalConnectionsAccepted}, time={_lastClientConnectTime:HH:mm:ss}"
                        );

                        // Handle this client until disconnect
                        HandleClient();

                        var connectionDuration = DateTime.UtcNow - _lastClientConnectTime;
                        Log.Message(
                            $"{Constants.LogPrefix} Client disconnected after {connectionDuration.TotalSeconds:F1}s, waiting for new connection..."
                        );
                    }
                    else
                    {
                        Thread.Sleep(ListenerPollIntervalMs); // Avoid busy-waiting
                    }
                }
            }
            catch (Exception e)
            {
                Log.Error($"{Constants.LogPrefix} Server error: {e.Message}\n{e.StackTrace}");
            }
            finally
            {
                _listener?.Stop();
            }
        }

        private static IPAddress GetBindAddress()
        {
            try
            {
                // Default to loopback for safety. Docker/multi-host scenarios can opt-in.
                // Examples:
                // - RIMTCP_BIND_ALL=1
                // - RIMTCP_BIND_ADDRESS=0.0.0.0
                var bindAll = Environment.GetEnvironmentVariable("RIMTCP_BIND_ALL");
                if (!string.IsNullOrWhiteSpace(bindAll))
                {
                    bindAll = bindAll.Trim();
                    if (
                        bindAll == "1"
                        || bindAll.Equals("true", StringComparison.OrdinalIgnoreCase)
                    )
                    {
                        return IPAddress.Any;
                    }
                }

                var bindAddressRaw = Environment.GetEnvironmentVariable("RIMTCP_BIND_ADDRESS");
                if (string.IsNullOrWhiteSpace(bindAddressRaw))
                {
                    return IPAddress.Loopback;
                }

                bindAddressRaw = bindAddressRaw.Trim();
                if (
                    bindAddressRaw == "0.0.0.0"
                    || bindAddressRaw == "*"
                    || bindAddressRaw.Equals("any", StringComparison.OrdinalIgnoreCase)
                )
                {
                    return IPAddress.Any;
                }

                if (bindAddressRaw.Equals("localhost", StringComparison.OrdinalIgnoreCase))
                {
                    return IPAddress.Loopback;
                }

                return IPAddress.Parse(bindAddressRaw);
            }
            catch (Exception e)
            {
                Log.Warning(
                    $"{Constants.LogPrefix} Failed to parse bind address env vars; defaulting to loopback. Error: {e.Message}"
                );
                return IPAddress.Loopback;
            }
        }

        private static string FormatBindAddress(IPAddress address)
        {
            if (address == null)
                return "<null>";
            if (address.Equals(IPAddress.Any))
                return "0.0.0.0";
            if (address.Equals(IPAddress.Loopback))
                return "127.0.0.1";
            return address.ToString();
        }

        private void HandleClient()
        {
            long clientMsgsReceived = 0;
            long clientMsgsSent = 0;

            try
            {
                const int ResponseTimeoutMs = 5000; // 5 seconds
                const int PollingIntervalMs = 10; // 10ms

                while (_isRunning && _client.Connected)
                {
                    // Read message from client
                    var command = ReadMessage<CommandMessage>(_stream);
                    if (command == null)
                        break; // Connection closed

                    clientMsgsReceived++;
                    _totalMessagesReceived++;

                    // Queue command for main thread processing
                    _commandQueue.Enqueue(command);

                    // Wait for response from main thread (with timeout)
                    RichStateMessage response = null;
                    int timeout = 0;
                    while (timeout < ResponseTimeoutMs && !_responseQueue.TryDequeue(out response))
                    {
                        Thread.Sleep(PollingIntervalMs);
                        timeout += PollingIntervalMs;
                    }

                    if (response == null)
                    {
                        // Timeout - send error response
                        response = new RichStateMessage
                        {
                            FrameId = _currentTick,
                            IsReady = false,
                            StatusMessage = "Timeout waiting for game response",
                            TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                        };
                        Log.Warning(
                            $"{Constants.LogPrefix} Response timeout for command {command.Type} after {ResponseTimeoutMs}ms"
                        );
                    }

                    // Send response back to client
                    WriteMessage(_stream, response);
                    clientMsgsSent++;
                    _totalMessagesSent++;
                }
            }
            catch (Exception e)
            {
                _totalErrors++;
                if (_isRunning) // Only log if not intentional shutdown
                {
                    Log.Warning(
                        $"{Constants.LogPrefix} Client handler error: {e.Message}, msgs_rx={clientMsgsReceived}, msgs_tx={clientMsgsSent}"
                    );
                }
            }
            finally
            {
                _stream?.Close();
                _client?.Close();
            }
        }

        /// <summary>
        /// TASK-008: Heartbeat for server health monitoring
        /// Call periodically from main thread to log server status
        /// </summary>
        public void Heartbeat()
        {
            if (!_isRunning)
                return;

            var now = DateTime.UtcNow;
            if ((now - _lastHeartbeatTime).TotalSeconds >= HeartbeatIntervalSeconds)
            {
                _lastHeartbeatTime = now;
                var uptime = now - _serverStartTime;
                var connected = IsConnected ? 1 : 0;

                Log.Message(
                    $"{Constants.LogPrefix} Heartbeat: uptime={uptime.TotalMinutes:F1}min, connected={connected}, "
                        + $"conns_total={_totalConnectionsAccepted}, msgs_rx={_totalMessagesReceived}, "
                        + $"msgs_tx={_totalMessagesSent}, errors={_totalErrors}"
                );
            }
        }

        /// <summary>
        /// Called from main thread to process queued commands
        /// </summary>
        public void ProcessCommands()
        {
            UpdateResetProgress();
            while (_commandQueue.TryDequeue(out var command))
            {
                try
                {
                    var response = ExecuteCommand(command);
                    _responseQueue.Enqueue(response);
                }
                catch (Exception e)
                {
                    _totalErrors++;
                    Log.Error(
                        $"{Constants.LogPrefix} Error executing command {command.Type}: {e.Message}\n{e.StackTrace}"
                    );
                    _responseQueue.Enqueue(
                        new RichStateMessage
                        {
                            FrameId = _currentTick,
                            IsReady = false,
                            StatusMessage = $"Error: {e.Message}",
                            TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                        }
                    );
                }
            }
        }

        private RichStateMessage ExecuteCommand(CommandMessage command)
        {
            Log.Message($"{Constants.LogPrefix} Executing command: {command.Type}");

            var state = new RichStateMessage
            {
                FrameId = _currentTick,
                IsReady = false,
                StatusMessage = $"Command {command.Type} executed",
                TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                ResetInProgress = _resetInProgress,
                ResetSaveName = _resetSaveName ?? string.Empty,
            };

            // If a reset is currently running, reject commands that would mutate sim state.
            // QueryState is still allowed so clients can poll for completion.
            if (
                _resetInProgress
                && command.Type != CommandType.QueryState
                && command.Type != CommandType.Reset
            )
            {
                state.IsReady = false;
                state.StatusMessage = "Reset in progress - try again after reset completes";
                return state;
            }

            // RESET must be allowed even when no game is loaded yet.
            // Other commands require a loaded game.
            if (command.Type != CommandType.Reset)
            {
                if (Current.Game == null || Find.CurrentMap == null)
                {
                    state.StatusMessage =
                        "Game not loaded - please load a save or start a new game";
                    return state;
                }

                state.IsReady = true;
            }

            switch (command.Type)
            {
                case CommandType.Step:
                    // Phase III: Grant permission to advance ticks
                    if (RimTcpMod.TrainingMode)
                    {
                        int ticksToRun = command.TicksToRun > 0 ? command.TicksToRun : 60;

                        // Deterministic stepping: keep the game paused and advance ticks explicitly.
                        // Relying on the normal tick scheduler is not reliable in headless quicktest.
                        Find.TickManager.CurTimeSpeed = TimeSpeed.Paused;

                        // Allow ticks and run them immediately on the main thread.
                        RimTcpMod.TicksToRun = ticksToRun;
                        RimTcpMod.StepPermitted = true;

                        Log.Message(
                            $"{Constants.LogPrefix} STEP command: running {ticksToRun} ticks (Training Mode)"
                        );
                        for (int i = 0; i < ticksToRun; i++)
                        {
                            Find.TickManager.DoSingleTick();
                        }

                        state.StatusMessage = $"Step completed: {ticksToRun} ticks (Training Mode)";
                    }
                    else
                    {
                        // In inference mode, STEP is not needed - game runs freely
                        state.StatusMessage =
                            "Game running freely (Inference Mode) - STEP command not needed";
                    }
                    break;

                case CommandType.QueryState:
                    // Return current state without advancing
                    state.StatusMessage = RimTcpMod.TrainingMode
                        ? "State queried (Training Mode)"
                        : "State queried (Inference Mode)";
                    break;

                case CommandType.SetMode:
                    // Phase III: Switch between training and inference modes
                    bool newMode = (command.Mode == ExecutionMode.ModeTraining);
                    string modeStr = newMode
                        ? "TRAINING (Synchronous)"
                        : "INFERENCE (Asynchronous)";

                    if (RimTcpMod.TrainingMode != newMode)
                    {
                        RimTcpMod.TrainingMode = newMode;
                        RimTcpMod.StepPermitted = false; // Reset step permission on mode change
                        RimTcpMod.TicksToRun = 0;

                        // When switching to inference mode, ensure game is unpaused
                        if (!newMode && Find.TickManager.Paused)
                        {
                            Find.TickManager.CurTimeSpeed = TimeSpeed.Normal;
                            Log.Message(
                                $"{Constants.LogPrefix} Auto-unpaused game for inference mode"
                            );
                        }

                        Log.Message($"{Constants.LogPrefix} Mode switched to: {modeStr}");
                        state.StatusMessage = $"Mode changed to {modeStr}";
                    }
                    else
                    {
                        state.StatusMessage = $"Already in {modeStr} mode";
                    }
                    break;

                case CommandType.SetSpeed:
                    // Set game speed for testing automation
                    TimeSpeed newSpeed = ConvertGameSpeed(command.Speed);
                    TimeSpeed oldSpeed = Find.TickManager.CurTimeSpeed;

                    if (oldSpeed != newSpeed)
                    {
                        Find.TickManager.CurTimeSpeed = newSpeed;
                        Log.Message(
                            $"{Constants.LogPrefix} Game speed changed: {oldSpeed} → {newSpeed}"
                        );
                        state.StatusMessage = $"Speed changed to {newSpeed}";
                    }
                    else
                    {
                        state.StatusMessage = $"Already at {newSpeed}";
                    }
                    break;

                case CommandType.Reset:
                    ExecuteReset(command, state);
                    break;

                case CommandType.ExecuteAction:
                    // Phase VI: Action execution requires pawn job queue integration
                    // Intent-based actions (DRAFT, GOTO, ATTACK) need validation and pathfinding
                    state.StatusMessage = "Action execution planned for Phase VI";
                    Log.Message(
                        $"{Constants.LogPrefix} ExecuteAction received - not yet implemented (Phase VI)"
                    );
                    break;
            }

            // Populate state with game data (with profiling if enabled)
            if (_resetInProgress)
            {
                // During reset we do not attempt to extract full state (it may be inconsistent).
                state.IsReady = false;
                state.ResetInProgress = true;
                state.ResetSaveName = _resetSaveName ?? string.Empty;
                state.StatusMessage = string.IsNullOrWhiteSpace(_lastResetError)
                    ? $"Reset in progress (loading save '{state.ResetSaveName}')"
                    : $"Reset in progress (last error: {_lastResetError})";
                return state;
            }

            var cycleStart = System.Diagnostics.Stopwatch.StartNew();
            PopulateGameState(state);
            cycleStart.Stop();

            // Finalize profiling stats
            Diagnostics.PerformanceProfiler.FinalizeStats(cycleStart.ElapsedMilliseconds);

            // Log performance stats periodically (every 100 frames)
            if (state.FrameId % 100 == 0)
            {
                Diagnostics.PerformanceProfiler.LogStats();
            }

            return state;
        }

        /// <summary>
        /// Populate rich game state with high-fidelity colonist data
        /// Uses ColonistService + ColonistAdapter for efficient DTO→Protobuf conversion
        /// Phase III: Adds velocity tracking and delta time calculation
        /// </summary>
        private void PopulateGameState(RichStateMessage state)
        {
            try
            {
                // Phase VI: expose reset status on every state message.
                state.ResetInProgress = _resetInProgress;
                state.ResetSaveName = _resetSaveName ?? string.Empty;

                if (_resetInProgress)
                {
                    state.IsReady = false;
                    state.StatusMessage = string.IsNullOrWhiteSpace(_lastResetError)
                        ? $"Reset in progress (loading save '{state.ResetSaveName}')"
                        : $"Reset in progress (last error: {_lastResetError})";
                    return;
                }

                if (!ServiceRegistry.IsGameReady())
                {
                    state.IsReady = false;
                    state.StatusMessage = "Game not loaded";
                    return;
                }

                lock (_tickLock)
                {
                    state.FrameId = Find.TickManager.TicksAbs;
                    _currentTick = state.FrameId;
                }

                // Phase III: Calculate delta time since last frame
                long currentTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                if (_lastFrameTimestamp > 0)
                {
                    state.DeltaTimeMs = currentTime - _lastFrameTimestamp;
                }
                else
                {
                    state.DeltaTimeMs = 0; // First frame
                }
                _lastFrameTimestamp = currentTime;
                state.TimestampMs = currentTime;

                // Phase III: Set current execution mode
                state.CurrentMode = RimTcpMod.TrainingMode
                    ? ExecutionMode.ModeTraining
                    : ExecutionMode.ModeInference;

                const int TicksPerDay = 60000;
                const int BaseYear = 5500;
                const int TicksPerYear = 360000;

                // Get weather from MapService
                var mapId = ServiceRegistry.GetCurrentMapId();
                var weather = ServiceRegistry.Maps.GetWeather(mapId);

                // Global state
                state.Global = new GlobalState
                {
                    Temperature = weather.Temperature,
                    Weather = weather.Weather,
                    Day = Find.TickManager.TicksAbs / TicksPerDay,
                    Year = BaseYear + (Find.TickManager.TicksAbs / TicksPerYear),
                };

                // Phase II: Get detailed colonist data via Service→DTO→Protobuf pipeline
                var colonistDTOs = ServiceRegistry.Colonists.GetColonistsDetailed();
                var colonistAdapter = new ColonistAdapter();

                foreach (var dto in colonistDTOs)
                {
                    var colonistState = colonistAdapter.ToProtobuf(dto);
                    state.Colonists.Add(colonistState);

                    // Phase III: Calculate velocity for position extrapolation
                    CalculateVelocity(colonistState, currentTime);
                }

                // Phase V: Add rich map, incident, and world state
                PopulatePhaseVState(state, mapId);

                // Phase III: In inference mode, could implement delta compression here
                // For now, always send full state (delta compression is an optimization)
                state.IsDelta = false;

                Log.Message(
                    $"{Constants.LogPrefix} Populated state: {state.Colonists.Count} colonists, {state.Map?.Buildings?.Count ?? 0} buildings, frame {state.FrameId}, dt={state.DeltaTimeMs}ms"
                );
            }
            catch (Exception e)
            {
                Log.Warning(
                    $"{Constants.LogPrefix} Error populating state: {e.Message}\n{e.StackTrace}"
                );
                state.IsReady = false;
                state.StatusMessage = $"Error populating state: {e.Message}";
            }
        }

        private void ExecuteReset(CommandMessage command, RichStateMessage state)
        {
            if (_resetInProgress)
            {
                state.IsReady = false;
                state.StatusMessage = "Reset already in progress";
                state.ResetInProgress = true;
                state.ResetSaveName = _resetSaveName ?? string.Empty;
                return;
            }

            var saveName = !string.IsNullOrWhiteSpace(command.ResetSaveName)
                ? command.ResetSaveName.Trim()
                : GetResetSaveNameFromEnv();

            if (string.IsNullOrWhiteSpace(saveName))
            {
                state.IsReady = false;
                state.StatusMessage =
                    "RESET requires a save name (CommandMessage.reset_save_name) or env var RIMTCP_RESET_SAVE";
                return;
            }

            _resetInProgress = true;
            _resetSaveName = saveName;
            _resetObservedLongEvent = false;
            _resetObservedNotReady = false;
            _lastResetError = null;

            // Ensure we don't accidentally advance the sim during load.
            RimTcpMod.StepPermitted = false;
            RimTcpMod.TicksToRun = 0;

            try
            {
                Log.Message($"{Constants.LogPrefix} RESET initiated: loading save '{saveName}'");

                // The actual load is queued as a long event so RimWorld can load safely.
                QueueLongEvent(
                    () =>
                    {
                        LoadSaveByReflection(saveName);
                    },
                    $"RimTCP: Loading save '{saveName}'"
                );

                state.IsReady = false;
                state.ResetInProgress = true;
                state.ResetSaveName = saveName;
                state.StatusMessage = $"Reset initiated: loading save '{saveName}'";
            }
            catch (Exception ex)
            {
                _lastResetError = ex.Message;
                _resetInProgress = false;
                state.IsReady = false;
                state.ResetInProgress = false;
                state.ResetSaveName = saveName;
                state.StatusMessage = $"Reset failed to start: {ex.Message}";

                Log.Error(
                    $"{Constants.LogPrefix} RESET failed to start for save '{saveName}': {ex.Message}\n{ex.StackTrace}"
                );
            }
        }

        private void UpdateResetProgress()
        {
            if (!_resetInProgress)
                return;

            try
            {
                if (IsAnyLongEventNowOrWaiting())
                {
                    _resetObservedLongEvent = true;
                }

                if (!ServiceRegistry.IsGameReady())
                {
                    _resetObservedNotReady = true;
                }

                // Only consider reset complete after we have observed the load cycle begin.
                if (
                    (_resetObservedLongEvent || _resetObservedNotReady)
                    && ServiceRegistry.IsGameReady()
                    && !IsAnyLongEventNowOrWaiting()
                )
                {
                    Log.Message(
                        $"{Constants.LogPrefix} RESET complete: save '{_resetSaveName}' loaded"
                    );

                    _resetInProgress = false;
                    _resetObservedLongEvent = false;
                    _resetObservedNotReady = false;
                    _lastResetError = null;

                    // Reinitialize services to avoid stale state after load.
                    ServiceRegistry.Reset();
                    ServiceRegistry.Initialize();

                    // Clear motion tracking to avoid bogus velocity deltas.
                    _lastPositions.Clear();
                    _lastPositionTimes.Clear();
                    _lastFrameTimestamp = 0;
                }
            }
            catch (Exception ex)
            {
                // Keep reset running; expose error via state messages.
                _lastResetError = ex.Message;
            }
        }

        private static string GetResetSaveNameFromEnv()
        {
            var raw = Environment.GetEnvironmentVariable("RIMTCP_RESET_SAVE");
            return string.IsNullOrWhiteSpace(raw) ? null : raw.Trim();
        }

        private static void LoadSaveByReflection(string saveName)
        {
            if (string.IsNullOrWhiteSpace(saveName))
            {
                throw new ArgumentException("Save name must be non-empty", nameof(saveName));
            }

            var gameAssembly = typeof(Root).Assembly;
            var loaderType =
                gameAssembly.GetType("Verse.GameDataSaveLoader")
                ?? gameAssembly.GetType("RimWorld.GameDataSaveLoader");

            if (loaderType == null)
            {
                throw new InvalidOperationException(
                    "Could not find GameDataSaveLoader type (expected Verse.GameDataSaveLoader)"
                );
            }

            // Prefer a LoadGame(string) method.
            var loadMethod = loaderType.GetMethod(
                "LoadGame",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static,
                binder: null,
                types: new[] { typeof(string) },
                modifiers: null
            );

            if (loadMethod == null)
            {
                throw new InvalidOperationException(
                    "Could not find static LoadGame(string) method on GameDataSaveLoader"
                );
            }

            loadMethod.Invoke(null, new object[] { saveName });
        }

        private static bool IsAnyLongEventNowOrWaiting()
        {
            try
            {
                var type = typeof(LongEventHandler);
                var prop = type.GetProperty(
                    "AnyEventNowOrWaiting",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static
                );
                if (prop != null && prop.PropertyType == typeof(bool))
                {
                    return (bool)prop.GetValue(null);
                }

                var method = type.GetMethod(
                    "AnyEventNowOrWaiting",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static,
                    binder: null,
                    types: Type.EmptyTypes,
                    modifiers: null
                );
                if (method != null && method.ReturnType == typeof(bool))
                {
                    return (bool)method.Invoke(null, null);
                }
            }
            catch
            {
                // If detection fails, assume no long events.
            }

            return false;
        }

        private static void QueueLongEvent(System.Action action, string label)
        {
            if (action == null)
                throw new ArgumentNullException(nameof(action));

            var type = typeof(LongEventHandler);
            var methods = type.GetMethods(
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static
                )
                .Where(m => m.Name == "QueueLongEvent")
                .ToArray();

            foreach (var method in methods)
            {
                var parameters = method.GetParameters();
                if (parameters.Length < 3)
                    continue;

                if (!typeof(System.Action).IsAssignableFrom(parameters[0].ParameterType))
                    continue;
                if (parameters[1].ParameterType != typeof(string))
                    continue;
                if (parameters[2].ParameterType != typeof(bool))
                    continue;

                var args = new object[parameters.Length];
                args[0] = action;
                args[1] = label;
                args[2] = false; // canReturnToGame

                for (int i = 3; i < parameters.Length; i++)
                {
                    var pType = parameters[i].ParameterType;
                    args[i] = pType.IsValueType ? Activator.CreateInstance(pType) : null;
                }

                method.Invoke(null, args);
                return;
            }

            throw new InvalidOperationException(
                "Could not find a compatible LongEventHandler.QueueLongEvent overload"
            );
        }

        /// <summary>
        /// Calculate velocity vector for an entity based on position history
        /// Allows Python agent to extrapolate position under latency
        /// </summary>
        private void CalculateVelocity(ColonistState colonist, long currentTime)
        {
            int colonistId = colonist.ThingId;
            var currentPos = colonist.Position;

            // Initialize velocity to zero
            colonist.Velocity = new Vector3
            {
                X = 0,
                Y = 0,
                Z = 0,
            };

            if (
                _lastPositions.TryGetValue(colonistId, out var lastPos)
                && _lastPositionTimes.TryGetValue(colonistId, out var lastTime)
            )
            {
                // Calculate time delta in seconds
                float deltaSeconds = (currentTime - lastTime) / 1000.0f;

                if (deltaSeconds > 0.001f) // Avoid division by near-zero
                {
                    // Calculate velocity (units per second)
                    float velocityX = (currentPos.X - lastPos.X) / deltaSeconds;
                    float velocityY = (currentPos.Y - lastPos.Y) / deltaSeconds;
                    float velocityZ = (currentPos.Z - lastPos.Z) / deltaSeconds;

                    colonist.Velocity = new Vector3
                    {
                        X = velocityX,
                        Y = velocityY,
                        Z = velocityZ,
                    };
                }
            }

            // Update position history
            _lastPositions[colonistId] = new Vector3
            {
                X = currentPos.X,
                Y = currentPos.Y,
                Z = currentPos.Z,
            };
            _lastPositionTimes[colonistId] = currentTime;
        }

        /// <summary>
        /// Read a length-prefixed protobuf message from stream
        /// </summary>
        private T ReadMessage<T>(NetworkStream stream)
            where T : IMessage<T>, new()
        {
            try
            {
                // Read 4-byte length prefix (big-endian)
                byte[] lengthBytes = new byte[4];
                int bytesRead = stream.Read(lengthBytes, 0, 4);
                if (bytesRead == 0)
                    return default(T); // Connection closed

                if (BitConverter.IsLittleEndian)
                    Array.Reverse(lengthBytes);

                int length = BitConverter.ToInt32(lengthBytes, 0);
                const int MaxMessageSizeBytes = 10 * 1024 * 1024;
                if (length <= 0 || length > MaxMessageSizeBytes) // 10MB max
                {
                    throw new InvalidDataException($"Invalid message length: {length}");
                }

                // Read message data
                byte[] buffer = new byte[length];
                int totalRead = 0;
                while (totalRead < length)
                {
                    int read = stream.Read(buffer, totalRead, length - totalRead);
                    if (read == 0)
                        throw new IOException("Connection closed while reading message");
                    totalRead += read;
                }

                // Deserialize protobuf
                var parser = new MessageParser<T>(() => new T());
                return parser.ParseFrom(buffer);
            }
            catch (IOException)
            {
                return default(T); // Connection closed
            }
        }

        /// <summary>
        /// Write a length-prefixed protobuf message to stream
        /// </summary>
        private void WriteMessage<T>(NetworkStream stream, T message)
            where T : IMessage
        {
            // Serialize to bytes
            byte[] data = message.ToByteArray();

            // Write length prefix (big-endian)
            byte[] lengthBytes = BitConverter.GetBytes(data.Length);
            if (BitConverter.IsLittleEndian)
                Array.Reverse(lengthBytes);

            stream.Write(lengthBytes, 0, 4);
            stream.Write(data, 0, data.Length);
            stream.Flush();
        }

        /// <summary>
        /// Phase V: Populate map, incident, and world state for complete observability
        /// Uses MapService, IncidentService, and extracts world data
        /// Target: <5ms total for full state extraction
        /// </summary>
        private void PopulatePhaseVState(RichStateMessage state, int mapId)
        {
            try
            {
                var map = MapService.GetMapByID(mapId);
                if (map == null)
                    return;

                // Start profiling map extraction
                Diagnostics.PerformanceProfiler.StartMapExtraction();

                // Get map state with terrain, buildings, items, zones, rooms
                var mapService = ServiceRegistry.Maps;
                var mapDto = new DTOs.MapDTO
                {
                    Id = mapId,
                    SizeX = map.Size.x,
                    SizeY = map.Size.z,
                    SizeZ = map.Size.y,
                    Biome = map.Biome?.defName ?? "Unknown",
                };

                // Get buildings
                mapDto.Buildings = mapService.GetMapBuildings(mapId);

                // Get zones
                var zonesData = mapService.GetMapZonesAndAreas(mapId);
                mapDto.Zones = zonesData.Zones;

                // Get rooms
                var roomsData = mapService.GetMapRooms(mapId);
                if (roomsData?.Rooms != null)
                {
                    foreach (var room in roomsData.Rooms)
                    {
                        mapDto.Rooms.Add(room);
                    }
                }

                // Convert to protobuf
                state.Map = MapAdapter.ToProtobuf(mapDto);

                // End profiling map extraction
                Diagnostics.PerformanceProfiler.EndMapExtraction(
                    state.Map?.Buildings?.Count ?? 0,
                    state.Map?.Items?.Count ?? 0
                );

                // Start profiling incident extraction
                Diagnostics.PerformanceProfiler.StartIncidentExtraction();

                // Get incident state
                var incidentService = ServiceRegistry.Incidents;
                var incidentsDto = incidentService.GetIncidents(mapId);
                var questsDto = incidentService.GetQuests();

                // Extract storyteller data
                var storytellerDto = new DTOs.StorytellerDTO
                {
                    DefName = Find.Storyteller?.def?.defName ?? "Unknown",
                    Label = Find.Storyteller?.def?.label ?? "Storyteller",
                    Difficulty = Find.Storyteller?.difficulty?.threatScale ?? 1.0f,
                    ThreatScale = Find.Storyteller?.difficulty?.threatScale ?? 1.0f,
                    // TicksSinceLastThreat not directly accessible - would require incident history tracking
                    TicksSinceLastThreat = 0,
                };

                // Get game conditions
                var conditions = map
                    .GameConditionManager?.ActiveConditions?.Select(c => new DTOs.GameConditionDTO
                    {
                        DefName = c.def?.defName ?? "Unknown",
                        Label = c.def?.label ?? c.def?.defName ?? "Condition",
                        TicksPassed = c.TicksPassed,
                        TicksLeft = c.TicksLeft,
                        Permanent = c.Permanent,
                    })
                    .ToList();

                state.Incidents = IncidentAdapter.ToProtobuf(
                    incidentsDto,
                    questsDto,
                    storytellerDto,
                    conditions
                );

                // End profiling incident extraction
                Diagnostics.PerformanceProfiler.EndIncidentExtraction(
                    state.Incidents?.IncidentHistory?.Count ?? 0
                );

                // Start profiling world extraction
                Diagnostics.PerformanceProfiler.StartWorldExtraction();

                // World state (factions, settlements, caravans)
                var worldDto = new DTOs.WorldStateDTO
                {
                    TileCount = Find.World?.grid?.TilesCount ?? 0,
                    // Coverage calculation would require tracking revealed tiles - expensive to compute
                    CoveragePercent = 0,
                    SeedString = Find.World?.info?.seedString ?? "",
                    PlanetName = Find.World?.info?.name ?? "Unknown",
                };

                // Get factions
                if (Find.FactionManager?.AllFactionsListForReading != null)
                {
                    foreach (var faction in Find.FactionManager.AllFactionsListForReading)
                    {
                        // Count settlements for this faction
                        var settlementCount =
                            Find.WorldObjects?.Settlements?.Count(s => s.Faction == faction) ?? 0;
                        if (!faction.IsPlayer)
                        {
                            worldDto.Factions.Add(
                                new DTOs.FactionDTO
                                {
                                    FactionId = faction.loadID,
                                    DefName = faction.def?.defName ?? "Unknown",
                                    Name = faction.Name ?? faction.def?.label ?? "Faction",
                                    Relation = faction.PlayerRelationKind.ToString(),
                                    Goodwill = faction.PlayerGoodwill,
                                    IsPlayer = faction.IsPlayer,
                                    Defeated = faction.defeated,
                                    SettlementCount = settlementCount,
                                }
                            );
                        }
                    }
                }

                state.World = WorldAdapter.ToProtobuf(worldDto);

                // End profiling world extraction
                Diagnostics.PerformanceProfiler.EndWorldExtraction(
                    state.World?.Factions?.Count ?? 0,
                    state.World?.Settlements?.Count ?? 0
                );

                Log.Message(
                    $"{Constants.LogPrefix} Phase V state: {state.Map?.Buildings?.Count ?? 0} buildings, "
                        + $"{state.Incidents?.IncidentHistory?.Count ?? 0} incidents, "
                        + $"{state.World?.Factions?.Count ?? 0} factions"
                );
            }
            catch (Exception e)
            {
                Log.Warning($"{Constants.LogPrefix} Error populating Phase V state: {e.Message}");
            }
        }

        /// <summary>
        /// Convert protobuf GameSpeed enum to RimWorld TimeSpeed
        /// </summary>
        private TimeSpeed ConvertGameSpeed(GameSpeed speed)
        {
            return speed switch
            {
                GameSpeed.SpeedPaused => TimeSpeed.Paused,
                GameSpeed.SpeedNormal => TimeSpeed.Normal,
                GameSpeed.SpeedFast => TimeSpeed.Fast,
                GameSpeed.SpeedSuperfast => TimeSpeed.Superfast,
                GameSpeed.SpeedUltrafast => TimeSpeed.Ultrafast,
                _ => TimeSpeed.Normal,
            };
        }
    }
}
