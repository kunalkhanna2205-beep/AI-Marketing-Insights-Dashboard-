# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 12:37:19 2026

@author: kunal
"""

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing AI Strategist - Enterprise Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%); }
        .glass-effect { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(51, 65, 85, 0.3); }
        .gradient-btn { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); transition: all 0.3s ease; }
        .gradient-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 24px rgba(59, 130, 246, 0.3); }
        .metric-card { background: rgba(30, 41, 59, 0.8); border-left: 4px solid #3b82f6; }
        .transition-smooth { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .spinner { border: 3px solid rgba(59, 130, 246, 0.2); border-top: 3px solid #3b82f6; border-radius: 50%; width: 48px; height: 48px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .tab-active { border-b-2 border-blue-500; color: #f1f5f9; }
        .tab-inactive { border-b-2 border-transparent; color: #94a3b8; }
        .chart-container { background: rgba(15, 23, 42, 0.5); border-radius: 12px; border: 1px solid rgba(51, 65, 85, 0.3); padding: 20px; }
    </style>
</head>
<body class="text-slate-100" x-data="dashboardApp()">

    <!-- LOADING OVERLAY -->
    <div id="loading-overlay" class="fixed inset-0 bg-black/60 backdrop-blur-md flex flex-col items-center justify-center z-50 hidden">
        <div class="spinner"></div>
        <h3 class="text-white text-lg font-semibold mt-6">Analyzing Data & Generating Insights</h3>
        <p class="text-slate-400 text-sm mt-2">This usually takes a few seconds</p>
    </div>

    <div class="flex h-screen overflow-hidden">

        <!-- SIDEBAR NAVIGATION -->
        <aside class="w-64 glass-effect border-r border-slate-700 flex flex-col overflow-y-auto">
            <div class="p-8 border-b border-slate-700">
                <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">📊 AI Strategist</h1>
                <p class="text-xs text-slate-400 mt-2">Enterprise Analytics Platform</p>
            </div>

            <nav class="flex-1 p-6 space-y-2">
                <button @click="activeTab = 'executive'" :class="activeTab === 'executive' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-slate-200 border-l-2 border-transparent'" class="w-full text-left px-4 py-3 rounded-lg transition-smooth font-medium text-sm">📈 Executive Strategy</button>
                <button @click="activeTab = 'deep-dive'" :class="activeTab === 'deep-dive' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-slate-200 border-l-2 border-transparent'" class="w-full text-left px-4 py-3 rounded-lg transition-smooth font-medium text-sm">📊 Deep Dive Analysis</button>
                <button @click="activeTab = 'audience'" :class="activeTab === 'audience' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-slate-200 border-l-2 border-transparent'" class="w-full text-left px-4 py-3 rounded-lg transition-smooth font-medium text-sm">🎯 Audience Explorer</button>
                <button @click="activeTab = 'forecast'" :class="activeTab === 'forecast' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-slate-200 border-l-2 border-transparent'" class="w-full text-left px-4 py-3 rounded-lg transition-smooth font-medium text-sm">🔮 Forecasting</button>
                <button @click="activeTab = 'ai-chat'" :class="activeTab === 'ai-chat' ? 'bg-blue-600/20 text-blue-300 border-l-2 border-blue-500' : 'text-slate-400 hover:text-slate-200 border-l-2 border-transparent'" class="w-full text-left px-4 py-3 rounded-lg transition-smooth font-medium text-sm">🤖 AI Assistant</button>
            </nav>

            <div class="p-6 border-t border-slate-700 text-xs text-slate-500">
                <p>Ready to optimize your campaigns with AI-powered insights.</p>
            </div>
        </aside>

        <!-- MAIN CONTENT -->
        <main class="flex-1 overflow-y-auto bg-gradient-to-br from-slate-900/50 to-slate-800/30">
            
            <!-- HEADER: FILE UPLOAD SECTION -->
            <div class="sticky top-0 z-40 bg-slate-900/80 backdrop-blur border-b border-slate-700 px-8 py-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="text-xl font-bold text-slate-100">Campaign Analytics Dashboard</h2>
                        <p id="file-status" class="text-sm text-slate-400 mt-1">No dataset loaded</p>
                    </div>
                    <label for="csv-upload" class="gradient-btn text-white font-semibold py-3 px-6 rounded-lg cursor-pointer hover:shadow-lg flex items-center gap-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path></svg>
                        Upload Dataset
                    </label>
                    <input type="file" id="csv-upload" accept=".csv" class="hidden">
                </div>
            </div>

            <!-- CONTENT TABS -->
            <div class="p-8">

                <!-- EXECUTIVE STRATEGY TAB -->
                <div x-show="activeTab === 'executive'" class="transition-smooth">
                    <!-- KPI METRICS GRID -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div class="metric-card rounded-xl p-6 shadow-lg hover:shadow-xl transition-smooth">
                            <div class="flex items-center justify-between mb-4">
                                <span class="text-xs font-semibold text-slate-400 uppercase tracking-widest">Total Impressions</span>
                                <span class="text-2xl">📈</span>
                            </div>
                            <h3 id="reach-val" class="text-3xl font-bold text-blue-400">-</h3>
                            <p class="text-xs text-slate-500 mt-3">Campaign Reach</p>
                        </div>

                        <div class="metric-card rounded-xl p-6 shadow-lg hover:shadow-xl transition-smooth">
                            <div class="flex items-center justify-between mb-4">
                                <span class="text-xs font-semibold text-slate-400 uppercase tracking-widest">Average ROI</span>
                                <span class="text-2xl">📊</span>
                            </div>
                            <h3 id="roi-val" class="text-3xl font-bold text-emerald-400">-</h3>
                            <p class="text-xs text-slate-500 mt-3">Return on Investment</p>
                        </div>

                        <div class="metric-card rounded-xl p-6 shadow-lg hover:shadow-xl transition-smooth">
                            <div class="flex items-center justify-between mb-4">
                                <span class="text-xs font-semibold text-slate-400 uppercase tracking-widest">Average CAC</span>
                                <span class="text-2xl">💰</span>
                            </div>
                            <h3 id="cac-val" class="text-3xl font-bold text-amber-400">-</h3>
                            <p class="text-xs text-slate-500 mt-3">Cost Per Acquisition</p>
                        </div>
                    </div>

                    <!-- SYNTHESIS INSIGHTS CARD -->
                    <div class="glass-effect rounded-xl p-8 shadow-lg border border-slate-700">
                        <div class="flex items-center gap-3 mb-6">
                            <span class="text-2xl">✨</span>
                            <h3 class="text-lg font-bold text-slate-100">Campaign Synthesis</h3>
                        </div>
                        <p id="synthesis-text" class="text-slate-300 leading-relaxed text-sm">
                            Upload a dataset to generate real-time macro-level insights and strategic recommendations...
                        </p>
                    </div>
                </div>

                <!-- DEEP DIVE ANALYSIS TAB -->
                <div x-show="activeTab === 'deep-dive'" class="transition-smooth">
                    <div class="glass-effect rounded-xl p-8 shadow-lg border border-slate-700">
                        <h3 class="text-lg font-bold text-slate-100 mb-6">Comparative KPI Analysis</h3>
                        
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                            <div>
                                <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">Category</label>
                                <select id="cat-select" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                    <option value="Channel_Used">Channel Used</option>
                                    <option value="Campaign_Goal">Campaign Goal</option>
                                    <option value="Age_Group">Age Group</option>
                                    <option value="Target_Gender">Target Gender</option>
                                    <option value="Location">Location</option>
                                    <option value="Language">Language</option>
                                    <option value="Customer_Segment">Customer Segment</option>
                                </select>
                            </div>

                            <div class="flex items-center justify-center text-slate-500 font-bold">VS</div>

                            <div>
                                <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">KPI Metric</label>
                                <select id="kpi-select" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                    <option value="ROI">ROI</option>
                                    <option value="Acquisition_Cost">Acquisition Cost</option>
                                    <option value="Conversion_Rate">Conversion Rate</option>
                                    <option value="Impressions">Impressions</option>
                                    <option value="Clicks">Clicks</option>
                                    <option value="Engagement_Score">Engagement Score</option>
                                </select>
                            </div>

                            <button onclick="drawDeepDive()" class="gradient-btn text-white font-semibold py-3 rounded-lg hover:shadow-lg flex items-center justify-center gap-2">
                                <span>⚡</span>
                                <span>Generate</span>
                            </button>
                        </div>

                        <div id="plotly-bar-chart" class="w-full h-96" style="border-radius: 8px;"></div>
                    </div>
                </div>

                <!-- AUDIENCE EXPLORER TAB -->
                <div x-show="activeTab === 'audience'" class="transition-smooth">
                    <div class="glass-effect rounded-xl p-8 shadow-lg border border-slate-700">
                        <h3 class="text-lg font-bold text-slate-100 mb-6">Audience Segmentation Sunburst</h3>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            <div class="space-y-4">
                                <div>
                                    <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">Ring 1 (Inner)</label>
                                    <select id="sun-ring-1" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                        <option value="Age_Group" selected>Age Group</option>
                                        <option value="Target_Gender">Target Gender</option>
                                        <option value="Channel_Used">Channel Used</option>
                                        <option value="Campaign_Goal">Campaign Goal</option>
                                        <option value="Location">Location</option>
                                        <option value="Customer_Segment">Customer Segment</option>
                                    </select>
                                </div>

                                <div>
                                    <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">Ring 2 (Middle)</label>
                                    <select id="sun-ring-2" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                        <option value="Target_Gender" selected>Target Gender</option>
                                        <option value="Age_Group">Age Group</option>
                                        <option value="Channel_Used">Channel Used</option>
                                        <option value="Campaign_Goal">Campaign Goal</option>
                                        <option value="Location">Location</option>
                                        <option value="Customer_Segment">Customer Segment</option>
                                    </select>
                                </div>

                                <div>
                                    <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">Ring 3 (Outer)</label>
                                    <select id="sun-ring-3" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                        <option value="Channel_Used" selected>Channel Used</option>
                                        <option value="Age_Group">Age Group</option>
                                        <option value="Target_Gender">Target Gender</option>
                                        <option value="Campaign_Goal">Campaign Goal</option>
                                        <option value="Location">Location</option>
                                        <option value="Customer_Segment">Customer Segment</option>
                                    </select>
                                </div>
                            </div>

                            <div class="space-y-4">
                                <div>
                                    <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">Slice Size</label>
                                    <select id="sun-value-select" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                        <option value="Impressions" selected>Impressions</option>
                                        <option value="Clicks">Clicks</option>
                                    </select>
                                </div>

                                <div>
                                    <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-widest">Color Metric</label>
                                    <select id="sun-color-select" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                        <option value="ROI" selected>ROI</option>
                                        <option value="Engagement_Score">Engagement Score</option>
                                    </select>
                                </div>

                                <button onclick="drawSunburst()" class="w-full gradient-btn text-white font-semibold py-3 rounded-lg hover:shadow-lg flex items-center justify-center gap-2">
                                    <span>🔮</span>
                                    <span>Generate Sunburst</span>
                                </button>
                            </div>
                        </div>

                        <div id="plotly-sunburst-chart" class="w-full" style="height: 550px; border-radius: 8px;"></div>
                    </div>
                </div>

                <!-- FORECASTING TAB -->
                <div x-show="activeTab === 'forecast'" class="transition-smooth">
                    <div class="glass-effect rounded-xl p-8 shadow-lg border border-slate-700">
                        <h3 class="text-lg font-bold text-slate-100 mb-6">Predictive Time Series Analysis</h3>
                        
                        <div class="mb-8">
                            <label class="block text-xs font-semibold text-slate-400 mb-3 uppercase tracking-widest">Select Metric to Project</label>
                            <select id="ts-metric-select" onchange="updateForecast()" class="w-full md:w-96 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-smooth">
                                <option value="ROI">ROI (Return on Investment)</option>
                                <option value="Acquisition_Cost">CAC (Acquisition Cost)</option>
                                <option value="Impressions">Daily Impressions</option>
                            </select>
                        </div>

                        <div id="forecast-chart" class="w-full h-96 rounded-lg flex items-center justify-center" style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(51, 65, 85, 0.3);">
                            <span class="text-slate-500">Awaiting Data...</span>
                        </div>
                    </div>
                </div>

                <!-- AI ASSISTANT TAB -->
                <div x-show="activeTab === 'ai-chat'" class="transition-smooth">
                    <div class="glass-effect rounded-xl overflow-hidden shadow-lg border border-slate-700 flex flex-col h-96">
                        <!-- Chat History -->
                        <div id="chat-history" class="flex-1 overflow-y-auto p-6 space-y-4">
                            <p class="text-center text-slate-500 text-sm py-8">Upload data to initialize the AI Strategist...</p>
                        </div>

                        <!-- Chat Input -->
                        <div class="border-t border-slate-700 bg-slate-900/50 p-4 flex gap-3">
                            <input type="text" id="chat-input" placeholder="Ask about campaign performance..." class="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-smooth">
                            <button onclick="sendMessage()" class="gradient-btn text-white font-semibold px-6 rounded-lg hover:shadow-lg flex items-center gap-2">
                                <span>➤</span>
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </main>

    </div>

    <script>
        function dashboardApp() {
            return {
                activeTab: 'executive'
            };
        }
    </script>
    <script src="js/app.js"></script>
</body>
</html>


#js 
let globalFactSheet = "";
let globalDeepDiveData = null; 
let globalSunburstRaw = null; 

function switchTab(event, tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabId).style.display = 'block';
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');

    // TRIGGER THE FORECAST WHEN TAB IS CLICKED
    if (tabId === 'forecast-tab') {
        updateForecast();
    }
}
// 1. FIXED DEEP DIVE ENGINE (Triggers on demand via Button click)
function drawDeepDive() {
    if (!globalDeepDiveData) { alert("Please upload data first!"); return; }
    
    const cat = document.getElementById('cat-select').value;
    const kpi = document.getElementById('kpi-select').value;
    const data = globalDeepDiveData[cat][kpi];

    const trace = {
        x: data.x,
        y: data.y,
        type: 'bar',
        marker: { color: '#2563eb' },
        text: data.y.map(val => val.toFixed(2)),
        textposition: 'auto',
    };
    
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#9ca3af' },
        margin: { t: 20, b: 40, l: 50, r: 20 }
    };

    Plotly.newPlot('plotly-bar-chart', [trace], layout);
}

// 2. NEW SUNBURST ENGINE (Calculates Custom 3-Tier Configurations)
function drawSunburst() {
    if (!globalSunburstRaw || globalSunburstRaw.length === 0) { alert("Please upload data first!"); return; }
    
    // Get the selected factors for the 3 rings
    const ring1 = document.getElementById('sun-ring-1').value;
    const ring2 = document.getElementById('sun-ring-2').value;
    const ring3 = document.getElementById('sun-ring-3').value;
    
    // Get the selected metrics
    const valueMetric = document.getElementById('sun-value-select').value;
    const colorMetric = document.getElementById('sun-color-select').value;

    let labels = [];
    let ids = [];
    let parents = [];
    let values = [];
    let colorValues = [];
    let map = {};

    globalSunburstRaw.forEach(row => {
        // Dynamically pull the selected column values (or default to "Unknown" if missing)
        let l1 = row[ring1] || "Unknown";
        let l2 = row[ring2] || "Unknown";
        let l3 = row[ring3] || "Unknown";
        
        let v = row[valueMetric] || 0;
        let c = row[colorMetric] || 0;

        // Establish Hierarchical Tree Keys
        let k1 = String(l1);
        let k2 = `${l1} - ${l2}`;
        let k3 = `${l1} - ${l2} - ${l3}`;

        // Initialize node in dictionary if it doesn't exist
        if (!map[k1]) map[k1] = { id: k1, label: l1, parent: "", val: 0, colSum: 0, count: 0 };
        if (!map[k2]) map[k2] = { id: k2, label: l2, parent: k1, val: 0, colSum: 0, count: 0 };
        if (!map[k3]) map[k3] = { id: k3, label: l3, parent: k2, val: 0, colSum: 0, count: 0 };

        // Aggregate values for all 3 levels
        [k1, k2, k3].forEach(k => {
            map[k].val += v;
            map[k].colSum += c;
            map[k].count += 1;
        });
    });

    // Format for Plotly
    Object.values(map).forEach(node => {
        ids.push(node.id);
        labels.push(node.label);
        parents.push(node.parent);
        values.push(node.val);
        colorValues.push(node.colSum / node.count); // Average the color metric (e.g., ROI)
    });

    const trace = {
        type: "sunburst",
        ids: ids,
        labels: labels,
        parents: parents,
        values: values,
        branchvalues: "total",
        marker: {
            colors: colorValues,
            colorscale: "Blues",
            showscale: true
        },
        hovertemplate: `<b>%{label}</b><br>${valueMetric}: %{value}<br>Avg ${colorMetric}: %{color:.2f}<extra></extra>`
    };

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#9ca3af' },
        margin: { t: 10, b: 10, l: 10, r: 10 }
    };

    Plotly.newPlot('plotly-sunburst-chart', [trace], layout);
}

// 3. FILE UPLOAD INTERCEPTOR
document.getElementById('csv-upload').addEventListener('change', async function(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 1. Instantly update the UI to show the file name in a loading state
    const fileNameDisplay = document.getElementById('file-name-display');
    fileNameDisplay.innerText = `⏳ Uploading: ${file.name}...`;
    fileNameDisplay.classList.remove('success');

    const loader = document.getElementById('loading-overlay');
    if(loader) loader.classList.remove('hidden');

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("http://127.0.0.1:8000/api/analyze", { method: "POST", body: formData });
        const data = await response.json();

        
        // Push KPI Cards
        document.getElementById('reach-val').innerText = data.kpis.reach || "0";
        document.getElementById('roi-val').innerText = data.kpis.roi ? data.kpis.roi.toFixed(2) : "0.00";
        document.getElementById('cac-val').innerText = data.kpis.cac ? "$" + data.kpis.cac.toFixed(2) : "$0.00";

        // Inject Data Synthesis Observations (Updated to innerHTML)
        if(document.getElementById('synthesis-text')) {
            document.getElementById('synthesis-text').innerHTML = data.synthesis || "No synthesis text generated.";
        }

        // Cache parameters globally
        globalFactSheet = data.fact_sheet;

        // Cache parameters globally
        globalFactSheet = data.fact_sheet;
        globalDeepDiveData = data.deep_dive_data;
        globalSunburstRaw = data.sunburst_raw_data;

        document.getElementById('chat-history').innerHTML = `<p class="system-msg">✅ Full Strategic Data Matrix Synced.</p>`;

        // 2. Turn the text green to prove it worked!
        fileNameDisplay.innerText = `✅ Loaded: ${file.name}`;
        fileNameDisplay.classList.add('success');

    } catch (error) {
        fileNameDisplay.innerText = `❌ Error uploading ${file.name}`;
        alert("Server communication breakdown.");
        console.error(error);
    } finally {
        if(loader) loader.classList.add('hidden');
 
    }
});
// In your app.js chat message renderer:
const responseText = data.reply;

// Check if there is reasoning in the response
if (responseText.includes("**Reasoning:**")) {
    const parts = responseText.split("**Final Answer:**");
    
    // You can now style the reasoning differently, maybe in a lighter font
    chatContainer.innerHTML = `
        <div class="ai-reasoning" style="font-size: 12px; color: #64748b; opacity: 0.8; margin-bottom: 10px;">
            ${parts[0]}
        </div>
        <div class="ai-answer">
            ${parts[1]}
        </div>
    `;
} else {
    chatContainer.innerHTML = responseText;
}

// 4. TIME SERIES FORECASTING LOGIC
async function updateForecast() {
    const metric = document.getElementById('ts-metric-select').value;
    const chartContainer = document.getElementById('forecast-chart');
    
    try {
        // Fetch from the new /api/timeseries endpoint
        const response = await fetch(`http://127.0.0.1:8000/api/timeseries?metric=${metric}`, { method: "POST" });
        const data = await response.json();
        
        // Handle "Upload dataset first" errors cleanly
        if (data.error) {
            chartContainer.innerHTML = `<span style="color:#ef4444; font-weight:600;">${data.error}</span>`;
            return;
        }
        
        // Trace 1: The Raw Daily Volatility (Light Gray & Faint)
        const traceRaw = {
            x: data.historical_dates,
            y: data.historical_raw,
            type: 'scatter',
            mode: 'lines',
            name: 'Daily Volatility',
            line: { color: 'rgba(148, 163, 184, 0.4)', width: 1 }
        };

        // Trace 2: The Smoothed Historical Trend (Solid Blue)
        const traceSmooth = {
            x: data.historical_dates,
            y: data.historical_smooth,
            type: 'scatter',
            mode: 'lines',
            name: '7-Day Moving Avg',
            line: { color: '#3b82f6', width: 3 }
        };

        // Trace 3: The AI Prediction (Dashed Green)
        // We connect it to the very last historical point so the line is seamless
        const lastHistDate = data.historical_dates[data.historical_dates.length - 1];
        const lastHistValue = data.historical_smooth[data.historical_smooth.length - 1];
        
        const tracePredict = {
            x: [lastHistDate, ...data.future_dates],
            y: [lastHistValue, ...data.future_prediction],
            type: 'scatter',
            mode: 'lines',
            name: '30-Day Projection',
            line: { color: '#10b981', width: 3, dash: 'dot' }
        };

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#f8fafc' },
            margin: { t: 40, b: 40, l: 40, r: 20 },
            xaxis: { showgrid: false },
            yaxis: { showgrid: true, gridcolor: '#1e293b' },
            hovermode: 'x unified',
            hoverlabel: {
                bgcolor: '#1e293b', // Deep dark blue background
                bordercolor: '#3b82f6', // Bright blue border
                font: { color: '#ffffff' } // Pure white text
            },
            legend: { orientation: 'h', y: -0.2 }
        };

        // Clear the container text and draw the plot!
        chartContainer.innerHTML = '';
        Plotly.newPlot('forecast-chart', [traceRaw, traceSmooth, tracePredict], layout);

    } catch (error) {
        console.error("Time Series Error:", error);
        chartContainer.innerHTML = `<span style="color:#ef4444;">Server Connection Failed. Is the Python server running?</span>`;
    }
}
// 4. CHAT INTERFACE FUNCTION
async function sendMessage() {
    const inputField = document.getElementById('chat-input');
    const message = inputField.value.trim();
    const historyBox = document.getElementById('chat-history');

    if (!message || !globalFactSheet) return;

    historyBox.innerHTML += `<div class="msg-user">${message}</div>`;
    inputField.value = "";
    historyBox.scrollTop = historyBox.scrollHeight;

    try {
        const response = await fetch("http://127.0.0.1:8000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: message, fact_sheet: globalFactSheet })
        });
        const data = await response.json();

        historyBox.innerHTML += `<div class="msg-ai"><strong>AI:</strong> ${data.reply}</div>`;
        historyBox.scrollTop = historyBox.scrollHeight;
    } catch (error) {
        historyBox.innerHTML += `<div class="system-msg" style="color: #ef4444;">Connection terminated.</div>`;
    }
}