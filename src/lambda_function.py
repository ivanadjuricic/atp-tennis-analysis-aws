import json
import pandas as pd
import boto3
from datetime import datetime
import os
import tempfile
import glob

def lambda_handler(event, context):
    """
    AWS Lambda function - ATP Tennis Analysis
    
    Steps:
    Implement dataset from Kaggle
    Data analysis - Top 50 tennis players
    Upload on S3
    Automation process through EventBridge
    """
    
    try:
        print("🚀 Lambda function started!")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # ==================================================
        # STEP 1: Kaggle autentification and download
        # ==================================================
        
        kaggle_username = os.environ.get('KAGGLE_USERNAME')
        kaggle_key = os.environ.get('KAGGLE_KEY')
        
        if not kaggle_username or not kaggle_key:
            raise Exception("❌ ERROR: Kaggle credentials aren't set in Environment Variables!")
        
        # CRITICAL: Set Kaggle config folder on /tmp (the only writable place in Lambda)
        kaggle_dir = '/tmp/.kaggle'
        os.makedirs(kaggle_dir, exist_ok=True)
        
        print(f"📁 Kaggle config folder: {kaggle_dir}")
        
        # Create kaggle.json file programatic in /tmp
        kaggle_json_path = os.path.join(kaggle_dir, 'kaggle.json')
        kaggle_config = {
            "username": kaggle_username,
            "key": kaggle_key
        }
        
        with open(kaggle_json_path, 'w') as f:
            json.dump(kaggle_config, f)
        
        # Set environment variable for Kaggle to use /tmp
        os.environ['KAGGLE_CONFIG_DIR'] = kaggle_dir
        
        print("✅ Kaggle credentials imported")
        
        # Now we can securely import Kaggle API
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        api.authenticate()
        
        print("✅ Kaggle API autentificated")
        
        # Dataset identifier
        dataset_name = os.environ.get('KAGGLE_DATASET', 'dissfya/atp-tennis-2000-2023daily-pull')
        
        print(f"📥 Taking over the dataset: {dataset_name}")
        
        # Create temporary folder for download (also in /tmp)
        temp_dir = tempfile.mkdtemp(dir='/tmp')
        print(f"📂 Temp folder: {temp_dir}")
        
        # Taking over the dataset
        api.dataset_download_files(dataset_name, path=temp_dir, unzip=True)
        
        print(f"✅ Dataset downloaded!")
        
        # ==================================================
        # STEP 2: Loading CSV file
        # ==================================================
        
        # Find all CSV files
        csv_files = glob.glob(f"{temp_dir}/*.csv")
        
        if not csv_files:
            raise Exception("❌ ERROR: CSV files not found in dataset!")
        
        print(f"📂 Found {len(csv_files)} files")
        for f in csv_files:
            print(f"   - {os.path.basename(f)}")
        
        # Load main file (atp_tennis.csv or joined file)
        main_file = None
        for f in csv_files:
            filename = os.path.basename(f).lower()
            if 'atp_tennis' in filename or 'all' in filename or 'combined' in filename:
                main_file = f
                break
        
        if not main_file:
            # Ako nema glavnog, uzmi prvi
            main_file = csv_files[0]
        
        print(f"📖 Loading: {os.path.basename(main_file)}")
        
        # Učitaj podatke
        df = pd.read_csv(main_file, low_memory=False)
        
        print(f"✅ Loaded {len(df)} matches")
        print(f"📊 Columns: {list(df.columns)[:10]}...")
        
        # ==================================================
        # STEP 3: Data analysis - Top 50 players
        # ==================================================
        
        print("🔍 Starting data analysis...")
        
        # Check if required columns exist (customized with actual names)
        required_cols = ['Winner', 'Series', 'Date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise Exception(f"❌ ERROR: Columns missing: {missing_cols}")
        
        # Očisti podatke
        df_clean = df.dropna(subset=['Winner', 'Date']).copy()
        
        print(f"✅ After cleaning: {len(df_clean)} matches")
        
        # Konvertuj datum u datetime format
        # Date format može biti različit - probaj više formata
        df_clean['date'] = pd.to_datetime(df_clean['Date'], errors='coerce')
        
        # Mapiranje Series nivoa na ATP kategorije
        # Series može biti: Grand Slam, Masters 1000, ATP 500, ATP 250, itd.
        def categorize_series(series):
            if pd.isna(series):
                return 'Other'
            series_lower = str(series).lower()
            if 'grand slam' in series_lower or 'gs' in series_lower:
                return 'Grand Slam'
            elif 'masters 1000' in series_lower or 'atp1000' in series_lower or 'masters' in series_lower:
                return 'ATP 1000'
            elif 'atp 500' in series_lower or 'atp500' in series_lower:
                return 'ATP 500'
            elif 'atp 250' in series_lower or 'atp250' in series_lower:
                return 'ATP 250'
            else:
                return 'Other'
        
        df_clean['category'] = df_clean['Series'].apply(categorize_series)
        
        # Rezultati za svakog igrača
        results = []
        
        # Grupisanje po igračima
        print("⚙️ calculating the stats for each player...")
        
        for player in df_clean['Winner'].unique():
            if pd.isna(player) or player == '':
                continue
            
            # Sve pobede ovog igrača
            player_wins = df_clean[df_clean['Winner'] == player]
            
            # Ukupan broj pobeda
            total_wins = len(player_wins)
            
            # Pobede na Grand Slam turnirima
            grand_slam_wins = len(player_wins[player_wins['category'] == 'Grand Slam'])
            
            # Pobede na ATP 1000 turnirima
            atp1000_wins = len(player_wins[player_wins['category'] == 'ATP 1000'])
            
            # Pobede na ATP 500 turnirima
            atp500_wins = len(player_wins[player_wins['category'] == 'ATP 500'])
            
            # Datumi prve i poslednje pobede
            dates = player_wins['date'].dropna()
            
            if len(dates) > 0:
                first_win = dates.min().strftime('%Y-%m-%d')
                last_win = dates.max().strftime('%Y-%m-%d')
            else:
                first_win = 'N/A'
                last_win = 'N/A'
            
            # Dodaj u rezultate
            results.append({
                'player_name': player,
                'total_wins': total_wins,
                'grand_slam_wins': grand_slam_wins,
                'atp1000_wins': atp1000_wins,
                'atp500_wins': atp500_wins,
                'first_win': first_win,
                'last_win': last_win
            })
        
        # Kreiraj DataFrame sa rezultatima
        results_df = pd.DataFrame(results)
        
        print(f"✅ Analyzed {len(results_df)} players")
        
        # Sortiraj po ukupnom broju pobeda (descending) i uzmi top 50
        results_df = results_df.sort_values('total_wins', ascending=False).head(50).reset_index(drop=True)
        
        print(f"🏆 Top 3 players:")
        for i in range(min(3, len(results_df))):
            player = results_df.iloc[i]
            print(f"   {i+1}. {player['player_name']} - {player['total_wins']} wins")
        
        # ==================================================
        # STEP 4: Creation of CSV file
        # ==================================================
        
        # Temporary date for file name
        today = datetime.now()
        csv_filename = f"atp-top-50-{today.strftime('%d-%m-%Y')}.csv"
        
        # Save in temp folder
        temp_csv_path = os.path.join(temp_dir, csv_filename)
        results_df.to_csv(temp_csv_path, index=False, encoding='utf-8')
        
        print(f"✅ CSV created: {csv_filename}")
        
        # ==================================================
        # STEP 5: Upload on S3
        # ==================================================
        
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        
        if not bucket_name:
            raise Exception("❌ ERROR: S3_BUCKET_NAME is not set in Environment Variables!")
        
        print(f"☁️ Upload on S3 bucket: {bucket_name}")
        
        # S3 klijent
        s3_client = boto3.client('s3')
        
        # S3 key (putanja u bucketu)
        s3_key = f"results/{csv_filename}"
        
        # Upload fajla
        s3_client.upload_file(
            Filename=temp_csv_path,
            Bucket=bucket_name,
            Key=s3_key
        )
        
        print(f"✅ File uploaded: s3://{bucket_name}/{s3_key}")
        
        # ==================================================
        # STEP 6: Cleanup (erasing of temp files)
        # ==================================================
        
        import shutil
        shutil.rmtree(temp_dir)
        
        print("🧹 Temp files erased")
        
        # ==================================================
        # STEP 7: Success Response
        # ==================================================
        
        top_player = results_df.iloc[0]
        
        success_message = {
            'message': '✅ Analysis successfully finished!',
            'csv_file': csv_filename,
            's3_location': f"s3://{bucket_name}/{s3_key}",
            'timestamp': today.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'stats': {
                'total_players_analyzed': len(results),
                'top_50_selected': 50,
                'top_player': {
                    'name': top_player['player_name'],
                    'total_wins': int(top_player['total_wins']),
                    'grand_slam_wins': int(top_player['grand_slam_wins'])
                }
            }
        }
        
        print("\n" + "="*50)
        print("🎉 SUCCESSFULLY FINISHED!")
        print("="*50)
        print(json.dumps(success_message, indent=2))
        
        return {
            'statusCode': 200,
            'body': json.dumps(success_message)
        }
        
    except Exception as e:
        # ==================================================
        # Error Handling
        # ==================================================
        
        print("\n" + "="*50)
        print("❌ ERROR!")
        print("="*50)
        print(f"Error: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            })
        }