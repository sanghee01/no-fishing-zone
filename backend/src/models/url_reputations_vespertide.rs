use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[sea_orm::model]
#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "url_reputations")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub url: String,
    pub description: Option<String>,
    #[sea_orm(indexed)]
    pub score: i32,
    #[sea_orm(default_value = false)]
    pub is_black: bool,
}


// Index definitions (SeaORM uses Statement builders externally)
// (unnamed) on [score]
impl ActiveModelBehavior for ActiveModel {}
