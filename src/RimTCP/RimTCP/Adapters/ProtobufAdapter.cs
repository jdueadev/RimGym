using System;

namespace RimTCP.Adapters
{
    /// <summary>
    /// Base class for DTO to Protobuf message adapters.
    /// Provides clean separation between internal C# representations and wire format.
    /// </summary>
    /// <typeparam name="TDto">Internal DTO type</typeparam>
    /// <typeparam name="TProto">Protobuf message type</typeparam>
    public abstract class ProtobufAdapter<TDto, TProto>
        where TDto : class
        where TProto : class
    {
        /// <summary>
        /// Convert a DTO to its Protobuf representation.
        /// </summary>
        public abstract TProto ToProtobuf(TDto dto);

        /// <summary>
        /// Convert a Protobuf message back to DTO (optional, for bidirectional adapters).
        /// </summary>
        public virtual TDto FromProtobuf(TProto proto)
        {
            throw new NotImplementedException("FromProtobuf not implemented for this adapter");
        }

        /// <summary>
        /// Safely convert a DTO, returning null if input is null.
        /// </summary>
        public TProto ToProtobufSafe(TDto dto)
        {
            return dto == null ? null : ToProtobuf(dto);
        }
    }
}
