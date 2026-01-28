use axum::{
    extract::{Query, State},
    http::StatusCode,
    Json,
};
use sea_orm::{ColumnTrait, DatabaseConnection, EntityTrait, QueryFilter, Set};
use serde::{Deserialize, Serialize};
use vespera::Schema;

use crate::models::url_reputations_vespertide::{self, Entity as UrlReputations};

/// URL 평판 정보 응답 스키마
#[derive(Serialize, Deserialize, Schema, Debug, Clone)]
pub struct UrlReputationResponse {
    /// 평가 대상 URL
    pub url: String,
    /// URL에 대한 설명
    pub description: Option<String>,
    /// 평판 점수 (0-100)
    pub score: i32,
    /// 블랙리스트 여부
    pub is_black: bool,
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
    /// 블랙리스트 여부
    pub is_black: bool,
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
    let result = UrlReputations::find()
        .filter(url_reputations_vespertide::Column::Url.eq(&query.url))
        .one(&db)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    match result {
        Some(model) => Ok(Json(UrlReputationResponse {
            url: model.url,
            description: model.description,
            score: model.score,
            is_black: model.is_black,
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
        is_black: Set(payload.is_black),
    };
    
    let result = UrlReputations::insert(model)
        .on_conflict(
            sea_orm::sea_query::OnConflict::column(url_reputations_vespertide::Column::Url)
                .update_columns([
                    url_reputations_vespertide::Column::Description,
                    url_reputations_vespertide::Column::Score,
                    url_reputations_vespertide::Column::IsBlack,
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
        is_black: result.is_black,
    }))
}
