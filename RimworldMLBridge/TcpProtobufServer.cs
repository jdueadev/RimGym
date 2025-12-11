using System;
using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using Google.Protobuf;
using RimworldMLBridge.Protos;
using RimworldMLBridge.Services;
using RimworldMLBridge.Adapters;
using Verse;

namespace RimworldMLBridge
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
        private readonly ConcurrentQueue<CommandMessage> _commandQueue = new ConcurrentQueue<CommandMessage>();

        // Thread-safe queue for responses from game (main thread) to client (background thread)
        private readonly ConcurrentQueue<RichStateMessage> _responseQueue = new ConcurrentQueue<RichStateMessage>();

        // Game state management
        private static long _currentTick = 0;
        private static readonly object _tickLock = new object();

        // Phase III: Velocity and timing tracking
        private long _lastFrameTimestamp = 0;  // Timestamp of last frame in milliseconds
        private readonly ConcurrentDictionary<int, Vector3> _lastPositions = new ConcurrentDictionary<int, Vector3>();
        private readonly ConcurrentDictionary<int, long> _lastPositionTimes = new ConcurrentDictionary<int, long>();

        public bool IsConnected => _client != null && _client.Connected;
        public bool IsRunning => _isRunning;

        public TcpProtobufServer(int port = 50051)
        {
            _port = port;
        }

        public void Start()
        {
            if (_isRunning)
            {
                Log.Warning("[MLBridge] Server is already running");
                return;
            }

            _isRunning = true;
            _serverThread = new Thread(ServerLoop)
            {
                IsBackground = true,
                Name = "MLBridge-TCP-Server"
            };
            _serverThread.Start();

            Log.Message($"[MLBridge] TCP Protobuf server started on port {_port}");
        }

        public void Stop()
        {
            _isRunning = false;

            try
            {
                _stream?.Close();
                _client?.Close();
                _listener?.Stop();
            }
            catch (Exception e)
            {
                Log.Warning($"[MLBridge] Error during shutdown: {e.Message}");
            }

            Log.Message("[MLBridge] TCP server stopped");
        }

        private void ServerLoop()
        {
            try
            {
                const int ListenerPollIntervalMs = 100;
                _listener = new TcpListener(IPAddress.Loopback, _port);
                _listener.Start();
                Log.Message($"[MLBridge] Waiting for Python client connection on localhost:{_port}...");

                while (_isRunning)
                {
                    // Accept connection (blocking call)
                    if (_listener.Pending())
                    {
                        _client = _listener.AcceptTcpClient();
                        _client.NoDelay = true; // Disable Nagle's algorithm for low latency
                        _stream = _client.GetStream();

                        Log.Message("[MLBridge] Python client connected!");

                        // Handle this client until disconnect
                        HandleClient();

                        Log.Message("[MLBridge] Client disconnected, waiting for new connection...");
                    }
                    else
                    {
                        Thread.Sleep(ListenerPollIntervalMs); // Avoid busy-waiting
                    }
                }
            }
            catch (Exception e)
            {
                Log.Error($"[MLBridge] Server error: {e.Message}\n{e.StackTrace}");
            }
            finally
            {
                _listener?.Stop();
            }
        }

        private void HandleClient()
        {


            try
            {
                const int ResponseTimeoutMs = 5000; // 5 seconds
                const int PollingIntervalMs = 10; // 10ms

                while (_isRunning && _client.Connected)
                {
                    // Read message from client
                    var command = ReadMessage<CommandMessage>(_stream);
                    if (command == null) break; // Connection closed

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
                            TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                        };
                    }

                    // Send response back to client
                    WriteMessage(_stream, response);
                }
            }
            catch (Exception e)
            {
                if (_isRunning) // Only log if not intentional shutdown
                {
                    Log.Warning($"[MLBridge] Client handler error: {e.Message}");
                }
            }
            finally
            {
                _stream?.Close();
                _client?.Close();
            }
        }

        /// <summary>
        /// Called from main thread to process queued commands
        /// </summary>
        public void ProcessCommands()
        {
            while (_commandQueue.TryDequeue(out var command))
            {
                try
                {
                    var response = ExecuteCommand(command);
                    _responseQueue.Enqueue(response);
                }
                catch (Exception e)
                {
                    Log.Error($"[MLBridge] Error executing command: {e.Message}");
                    _responseQueue.Enqueue(new RichStateMessage
                    {
                        FrameId = _currentTick,
                        IsReady = false,
                        StatusMessage = $"Error: {e.Message}",
                        TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                    });
                }
            }
        }

        private RichStateMessage ExecuteCommand(CommandMessage command)
        {
            Log.Message($"[MLBridge] Executing command: {command.Type}");

            var state = new RichStateMessage
            {
                FrameId = _currentTick,
                IsReady = false,
                StatusMessage = $"Command {command.Type} executed",
                TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            };

            // Check if game is loaded before executing commands
            if (Current.Game == null || Find.CurrentMap == null)
            {
                state.StatusMessage = "Game not loaded - please load a save or start a new game";
                return state;
            }

            state.IsReady = true;

            switch (command.Type)
            {
                case CommandType.Step:
                    // Phase III: Grant permission to advance ticks
                    if (MlBridgeMod.TrainingMode)
                    {
                        int ticksToRun = command.TicksToRun > 0 ? command.TicksToRun : 60;

                        // Ensure game is unpaused so ticks can advance
                        if (Find.TickManager.Paused)
                        {
                            Find.TickManager.CurTimeSpeed = TimeSpeed.Normal;
                            Log.Message("[MLBridge] Auto-unpaused game for training mode STEP");
                        }

                        // Set flags to allow tick advancement
                        MlBridgeMod.TicksToRun = ticksToRun;
                        MlBridgeMod.StepPermitted = true;

                        state.StatusMessage = $"Step initiated: {ticksToRun} ticks (Training Mode)";
                        Log.Message($"[MLBridge] STEP command: granting permission for {ticksToRun} ticks");
                    }
                    else
                    {
                        // In inference mode, STEP is not needed - game runs freely
                        state.StatusMessage = "Game running freely (Inference Mode) - STEP command not needed";
                    }
                    break;

                case CommandType.QueryState:
                    // Return current state without advancing
                    state.StatusMessage = MlBridgeMod.TrainingMode ?
                        "State queried (Training Mode)" :
                        "State queried (Inference Mode)";
                    break;

                case CommandType.SetMode:
                    // Phase III: Switch between training and inference modes
                    bool newMode = (command.Mode == ExecutionMode.ModeTraining);
                    string modeStr = newMode ? "TRAINING (Synchronous)" : "INFERENCE (Asynchronous)";

                    if (MlBridgeMod.TrainingMode != newMode)
                    {
                        MlBridgeMod.TrainingMode = newMode;
                        MlBridgeMod.StepPermitted = false; // Reset step permission on mode change
                        MlBridgeMod.TicksToRun = 0;

                        // When switching to inference mode, ensure game is unpaused
                        if (!newMode && Find.TickManager.Paused)
                        {
                            Find.TickManager.CurTimeSpeed = TimeSpeed.Normal;
                            Log.Message("[MLBridge] Auto-unpaused game for inference mode");
                        }

                        Log.Message($"[MLBridge] Mode switched to: {modeStr}");
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
                        Log.Message($"[MLBridge] Game speed changed: {oldSpeed} → {newSpeed}");
                        state.StatusMessage = $"Speed changed to {newSpeed}";
                    }
                    else
                    {
                        state.StatusMessage = $"Already at {newSpeed}";
                    }
                    break;

                case CommandType.Reset:
                    // TODO: Implement game reset logic
                    state.StatusMessage = "Reset not yet implemented";
                    break;

                case CommandType.ExecuteAction:
                    // TODO: Execute actions on pawns
                    state.StatusMessage = "Actions not yet implemented";
                    break;
            }

            // Populate state with game data
            PopulateGameState(state);

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
                state.CurrentMode = MlBridgeMod.TrainingMode ?
                    ExecutionMode.ModeTraining : ExecutionMode.ModeInference;

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
                    Year = BaseYear + (Find.TickManager.TicksAbs / TicksPerYear)
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

                // Phase III: In inference mode, could implement delta compression here
                // For now, always send full state (delta compression is an optimization)
                state.IsDelta = false;

                Log.Message($"[MLBridge] Populated state: {state.Colonists.Count} colonists, frame {state.FrameId}, dt={state.DeltaTimeMs}ms");
            }
            catch (Exception e)
            {
                Log.Warning($"[MLBridge] Error populating state: {e.Message}\n{e.StackTrace}");
                state.IsReady = false;
                state.StatusMessage = $"Error: {e.Message}";
            }
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
            colonist.Velocity = new Vector3 { X = 0, Y = 0, Z = 0 };

            if (_lastPositions.TryGetValue(colonistId, out var lastPos) &&
                _lastPositionTimes.TryGetValue(colonistId, out var lastTime))
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
                        Z = velocityZ
                    };
                }
            }

            // Update position history
            _lastPositions[colonistId] = new Vector3 { X = currentPos.X, Y = currentPos.Y, Z = currentPos.Z };
            _lastPositionTimes[colonistId] = currentTime;
        }

        /// <summary>
        /// Read a length-prefixed protobuf message from stream
        /// </summary>
        private T ReadMessage<T>(NetworkStream stream) where T : IMessage<T>, new()
        {
            try
            {
                // Read 4-byte length prefix (big-endian)
                byte[] lengthBytes = new byte[4];
                int bytesRead = stream.Read(lengthBytes, 0, 4);
                if (bytesRead == 0) return default(T); // Connection closed

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
                    if (read == 0) throw new IOException("Connection closed while reading message");
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
        private void WriteMessage<T>(NetworkStream stream, T message) where T : IMessage
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
        /// Convert protobuf GameSpeed enum to RimWorld TimeSpeed
        /// </summary>
        private TimeSpeed ConvertGameSpeed(GameSpeed speed)
        {
            switch (speed)
            {
                case GameSpeed.SpeedPaused:
                    return TimeSpeed.Paused;
                case GameSpeed.SpeedNormal:
                    return TimeSpeed.Normal;
                case GameSpeed.SpeedFast:
                    return TimeSpeed.Fast;
                case GameSpeed.SpeedSuperfast:
                    return TimeSpeed.Superfast;
                case GameSpeed.SpeedUltrafast:
                    return TimeSpeed.Ultrafast;
                default:
                    return TimeSpeed.Normal;
            }
        }
    }
}
