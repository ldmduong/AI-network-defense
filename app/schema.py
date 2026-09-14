from pydantic import BaseModel, ConfigDict, Field


class NetworkFlowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination_port: float = Field(alias="Destination Port")
    flow_duration: float = Field(alias="Flow Duration")
    total_fwd_packets: float = Field(alias="Total Fwd Packets")
    total_length_of_fwd_packets: float = Field(
        alias="Total Length of Fwd Packets"
    )
    fwd_packet_length_max: float = Field(alias="Fwd Packet Length Max")
    fwd_packet_length_min: float = Field(alias="Fwd Packet Length Min")
    fwd_packet_length_mean: float = Field(alias="Fwd Packet Length Mean")
    fwd_packet_length_std: float = Field(alias="Fwd Packet Length Std")
    bwd_packet_length_max: float = Field(alias="Bwd Packet Length Max")
    bwd_packet_length_min: float = Field(alias="Bwd Packet Length Min")
    bwd_packet_length_mean: float = Field(alias="Bwd Packet Length Mean")
    bwd_packet_length_std: float = Field(alias="Bwd Packet Length Std")
    flow_bytes_per_second: float = Field(alias="Flow Bytes/s")
    flow_packets_per_second: float = Field(alias="Flow Packets/s")
    flow_iat_mean: float = Field(alias="Flow IAT Mean")
    flow_iat_std: float = Field(alias="Flow IAT Std")
    flow_iat_max: float = Field(alias="Flow IAT Max")
    flow_iat_min: float = Field(alias="Flow IAT Min")
    fwd_iat_total: float = Field(alias="Fwd IAT Total")
    fwd_iat_mean: float = Field(alias="Fwd IAT Mean")
    fwd_iat_std: float = Field(alias="Fwd IAT Std")
    fwd_iat_max: float = Field(alias="Fwd IAT Max")
    fwd_iat_min: float = Field(alias="Fwd IAT Min")
    bwd_iat_total: float = Field(alias="Bwd IAT Total")
    bwd_iat_mean: float = Field(alias="Bwd IAT Mean")
    bwd_iat_std: float = Field(alias="Bwd IAT Std")
    bwd_iat_max: float = Field(alias="Bwd IAT Max")
    bwd_iat_min: float = Field(alias="Bwd IAT Min")
    fwd_header_length: float = Field(alias="Fwd Header Length")
    bwd_header_length: float = Field(alias="Bwd Header Length")
    fwd_packets_per_second: float = Field(alias="Fwd Packets/s")
    bwd_packets_per_second: float = Field(alias="Bwd Packets/s")
    min_packet_length: float = Field(alias="Min Packet Length")
    max_packet_length: float = Field(alias="Max Packet Length")
    packet_length_mean: float = Field(alias="Packet Length Mean")
    packet_length_std: float = Field(alias="Packet Length Std")
    packet_length_variance: float = Field(alias="Packet Length Variance")
    fin_flag_count: float = Field(alias="FIN Flag Count")
    psh_flag_count: float = Field(alias="PSH Flag Count")
    ack_flag_count: float = Field(alias="ACK Flag Count")
    average_packet_size: float = Field(alias="Average Packet Size")
    subflow_fwd_bytes: float = Field(alias="Subflow Fwd Bytes")
    init_win_bytes_forward: float = Field(
        alias="Init_Win_bytes_forward"
    )
    init_win_bytes_backward: float = Field(
        alias="Init_Win_bytes_backward"
    )
    act_data_pkt_fwd: float = Field(alias="act_data_pkt_fwd")
    min_seg_size_forward: float = Field(alias="min_seg_size_forward")
    active_mean: float = Field(alias="Active Mean")
    active_max: float = Field(alias="Active Max")
    active_min: float = Field(alias="Active Min")
    idle_mean: float = Field(alias="Idle Mean")
    idle_max: float = Field(alias="Idle Max")
    idle_min: float = Field(alias="Idle Min")


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_attack: str
    actual_attack: str
    recommended_action: str
    action_was_correct: bool
    comment: str | None = None
