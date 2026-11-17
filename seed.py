"""Script khởi tạo dữ liệu mẫu (Seed Data) cho dự án AI Interview & Project Management."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Sau đó mới import các module của app
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
...
import sys
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task


def seed_data():
    """Tự động kiểm tra và chèn dữ liệu mẫu vào Database."""
    print("🌱 Đang kết nối Database và kiểm tra cấu trúc bảng...")
    
    # Tự động tạo các bảng nếu chưa có
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()

    try:
        # 1. Kiểm tra xem đã có dữ liệu trong bảng users chưa
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️ Database đã có dữ liệu sẵn! Bỏ qua quá trình seed để tránh trùng lặp.")
            return

        print("🚀 Đang khởi tạo dữ liệu mẫu...")

        # 2. Tạo User mẫu (1 Admin, 2 User thường)
        admin = User(
            email="admin@gmail.com",
            full_name="Quản trị viên (Admin)",
            hashed_password=hash_password("admin123"),
            role="ADMIN",
            is_active=True,
        )
        user1 = User(
            email="viet.tran@gmail.com",
            full_name="Trần Nguyễn Quốc Việt",
            hashed_password=hash_password("user123"),
            role="USER",
            is_active=True,
        )
        user2 = User(
            email="dev.member@gmail.com",
            full_name="Lập trình viên mẫu",
            hashed_password=hash_password("user123"),
            role="USER",
            is_active=True,
        )

        db.add_all([admin, user1, user2])
        db.commit()
        db.refresh(admin)
        db.refresh(user1)
        db.refresh(user2)
        print("  ✓ Đã khởi tạo 3 Users mẫu.")

        # 3. Tạo Project mẫu
        project1 = Project(
            name="Dự án AI Interview Backend",
            description="Xây dựng hệ thống backend quản lý phỏng vấn AI bằng FastAPI & MySQL.",
            owner_id=user1.id,
        )
        project2 = Project(
            name="Dự án E-Commerce TQV Shop",
            description="Hệ thống bán hàng trực tuyến với giao diện chuẩn Gray & Dark mode.",
            owner_id=admin.id,
        )

        db.add_all([project1, project2])
        db.commit()
        db.refresh(project1)
        db.refresh(project2)
        print("  ✓ Đã khởi tạo 2 Projects mẫu.")

        # 4. Tạo Thành viên dự án (ProjectMember)
        pm1 = ProjectMember(project_id=project1.id, user_id=user1.id, role="OWNER")
        pm2 = ProjectMember(project_id=project1.id, user_id=user2.id, role="MEMBER")
        pm3 = ProjectMember(project_id=project2.id, user_id=admin.id, role="OWNER")
        pm4 = ProjectMember(project_id=project2.id, user_id=user1.id, role="MANAGER")

        db.add_all([pm1, pm2, pm3, pm4])
        db.commit()
        print("  ✓ Đã gán thành viên vào các dự án.")

        # 5. Tạo Task mẫu
        task1 = Task(
            title="[Database] Kết nối DB MySQL",
            description="Kết nối MySQL bằng SQLAlchemy; xây dựng engine, SessionLocal và dependency get_db.",
            status="DONE",
            priority="HIGH",
            project_id=project1.id,
            assignee_id=user1.id,
        )
        task2 = Task(
            title="[Database] Pydantic schema",
            description="Tạo Base/Create/Update/Response schema cho các entity chính; bật ORM/from_attributes.",
            status="DONE",
            priority="HIGH",
            project_id=project1.id,
            assignee_id=user1.id,
        )
        task3 = Task(
            title="[Validation] Lỗi nghiệp vụ Auth",
            description="Xử lý lỗi token hết hạn/sai, đăng nhập sai credentials, tài khoản không hoạt động.",
            status="IN_PROGRESS",
            priority="HIGH",
            project_id=project1.id,
            assignee_id=user1.id,
        )
        task4 = Task(
            title="[Core] Viết Unit Test cho Auth",
            description="Viết test case cho endpoint đăng ký và đăng nhập tài khoản.",
            status="TODO",
            priority="MEDIUM",
            project_id=project1.id,
            assignee_id=user2.id,
        )

        db.add_all([task1, task2, task3, task4])
        db.commit()
        print("  ✓ Đã tạo 4 Tasks mẫu.")

        print("\n🎉 HOÀN THÀNH SEED DỮ LIỆU THÀNH CÔNG!")
        print("---------------------------------------")
        print("Tài khoản mẫu để test:")
        print(" 🔑 Admin:  admin@gmail.com     / Mật khẩu: admin123")
        print(" 🔑 User 1: viet.tran@gmail.com / Mật khẩu: user123")
        print(" 🔑 User 2: dev.member@gmail.com / Mật khẩu: user123")
        print("---------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi trong quá trình seed dữ liệu: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()