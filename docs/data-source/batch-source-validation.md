
## Selected Batch Source: Heart Disease UCI (Kaggle)
- **Primary Dataset**: `kamilpytlak/personal-key-indicators-of-heart-disease`
- **URL**: https://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease
- **Authentication**: Kaggle account required for download
- **Data Format**: CSV (`heart_2020_cleaned.csv`)
- **Dataset Details**: Cleaned and preprocessed health survey data for heart disease prediction, including demographic, behavioral, and medical risk factors.
- **Volume**: ~320,000 rows, 18 columns
- **Update Frequency**: Static snapshot
- **Download Location**: `data/external/heart_2020_cleaned.csv`
- **Why Selected**: Public, well-documented, and suitable for health analytics and ML tasks. Easily accessible via kaggle API and integrates with the pipeline.


## Fallback Datasets (Tested)
*None required. The heart disease dataset is stable and public.*


## Data Pipeline Integration
- **Collection Script**: `scripts/ingestion/collect_batch_data.py`
- **Target Directory**: `data/external/heart_2020_cleaned.csv`
- **Processing**: Automated download and copy to project directory via kaggle API


## Testing Results
- [x] Primary dataset (`kamilpytlak/personal-key-indicators-of-heart-disease`) accessible
- [x] heart_2020_cleaned.csv successfully downloaded
- [x] Data copied to project directory
- [x] File structure validated
- [x] Kaggle API integration working
- [x] Automated download pipeline functional

---


**Sample Output (heart_2020_cleaned.csv):**
```csv
HeartDisease,BMI,Smoking,AlcoholDrinking,Stroke,PhysicalHealth,MentalHealth,DiffWalking,Sex,AgeCategory,Race,Diabetic,PhysicalActivity,GenHealth,SleepTime,Asthma,KidneyDisease,SkinCancer
No,16.6,No,No,No,3.0,30.0,No,Female,18-24,White,No,Yes,Very good,5.0,No,No,No
No,20.3,No,No,No,0.0,0.0,No,Male,55-59,White,No,Yes,Good,7.0,No,No,No
Yes,26.2,Yes,No,No,0.0,0.0,No,Female,65-69,White,No,Yes,Good,8.0,No,No,No
```

**Data Schema:**
- **Target**: HeartDisease (Yes/No)
- **Features**: BMI, Smoking, AlcoholDrinking, Stroke, PhysicalHealth, MentalHealth, DiffWalking, Sex, AgeCategory, Race, Diabetic, PhysicalActivity, GenHealth, SleepTime, Asthma, KidneyDisease, SkinCancer


**Download Process:**
```bash
# Automated via collect_batch_data.py
📥 Trying dataset: kamilpytlak/personal-key-indicators-of-heart-disease
Path to dataset files: <user_kaggle_cache>/kamilpytlak/personal-key-indicators-of-heart-disease
Files in download path:
  - heart_2020_cleaned.csv (file)
  ✅ Copied: heart_2020_cleaned.csv
✅ Successfully downloaded kamilpytlak/personal-key-indicators-of-heart-disease
```


**Summary:**
The Heart Disease UCI dataset (`kamilpytlak/personal-key-indicators-of-heart-disease`) is successfully integrated as the primary batch data source. The dataset provides cleaned health survey data for heart disease prediction, automatically downloaded via the Kaggle API and processed by the data pipeline. The pipeline is robust, with automated validation and integration steps.
