using System;
using System.Linq;
using RimworldMLBridge.DTOs;
using RimworldMLBridge.Protos;

namespace RimworldMLBridge.Adapters
{
    /// <summary>
    /// Adapter for converting ColonistDetailedDTO to ColonistState Protobuf message.
    /// Optimized for minimal allocations and <1ms performance target.
    /// </summary>
    public class ColonistAdapter : ProtobufAdapter<ColonistDetailedDTO, ColonistState>
    {
        /// <summary>
        /// Convert a detailed colonist DTO to Protobuf ColonistState.
        /// </summary>
        public override ColonistState ToProtobuf(ColonistDetailedDTO dto)
        {
            if (dto?.Colonist == null)
            {
                return null;
            }

            var state = new ColonistState
            {
                // Identity
                ThingId = dto.Colonist.Id,
                Name = dto.Colonist.Name ?? "",
                DefName = "Human", // Could be extracted if needed
                FactionId = 1, // Player faction

                // Position
                Position = new Protos.Vector3
                {
                    X = dto.Colonist.Position?.X ?? 0,
                    Y = dto.Colonist.Position?.Y ?? 0,
                    Z = dto.Colonist.Position?.Z ?? 0,
                },
                MapId = 1, // Could extract from game if needed

                // Core stats
                HealthPercent = dto.ColonistMedicalInfo?.Health ?? dto.Colonist.Health,
                MoodPercent = dto.Colonist.Mood,
                IsDrafted = dto.Colonist.IsDrafted,
                IsDowned = dto.Colonist.IsDowned,
                IsDead = dto.Colonist.IsDead,

                // Age
                AgeBiologicalTicks = dto.Colonist.Age * 3600000, // Years to ticks approximation
                AgeChronologicalTicks = dto.Colonist.Age * 3600000,
                Gender = dto.Colonist.Gender ?? "Male",
            };

            // Convert skills
            if (dto.ColonistWorkInfo?.Skills != null)
            {
                foreach (var skill in dto.ColonistWorkInfo.Skills)
                {
                    state.Skills.Add(MapSkillToProtobuf(skill));
                }
            }

            // Convert needs (create from available DTO data)
            // Food (Hunger)
            state.Needs.Add(
                new NeedState
                {
                    DefName = "Food",
                    Label = "Food",
                    CurLevel = dto.Colonist.Hunger,
                    MaxLevel = 1.0f,
                    Category = "Basic",
                }
            );

            // Rest (Sleep)
            state.Needs.Add(
                new NeedState
                {
                    DefName = "Rest",
                    Label = "Rest",
                    CurLevel = dto.Sleep,
                    MaxLevel = 1.0f,
                    Category = "Basic",
                }
            );

            // Mood
            state.Needs.Add(
                new NeedState
                {
                    DefName = "Mood",
                    Label = "Mood",
                    CurLevel = dto.Colonist.Mood,
                    MaxLevel = 1.0f,
                    Category = "Basic",
                }
            );

            // Comfort
            if (dto.Comfort > 0)
            {
                state.Needs.Add(
                    new NeedState
                    {
                        DefName = "Comfort",
                        Label = "Comfort",
                        CurLevel = dto.Comfort,
                        MaxLevel = 1.0f,
                        Category = "Comfort",
                    }
                );
            }

            // Beauty
            if (dto.SurroundingBeauty > 0)
            {
                state.Needs.Add(
                    new NeedState
                    {
                        DefName = "Beauty",
                        Label = "Beauty",
                        CurLevel = dto.SurroundingBeauty,
                        MaxLevel = 1.0f,
                        Category = "Environment",
                    }
                );
            }

            // Outdoors (Fresh Air)
            if (dto.FreshAir > 0)
            {
                state.Needs.Add(
                    new NeedState
                    {
                        DefName = "Outdoors",
                        Label = "Outdoors",
                        CurLevel = dto.FreshAir,
                        MaxLevel = 1.0f,
                        Category = "Environment",
                    }
                );
            }

            // Current job
            if (!string.IsNullOrEmpty(dto.ColonistWorkInfo?.CurrentJob))
            {
                state.CurrentJob = new JobState
                {
                    DefName = dto.ColonistWorkInfo.CurrentJob,
                    Label = dto.ColonistWorkInfo.CurrentJob,
                    TargetThingId = 0,
                    TargetPosition = new Protos.Vector3(),
                    StartTick = 0,
                };
            }

            // Work priorities
            if (dto.ColonistWorkInfo?.WorkPriorities != null)
            {
                foreach (var priority in dto.ColonistWorkInfo.WorkPriorities)
                {
                    if (!string.IsNullOrEmpty(priority.WorkType))
                    {
                        state.WorkPriorities[priority.WorkType] = priority.Priority;
                    }
                }
            }

            // Health capacities (derive from health data)
            state.Capacities.Add(
                new HealthCapacity
                {
                    Label = "Consciousness",
                    Efficiency = dto.ColonistMedicalInfo?.Health ?? 1.0f,
                    CanBeAwake = true,
                }
            );

            return state;
        }

        /// <summary>
        /// Map a skill DTO to Protobuf SkillState.
        /// </summary>
        private SkillState MapSkillToProtobuf(SkillDTO skill)
        {
            if (skill == null)
                return null;

            return new SkillState
            {
                DefName = skill.Name ?? "",
                Label = skill.LevelDescriptor ?? skill.Name ?? "",
                Level = skill.Level,
                Xp = skill.XpTotalEarned,
                Passion = MapPassion(skill.Passion),
                Disabled = skill.TotallyDisabled || skill.PermanentlyDisabled,
            };
        }

        /// <summary>
        /// Map passion integer to Protobuf Passion enum.
        /// </summary>
        private Passion MapPassion(int passionValue)
        {
            // RimWorld passion: 0 = None, 1 = Minor, 2 = Major
            if (passionValue == 2)
                return Passion.Major;
            if (passionValue == 1)
                return Passion.Minor;
            return Passion.None;
        }
    }
}
