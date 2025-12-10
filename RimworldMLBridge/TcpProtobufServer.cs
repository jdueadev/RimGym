using System;
using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using Google.Protobuf;
using RimworldMLBridge.Protos;
using Verse;

namespace RimworldMLBridge
{
    /// <summary>
    /// High-performance TCP server using Protocol Buffers for serialization.
    /// Handles communication with Python RL agent without requiring native gRPC libraries.
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
        private readonly ConcurrentQueue<StateMessage> _responseQueue = new ConcurrentQueue<StateMessage>();

        // Game state management
        private static long _currentTick = 0;
        private static readonly object _tickLock = new object();

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
                    StateMessage response = null;
                    int timeout = 0;
                    while (timeout < ResponseTimeoutMs && !_responseQueue.TryDequeue(out response))
                    {
                        Thread.Sleep(PollingIntervalMs);
                        timeout += PollingIntervalMs;
                    }

                    if (response == null)
                    {
                        // Timeout - send error response
                        response = new StateMessage
                        {
                            FrameId = _currentTick,
                            IsReady = false,
                            StatusMessage = "Timeout waiting for game response"
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
                    _responseQueue.Enqueue(new StateMessage
                    {
                        FrameId = _currentTick,
                        IsReady = false,
                        StatusMessage = $"Error: {e.Message}"
                    });
                }
            }
        }

        private StateMessage ExecuteCommand(CommandMessage command)
        {
            Log.Message($"[MLBridge] Executing command: {command.Type}");

            var state = new StateMessage
            {
                FrameId = _currentTick,
                IsReady = false,
                StatusMessage = $"Command {command.Type} executed"
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
                    // Advance simulation by specified ticks
                    int ticksToRun = command.TicksToRun > 0 ? command.TicksToRun : 60;
                    for (int i = 0; i < ticksToRun; i++)
                    {
                        Find.TickManager.DoSingleTick();
                        _currentTick++;
                    }
                    state.StatusMessage = $"Advanced {ticksToRun} ticks";
                    break;

                case CommandType.QueryState:
                    // Return current state without advancing
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

        private void PopulateGameState(StateMessage state)
        {
            try
            {
                if (Current.Game == null || Find.CurrentMap == null)
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

                const int TicksPerDay = 60000;
                const int BaseYear = 5500;
                const int TicksPerYear = 360000;
                // Global state
                state.Global = new GlobalState
                {
                    Temperature = Find.CurrentMap.mapTemperature.OutdoorTemp,
                    Weather = Find.CurrentMap.weatherManager.CurWeatherPerceived?.defName ?? "Clear",
                    Day = Find.TickManager.TicksAbs / TicksPerDay, // Approximate day (60000 ticks per day)
                    Year = BaseYear + (Find.TickManager.TicksAbs / TicksPerYear) // Approximate year
                };

                // Colonist entities
                foreach (var pawn in Find.CurrentMap.mapPawns.FreeColonistsSpawned)
                {
                    var entity = new Protos.Entity
                    {
                        Id = pawn.thingIDNumber,
                        Type = "Pawn",
                        DefName = pawn.def.defName,
                        Position = new Protos.Vector3
                        {
                            X = pawn.Position.x,
                            Y = pawn.Position.y,
                            Z = pawn.Position.z
                        },
                        FactionId = pawn.Faction?.loadID ?? -1,
                        State = new EntityState
                        {
                            Health = pawn.health.summaryHealth.SummaryHealthPercent,
                            IsDrafted = pawn.Drafted,
                            CurrentJob = pawn.CurJobDef?.defName ?? "None"
                        }
                    };

                    // Add needs
                    if (pawn.needs != null)
                    {
                        entity.State.Mood = pawn.needs.mood?.CurLevel ?? 0;
                        entity.State.Hunger = pawn.needs.food?.CurLevel ?? 0;
                        entity.State.Rest = pawn.needs.rest?.CurLevel ?? 0;
                    }

                    state.Entities.Add(entity);
                }
            }
            catch (Exception e)
            {
                Log.Warning($"[MLBridge] Error populating state: {e.Message}");
                state.IsReady = false;
                state.StatusMessage = $"Error: {e.Message}";
            }
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
    }
}
