use sea_orm::Database;
use vespera::vespera;

mod routes;
mod models;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. DB 연결
    let db = Database::connect("postgresql://localhost/aegis_link_db").await?;

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
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    println!("🚀 Server running at http://localhost:3000");
    println!("📚 Swagger UI: http://localhost:3000/docs");
    axum::serve(listener, app).await?;

    Ok(())
}
