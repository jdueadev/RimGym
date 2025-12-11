using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;
using RimworldMLBridge.Adapters;
using RimworldMLBridge.DTOs;
using RimworldMLBridge.Protos;

namespace RimworldMLBridge.Tests.Adapters
{
    /// <summary>
    /// Unit tests for ColonistAdapter - verifies accurate DTO to Protobuf conversion.
    /// Tests cover nominal cases, edge cases, and null handling.
    /// </summary>
    public class ColonistAdapterTests
    {
        private readonly ColonistAdapter _adapter;

        public ColonistAdapterTests()
        {
            _adapter = new ColonistAdapter();
        }

        [Fact]
        public void ToProtobuf_WithCompleteDTO_MapsAllFields()
        {
            // Arrange
            var dto = CreateCompleteColonistDTO();

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(12345, result.ThingId);
            Assert.Equal("John Smith", result.Name);
            Assert.Equal("Human", result.DefName);
            Assert.Equal(1, result.FactionId);

            // Position
            Assert.Equal(10f, result.Position.X);
            Assert.Equal(20f, result.Position.Y);
            Assert.Equal(5f, result.Position.Z);

            // Core stats
            Assert.Equal(0.95f, result.HealthPercent);
            Assert.Equal(0.75f, result.MoodPercent);

            // Age
            Assert.Equal(25 * 3600000, result.AgeBiologicalTicks);
            Assert.Equal("Male", result.Gender);
        }

        [Fact]
        public void ToProtobuf_WithSkills_MapsAllSkillData()
        {
            // Arrange
            var dto = CreateCompleteColonistDTO();

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert - Skills
            Assert.NotEmpty(result.Skills);
            Assert.Equal(3, result.Skills.Count);

            var shootingSkill = result.Skills.FirstOrDefault(s => s.DefName == "Shooting");
            Assert.NotNull(shootingSkill);
            Assert.Equal(12, shootingSkill.Level);
            Assert.Equal(Passion.Major, shootingSkill.Passion);
            Assert.Equal(5000f, shootingSkill.Xp);
            Assert.False(shootingSkill.Disabled);

            var constructionSkill = result.Skills.FirstOrDefault(s => s.DefName == "Construction");
            Assert.NotNull(constructionSkill);
            Assert.Equal(8, constructionSkill.Level);
            Assert.Equal(Passion.Minor, constructionSkill.Passion);

            var cookingSkill = result.Skills.FirstOrDefault(s => s.DefName == "Cooking");
            Assert.NotNull(cookingSkill);
            Assert.Equal(Passion.None, cookingSkill.Passion);
        }

        [Fact]
        public void ToProtobuf_WithPassionValues_MapsCorrectly()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO { Id = 1, Name = "Test" },
                ColonistWorkInfo = new ColonistWorkInfoDTO
                {
                    Skills = new List<SkillDTO>
                    {
                        new SkillDTO { Name = "Skill1", Passion = 0 }, // None
                        new SkillDTO { Name = "Skill2", Passion = 1 }, // Minor
                        new SkillDTO { Name = "Skill3", Passion = 2 }  // Major
                    }
                }
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.Equal(Passion.None, result.Skills[0].Passion);
            Assert.Equal(Passion.Minor, result.Skills[1].Passion);
            Assert.Equal(Passion.Major, result.Skills[2].Passion);
        }

        [Fact]
        public void ToProtobuf_WithNeeds_CreatesNeedStates()
        {
            // Arrange
            var dto = CreateCompleteColonistDTO();

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert - Needs
            Assert.NotEmpty(result.Needs);
            Assert.True(result.Needs.Count >= 3); // Food, Rest, Mood at minimum

            var foodNeed = result.Needs.FirstOrDefault(n => n.DefName == "Food");
            Assert.NotNull(foodNeed);
            Assert.Equal(0.8f, foodNeed.CurLevel);
            Assert.Equal(1.0f, foodNeed.MaxLevel);

            var restNeed = result.Needs.FirstOrDefault(n => n.DefName == "Rest");
            Assert.NotNull(restNeed);
            Assert.Equal(0.6f, restNeed.CurLevel);

            var moodNeed = result.Needs.FirstOrDefault(n => n.DefName == "Mood");
            Assert.NotNull(moodNeed);
            Assert.Equal(0.75f, moodNeed.CurLevel);
        }

