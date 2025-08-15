import sqlalchemy
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_FILE = "vrm_motioncapture.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Model Definitions ---

class AppSettings(Base):
    __tablename__ = "app_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    auth_token = Column(Text, nullable=False)
    engine_http_port = Column(Integer, nullable=False, default=8800)

    __table_args__ = (
        CheckConstraint('id=1', name='singleton_check'),
    )

class OscTargets(Base):
    __tablename__ = "osc_targets"
    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    protocol = Column(Text, nullable=False)
    host = Column(Text, nullable=False)
    port = Column(Integer, nullable=False)
    path_prefix = Column(Text, default='/ps')
    send_rate_hz = Column(Integer, nullable=False, default=30)

    __table_args__ = (
        CheckConstraint(protocol.in_(['OSC', 'VMC']), name='protocol_check'),
        UniqueConstraint('host', 'port', 'protocol', name='uix_host_port_protocol'),
    )

class CameraSources(Base):
    __tablename__ = "camera_sources"
    id = Column(Text, primary_key=True)
    kind = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    device_index = Column(Integer)
    url = Column(Text)
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Integer)
    enabled = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint(kind.in_(['DEVICE', 'RTSP', 'FILE']), name='kind_check'),
    )

class VrmModels(Base):
    __tablename__ = "vrm_models"
    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    version = Column(Text)
    path = Column(Text, nullable=False)
    humanoid_json = Column(Text, nullable=False)
    expressions_json = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)

class Pipelines(Base):
    __tablename__ = "pipelines"
    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    camera_id = Column(Text, ForeignKey("camera_sources.id", ondelete="CASCADE"), nullable=False)
    osc_target_id = Column(Text, ForeignKey("osc_targets.id", ondelete="CASCADE"), nullable=False)
    vrm_id = Column(Text, ForeignKey("vrm_models.id", ondelete="RESTRICT"), nullable=False)
    pose_enabled = Column(Integer, nullable=False, default=1)
    face_enabled = Column(Integer, nullable=False, default=1)
    hands_enabled = Column(Integer, nullable=False, default=0)
    shrug_enabled = Column(Integer, nullable=False, default=0)
    gaze_enabled = Column(Integer, nullable=False, default=0)
    smoothing_alpha = Column(Float, nullable=False, default=0.7)
    scale = Column(Float, nullable=False, default=1.0)
    active = Column(Integer, nullable=False, default=0)

    camera_source = relationship("CameraSources")
    osc_target = relationship("OscTargets")
    vrm_model = relationship("VrmModels")

class TxChannels(Base):
    __tablename__ = "tx_channels"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_id = Column(Text, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    kind = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    map_expr = Column(Text)
    enabled = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint(kind.in_(['BONE', 'BLENDSHAPE']), name='kind_check'),
        UniqueConstraint('pipeline_id', 'kind', 'name', name='uix_pipeline_kind_name'),
    )
    pipeline = relationship("Pipelines")


class ExportJobs(Base):
    __tablename__ = "export_jobs"
    id = Column(Text, primary_key=True)
    pipeline_id = Column(Text, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    fmt = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    enabled = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint(fmt.in_(['jsonl', 'csv']), name='fmt_check'),
    )
    pipeline = relationship("Pipelines")


class Replays(Base):
    __tablename__ = "replays"
    id = Column(Text, primary_key=True)
    pipeline_id = Column(Text, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    path = Column(Text, nullable=False)
    duration_sec = Column(Float, nullable=False)

    pipeline = relationship("Pipelines")


def create_db_and_tables():
    """
    Initializes the database and creates all tables.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing database and creating tables...")
    create_db_and_tables()
    print(f"Database '{DATABASE_FILE}' created successfully with all tables.")
