/// Health Check 엔드포인트
/// 
/// Docker의 healthcheck에서 사용됩니다.
/// 서버가 정상적으로 실행 중인지 확인하는 간단한 엔드포인트입니다.
#[vespera::route(get, path = "", tags = ["system"])]
pub async fn health_check() -> &'static str {
    "OK"
}