        [Fact]
        public void ToProtobuf_WithCurrentJob_MapsJobState()
        {
            // Arrange
            var dto = CreateCompleteColonistDTO();

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert - Current job
            Assert.NotNull(result.CurrentJob);
            Assert.Equal("Hunt", result.CurrentJob.DefName);
            Assert.Equal("Hunt", result.CurrentJob.Label);
        }

        [Fact]
        public void ToProtobuf_WithWorkPriorities_MapsCorrectly()
        {
            // Arrange
            var dto = CreateCompleteColonistDTO();

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert - Work priorities
            Assert.NotEmpty(result.WorkPriorities);
            Assert.Equal(3, result.WorkPriorities.Count);
            Assert.Equal(1, result.WorkPriorities["Doctor"]);
            Assert.Equal(2, result.WorkPriorities["Construction"]);
            Assert.Equal(3, result.WorkPriorities["Hunting"]);
        }

        [Fact]
        public void ToProtobuf_WithHealthCapacities_CreatesCapacityData()
        {
            // Arrange
            var dto = CreateCompleteColonistDTO();

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert - Health capacities
            Assert.NotEmpty(result.Capacities);
            var consciousness = result.Capacities.FirstOrDefault(c => c.Label == "Consciousness");
            Assert.NotNull(consciousness);
            Assert.Equal(0.95f, consciousness.Efficiency);
            Assert.True(consciousness.CanBeAwake);
        }

        [Fact]
        public void ToProtobuf_WithNullDTO_ReturnsNull()
        {
            // Act
            var result = _adapter.ToProtobuf(null);

            // Assert
            Assert.Null(result);
        }

