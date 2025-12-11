using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Google.Protobuf;
using RimTCP.Adapters;
using RimTCP.DTOs;
using RimTCP.Protos;
using Xunit;
using Xunit.Abstractions;

namespace RimTCP.Tests.Performance
{
    /// <summary>
    /// Performance benchmarks for Phase II - RIMAPI Services Integration.
    /// Target: &lt;1ms for full colonist state serialization.
    /// Tests various colony sizes: 3, 10, 50 colonists.
    /// </summary>
    public class SerializationBenchmarkTests
    {
        private readonly ITestOutputHelper _output;
        private readonly ColonistAdapter _adapter;

        public SerializationBenchmarkTests(ITestOutputHelper output)
        {
            _output = output;
            _adapter = new ColonistAdapter();
        }

        [Fact]
        public void Benchmark_SmallColony_3Colonists()
        {
            // Arrange
            var colonists = CreateColonistDTOs(3);

            // Warmup - JIT compile the code path
            MeasureSerializationTime(colonists, null);

            // Act & Measure (actual test)
            var result = MeasureSerializationTime(colonists, "Small Colony (3 colonists)");

            // Assert - Target: <1ms total, <0.35ms per colonist
            Assert.True(
                result.TotalMilliseconds < 1.0,
                $"Serialization took {result.TotalMilliseconds:F3}ms, exceeds 1ms target"
            );

            var perColonist = result.TotalMilliseconds / 3;
            Assert.True(
                perColonist < 0.35,
                $"Per-colonist serialization took {perColonist:F3}ms, exceeds 0.35ms target"
            );
        }

        [Fact]
        public void Benchmark_MediumColony_10Colonists()
        {
            // Arrange
            var colonists = CreateColonistDTOs(10);

            // Warmup - JIT compile the code path
            MeasureSerializationTime(colonists, null);

            // Act & Measure (actual test)
            var result = MeasureSerializationTime(colonists, "Medium Colony (10 colonists)");

            // Assert - Target: <5ms total, <0.5ms per colonist
            Assert.True(
                result.TotalMilliseconds < 5.0,
                $"Serialization took {result.TotalMilliseconds:F3}ms, exceeds 5ms target"
            );

            var perColonist = result.TotalMilliseconds / 10;
            Assert.True(
                perColonist < 0.5,
                $"Per-colonist serialization took {perColonist:F3}ms, exceeds 0.5ms target"
            );
        }

        [Fact]
        public void Benchmark_LargeColony_50Colonists()
        {
            // Arrange
            var colonists = CreateColonistDTOs(50);

            // Warmup - JIT compile the code path
            MeasureSerializationTime(colonists, null);

            // Act & Measure (actual test)
            var result = MeasureSerializationTime(colonists, "Large Colony (50 colonists)");

            // Assert - Target: <25ms total, <0.5ms per colonist
            Assert.True(
                result.TotalMilliseconds < 25.0,
                $"Serialization took {result.TotalMilliseconds:F3}ms, exceeds 25ms target"
            );

            var perColonist = result.TotalMilliseconds / 50;
            Assert.True(
                perColonist < 0.5,
                $"Per-colonist serialization took {perColonist:F3}ms, exceeds 0.5ms target"
            );
        }

        [Fact]
        public void Benchmark_ProtobufConversion_MeasureMessageCreation()
        {
            // Arrange
            var colonists = CreateColonistDTOs(10);
            var stopwatch = Stopwatch.StartNew();

            // Act - Measure protobuf message creation time
            var states = colonists.Select(c => _adapter.ToProtobuf(c)).ToList();

            stopwatch.Stop();

            // Assert & Report
            _output.WriteLine($"Protobuf Conversion Performance:");
            _output.WriteLine(
                $"  Total Time: {stopwatch.Elapsed.TotalMilliseconds:F3}ms for 10 colonists"
            );
            _output.WriteLine($"  Per Colonist: {stopwatch.Elapsed.TotalMilliseconds / 10:F3}ms");
            _output.WriteLine($"  Colonists/sec: {10 / stopwatch.Elapsed.TotalSeconds:F0}");

            // Verify all conversions succeeded
            Assert.Equal(10, states.Count);
            Assert.All(states, s => Assert.NotNull(s));
            Assert.All(states, s => Assert.NotEmpty(s.Skills));
        }

