use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::sse::{Event, Sse},
    Json,
};
use futures::stream;
use sea_orm::{ColumnTrait, DatabaseConnection, EntityTrait, QueryFilter, Set};
use serde::{Deserialize, Serialize};
use std::convert::Infallible;
use std::time::Duration;
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
/// DB에 저장된 URL 평판 정보를 조회합니다.
/// DB에 해당 URL이 없으면 404를 반환합니다.
/// 새로운 URL 분석은 /analyze-stream SSE 엔드포인트를 사용하세요.
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

    // DB에 없으면 404 반환 (분석은 analyze_stream에서 수행)
    println!("⚠️ Not found in DB: {}. Use /analyze-stream for new URLs.", query.url);
    Err(StatusCode::NOT_FOUND)
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

/// SSE 진행 상태 이벤트
#[derive(Serialize, Clone)]
struct ProgressEvent {
    step: u8,
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<UrlReputationResponse>,
    done: bool,
}

/// URL 분석 스트림 (SSE)
/// 
/// 실시간으로 분석 진행 상태를 전송합니다.
/// - step 1: 접속 기록 분석 (DB 조회)
/// - step 2: 불법 데이터 식별 (AI 분석)
/// - step 3: 증거 자료 수집 (결과 저장)
pub async fn analyze_stream(
    State(db): State<DatabaseConnection>,
    Query(query): Query<GetUrlQuery>,
) -> impl axum::response::IntoResponse {
    let url = query.url.clone();
    
    let stream = stream::unfold(
        AnalyzeState::Start { db, url },
        |state| async move {
            match state {
                AnalyzeState::Start { db, url } => {
                    // Cloudflare 버퍼링 방지를 위한 초기 패딩 (110KB - Quick Tunnel 강제 Flush용)
                    // Quick Tunnel은 대시보드 설정이 불가능하므로 무식하게 버퍼를 채워야 함
                    let padding = " ".repeat(1024 * 110);
                    Some((
                        Ok::<_, Infallible>(Event::default().comment(padding)),
                        AnalyzeState::Step1 { db, url },
                    ))
                }
                AnalyzeState::Step1 { db, url } => {
                    // Step 1: DB 조회 시작
                    let event = ProgressEvent {
                        step: 1,
                        status: "in_progress".to_string(),
                        result: None,
                        done: false,
                    };
                    // 플러시 보장을 위한 딜레이
                    tokio::time::sleep(Duration::from_millis(50)).await;
                    Some((
                        Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                        AnalyzeState::CheckDb { db, url },
                    ))
                }
                AnalyzeState::CheckDb { db, url } => {
                    // DB에서 조회
                    let result = UrlReputations::find()
                        .filter(url_reputations_vespertide::Column::Url.eq(&url))
                        .one(&db)
                        .await
                        .ok()
                        .flatten();
                    
                    if let Some(model) = result {
                        // DB에 있음 - 모든 단계 완료
                        let response = UrlReputationResponse {
                            url: model.url,
                            description: model.description,
                            score: model.score,
                            status: model.status,
                        };
                        let event = ProgressEvent {
                            step: 3,
                            status: "completed".to_string(),
                            result: Some(response),
                            done: true,
                        };
                        Some((
                            Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                            AnalyzeState::Done,
                        ))
                    } else {
                        // DB에 없음 - Step 1 완료, Step 2 시작
                        let event = ProgressEvent {
                            step: 1,
                            status: "completed".to_string(),
                            result: None,
                            done: false,
                        };
                        // 플러시 보장을 위한 딜레이
                        tokio::time::sleep(Duration::from_millis(50)).await;
                        Some((
                            Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                            AnalyzeState::StartAi { db, url },
                        ))
                    }
                }
                AnalyzeState::StartAi { db, url } => {
                    // Step 2: AI 분석 시작
                    let event = ProgressEvent {
                        step: 2,
                        status: "in_progress".to_string(),
                        result: None,
                        done: false,
                    };
                    // 플러시 보장을 위한 딜레이
                    tokio::time::sleep(Duration::from_millis(50)).await;
                    Some((
                        Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                        AnalyzeState::CallAi { db, url },
                    ))
                }
                AnalyzeState::CallAi { db, url } => {
                    // AI 서버 호출
                    let client = reqwest::Client::new();
                    let ai_server_url = std::env::var("AI_SERVER_URL")
                        .unwrap_or_else(|_| "http://ai:8001".to_string());
                    let request_id = uuid::Uuid::new_v4().to_string();
                    
                    let ai_result = client
                        .post(format!("{}/analyze", ai_server_url))
                        .json(&serde_json::json!({
                            "url": url,
                            "request_id": request_id
                        }))
                        .send()
                        .await;
                    
                    match ai_result {
                        Ok(response) if response.status().is_success() => {
                            #[derive(Deserialize)]
                            struct AiResponse {
                                url: String,
                                status: String,
                                risk_score: i32,
                                reasons: Option<Vec<String>>,
                            }
                            
                            if let Ok(ai_data) = response.json::<AiResponse>().await {
                                let status_enum = match ai_data.status.as_str() {
                                    "SAFE" => UrlStatus::SAFE,
                                    "WARNING" => UrlStatus::WARNING,
                                    _ => UrlStatus::BLOCK,
                                };
                                let description = ai_data.reasons
                                    .filter(|r| !r.is_empty())
                                    .map(|r| r.join(", "));
                                
                                // Step 2 완료
                                let event = ProgressEvent {
                                    step: 2,
                                    status: "completed".to_string(),
                                    result: None,
                                    done: false,
                                };
                                // 플러시 보장을 위한 딜레이
                                tokio::time::sleep(Duration::from_millis(50)).await;
                                Some((
                                    Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                                    AnalyzeState::SaveResult {
                                        db,
                                        url: ai_data.url,
                                        description,
                                        score: ai_data.risk_score,
                                        status: status_enum,
                                    },
                                ))
                            } else {
                                // 파싱 실패
                                Some((
                                    Ok::<_, Infallible>(Event::default().data("error: AI response parse failed")),
                                    AnalyzeState::Done,
                                ))
                            }
                        }
                        _ => {
                            // AI 호출 실패
                            Some((
                                Ok::<_, Infallible>(Event::default().data("error: AI server error")),
                                AnalyzeState::Done,
                            ))
                        }
                    }
                }
                AnalyzeState::SaveResult { db, url, description, score, status } => {
                    // Step 3: 결과 저장 시작
                    let event = ProgressEvent {
                        step: 3,
                        status: "in_progress".to_string(),
                        result: None,
                        done: false,
                    };
                    // 플러시 보장을 위한 딜레이
                    tokio::time::sleep(Duration::from_millis(50)).await;
                    Some((
                        Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                        AnalyzeState::DoSave { db, url, description, score, status },
                    ))
                }
                AnalyzeState::DoSave { db, url, description, score, status } => {
                    // DB에 저장
                    let save_result = upsert_url_reputation(&db, url, description, score, status.clone()).await;
                    
                    match save_result {
                        Ok(model) => {
                            let response = UrlReputationResponse {
                                url: model.url,
                                description: model.description,
                                score: model.score,
                                status: model.status,
                            };
                            let event = ProgressEvent {
                                step: 3,
                                status: "completed".to_string(),
                                result: Some(response),
                                done: true,
                            };
                            Some((
                                Ok::<_, Infallible>(Event::default().json_data(&event).unwrap()),
                                AnalyzeState::Done,
                            ))
                        }
                        Err(_) => {
                            Some((
                                Ok::<_, Infallible>(Event::default().data("error: DB save failed")),
                                AnalyzeState::Done,
                            ))
                        }
                    }
                }
                AnalyzeState::Done => None,
            }
        },
    );
    
    let sse = Sse::new(stream).keep_alive(
        axum::response::sse::KeepAlive::new()
            .interval(Duration::from_secs(1))
            .text("keep-alive-ping"),
    );
    
    // 중요: 버퍼링 방지 헤더 추가
    use axum::response::IntoResponse;
    use axum::http::{header, HeaderName, HeaderValue};
    
    let mut response = sse.into_response();
    let headers = response.headers_mut();
    
    headers.insert(
        header::CACHE_CONTROL,
        HeaderValue::from_static("no-cache, no-transform"),
    );
    headers.insert(
        header::CONNECTION,
        HeaderValue::from_static("keep-alive"),
    );
    headers.insert(
        header::CONTENT_ENCODING,
        HeaderValue::from_static("identity"),
    );
    headers.insert(
        HeaderName::from_static("x-accel-buffering"),
        HeaderValue::from_static("no"),
    );
    
    response
}

/// 분석 상태 머신
enum AnalyzeState {
    Start { db: DatabaseConnection, url: String },
    Step1 { db: DatabaseConnection, url: String },
    CheckDb { db: DatabaseConnection, url: String },
    StartAi { db: DatabaseConnection, url: String },
    CallAi { db: DatabaseConnection, url: String },
    SaveResult {
        db: DatabaseConnection,
        url: String,
        description: Option<String>,
        score: i32,
        status: UrlStatus,
    },
    DoSave {
        db: DatabaseConnection,
        url: String,
        description: Option<String>,
        score: i32,
        status: UrlStatus,
    },
    Done,
}