        [Fact]
        public void ToProtobuf_WithNullColonist_ReturnsNull()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = null
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.Null(result);
        }

        [Fact]
        public void ToProtobuf_WithNullPosition_UsesZeroCoordinates()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO
                {
                    Id = 1,
                    Name = "Test",
                    Position = null
                }
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.NotNull(result.Position);
            Assert.Equal(0f, result.Position.X);
            Assert.Equal(0f, result.Position.Y);
            Assert.Equal(0f, result.Position.Z);
        }

        [Fact]
        public void ToProtobuf_WithNullName_UsesEmptyString()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO
                {
                    Id = 1,
                    Name = null
                }
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.NotNull(result);
            Assert.Equal("", result.Name);
        }

        [Fact]
        public void ToProtobuf_WithNullSkills_CreatesEmptySkillsList()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO { Id = 1, Name = "Test" },
                ColonistWorkInfo = new ColonistWorkInfoDTO
                {
                    Skills = null
                }
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.NotNull(result);
            Assert.Empty(result.Skills);
        }

        [Fact]
        public void ToProtobuf_WithNullWorkPriorities_CreatesEmptyMap()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO { Id = 1, Name = "Test" },
                ColonistWorkInfo = new ColonistWorkInfoDTO
                {
                    WorkPriorities = null
                }
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.NotNull(result);
            Assert.Empty(result.WorkPriorities);
        }

        [Fact]
        public void ToProtobuf_WithZeroValues_PreservesZeros()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO
                {
                    Id = 1,
                    Name = "Test",
                    Health = 0f,
                    Mood = 0f,
                    Hunger = 0f,
                    Age = 0
                },
                Sleep = 0f,
                Comfort = 0f
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(0f, result.HealthPercent);
            Assert.Equal(0f, result.MoodPercent);
            Assert.Equal(0, result.AgeBiologicalTicks);
        }

        [Fact]
        public void ToProtobuf_WithDisabledSkill_MapsDisabledFlag()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO { Id = 1, Name = "Test" },
                ColonistWorkInfo = new ColonistWorkInfoDTO
                {
                    Skills = new List<SkillDTO>
                    {
                        new SkillDTO
                        {
                            Name = "DisabledSkill",
                            Level = 0,
                            TotallyDisabled = true,
                            PermanentlyDisabled = false
                        },
                        new SkillDTO
                        {
                            Name = "PermanentlyDisabledSkill",
                            Level = 0,
                            TotallyDisabled = false,
                            PermanentlyDisabled = true
                        }
                    }
                }
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.True(result.Skills[0].Disabled);
            Assert.True(result.Skills[1].Disabled);
        }

        [Fact]
        public void ToProtobuf_WithOptionalNeeds_OnlyIncludesPositiveValues()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO
                {
                    Id = 1,
                    Name = "Test",
                    Hunger = 0.5f,
                    Mood = 0.5f
                },
                Sleep = 0.5f,
                Comfort = 0f,  // Should not be included
                SurroundingBeauty = 0.3f,
                FreshAir = 0f  // Should not be included
            };

            // Act
            var result = _adapter.ToProtobuf(dto);

            // Assert
            Assert.Contains(result.Needs, n => n.DefName == "Food");
            Assert.Contains(result.Needs, n => n.DefName == "Rest");
            Assert.Contains(result.Needs, n => n.DefName == "Mood");
            Assert.Contains(result.Needs, n => n.DefName == "Beauty");
            Assert.DoesNotContain(result.Needs, n => n.DefName == "Comfort");
            Assert.DoesNotContain(result.Needs, n => n.DefName == "Outdoors");
        }

        [Fact]
        public void ToProtobufSafe_WithNullInput_ReturnsNull()
        {
            // Act
            var result = _adapter.ToProtobufSafe(null);

            // Assert
            Assert.Null(result);
        }

        [Fact]
        public void ToProtobufSafe_WithValidInput_ReturnsResult()
        {
            // Arrange
            var dto = new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO { Id = 1, Name = "Test" }
            };

            // Act
            var result = _adapter.ToProtobufSafe(dto);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(1, result.ThingId);
        }

        // Helper method to create a complete DTO for testing
        private ColonistDetailedDTO CreateCompleteColonistDTO()
        {
            return new ColonistDetailedDTO
            {
                Colonist = new ColonistDTO
                {
                    Id = 12345,
                    Name = "John Smith",
                    Health = 0.95f,
                    Mood = 0.75f,
                    Hunger = 0.8f,
                    Age = 25,
                    Gender = "Male",
                    Position = new PositionDTO
                    {
                        X = 10,
                        Y = 20,
                        Z = 5
                    }
                },
                ColonistMedicalInfo = new ColonistMedicalInfoDTO
                {
                    Health = 0.95f
                },
                Sleep = 0.6f,
                Comfort = 0.7f,
                SurroundingBeauty = 0.4f,
                FreshAir = 0.9f,
                ColonistWorkInfo = new ColonistWorkInfoDTO
                {
                    CurrentJob = "Hunt",
                    Skills = new List<SkillDTO>
                    {
                        new SkillDTO
                        {
                            Name = "Shooting",
                            Level = 12,
                            Passion = 2, // Major
                            XpTotalEarned = 5000f,
                            LevelDescriptor = "Expert",
                            TotallyDisabled = false,
                            PermanentlyDisabled = false
                        },
                        new SkillDTO
                        {
                            Name = "Construction",
                            Level = 8,
                            Passion = 1, // Minor
                            XpTotalEarned = 3000f,
                            LevelDescriptor = "Capable",
                            TotallyDisabled = false,
                            PermanentlyDisabled = false
                        },
                        new SkillDTO
                        {
                            Name = "Cooking",
                            Level = 5,
                            Passion = 0, // None
                            XpTotalEarned = 1000f,
                            LevelDescriptor = "Average",
                            TotallyDisabled = false,
                            PermanentlyDisabled = false
                        }
                    },
                    WorkPriorities = new List<WorkPriorityDTO>
                    {
                        new WorkPriorityDTO { WorkType = "Doctor", Priority = 1 },
                        new WorkPriorityDTO { WorkType = "Construction", Priority = 2 },
                        new WorkPriorityDTO { WorkType = "Hunting", Priority = 3 }
                    }
                }
            };
        }
    }
}