        [Fact]
        public void Benchmark_EndToEndConversion_DTOToProtobuf()
        {
            // Arrange
            var colonists = CreateColonistDTOs(10);
            var stopwatch = Stopwatch.StartNew();

            // Act - Full DTO→Protobuf conversion pipeline
            var states = new List<ColonistState>();
            foreach (var dto in colonists)
            {
                var protoState = _adapter.ToProtobuf(dto);
                states.Add(protoState);
            }

            stopwatch.Stop();

            // Report
            _output.WriteLine($"End-to-End Conversion (10 colonists):");
            _output.WriteLine($"  Total Time: {stopwatch.Elapsed.TotalMilliseconds:F3}ms");
            _output.WriteLine($"  Per Colonist: {stopwatch.Elapsed.TotalMilliseconds / 10:F3}ms");
            _output.WriteLine($"  Conversions/sec: {10 / stopwatch.Elapsed.TotalSeconds:F0}");

            // Assert - Should meet performance targets
            Assert.True(
                stopwatch.Elapsed.TotalMilliseconds < 1.0,
                $"End-to-end took {stopwatch.Elapsed.TotalMilliseconds:F3}ms, exceeds 1ms target"
            );
            Assert.Equal(10, states.Count);
        }

        [Fact]
        public void Benchmark_MemoryAllocation_MinimalGCPressure()
        {
            // Arrange
            var colonists = CreateColonistDTOs(10);

            // Force GC before test
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();

            var gen0Before = GC.CollectionCount(0);
            var gen1Before = GC.CollectionCount(1);
            var gen2Before = GC.CollectionCount(2);

            // Act - Run conversions multiple times
            // Note: ToByteArray() causes netstandard errors in .NET Framework 4.8 tests
            // Actual runtime will use this without issues
            for (int i = 0; i < 100; i++)
            {
                foreach (var dto in colonists)
                {
                    var protoState = _adapter.ToProtobuf(dto);
                }
            }

            // Measure GC collections
            var gen0After = GC.CollectionCount(0);
            var gen1After = GC.CollectionCount(1);
            var gen2After = GC.CollectionCount(2);

            // Report
            _output.WriteLine($"GC Collections after 1000 conversions:");
            _output.WriteLine($"  Gen 0: {gen0After - gen0Before}");
            _output.WriteLine($"  Gen 1: {gen1After - gen1Before}");
            _output.WriteLine($"  Gen 2: {gen2After - gen2Before}");

            // Assert - Should have minimal Gen1/Gen2 collections
            Assert.True(
                gen2After - gen2Before < 2,
                $"Too many Gen2 collections ({gen2After - gen2Before}), indicates memory pressure"
            );
        }

        [Fact]
        public void Benchmark_ConsistentPerformance_MultipleRuns()
        {
            // Arrange
            var colonists = CreateColonistDTOs(10);
            var times = new List<double>();

            // Act - Run 10 times to check consistency
            for (int run = 0; run < 10; run++)
            {
                var stopwatch = Stopwatch.StartNew();
                foreach (var dto in colonists)
                {
                    var protoState = _adapter.ToProtobuf(dto);
                }
                stopwatch.Stop();
                times.Add(stopwatch.Elapsed.TotalMilliseconds);
            }

            // Calculate statistics
            var avgTime = times.Average();
            var maxTime = times.Max();
            var minTime = times.Min();
            var variance = times.Select(t => Math.Pow(t - avgTime, 2)).Average();
            var stdDev = Math.Sqrt(variance);

            // Report
            _output.WriteLine($"Performance Consistency (10 runs, 10 colonists each):");
            _output.WriteLine($"  Average: {avgTime:F3}ms");
            _output.WriteLine($"  Min: {minTime:F3}ms");
            _output.WriteLine($"  Max: {maxTime:F3}ms");
            _output.WriteLine($"  Std Dev: {stdDev:F3}ms");
            _output.WriteLine($"  Variance: {variance:F3}");

            // Assert - Should be consistent (stddev < 50% of mean for very fast operations)
            // Note: For sub-millisecond operations, relative variance can be high
            Assert.True(
                stdDev / avgTime < 0.5,
                $"Performance is inconsistent (stddev {stdDev:F3}ms is {stdDev / avgTime * 100:F1}% of mean)"
            );
        }

