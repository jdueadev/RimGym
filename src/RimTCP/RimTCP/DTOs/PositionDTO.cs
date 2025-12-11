namespace RimTCP.DTOs
{
    /// <summary>
    /// Position data transfer object for 3D coordinates.
    /// </summary>
    public class PositionDTO
    {
        public int X { get; set; }
        public int Y { get; set; }
        public int Z { get; set; }

        public PositionDTO() { }

        public PositionDTO(int x, int y, int z)
        {
            X = x;
            Y = y;
            Z = z;
        }
    }
}
