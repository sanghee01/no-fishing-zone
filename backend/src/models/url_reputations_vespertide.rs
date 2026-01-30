use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, EnumIter, DeriveActiveEnum, Serialize, Deserialize, vespera::Schema)]
#[sea_orm(rs_type = "String", db_type = "Enum", enum_name = "url_reputations_url_status")]
pub enum UrlStatus {
    #[sea_orm(string_value = "SAFE")]
    SAFE,
    #[sea_orm(string_value = "WARNING")]
    WARNING,
    #[sea_orm(string_value = "BLOCK")]
    BLOCK,
}

#[sea_orm::model]
#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "url_reputations")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub url: String,
    pub description: Option<String>,
    #[sea_orm(indexed)]
    pub score: i32,
    #[sea_orm(default_value = "SAFE")]
    pub status: UrlStatus,
}


// Index definitions (SeaORM uses Statement builders externally)
// (unnamed) on [score]
impl ActiveModelBehavior for ActiveModel {}