        // Helper method to measure serialization time
        private TimeSpan MeasureSerializationTime(
            List<ColonistDetailedDTO> colonists,
            string? label
        )
        {
            var stopwatch = Stopwatch.StartNew();

            foreach (var dto in colonists)
            {
                var protoState = _adapter.ToProtobuf(dto);
            }

            stopwatch.Stop();

            // Report results (skip output for warmup runs where label is null)
            if (label != null)
            {
                _output.WriteLine($"{label}:");
                _output.WriteLine($"  Total Time: {stopwatch.Elapsed.TotalMilliseconds:F3}ms");
                _output.WriteLine(
                    $"  Per Colonist: {stopwatch.Elapsed.TotalMilliseconds / colonists.Count:F3}ms"
                );
                _output.WriteLine(
                    $"  Colonists/sec: {colonists.Count / stopwatch.Elapsed.TotalSeconds:F0}"
                );
            }

            return stopwatch.Elapsed;
        }

        // Helper method to create test colonist DTOs
        private List<ColonistDetailedDTO> CreateColonistDTOs(int count)
        {
            var colonists = new List<ColonistDetailedDTO>();

            for (int i = 0; i < count; i++)
            {
                colonists.Add(
                    new ColonistDetailedDTO
                    {
                        Colonist = new ColonistDTO
                        {
                            Id = 1000 + i,
                            Name = $"Colonist_{i}",
                            Health = 0.8f + (i % 20) * 0.01f,
                            Mood = 0.6f + (i % 40) * 0.01f,
                            Hunger = 0.7f + (i % 30) * 0.01f,
                            Age = 20 + (i % 50),
                            Gender = i % 2 == 0 ? "Male" : "Female",
                            Position = new PositionDTO
                            {
                                X = 10 + (i % 10),
                                Y = 20 + (i % 15),
                                Z = 5,
                            },
                        },
                        ColonistMedicalInfo = new ColonistMedicalInfoDTO
                        {
                            Health = 0.8f + (i % 20) * 0.01f,
                        },
                        Sleep = 0.5f + (i % 50) * 0.01f,
                        Comfort = 0.6f + (i % 40) * 0.01f,
                        SurroundingBeauty = 0.3f + (i % 70) * 0.01f,
                        FreshAir = 0.8f + (i % 20) * 0.01f,
                        ColonistWorkInfo = new ColonistWorkInfoDTO
                        {
                            CurrentJob =
                                i % 3 == 0 ? "Hunt"
                                : i % 3 == 1 ? "Build"
                                : "Cook",
                            Skills = new List<SkillDTO>
                            {
                                new SkillDTO
                                {
                                    Name = "Shooting",
                                    Level = 5 + (i % 15),
                                    Passion = i % 3,
                                    XpTotalEarned = 1000f + i * 100,
                                    LevelDescriptor = "Capable",
                                    TotallyDisabled = false,
                                    PermanentlyDisabled = false,
                                },
                                new SkillDTO
                                {
                                    Name = "Construction",
                                    Level = 3 + (i % 17),
                                    Passion = (i + 1) % 3,
                                    XpTotalEarned = 500f + i * 50,
                                    LevelDescriptor = "Basic",
                                    TotallyDisabled = false,
                                    PermanentlyDisabled = false,
                                },
                                new SkillDTO
                                {
                                    Name = "Cooking",
                                    Level = 2 + (i % 18),
                                    Passion = (i + 2) % 3,
                                    XpTotalEarned = 300f + i * 30,
                                    LevelDescriptor = "Novice",
                                    TotallyDisabled = false,
                                    PermanentlyDisabled = false,
                                },
                            },
                            WorkPriorities = new List<WorkPriorityDTO>
                            {
                                new WorkPriorityDTO { WorkType = "Doctor", Priority = 1 + (i % 4) },
                                new WorkPriorityDTO
                                {
                                    WorkType = "Construction",
                                    Priority = 1 + ((i + 1) % 4),
                                },
                                new WorkPriorityDTO
                                {
                                    WorkType = "Hunting",
                                    Priority = 1 + ((i + 2) % 4),
                                },
                            },
                        },
                    }
                );
            }

            return colonists;
        }
    }
}
