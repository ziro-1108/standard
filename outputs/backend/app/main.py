from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analysis_standards.db")
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-development-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


class Role(str, Enum):
    viewer = "viewer"
    engineer = "engineer"
    executive = "executive"
    server_admin = "server_admin"


class StandardStatus(str, Enum):
    in_progress = "in_progress"
    complete = "complete"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SqlEnum(Role), default=Role.viewer)


class ManagedAccount(Base):
    __tablename__ = "managed_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad_account: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), default=Role.viewer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


@dataclass
class Principal:
    id: int
    username: str
    role: Role


class SubProduct(Base):
    __tablename__ = "sub_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class HomeImage(Base):
    __tablename__ = "home_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot: Mapped[int] = mapped_column(Integer, unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class AnalysisPurpose(Base):
    __tablename__ = "analysis_purposes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    sub_product: Mapped[str] = mapped_column(String(100), default="하위제품 1")
    status: Mapped[StandardStatus] = mapped_column(SqlEnum(StandardStatus), default=StandardStatus.in_progress)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    documents: Mapped[list[StandardDocument]] = relationship(back_populates="purpose", cascade="all, delete-orphan")


class StandardDocument(Base):
    __tablename__ = "standard_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purpose_id: Mapped[int] = mapped_column(ForeignKey("analysis_purposes.id"))
    stage: Mapped[str] = mapped_column(String(50))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    thumbnail_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    purpose: Mapped[AnalysisPurpose] = relationship(back_populates="documents")


