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
/// DB에 해당 URL이 없으면 404를 반환합니다.
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
    
    if let Some(ref model) = result {
        println!("✅ Found: {}", model.url);
    } else {
        println!("⚠️ Not found in DB: {}", query.url);
    }
    
    match result {
        Some(model) => Ok(Json(UrlReputationResponse {
            url: model.url,
            description: model.description,
            score: model.score,
            status: model.status,
        })),
        None => Err(StatusCode::NOT_FOUND),
    }
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
    use url_reputations_vespertide::ActiveModel;
    
    let model = ActiveModel {
        url: Set(payload.url.clone()),
        description: Set(payload.description.clone()),
        score: Set(payload.score),
        status: Set(payload.status),
    };
    
    let result = UrlReputations::insert(model)
        .on_conflict(
            sea_orm::sea_query::OnConflict::column(url_reputations_vespertide::Column::Url)
                .update_columns([
                    url_reputations_vespertide::Column::Description,
                    url_reputations_vespertide::Column::Score,
                    url_reputations_vespertide::Column::Status,
                ])
                .to_owned(),
        )
        .exec_with_returning(&db)
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
