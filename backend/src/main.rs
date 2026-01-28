use sea_orm::Database;
use vespera::vespera;

mod routes;
mod models;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. 환경변수에서 DATABASE_URL 읽기 (Docker 환경 지원)
    // 환경변수가 없으면 로컬 개발용 기본값 사용
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgresql://localhost/aegis_link_db".to_string());
    
    println!("🔌 Connecting to database: {}", database_url);
    let db = Database::connect(&database_url).await?;

    // 2. 마이그레이션 자동 실행 (컴파일 타임에 SQL 생성)
    vespertide::vespertide_migration!(&db).await?;

    println!("✅ Database migrations applied successfully!");

    // 3. Vespera 앱 설정 (DB를 State로 공유)
    let app = vespera!(
        openapi = "openapi.json",
        title = "Aegis Link API - URL Reputation Management",
        version = "1.0.0",
        docs_url = "/docs"
    )
    .with_state(db.clone());

    // 4. 서버 시작
    // 환경변수에서 PORT 읽기 (Docker: 8000, 로컬: 3000)
    let port = std::env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let addr = format!("0.0.0.0:{}", port);
    
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    println!("🚀 Server running at http://{}", addr);
    println!("📚 Swagger UI: http://{}/docs", addr);
    axum::serve(listener, app).await?;

    Ok(())
}