class Announcement(Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(4000))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LoginInput(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: Role


class PurposeCreate(BaseModel):
    title: str
    sub_product: str = "하위제품 1"


class PurposeUpdate(BaseModel):
    status: StandardStatus | None = None
    title: str | None = None


class SubProductCreate(BaseModel):
    name: str
    is_visible: bool = True


class SubProductUpdate(BaseModel):
    is_visible: bool


class HomeImageUpdate(BaseModel):
    is_visible: bool


class ManagedAccountCreate(BaseModel):
    ad_account: str
    role: Role


class ManagedAccountUpdate(BaseModel):
    role: Role


class ManagedAccountDelete(BaseModel):
    ids: list[int]


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    is_published: bool = True


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_published: bool | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()
app = FastAPI(title="분석 표준 관리 API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
STAGES = ["시료제작1", "시료제작2", "시료제작3", "촬영", "측정"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def issue_token(user: User | Principal):
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "ad_account": user.username, "role": user.role.value, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> Principal:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        ad_account = str(payload.get("ad_account") or "")
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
    account = db.scalar(select(ManagedAccount).where(ManagedAccount.ad_account == (ad_account or user.username)))
    return Principal(id=user.id, username=ad_account or user.username, role=account.role if account else Role.viewer)


def require(*roles: Role):
    def checker(user: Principal = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
        return user
    return checker


def document_out(document: StandardDocument):
    age = max(0, (datetime.now(timezone.utc).replace(tzinfo=None) - document.uploaded_at.replace(tzinfo=None)).days)
    return {
        "id": document.id, "stage": document.stage, "original_name": document.original_name,
        "uploaded_at": document.uploaded_at.isoformat(), "age_days": age,
        "file_url": f"/api/files/{document.stored_name}",
        "thumbnail_url": f"/api/thumbnails/{document.thumbnail_name}" if document.thumbnail_name else None,
    }


def purpose_out(purpose: AnalysisPurpose):
    docs = {d.stage: document_out(d) for d in purpose.documents}
    return {"id": purpose.id, "title": purpose.title, "sub_product": purpose.sub_product, "status": purpose.status.value,
            "created_at": purpose.created_at.isoformat(), "documents": docs}


def announcement_out(announcement: Announcement):
    return {
        "id": announcement.id,
        "title": announcement.title,
        "content": announcement.content,
        "is_published": announcement.is_published,
        "created_at": announcement.created_at.isoformat(),
        "updated_at": announcement.updated_at.isoformat(),
    }


def sub_product_out(product: SubProduct):
    return {"id": product.id, "name": product.name, "is_visible": product.is_visible, "created_at": product.created_at.isoformat()}


def home_image_out(image: HomeImage):
    return {"id": image.id, "slot": image.slot, "original_name": image.original_name, "is_visible": image.is_visible,
            "uploaded_at": image.uploaded_at.isoformat(), "image_url": f"/api/home-images/assets/{image.stored_name}"}


def create_thumbnail(pptx_path: Path, original_name: str, filename: str) -> str | None:
    """Render slide 1 at 1400×1000; use a clear fallback if a local renderer is unavailable."""
    thumb = f"{Path(filename).stem}.png"
    try:
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(work), str(pptx_path)], check=True, timeout=90, capture_output=True)
            pdf = work / f"{pptx_path.stem}.pdf"
            rendered = work / "slide-1.png"
            subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-png", "-scale-to-x", "1400", "-scale-to-y", "1000", str(pdf), str(rendered.with_suffix(""))], check=True, timeout=30, capture_output=True)
            shutil.copy2(rendered, UPLOAD_DIR / thumb)
            return thumb
    except Exception:
        pass
    try:
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new("RGB", (1400, 1000), "#f7f9ff")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((70, 70, 1330, 930), radius=28, fill="#ffffff", outline="#d8e1f0", width=4)
        draw.rectangle((70, 70, 1330, 215), fill="#da4a5d")
        draw.text((140, 335), "ANALYSIS STANDARD", fill="#1e2c45", font=ImageFont.load_default())
        draw.text((140, 405), original_name or "PPTX", fill="#52637d", font=ImageFont.load_default())
        draw.text((140, 770), "PPTX PREVIEW", fill="#da4a5d", font=ImageFont.load_default())
        image.save(UPLOAD_DIR / thumb)
        return thumb
    except Exception:
        return None


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    if "analysis_purposes" in inspect(engine).get_table_names():
        columns = {column["name"] for column in inspect(engine).get_columns("analysis_purposes")}
        if "sub_product" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE analysis_purposes ADD COLUMN sub_product VARCHAR(100) NOT NULL DEFAULT '하위제품 1'"))
    with SessionLocal() as db:
        for username, role in [("viewer", Role.viewer), ("engineer", Role.engineer), ("executive", Role.executive), ("server_admin", Role.server_admin)]:
            if not db.scalar(select(User.id).where(User.username == username)):
                db.add(User(username=username, password_hash=pwd_context.hash("demo1234"), role=role))
            if role != Role.viewer and not db.scalar(select(ManagedAccount.id).where(ManagedAccount.ad_account == username)):
                db.add(ManagedAccount(ad_account=username, role=role))
        if not db.scalar(select(AnalysisPurpose.id).limit(1)):
            completed = AnalysisPurpose(title="전해액 조성에 따른 전지 특성 분석", sub_product="하위제품 1", status=StandardStatus.complete)
            pending = AnalysisPurpose(title="고온 보관 조건 신뢰성 분석", sub_product="하위제품 2", status=StandardStatus.in_progress)
            db.add_all([completed, pending])
        product_names = {"하위제품 1", "하위제품 2"}
        product_names.update(db.scalars(select(AnalysisPurpose.sub_product).distinct()).all())
        for product_name in product_names:
            if product_name and not db.scalar(select(SubProduct.id).where(SubProduct.name == product_name)):
                db.add(SubProduct(name=product_name, is_visible=True))
        db.commit()


@app.post("/api/auth/login")
def login(body: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    account = db.scalar(select(ManagedAccount).where(ManagedAccount.ad_account == user.username))
    principal = Principal(id=user.id, username=user.username, role=account.role if account else Role.viewer)
    return {"access_token": issue_token(principal), "token_type": "bearer", "user": UserOut(id=principal.id, username=principal.username, role=principal.role)}


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    purposes = db.scalars(select(AnalysisPurpose)).all()
    visible = [p for p in purposes if p.status == StandardStatus.complete or user.role != Role.viewer]
    total_docs = sum(len(p.documents) for p in visible)
    return {"purpose_count": len(visible), "document_count": total_docs,
            "stage_counts": {stage: sum(1 for p in visible if any(d.stage == stage for d in p.documents)) for stage in STAGES}}


@app.get("/api/my-page")
def my_page_summary(user: User = Depends(require(Role.engineer, Role.executive)), db: Session = Depends(get_db)):
    purposes = db.scalars(select(AnalysisPurpose)).all()
    stage_counts = {stage: sum(1 for purpose in purposes if any(document.stage == stage for document in purpose.documents)) for stage in STAGES}
    return {
        "username": user.username,
        "role": user.role.value,
        "total_documents": sum(stage_counts.values()),
        "stage_counts": stage_counts,
    }


@app.get("/api/admin/managed-accounts")
def list_managed_accounts(user: Principal = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    accounts = db.scalars(select(ManagedAccount).where(ManagedAccount.role != Role.viewer).order_by(ManagedAccount.role, ManagedAccount.ad_account)).all()
    return [{"id": account.id, "ad_account": account.ad_account, "role": account.role.value, "created_at": account.created_at.isoformat()} for account in accounts]


@app.post("/api/admin/managed-accounts", status_code=status.HTTP_201_CREATED)
def create_managed_account(body: ManagedAccountCreate, user: Principal = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    ad_account = body.ad_account.strip()
    if not ad_account or len(ad_account) > 120:
        raise HTTPException(status_code=422, detail="AD 계정명은 1~120자로 입력해 주세요.")
    if db.scalar(select(ManagedAccount.id).where(ManagedAccount.ad_account == ad_account)):
        raise HTTPException(status_code=409, detail="이미 관리 중인 AD 계정입니다.")
    if body.role == Role.viewer:
        raise HTTPException(status_code=422, detail="Viewer는 기본 권한이므로 관리 목록에 추가할 수 없습니다.")
    account = ManagedAccount(ad_account=ad_account, role=body.role)
    db.add(account); db.commit(); db.refresh(account)
    return {"id": account.id, "ad_account": account.ad_account, "role": account.role.value, "created_at": account.created_at.isoformat()}


@app.patch("/api/admin/managed-accounts/{account_id}")
def update_managed_account(account_id: int, body: ManagedAccountUpdate, user: Principal = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    account = db.get(ManagedAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="관리 계정을 찾을 수 없습니다.")
    if body.role == Role.viewer:
        raise HTTPException(status_code=422, detail="Viewer로 변경하려면 관리 목록에서 제거해 주세요.")
    account.role = body.role
    db.commit(); db.refresh(account)
    return {"id": account.id, "ad_account": account.ad_account, "role": account.role.value, "created_at": account.created_at.isoformat()}


@app.delete("/api/admin/managed-accounts", status_code=status.HTTP_204_NO_CONTENT)
def delete_managed_accounts(body: ManagedAccountDelete, user: Principal = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    accounts = db.scalars(select(ManagedAccount).where(ManagedAccount.id.in_(body.ids))).all()
    if any(account.ad_account == user.username for account in accounts):
        raise HTTPException(status_code=409, detail="현재 로그인한 서버 관리자 계정은 제거할 수 없습니다.")
    for account in accounts:
        db.delete(account)
    db.commit()


@app.get("/api/sub-products")
def list_sub_products(user: User = Depends(current_user), db: Session = Depends(get_db)):
    products = db.scalars(select(SubProduct).where(SubProduct.is_visible.is_(True)).order_by(SubProduct.id)).all()
    return [sub_product_out(product) for product in products]


@app.get("/api/purposes")
def list_purposes(sub_product: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if sub_product and not db.scalar(select(SubProduct.id).where(SubProduct.name == sub_product)):
        raise HTTPException(status_code=422, detail="유효하지 않은 하위제품입니다.")
    purposes = db.scalars(select(AnalysisPurpose).order_by(AnalysisPurpose.created_at.desc())).unique().all()
    if sub_product:
        purposes = [purpose for purpose in purposes if purpose.sub_product == sub_product]
    if user.role == Role.viewer:
        purposes = [p for p in purposes if p.status == StandardStatus.complete]
    return [purpose_out(p) for p in purposes]


@app.get("/api/admin/sub-products")
def list_admin_sub_products(user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    return [sub_product_out(product) for product in db.scalars(select(SubProduct).order_by(SubProduct.id)).all()]


@app.post("/api/admin/sub-products", status_code=status.HTTP_201_CREATED)
def create_sub_product(body: SubProductCreate, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    name = body.name.strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=422, detail="하위제품 이름은 1~100자로 입력해 주세요.")
    if db.scalar(select(SubProduct.id).where(SubProduct.name == name)):
        raise HTTPException(status_code=409, detail="이미 등록된 하위제품입니다.")
    product = SubProduct(name=name, is_visible=body.is_visible)
    db.add(product); db.commit(); db.refresh(product)
    return sub_product_out(product)


@app.patch("/api/admin/sub-products/{product_id}")
def update_sub_product(product_id: int, body: SubProductUpdate, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    product = db.get(SubProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="하위제품을 찾을 수 없습니다.")
    product.is_visible = body.is_visible
    db.commit(); db.refresh(product)
    return sub_product_out(product)


@app.delete("/api/admin/sub-products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sub_product(product_id: int, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    product = db.get(SubProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="하위제품을 찾을 수 없습니다.")
    if db.scalar(select(AnalysisPurpose.id).where(AnalysisPurpose.sub_product == product.name).limit(1)):
        raise HTTPException(status_code=409, detail="분석 표준이 등록된 하위제품은 삭제할 수 없습니다. 먼저 표준을 정리해 주세요.")
    db.delete(product)
    db.commit()


@app.get("/api/home-images")
def list_visible_home_images(db: Session = Depends(get_db)):
    images = db.scalars(select(HomeImage).where(HomeImage.is_visible.is_(True)).order_by(HomeImage.slot)).all()
    return [home_image_out(image) for image in images]


@app.get("/api/home-images/assets/{filename}")
def get_home_image(filename: str):
    path = UPLOAD_DIR / Path(filename).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    return FileResponse(path)


@app.get("/api/admin/home-images")
def list_admin_home_images(user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    return [home_image_out(image) for image in db.scalars(select(HomeImage).order_by(HomeImage.slot)).all()]


@app.post("/api/admin/home-images", status_code=status.HTTP_201_CREATED)
async def upload_home_image(slot: int = Form(...), file: UploadFile = File(...), user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    if slot not in (1, 2, 3):
        raise HTTPException(status_code=422, detail="이미지 위치는 1~3 중에서 선택해 주세요.")
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    extension = Path(file.filename or "").suffix.lower()
    if extension not in allowed:
        raise HTTPException(status_code=422, detail="JPG, PNG, WebP 이미지 파일만 업로드할 수 있습니다.")
    stored_name = f"home-{slot}-{uuid.uuid4().hex}{extension}"
    target = UPLOAD_DIR / stored_name
    with target.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    if target.stat().st_size > 10 * 1024 * 1024:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="이미지 파일은 10MB 이하만 업로드할 수 있습니다.")
    existing = db.scalar(select(HomeImage).where(HomeImage.slot == slot))
    if existing:
        (UPLOAD_DIR / existing.stored_name).unlink(missing_ok=True)
        db.delete(existing)
    image = HomeImage(slot=slot, original_name=file.filename or stored_name, stored_name=stored_name)
    db.add(image); db.commit(); db.refresh(image)
    return home_image_out(image)


@app.patch("/api/admin/home-images/{image_id}")
def update_home_image(image_id: int, body: HomeImageUpdate, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    image = db.get(HomeImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    image.is_visible = body.is_visible
    db.commit(); db.refresh(image)
    return home_image_out(image)


@app.delete("/api/admin/home-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_home_image(image_id: int, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    image = db.get(HomeImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    (UPLOAD_DIR / image.stored_name).unlink(missing_ok=True)
    db.delete(image)
    db.commit()


@app.get("/api/announcements")
def list_published_announcements(user: User = Depends(current_user), db: Session = Depends(get_db)):
    announcements = db.scalars(select(Announcement).where(Announcement.is_published.is_(True)).order_by(Announcement.created_at.desc())).all()
    return [announcement_out(announcement) for announcement in announcements]


@app.get("/api/admin/announcements")
def list_admin_announcements(user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    announcements = db.scalars(select(Announcement).order_by(Announcement.created_at.desc())).all()
    return [announcement_out(announcement) for announcement in announcements]


@app.post("/api/admin/announcements", status_code=status.HTTP_201_CREATED)
def create_announcement(body: AnnouncementCreate, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    title, content = body.title.strip(), body.content.strip()
    if not title or not content or len(title) > 200 or len(content) > 4000:
        raise HTTPException(status_code=422, detail="공지 제목과 내용을 확인해 주세요.")
    announcement = Announcement(title=title, content=content, is_published=body.is_published)
    db.add(announcement); db.commit(); db.refresh(announcement)
    return announcement_out(announcement)


@app.patch("/api/admin/announcements/{announcement_id}")
def update_announcement(announcement_id: int, body: AnnouncementUpdate, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    announcement = db.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="공지를 찾을 수 없습니다.")
    if body.title is not None:
        announcement.title = body.title.strip()
    if body.content is not None:
        announcement.content = body.content.strip()
    if body.is_published is not None:
        announcement.is_published = body.is_published
    if not announcement.title or not announcement.content:
        raise HTTPException(status_code=422, detail="공지 제목과 내용을 입력해 주세요.")
    db.commit(); db.refresh(announcement)
    return announcement_out(announcement)


@app.delete("/api/admin/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(announcement_id: int, user: User = Depends(require(Role.server_admin)), db: Session = Depends(get_db)):
    announcement = db.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="공지를 찾을 수 없습니다.")
    db.delete(announcement)
    db.commit()


@app.post("/api/purposes", status_code=201)
def create_purpose(body: PurposeCreate, user: User = Depends(require(Role.engineer, Role.executive)), db: Session = Depends(get_db)):
    title = body.title.strip()
    if not title or len(title) > 200:
        raise HTTPException(status_code=422, detail="분석 목적은 1~200자로 입력해 주세요.")
    if not db.scalar(select(SubProduct.id).where(SubProduct.name == body.sub_product, SubProduct.is_visible.is_(True))):
        raise HTTPException(status_code=422, detail="유효하지 않은 하위제품입니다.")
    purpose = AnalysisPurpose(title=title, sub_product=body.sub_product)
    db.add(purpose); db.commit(); db.refresh(purpose)
    return purpose_out(purpose)


@app.patch("/api/purposes/{purpose_id}")
def update_purpose(purpose_id: int, body: PurposeUpdate, user: Principal = Depends(require(Role.executive, Role.server_admin)), db: Session = Depends(get_db)):
    purpose = db.get(AnalysisPurpose, purpose_id)
    if not purpose: raise HTTPException(status_code=404, detail="분석 목적을 찾을 수 없습니다.")
    if body.status is None and body.title is None:
        raise HTTPException(status_code=422, detail="변경할 분석 목적 정보가 없습니다.")
    if body.title is not None:
        title = body.title.strip()
        if not title or len(title) > 200:
            raise HTTPException(status_code=422, detail="분석 목적은 1~200자로 입력해 주세요.")
        purpose.title = title
    if body.status is not None:
        purpose.status = body.status
    db.commit(); db.refresh(purpose)
    return purpose_out(purpose)


@app.delete("/api/purposes/{purpose_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purpose(purpose_id: int, user: Principal = Depends(require(Role.executive, Role.server_admin)), db: Session = Depends(get_db)):
    purpose = db.get(AnalysisPurpose, purpose_id)
    if not purpose:
        raise HTTPException(status_code=404, detail="분석 목적을 찾을 수 없습니다.")
    for document in purpose.documents:
        for name in [document.stored_name, document.thumbnail_name]:
            if name:
                (UPLOAD_DIR / Path(name).name).unlink(missing_ok=True)
    db.delete(purpose)
    db.commit()


@app.post("/api/purposes/{purpose_id}/documents", status_code=201)
async def upload_document(purpose_id: int, stage: str = Form(...), file: UploadFile = File(...), user: User = Depends(require(Role.engineer, Role.executive)), db: Session = Depends(get_db)):
    if stage not in STAGES: raise HTTPException(status_code=422, detail="유효하지 않은 하위 표준입니다.")
    if not file.filename or not file.filename.lower().endswith(".pptx"):
        raise HTTPException(status_code=422, detail="PPTX 파일만 업로드할 수 있습니다.")
    purpose = db.get(AnalysisPurpose, purpose_id)
    if not purpose: raise HTTPException(status_code=404, detail="분석 목적을 찾을 수 없습니다.")
    stored_name = f"{uuid.uuid4().hex}.pptx"
    target = UPLOAD_DIR / stored_name
    with target.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    existing = db.scalar(select(StandardDocument).where(StandardDocument.purpose_id == purpose_id, StandardDocument.stage == stage))
    if existing:
        for old in [existing.stored_name, existing.thumbnail_name]:
            if old: (UPLOAD_DIR / old).unlink(missing_ok=True)
        db.delete(existing)
    thumbnail = create_thumbnail(target, file.filename, stored_name)
    document = StandardDocument(purpose_id=purpose_id, stage=stage, original_name=file.filename, stored_name=stored_name, thumbnail_name=thumbnail)
    db.add(document); db.commit(); db.refresh(document)
    return document_out(document)


def visible_document_or_404(filename: str, user: User, db: Session) -> StandardDocument:
    safe_name = Path(filename).name
    document = db.scalar(select(StandardDocument).where((StandardDocument.stored_name == safe_name) | (StandardDocument.thumbnail_name == safe_name)))
    if not document:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    if user.role in (Role.viewer, Role.server_admin) and document.purpose.status != StandardStatus.complete:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return document


@app.get("/api/files/{filename}")
def get_file(filename: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    document = visible_document_or_404(filename, user, db)
    path = UPLOAD_DIR / Path(filename).name
    if not path.exists(): raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=document.original_name)


@app.get("/api/thumbnails/{filename}")
def get_thumbnail(filename: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    visible_document_or_404(filename, user, db)
    path = UPLOAD_DIR / Path(filename).name
    if not path.exists(): raise HTTPException(status_code=404, detail="미리보기를 찾을 수 없습니다.")
    return FileResponse(path, media_type="image/png")


@app.delete("/api/purposes/{purpose_id}/documents/{stage}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(purpose_id: int, stage: str, user: User = Depends(require(Role.engineer, Role.executive)), db: Session = Depends(get_db)):
    if stage not in STAGES:
        raise HTTPException(status_code=422, detail="유효하지 않은 하위 표준입니다.")
    document = db.scalar(select(StandardDocument).where(StandardDocument.purpose_id == purpose_id, StandardDocument.stage == stage))
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    for name in [document.stored_name, document.thumbnail_name]:
        if name:
            (UPLOAD_DIR / Path(name).name).unlink(missing_ok=True)
    db.delete(document)
    db.commit()
