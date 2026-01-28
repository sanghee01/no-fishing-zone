use sea_orm::Database;
use vespera::vespera;
use tower_http::cors::CorsLayer;

mod routes;
mod models;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    match run().await {
        Ok(_) => Ok(()),
        Err(e) => {
            eprintln!("❌ Fatal error: {:?}", e);
            Err(e)
        }
    }
}

async fn run() -> anyhow::Result<()> {
    // 1. 환경변수가 없으면 로컬 개발용 기본값 사용
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgresql://localhost/aegis_link_db".to_string());
    
    println!("🔌 Connecting to database: {}", database_url);
    let db = Database::connect(&database_url).await?;

    // 2. 마이그레이션 자동 실행
    vespertide::vespertide_migration!(&db).await?;

    println!("✅ Database migrations applied successfully!");

    // 3. CORS 설정 (모든 오리진, 메서드, 헤더 허용)
    let cors = CorsLayer::permissive();

    // 4. Vespera 앱 설정 (CORS 레이어 추가)
    let app = vespera!(
        openapi = "openapi.json",
        title = "Aegis Link API - URL Reputation Management",
        version = "1.0.0",
        docs_url = "/docs",
        dir = "routes"
    )
    .with_state(db.clone())
    .layer(cors);

    // 5. 서버 시작 (기본 포트 8000)
    let port = std::env::var("PORT").unwrap_or_else(|_| "8000".to_string());
    let addr = format!("0.0.0.0:{}", port);
    
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    println!("🚀 Server running at http://localhost:{}", port);
    println!("📚 Swagger UI: http://localhost:{}/docs", port);
    axum::serve(listener, app).await?;

    Ok(())
}
