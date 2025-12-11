using System.Collections.Generic;

namespace RimworldMLBridge.DTOs
{
    /// <summary>
    /// Basic colonist data transfer object.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// </summary>
    public class ColonistDTO
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Gender { get; set; }
        public int Age { get; set; }
        public float Health { get; set; }
        public float Mood { get; set; }
        public float Hunger { get; set; }
        public PositionDTO Position { get; set; }

        // Status flags
        public bool IsDrafted { get; set; }
        public bool IsDowned { get; set; }
        public bool IsDead { get; set; }
    }

    /// <summary>
    /// Detailed colonist information with all needs, skills, and work info.
    /// </summary>
    public class ColonistDetailedDTO
    {
        public float Sleep { get; set; }
        public float Comfort { get; set; }
        public float SurroundingBeauty { get; set; }
        public float FreshAir { get; set; }
        public ColonistDTO Colonist { get; set; }
        public ColonistWorkInfoDTO ColonistWorkInfo { get; set; }
        public ColonistMedicalInfoDTO ColonistMedicalInfo { get; set; }
        public ColonistSocialInfoDTO ColonistSocialInfo { get; set; }
    }

    /// <summary>
    /// Work-related colonist information.
    /// </summary>
    public class ColonistWorkInfoDTO
    {
        public List<SkillDTO> Skills { get; set; } = new List<SkillDTO>();
        public string CurrentJob { get; set; }
        public List<TraitDTO> Traits { get; set; } = new List<TraitDTO>();
        public List<WorkPriorityDTO> WorkPriorities { get; set; } = new List<WorkPriorityDTO>();
    }

    /// <summary>
    /// Skill data for a colonist.
    /// </summary>
    public class SkillDTO
    {
        public string Name { get; set; }
        public int Level { get; set; }
        public string Description { get; set; }
        public int MinLevel { get; set; }
        public int MaxLevel { get; set; }
        public string LevelDescriptor { get; set; }
        public bool PermanentlyDisabled { get; set; }
        public bool TotallyDisabled { get; set; }
        public float XpTotalEarned { get; set; }
        public float XpProgressPercent { get; set; }
        public float XpRequiredForLevelUp { get; set; }
        public float XpSinceLastLevel { get; set; }
        public int Aptitude { get; set; }
        public int Passion { get; set; }
        public int DisabledWorkTags { get; set; }
    }

    /// <summary>
    /// Trait data for a colonist.
    /// </summary>
    public class TraitDTO
    {
        public string Name { get; set; }
        public string Label { get; set; }
        public string Description { get; set; }
        public int DisabledWorkTags { get; set; }
        public bool Suppressed { get; set; }
    }

    /// <summary>
    /// Work priority setting for a colonist.
    /// </summary>
    public class WorkPriorityDTO
    {
        public string WorkType { get; set; }
        public int Priority { get; set; }
        public bool IsTotallyDisabled { get; set; }
    }

    /// <summary>
    /// Medical information for a colonist.
    /// </summary>
    public class ColonistMedicalInfoDTO
    {
        public float Health { get; set; }
        public List<HediffDTO> Hediffs { get; set; } = new List<HediffDTO>();
        public int MedicalPolicyId { get; set; }
        public bool IsSelfTendAllowed { get; set; }
    }

    /// <summary>
    /// Health condition (hediff) data.
    /// </summary>
    public class HediffDTO
    {
        public int LoadId { get; set; }
        public string DefName { get; set; }
        public string Label { get; set; }
        public string LabelCap { get; set; }
        public float Severity { get; set; }
        public string SeverityLabel { get; set; }
        public int CurStageIndex { get; set; }
        public string CurStageLabel { get; set; }
        public string PartLabel { get; set; }
        public string PartDefName { get; set; }
        public int AgeTicks { get; set; }
        public bool Visible { get; set; }
        public bool IsPermanent { get; set; }
        public bool IsTended { get; set; }
        public bool TendableNow { get; set; }
        public bool Bleeding { get; set; }
        public float BleedRate { get; set; }
        public bool IsLethal { get; set; }
        public float PainFactor { get; set; }
        public float PainOffset { get; set; }
    }

    /// <summary>
    /// Social relationships and family info for a colonist.
    /// </summary>
    public class ColonistSocialInfoDTO
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public List<RelationDTO> DirectRelations { get; set; } = new List<RelationDTO>();
        public int ChildrenCount { get; set; }
    }

    /// <summary>
    /// A social relationship between pawns.
    /// </summary>
    public class RelationDTO
    {
        public string RelationDefName { get; set; }
        public string OtherPawnId { get; set; }
        public string OtherPawnName { get; set; }
    }

    /// <summary>
    /// Inventory items carried by a colonist.
    /// </summary>
    public class ColonistInventoryDTO
    {
        public List<ThingDTO> Items { get; set; } = new List<ThingDTO>();
        public List<ThingDTO> Apparels { get; set; } = new List<ThingDTO>();
        public List<ThingDTO> Equipment { get; set; } = new List<ThingDTO>();
    }
}
