using System;
using System.Collections.Generic;
using System.Linq;
using RimTCP.DTOs;
using RimTCP.Protos;

namespace RimTCP.Adapters
{
    /// <summary>
    /// Phase V: Adapter for converting Incident DTOs to Protobuf messages
    /// Handles incident history, storyteller state, and active threats
    /// Target: <1ms conversion time
    /// </summary>
    public class IncidentAdapter
    {
        /// <summary>
        /// Convert IncidentService data to Protobuf IncidentState
        /// </summary>
        public static IncidentState ToProtobuf(
            IncidentsDTO incidentsDto,
            QuestsDTO questsDto = null,
            StorytellerDTO storytellerDto = null,
            List<GameConditionDTO> conditionsDto = null)
        {
            var incidentState = new IncidentState();

            // Add incidents history
            if (incidentsDto?.Incidents != null)
            {
                foreach (var incident in incidentsDto.Incidents.Take(100)) // Limit to 100 most recent
                {
                    incidentState.IncidentHistory.Add(ToProtobufIncident(incident));
                }
            }

            // Add storyteller state
            if (storytellerDto != null)
            {
                incidentState.Storyteller = ToProtobufStoryteller(storytellerDto);
            }

            // Add active conditions
            if (conditionsDto != null)
            {
                foreach (var condition in conditionsDto.Where(c => c.TicksLeft > 0))
                {
                    incidentState.ActiveConditions.Add(condition.Label ?? condition.DefName);
                }
            }

            // Add quest status
            if (questsDto?.ActiveQuests != null)
            {
                incidentState.HasActiveQuest = questsDto.ActiveQuests.Count > 0;
            }

            return incidentState;
        }

        /// <summary>
        /// Convert IncidentDTO to Protobuf IncidentRecord
        /// </summary>
        private static IncidentRecord ToProtobufIncident(IncidentDTO incidentDto)
        {
            var record = new IncidentRecord
            {
                DefName = incidentDto.IncidentDef ?? "Unknown",
                Label = incidentDto.Label ?? incidentDto.IncidentDef ?? "Incident",
                Type = ParseIncidentType(incidentDto.Category),
                Severity = ParseIncidentSeverity(incidentDto.Category),
                IsActive = incidentDto.DaysSinceOccurred < 0.1f, // Active if less than 2.4 hours
                StartTick = (int)(incidentDto.IncidentHour * 2500) // Approximate conversion
            };

            return record;
        }

        /// <summary>
        /// Convert StorytellerDTO to Protobuf StorytellerState
        /// </summary>
        private static StorytellerState ToProtobufStoryteller(StorytellerDTO dto)
        {
            return new StorytellerState
            {
                DefName = dto.DefName ?? "Unknown",
                Label = dto.Label ?? dto.DefName ?? "Storyteller",
                Difficulty = dto.Difficulty,
                ThreatScale = dto.ThreatScale,
                TicksSinceLastThreat = dto.TicksSinceLastThreat,
                AdaptationDays = dto.AdaptationDays
            };
        }

        #region Enum Parsers

        private static IncidentType ParseIncidentType(string category)
        {
            if (string.IsNullOrEmpty(category))
                return IncidentType.IncidentUnknown;

            var categoryLower = category.ToLowerInvariant();

            if (categoryLower.Contains("raid") || categoryLower.Contains("attack"))
                return IncidentType.IncidentRaid;
            if (categoryLower.Contains("trade") || categoryLower.Contains("caravan"))
                return IncidentType.IncidentTradeCaravan;
            if (categoryLower.Contains("manhunter"))
                return IncidentType.IncidentManhunter;
            if (categoryLower.Contains("solar") || categoryLower.Contains("flare"))
                return IncidentType.IncidentSolarFlare;
            if (categoryLower.Contains("eclipse"))
                return IncidentType.IncidentEclipse;
            if (categoryLower.Contains("toxic") || categoryLower.Contains("fallout"))
                return IncidentType.IncidentToxicFallout;
            if (categoryLower.Contains("volcanic") || categoryLower.Contains("winter"))
                return IncidentType.IncidentVolcanicWinter;
            if (categoryLower.Contains("heat") || categoryLower.Contains("wave"))
                return IncidentType.IncidentHeatWave;
            if (categoryLower.Contains("cold") || categoryLower.Contains("snap"))
                return IncidentType.IncidentColdSnap;
            if (categoryLower.Contains("fire"))
                return IncidentType.IncidentFire;
            if (categoryLower.Contains("disease") || categoryLower.Contains("plague"))
                return IncidentType.IncidentDisease;
            if (categoryLower.Contains("mental") || categoryLower.Contains("break"))
                return IncidentType.IncidentMentalBreak;
            if (categoryLower.Contains("quest"))
                return IncidentType.IncidentQuest;

            return IncidentType.IncidentUnknown;
        }

        private static IncidentSeverity ParseIncidentSeverity(string category)
        {
            if (string.IsNullOrEmpty(category))
                return IncidentSeverity.SeverityMinor;

            var categoryLower = category.ToLowerInvariant();

            if (categoryLower.Contains("major") || categoryLower.Contains("extreme"))
                return IncidentSeverity.SeverityMajor;
            if (categoryLower.Contains("moderate"))
                return IncidentSeverity.SeverityModerate;

            // Default categorization by incident type
            if (categoryLower.Contains("raid") || categoryLower.Contains("toxic") || 
                categoryLower.Contains("volcanic") || categoryLower.Contains("infestation"))
                return IncidentSeverity.SeverityMajor;

            return IncidentSeverity.SeverityMinor;
        }

        #endregion
    }
}
