from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import json
import io
import os
from groq import Groq
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from fastapi.responses import Response
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This tells Render to accept requests from ANY website (including Vercel)
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, etc.
    allow_headers=["*"],
)


# Load variables from the .env file
load_dotenv()

# Securely fetch the key
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# 🚨 THE MEMORY BANK: This stores the uploaded file directly in RAM
APP_STATE = {}

class ChatRequest(BaseModel):
    prompt: str
    fact_sheet: str

class NarrativeRequest(BaseModel):
    roi: str
    top_seg: str
    bot_seg: str
    diagnostic_reason: str

@app.post("/api/upload")
async def analyze_data(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # 1. Clean data safely
        if 'Acquisition_Cost' in df.columns and df['Acquisition_Cost'].dtype == 'object':
            df['Acquisition_Cost'] = df['Acquisition_Cost'].replace(r'[$,]', '', regex=True).astype(float)

                # List of columns that should strictly be numbers
        numeric_columns = ['Impressions', 'ROI', 'Acquisition_Cost', 'Clicks', 'Engagement_Score']

        for col in numeric_columns:
            if col in df.columns:
                # Convert to string first to use string methods safely, then remove $, %, and commas
                df[col] = df[col].astype(str).str.replace(r'[$,%]', '', regex=True)
                # Convert back to numeric, turning empty/bad values into NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # 2. SAVE TO RAM (Instantly)
        APP_STATE["current_dataset"] = df
        
        # Calculate Core Numbers
        reach = df['Impressions'].sum() if 'Impressions' in df.columns else 0
        avg_roi = df['ROI'].mean() if 'ROI' in df.columns else 0.0
        avg_cac = df['Acquisition_Cost'].mean() if 'Acquisition_Cost' in df.columns else 0.0
        
        # DATA SYNTHESIS GENERATION
        top_channel = df.groupby('Channel_Used')['ROI'].mean().idxmax() if 'Channel_Used' in df.columns else "N/A"
        top_audience = df.groupby('Age_Group')['ROI'].mean().idxmax() if 'Age_Group' in df.columns else "N/A"
        lowest_cac_goal = df.groupby('Campaign_Goal')['Acquisition_Cost'].mean().idxmin() if 'Campaign_Goal' in df.columns and 'Acquisition_Cost' in df.columns else "N/A"
        
        synthesis_notes = f"""
        <ul style="margin: 0; padding-left: 20px; line-height: 1.8; color: #d1d5db; font-size: 15px;">
            <li><strong>Top Channel:</strong> Performance is anchored by <span style="color: #60a5fa;">{top_channel}</span>, yielding the highest average ROI.</li>
            <li><strong>Key Demographic:</strong> Tracking shows <span style="color: #60a5fa;">{top_audience}</span> as the highest-converting demographic segment.</li>
            <li><strong>Budget Optimization:</strong> Prioritize <span style="color: #60a5fa;">'{lowest_cac_goal}'</span> initiatives to maintain the lowest baseline acquisition thresholds.</li>
        </ul>
        """

        # DEEP DIVE PRE-COMPUTATION
        categories = ['Channel_Used', 'Campaign_Goal', 'Age_Group', 'Target_Gender', 'Location', 'Language', 'Customer_Segment']
        kpis = ['ROI', 'Acquisition_Cost', 'Conversion_Rate', 'Impressions', 'Clicks', 'Engagement_Score']
        
        deep_dive_data = {}
        for cat in categories:
            if cat in df.columns:
                deep_dive_data[cat] = {}
                for kpi in kpis:
                    if kpi in df.columns:
                        grouped = df.groupby(cat)[kpi].mean().reset_index()
                        deep_dive_data[cat][kpi] = {
                            "x": grouped[cat].tolist(),
                            "y": grouped[kpi].tolist()
                        }

       # THE ULTIMATE MEMORY BYPASS: 100% Data, Zero FastAPI Validation Overhead
        sunburst_columns = [
            'Age_Group', 'Target_Gender', 'Channel_Used', 'Campaign_Goal', 
            'Location', 'Language', 'Customer_Segment', 'Impressions', 
            'Clicks', 'ROI', 'Engagement_Score', 'Acquisition_Cost' 
        ]
        available_sun_cols = [c for c in sunburst_columns if c in df.columns]
        
        # 1. Use Pandas ultra-fast C-engine to convert directly to a JSON string (Uses almost zero RAM)
        sunburst_json_str = df[available_sun_cols].to_json(orient='records')
        
        # CONSOLIDATED AI KNOWLEDGE BASE
        def get_2way_avg(col1, col2, metric):
            if all(c in df.columns for c in [col1, col2, metric]):
                grouped = df.groupby([col1, col2])[metric].mean().reset_index()
                return {f"{row[col1]} - {row[col2]}": round(row[metric], 2) for _, row in grouped.iterrows()}
            return {}

        def get_2way_sum(col1, col2, metric):
            if all(c in df.columns for c in [col1, col2, metric]):
                grouped = df.groupby([col1, col2])[metric].sum().reset_index()
                return {f"{row[col1]} - {row[col2]}": int(row[metric]) for _, row in grouped.iterrows()}
            return {}

        ai_knowledge_base = {
            "Macro_Overview": {
                "Total_Impressions": int(reach), 
                "Total_Clicks": int(df['Clicks'].sum()) if 'Clicks' in df.columns else 0,
                "Avg_ROI": round(avg_roi, 2), 
                "Avg_CAC": round(avg_cac, 2)
            },
            "Core_Averages": {
                "ROI_by_Channel": df.groupby('Channel_Used')['ROI'].mean().round(2).to_dict() if 'Channel_Used' in df.columns else {},
                "ROI_by_Location": df.groupby('Location')['ROI'].mean().round(2).to_dict() if 'Location' in df.columns else {},
                "ROI_by_Target_Gender": df.groupby('Target_Gender')['ROI'].mean().round(2).to_dict() if 'Target_Gender' in df.columns else {},
                "ROI_by_Age_Group": df.groupby('Age_Group')['ROI'].mean().round(2).to_dict() if 'Age_Group' in df.columns else {}
            },
            "The_Money_Intersections": {
                "Total_Clicks_by_Channel_and_Gender": get_2way_sum('Channel_Used', 'Target_Gender', 'Clicks'),
                "Avg_ROI_by_Channel_and_Age": get_2way_avg('Channel_Used', 'Age_Group', 'ROI'),
                "Avg_CAC_by_Channel_and_Goal": get_2way_avg('Channel_Used', 'Campaign_Goal', 'Acquisition_Cost')
            }
        }

        # 2. Build the final JSON string manually to completely bypass FastAPI memory spikes
        kpis_json = json.dumps({
            "reach": f"{reach / 1_000_000:.1f}M" if reach > 0 else "0",
            "roi": round(avg_roi, 2),
            "cac": round(avg_cac, 2)
        })
        
        synthesis_json = json.dumps(synthesis_notes)
        fact_sheet_json = json.dumps(json.dumps(ai_knowledge_base)) 
        deep_dive_json = json.dumps(deep_dive_data)

        # Stitch it all together into one raw text payload
        final_json_str = f'{{"kpis": {kpis_json}, "synthesis": {synthesis_json}, "fact_sheet": {fact_sheet_json}, "deep_dive_data": {deep_dive_json}, "sunburst_raw_data": {sunburst_json_str}}}'

        # 3. Clean out RAM instantly
        gc.collect()

        # 4. Return raw response (FastAPI won't try to validate it, saving massive memory)
        return Response(content=final_json_str, media_type="application/json")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return Response(content=json.dumps({"error": str(e)}), media_type="application/json")

@app.post("/api/timeseries")
async def get_time_series(metric: str = "ROI", window: str = "daily_7", forecast_days: int = 30):
    try:
        # Read directly from RAM
        df = APP_STATE.get("current_dataset")
        if df is None:
            return {"error": "Please upload a dataset first."}
            
        if metric not in df.columns:
            return {"error": f"Metric {metric} not found in dataset."}

        if 'Date' not in df.columns:
            return {"error": "No 'Date' column found in dataset."}

        # Make a copy to avoid warnings
        df_ts = df.copy()
        
        # 1. ROBUST DATE PARSING & INDEXING
        # Removed the strict '%d-%m-%Y' format to allow Pandas to dynamically parse the true dates
        df_ts['Date'] = pd.to_datetime(df_ts['Date'], format='mixed', errors='coerce')
        df_ts = df_ts.dropna(subset=['Date']).sort_values('Date')
        df_ts.set_index('Date', inplace=True) 
        
        # 2. DETERMINE FREQUENCY, WINDOW, & SEASONALITY
        if window == 'weekly_30':
            resample_freq = 'W'    
            rolling_win = 30       
            seasonal_periods = 4   # 4 weeks in a month
        elif window == 'monthly_90':
            resample_freq = 'MS'   
            rolling_win = 90       
            seasonal_periods = 12  # 12 months in a year
        else: # default to daily_7
            resample_freq = 'D'    
            rolling_win = 7        
            seasonal_periods = 7   # 7 days in a week (captures weekend cyclic variance)

        # 3. AGGREGATE & SMOOTH
        agg_data = df_ts[metric].resample(resample_freq).mean().reset_index()
        
        # Interpolate missing gaps instead of filling with 0 (which breaks time series models)
        agg_data[metric] = agg_data[metric].interpolate(method='linear').fillna(method='bfill').fillna(0)
        
        # Apply dynamic rolling average
        agg_data['Moving_Avg'] = agg_data[metric].rolling(window=rolling_win, min_periods=1).mean()
        
        # 4. ADVANCED PREDICTIVE MATH (Holt-Winters)
        y_historical = agg_data['Moving_Avg'].values
        
        # Protect the model in case the dataset is too small to calculate seasonality
        if len(y_historical) >= seasonal_periods * 2:
            model = ExponentialSmoothing(
                y_historical, 
                trend='add', 
                seasonal='add', 
                seasonal_periods=seasonal_periods,
                initialization_method="estimated"
            )
            fit_model = model.fit()
            y_future = fit_model.forecast(forecast_days)
        else:
            # Fallback to a flat line if the user uploads a tiny dataset (e.g., 5 rows)
            y_future = np.full(forecast_days, y_historical[-1])
        
        # 5. DYNAMIC DATE GENERATION
        last_date = agg_data['Date'].iloc[-1]
        future_dates_idx = pd.date_range(start=last_date, periods=forecast_days + 1, freq=resample_freq)[1:]
        future_dates = [d.strftime('%Y-%m-%d') for d in future_dates_idx]

        return {
            "historical_dates": agg_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
            "historical_raw": agg_data[metric].round(2).tolist(),
            "historical_smooth": agg_data['Moving_Avg'].round(2).tolist(),
            "future_dates": future_dates,
            "future_prediction": np.round(y_future, 2).tolist()
        }
    except Exception as e:
        print(f"Time Series Error: {str(e)}")
        return {"error": "Failed to calculate Time Series. Please check terminal."}

@app.post("/api/chat")
async def chat_strategist(request: ChatRequest):
    try:
        client = Groq()
        
        SYSTEM_PROMPT = """You are an elite corporate marketing AI Strategist. 

        RULES:
        1. Be Precise do not exceed more than 2-3 lines for the answer.
        2. Answer the user's question directly using ONLY the data in the JSON context matrix.
        3. Keep your final answer punchy, professional, and actionable.
        4. If a calculation is not possible with the provided data, redirect the user to the Sunburst tool.
        
        Example format for your response:
        ---
      
        
        [Your concise summary here]
        ---
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + [
                {
                    "role": "user", 
                    "content": f"Context Matrix: {request.fact_sheet}\n\nUser Prompt: {request.prompt}"
                }
            ]
        )
        
        return {"reply": response.choices[0].message.content}
        
    except Exception as e:
        return {"reply": f"API Connection Fault: {str(e)}"}

class NarrativeResponse(BaseModel):
    executive_summary: str
    health_assessment: str
    scale_rationale: str
    halt_rationale: str
    performance_drivers: str
    underperforming_segments: str
    portfolio_risks: str
    strategic_outlook: str
    final_conclusion: str

class NarrativeRequest(BaseModel):
    roi: str
    top_seg: str
    bot_seg: str
    diagnostic_reason: str
    total_spend: str
    blended_cac: str
    ltv_cac_ratio: str
    top_roi: str
    top_cac: str
    bot_roi: str
    bot_cac: str
    reallocation_amount: str
    
    # NEW DETERMINISTIC FIELDS
    opportunity_cost: str
    expected_revenue_lift: str
    concentration_risk_pct: str
    forecast_stats: dict | None = None

@app.post("/api/report/narrative")
async def generate_narrative(req: NarrativeRequest):
    
    # 1. Compile the quantitative data into a strict payload
    data_payload = f"""
    PORTFOLIO SNAPSHOT:
    Total Spend: {req.total_spend} | Blended CAC: {req.blended_cac} | Aggregate LTV:CAC: {req.ltv_cac_ratio} | Blended ROI: {req.roi}
    
    TOP PERFORMING SEGMENT: {req.top_seg}
    Top ROI: {req.top_roi} | Top CAC: {req.top_cac}
    
    CRITICAL UNDERPERFORMER: {req.bot_seg}
    Bot ROI: {req.bot_roi} | Bot CAC: {req.bot_cac} | Diagnosis: {req.diagnostic_reason}
    
    DETERMINISTIC PROJECTIONS & RISK (USE THESE EXACT FIGURES):
    Proposed Reallocation: {req.reallocation_amount}
    Opportunity Cost of Inaction: {req.opportunity_cost}
    Expected Revenue Lift (Adjusted for Saturation): {req.expected_revenue_lift}
    Post-Reallocation Concentration Risk: {req.concentration_risk_pct}
    
    FORECAST DATA: {json.dumps(req.forecast_stats) if req.forecast_stats else "Forecast unavailable"}
    """

    # 2. The Upgraded System Prompt with Anti-Hallucination Guardrails
    system_prompt = """
    You are a Senior Partner at a top-tier management consulting firm (McKinsey, Bain, BCG). 
    Your objective is to synthesize marketing campaign data into a highly actionable, evidence-based executive briefing.

    STRICT CONSULTING STYLE RULES (FAILURE IS NOT AN OPTION):
    1. DATA GROUNDING DIRECTIVE (CRITICAL): You are strictly forbidden from calculating, estimating, predicting, or generating your own dollar amounts, percentages, lifts, or opportunity costs. You MUST exclusively use the quantitative estimates provided in the 'DETERMINISTIC PROJECTIONS & RISK' section of the data payload. If you need a number for an Action Plan priority and it is not provided, state the outcome qualitatively.
    2. TONE & VOCABULARY: Use precise, evidence-backed executive language. NEVER use generic corporate fluff (e.g., "synergy," "optimize") or AI filler phrases ("It is important to note," "Overall," "Strong performance"). 
    3. COHESIVE NARRATIVE: Do not write disconnected observations. Every paragraph must flow into the next, establishing a clear business narrative of cause, effect, and resolution.
    4. NO REDUNDANCY: The Executive Summary and Portfolio Conclusions must serve different purposes. Do not repeat facts between them.
    5. THEMATIC SYNTHESIS: Group segment insights into strategic themes. Explain recurring patterns across channels, goals, and demographics.

    REQUIRED SECTION GUIDELINES:
    - executive_summary (Max 3 paragraphs): Write ONE cohesive business narrative. Detail the macro performance, the primary friction point causing capital bleed, and the immediate strategic imperative. No isolated bullet points.
    - health_assessment: Provide a narrative assessment of overall portfolio quality, systemic risk, and capital efficiency.
    - cross_segment_patterns: Synthesize the data. Identify recurring structural patterns across Channel, Goal, and Demographics. 
    - scale_rationale: Provide business justification for moving capital to the top segment. You MUST cite the 'Expected Revenue Lift' from the payload.
    - halt_rationale: Explain the systemic failure of the bottom segment. You MUST cite the 'Opportunity Cost of Inaction' from the payload.
    - portfolio_risks: List systemic business risks, explicitly citing the 'Post-Reallocation Concentration Risk' percentage provided in the payload.
    - strategic_outlook (Forecast): Discuss statistical confidence, variance, and execution considerations based on the forecast data. 
    -portfolio_risks: "Exactly 3 HTML bullet points (<li><strong>Risk Title:</strong> Explanation tied to metrics</li>) specifying: "
                     "1. Concentration Risk: State the exact % of total spend now sitting in the Top Segment. "
                     "2. Attribution Risk: Mention the baseline CAC shift if upper-funnel organic halo drops. "
                     "3. Saturation Risk: Define the frequency cap or ROI decay threshold (e.g., if Top ROI drops below 3.0, pause scaling)."- strategic_outlook (Forecast): Discuss statistical confidence, variance/uncertainty, and execution considerations based on the forecast data. State the quantitative risk of deviation from the mean.    - action_plan: Format STRICTLY as:
      Priority 1 (High): [Systemic Business Issue] -> [Concrete Action] -> [Expected Impact (Use provided data or Qualitative)]
      Priority 2 (Medium): [Systemic Business Issue] -> [Concrete Action] -> [Expected Impact (Use provided data or Qualitative)]
      Priority 3 (Low): [Systemic Business Issue] -> [Concrete Action] -> [Expected Impact (Use provided data or Qualitative)]

    OUTPUT FORMAT:
    Return a raw, valid JSON object exactly matching the keys below. Use basic HTML formatting (<p>, <strong>, <br>) inside the strings for readability.

    {
        "executive_summary": "...",
        "health_assessment": "...",
        "cross_segment_patterns": "...",
        "scale_rationale": "...",
        "halt_rationale": "...",
        "portfolio_risks": "<li>...</li>",
        "strategic_outlook": "...",
        "portfolio_conclusions": "...",
        "action_plan": "..."
    }
    """

    # 3. Execute LLM Call
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_payload}
            ],
            temperature=0.1, # Extremely low temperature to enforce strict adherence to provided numbers
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)
        
    except Exception as e:
        return {"error": str(e)}