use axum::{
    extract::{Query, State},
    http::StatusCode,
    Json,
};
use sea_orm::{ColumnTrait, DatabaseConnection, EntityTrait, QueryFilter, Set};
use serde::{Deserialize, Serialize};
use vespera::Schema;

use crate::models::url_reputations_vespertide::{self, Entity as UrlReputations, UrlStatus};

/// URL 평판 정보 응답 스키마
#[derive(Serialize, Deserialize, Schema, Debug, Clone)]
pub struct UrlReputationResponse {
    /// 평가 대상 URL
    pub url: String,
    /// URL에 대한 설명
    pub description: Option<String>,
    /// 평판 점수 (0-100)
    pub score: i32,
    /// URL 상태 (SAFE | WARNING | BLOCK)
    pub status: UrlStatus,
}

/// URL 평판 정보 생성/업데이트 요청 스키마
#[derive(Deserialize, Schema, Debug, Clone)]
pub struct CreateUrlReputation {
    /// 평가 대상 URL
    pub url: String,
    /// URL에 대한 설명
    pub description: Option<String>,
    /// 평판 점수 (0-100)
    pub score: i32,
    /// URL 상태 (SAFE | WARNING | BLOCK)
    pub status: UrlStatus,
}

/// URL 조회 쿼리 파라미터
#[derive(Deserialize, Schema, Debug)]
pub struct GetUrlQuery {
    /// 조회할 URL
    pub url: String,
}

/// URL 평판 정보 조회
/// 
/// 사용자가 URL 클릭 시 해당 URL의 안전성을 확인하기 위해 사용합니다.
/// DB에 해당 URL이 없으면 AI 서버에 분석을 요청하고 결과를 저장 후 반환합니다.
/// AI 서버 분석 결과는 DB에 저장됩니다.
#[vespera::route(get, path = "", tags = ["url-reputations"])]
pub async fn get_url_reputation(
    State(db): State<DatabaseConnection>,
    Query(query): Query<GetUrlQuery>,
) -> Result<Json<UrlReputationResponse>, StatusCode> {
    println!("🔍 Searching for URL reputation: [{}]", query.url);
    
    let result = UrlReputations::find()
        .filter(url_reputations_vespertide::Column::Url.eq(&query.url))
        .one(&db)
        .await
        .map_err(|e| {
            println!("❌ Database query error: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;
    
    if let Some(model) = result {
        println!("✅ Found: {}", model.url);
        return Ok(Json(UrlReputationResponse {
            url: model.url,
            description: model.description,
            score: model.score,
            status: model.status,
        }));
    }

    println!("⚠️ Not found in DB: {}. Requesting AI analysis...", query.url);

    // AI Server로 분석 요청
    let client = reqwest::Client::new();
    let ai_server_url = std::env::var("AI_SERVER_URL").unwrap_or_else(|_| "http://ai:8001".to_string());
    
    // AI 서버가 기대하는 요청 포맷: { "url": "...", "request_id": "..." }
    let request_id = uuid::Uuid::new_v4().to_string();
    
    let ai_response = client
        .post(format!("{}/analyze", ai_server_url))
        .json(&serde_json::json!({
            "url": query.url,
            "request_id": request_id
        }))
        .send()
        .await
        .map_err(|e| {
            println!("❌ AI Server connection error: {:?}", e);
            StatusCode::BAD_GATEWAY
        })?;

    if !ai_response.status().is_success() {
        println!("❌ AI Server returned error: {}", ai_response.status());
        // 응답 본문 로깅 (디버깅용)
        let error_body = ai_response.text().await.unwrap_or_default();
        println!("Error body: {}", error_body);
        return Err(StatusCode::BAD_GATEWAY);
    }

    // AI 서버 응답 포맷에 맞춰 디코딩 (Python: AnalyzeResponse)
    #[derive(Deserialize, Debug)]
    struct AiAnalyzeResponse {
        url: String,
        status: String,
        risk_score: i32,
        // category, reasons 등 추가 필드는 필요시 사용하거나 일단 무시
        reasons: Option<Vec<String>>,
    }

    let ai_data: AiAnalyzeResponse = ai_response.json().await.map_err(|e| {
        println!("❌ Failed to parse AI response: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;

    println!("🤖 AI Analysis complete: {:?}", ai_data);

    // AI 상태 문자열을 Enum으로 변환
    let status_enum = match ai_data.status.as_str() {
        "SAFE" => UrlStatus::SAFE,
        "WARNING" => UrlStatus::WARNING,
        "BLOCK" => UrlStatus::BLOCK,
        _ => UrlStatus::BLOCK, // 알 수 없는 상태는 안전하게 차단 처리
    };

    // 설명 생성 (reasons 리스트를 문자열로 합침)
    let description = if let Some(reasons) = ai_data.reasons {
        if reasons.is_empty() {
            None
        } else {
            Some(reasons.join(", "))
        }
    } else {
        None
    };

    // AI 분석 결과를 DB에 저장
    let result = upsert_url_reputation(
        &db,
        ai_data.url,
        description,
        ai_data.risk_score,
        status_enum,
    )
    .await
    .map_err(|e| {
        println!("❌ Database save error: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;

    Ok(Json(UrlReputationResponse {
        url: result.url,
        description: result.description,
        score: result.score,
        status: result.status,
    }))
}

/// URL 평판 정보 등록/업데이트
/// 
/// AI Agent가 수집한 URL 정보를 DB에 저장합니다.
/// 이미 존재하는 URL이면 업데이트하고, 없으면 새로 생성합니다.
#[vespera::route(post, path = "", tags = ["url-reputations"])]
pub async fn create_url_reputation(
    State(db): State<DatabaseConnection>,
    Json(payload): Json<CreateUrlReputation>,
) -> Result<Json<UrlReputationResponse>, StatusCode> {
    let result = upsert_url_reputation(
        &db,
        payload.url,
        payload.description,
        payload.score,
        payload.status,
    )
    .await
    .map_err(|e| {
        println!("❌ Database error: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;
    
    Ok(Json(UrlReputationResponse {
        url: result.url,
        description: result.description,
        score: result.score,
        status: result.status,
    }))
}

/// URL 평판 정보를 DB에 추가하거나 업데이트 (Upsert)
async fn upsert_url_reputation(
    db: &DatabaseConnection,
    url: String,
    description: Option<String>,
    score: i32,
    status: UrlStatus,
) -> Result<url_reputations_vespertide::Model, sea_orm::DbErr> {
    use url_reputations_vespertide::ActiveModel;
    
    let model = ActiveModel {
        url: Set(url),
        description: Set(description),
        score: Set(score),
        status: Set(status),
    };
    
    UrlReputations::insert(model)
        .on_conflict(
            sea_orm::sea_query::OnConflict::column(url_reputations_vespertide::Column::Url)
                .update_columns([
                    url_reputations_vespertide::Column::Description,
                    url_reputations_vespertide::Column::Score,
                    url_reputations_vespertide::Column::Status,
                ])
                .to_owned(),
        )
        .exec_with_returning(db)
        .await
}
