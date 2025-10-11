WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'raw_data') }}
),
renamed AS (
  SELECT
      HeartDisease::BOOLEAN           AS heart_disease,
      BMI::FLOAT             AS bmi,
      Smoking::BOOLEAN                AS smoking,
      Alcohol_Drinking::BOOLEAN        AS alcohol_drinking,
      Stroke::BOOLEAN                 AS stroke,
      Physical_Health::FLOAT  AS physical_health,
      Mental_Health::FLOAT    AS mental_health,
      Diff_Walking::BOOLEAN            AS diff_walking,
      Sex::STRING                    AS sex,
      Age_Category::STRING            AS age_category,
      Race::STRING                   AS race,
      Diabetic::STRING               AS diabetic,
      Physical_Activity::BOOLEAN       AS physical_activity,
      Gen_Health::STRING              AS gen_health,
      Sleep_Time::FLOAT       AS sleep_time,
      Asthma::BOOLEAN                 AS asthma,
      Kidney_Disease::BOOLEAN          AS kidney_disease,
      Skin_Cancer::BOOLEAN             AS skin_cancer,
      CURRENT_TIMESTAMP()    AS processed_at,
      'dbt_staging'          AS processing_source
  FROM source
)
SELECT * FROM renamed