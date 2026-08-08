let globalFactSheet = "";
let globalDeepDiveData = null; 
let globalSunburstRaw = null; 
// ==========================================
// 1. FILE UPLOAD INTERCEPTOR
// ==========================================
document.getElementById('csv-upload')?.addEventListener('change', async function(event) {
    const file = event.target.files[0];
    if (!file) return;
    const fileStatus = document.getElementById('file-status');
    if (fileStatus) {
        fileStatus.innerText = `⏳ Uploading: ${file.name}...`;
        fileStatus.classList.remove('text-emerald-400');
        fileStatus.classList.add('text-amber-400');
    }
    const loader = document.getElementById('loading-overlay');
    if(loader) loader.classList.remove('hidden');
    const formData = new FormData();
    formData.append("file", file);
    try {
        const response = await fetch("https://ai-marketing-insights-dashboard.onrender.com/api/upload", { method: "POST", body: formData });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Push KPI Cards
        if (document.getElementById('reach-val')) document.getElementById('reach-val').innerText = data.kpis.reach || "0";
        if (document.getElementById('roi-val')) document.getElementById('roi-val').innerText = data.kpis.roi ? data.kpis.roi.toFixed(2) : "0.00";
        if (document.getElementById('cac-val')) document.getElementById('cac-val').innerText = data.kpis.cac ? "$" + data.kpis.cac.toFixed(2) : "$0.00";
        
        if (document.getElementById('synthesis-text')) {
            document.getElementById('synthesis-text').innerHTML = data.synthesis || "No synthesis text generated.";
        }
        // Cache parameters globally
        globalFactSheet = data.fact_sheet;
        globalDeepDiveData = data.deep_dive_data;
        globalSunburstRaw = data.sunburst_raw_data;
        // Trigger Charts Automatically (Safely)
        if (globalSunburstRaw && globalSunburstRaw.length > 0) {
            setTimeout(() => {
                try { drawDeepDive(); } catch(e) { console.error("Deep Dive Error:", e); }
                try { drawSunburst(); } catch(e) { console.error("Sunburst Error:", e); }
                try { updateForecast(); } catch(e) { console.error("Forecast Error:", e); } // 🔥 THIS FIXES THE CHART
            }, 100);
        }
        if (document.getElementById('chat-history')) {
            document.getElementById('chat-history').innerHTML = `<p class="text-center text-emerald-500 text-sm py-8">✓ Strategic Data Matrix Synced</p>`;
        }
        
        if (fileStatus) {
            fileStatus.innerText = `✓ Loaded: ${file.name}`;
            fileStatus.classList.remove('text-amber-400');
            fileStatus.classList.add('text-emerald-400');
        }
    } catch (error) {
        if (fileStatus) {
            // This will now print the exact Python error on your screen
            fileStatus.innerText = `✗ ${error.message}`; 
            fileStatus.classList.add('text-red-400');
        }
        console.error("Upload Error:", error);
    } finally {
        if(loader) loader.classList.add('hidden');
    }
    // Unhide the report button
    document.getElementById('generate-report-btn').classList.remove('hidden');
});
// ==========================================
// 2. DEEP DIVE CHART ENGINE
// ==========================================
function drawDeepDive() {
    if (!globalDeepDiveData) return;
    
    const catSelect = document.getElementById('cat-select');
    const kpiSelect = document.getElementById('kpi-select');
    const container = document.getElementById('plotly-bar-chart');
    const insightsBox = document.getElementById('insights-box');
    
    if (!catSelect || !kpiSelect || !container) return;
    const cat = catSelect.value;
    const kpi = kpiSelect.value;
    
    if (!globalDeepDiveData[cat] || !globalDeepDiveData[cat][kpi]) return;
    const data = globalDeepDiveData[cat][kpi];
    const values = data.y;
    const labels = data.x;
    const meanVal = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((a, b) => a + Math.pow(b - meanVal, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    const cv = meanVal > 0 ? (stdDev / meanVal) * 100 : 0;
    
    const invertedKPIs = ["Acquisition_Cost", "Acquisition Cost", "CAC"];
    const isInverted = invertedKPIs.includes(kpi);
    
    const maxVal = Math.max(...values);
    const minVal = Math.min(...values);
    const bestVal = isInverted ? minVal : maxVal;
    const worstVal = isInverted ? maxVal : minVal;
    
    const topPerformer = labels[values.indexOf(bestVal)];
    const bottomPerformer = labels[values.indexOf(worstVal)];
    
    const epsilon = 0.0001;
    const zScore = stdDev > epsilon ? (bestVal - meanVal) / stdDev : 0;
    
    let strategy = "";
    if (stdDev <= epsilon || cv < 2.0) {
        strategy = "Performance variance is too small to be practically significant. Maintain current baseline allocation.";
    } else if ((!isInverted && zScore >= 1.0) || (isInverted && zScore <= -1.0)) {
        strategy = `High Statistical Confidence: Scale ${topPerformer} budget by 20% to exploit efficiency.`;
    } else {
        strategy = `Monitor ${topPerformer}; performing slightly above average, but not a significant outlier.`;
    }
    const delta = minVal > 0 ? (((maxVal - minVal) / minVal) * 100).toFixed(1) : "0.0";
    
    if (insightsBox) {
        insightsBox.innerHTML = `
            <div class="glass-effect p-6 border border-blue-900/50 bg-blue-900/10 flex items-center justify-between">
                <div>
                    <h4 class="text-blue-400 font-bold mb-1 text-sm">Statistical Delta Insight</h4>
                    <p class="text-sm text-slate-300">
                        <strong>${topPerformer}</strong> outperforms <strong>${bottomPerformer}</strong> 
                        by <span class="text-emerald-400 font-bold">${delta}%</span>.
                    </p>
                    <p class="text-xs text-slate-400 mt-1">
                        μ: ${meanVal.toFixed(2)} | σ: ${stdDev.toFixed(2)} | Z: ${zScore.toFixed(2)} | CV: ${cv.toFixed(2)}%
                    </p>
                </div>
                <div class="text-right max-w-xs">
                    <span class="text-xs text-slate-500 uppercase block">Strategic Recommendation</span>
                    <p class="text-sm text-blue-200 font-medium leading-relaxed">${strategy}</p>
                </div>
            </div>
        `;
    }
    const trace = {
        x: labels, y: values, type: 'bar',
        marker: { color: '#3b82f6', line: { color: '#0f172a', width: 2 } },
        text: values.map(val => val.toFixed(2)), textposition: 'auto',
        textfont: { family: 'Inter, sans-serif', size: 11, color: '#ffffff' },
        hovertemplate: `<b>%{x}</b><br>${kpi}: %{y:.2f}<extra></extra>`
    };
    
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#94a3b8' },
        margin: { t: 40, b: 40, l: 50, r: 20 }, bargap: 0.4, 
        xaxis: { color: '#64748b', showgrid: false, tickfont: { size: 11 }, categoryorder: 'total descending' },
        yaxis: { color: '#64748b', gridcolor: 'rgba(255, 255, 255, 0.05)', zerolinecolor: 'rgba(255, 255, 255, 0.1)', tickfont: { size: 11 } },
        hoverlabel: { bgcolor: '#1e293b', bordercolor: '#334155', font: { family: 'Inter, sans-serif', color: '#f1f5f9' } }
    };
    
    Plotly.newPlot(container, [trace], layout, { responsive: true });
    new ResizeObserver(() => { Plotly.Plots.resize(container); }).observe(container);
}
// ==========================================
// 3. SUNBURST ENGINE
// ==========================================
function drawSunburst() {
    if (!globalSunburstRaw || globalSunburstRaw.length === 0) return;
    
    const ring1El = document.getElementById('sun-ring-1');
    const ring2El = document.getElementById('sun-ring-2');
    const ring3El = document.getElementById('sun-ring-3');
    const valEl = document.getElementById('sun-value-select');
    const colEl = document.getElementById('sun-color-select');
    const container = document.getElementById('plotly-sunburst-chart');
    if (!ring1El || !ring2El || !ring3El || !valEl || !colEl || !container) return;
    const ring1 = ring1El.value;
    const ring2 = ring2El.value;
    const ring3 = ring3El.value;
    const valueMetric = valEl.value;
    const colorMetric = colEl.value;
    let labels = [], ids = [], parents = [], values = [], colorValues = [], map = {};
    globalSunburstRaw.forEach(row => {
        let l1 = row[ring1] || "Unknown", l2 = row[ring2] || "Unknown", l3 = row[ring3] || "Unknown";
        let v = parseFloat(row[valueMetric]) || 0;
        let rawColor = String(row[colorMetric] || "0").replace(/[^0-9.-]+/g, "");
        let c = parseFloat(rawColor) || 0;
        let k1 = String(l1);
        let k2 = `${l1} - ${l2}`;
        let k3 = `${l1} - ${l2} - ${l3}`;
        if (!map[k1]) map[k1] = { id: k1, label: l1, parent: "", val: 0, colSum: 0, count: 0 };
        if (!map[k2]) map[k2] = { id: k2, label: l2, parent: k1, val: 0, colSum: 0, count: 0 };
        if (!map[k3]) map[k3] = { id: k3, label: l3, parent: k2, val: 0, colSum: 0, count: 0 };
        [k1, k2, k3].forEach(k => {
            map[k].val += v;
            map[k].colSum += c;
            map[k].count += 1;
        });
    });
    Object.values(map).forEach(node => {
        ids.push(node.id);
        labels.push(node.label);
        parents.push(node.parent);
        values.push(node.val);
        colorValues.push(node.colSum / node.count); 
    });
    const trace = {
        type: "sunburst", ids: ids, labels: labels, parents: parents, values: values, branchvalues: "total",
        marker: {
            colors: colorValues,
            colorscale: [['0.0', '#1e293b'], ['0.3', '#2563eb'], ['0.7', '#3b82f6'], ['1.0', '#93c5fd']], 
            showscale: true, line: { color: '#0f172a', width: 1.5 }, 
            colorbar: {
                title: { text: colorMetric, font: { size: 11, color: '#94a3b8' } },
                thickness: 10, len: 0.75, x: 1.02, tickfont: { size: 10, color: '#64748b' },
                outlinewidth: 0, ticks: 'outside', tickcolor: '#334155'
            }
        },
        textinfo: "label", insidetextorientation: 'auto', 
        insidetextfont: { family: 'Inter, sans-serif', size: 10, color: '#e2e8f0' }, 
        hovertemplate: `<b>%{label}</b><br>${valueMetric}: %{value}<br>Avg ${colorMetric}: %{color:.2f}<extra></extra>`
    };
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 20, b: 20, l: 20, r: 80 }, 
        hoverlabel: { bgcolor: '#1e293b', bordercolor: '#334155', font: { family: 'Inter, sans-serif', color: '#f1f5f9' } }
    };
    
    Plotly.newPlot(container, [trace], layout, { responsive: true });
    new ResizeObserver(() => { Plotly.Plots.resize(container); }).observe(container);
}
// ==========================================
// 4. GOD-MODE MATRIX ENGINE
// ==========================================
function runGodModeMatrix() {
    if (!globalSunburstRaw || globalSunburstRaw.length === 0) { alert("Please upload dataset first."); return; }
    const checkboxes = document.querySelectorAll('.matrix-dim:checked');
    const selectedDims = Array.from(checkboxes).map(cb => cb.value);
    if (selectedDims.length === 0) { alert("You must select at least one dimension."); return; }
    const groupMap = new Map();
    globalSunburstRaw.forEach(row => {
        const keyParts = selectedDims.map(dim => row[dim] || "Unknown");
        const comboKey = keyParts.join(" | ");
        if (!groupMap.has(comboKey)) {
            groupMap.set(comboKey, { comboName: comboKey, impressions: 0, totalROI: 0, totalCAC: 0, count: 0 });
        }
        const group = groupMap.get(comboKey);
        const rawROI = String(row.ROI || "0").replace(/[^0-9.-]+/g, "");
        const rawCAC = String(row.Acquisition_Cost || "0").replace(/[^0-9.-]+/g, "");
        group.impressions += parseInt(row.Impressions, 10) || 0;
        group.totalROI += parseFloat(rawROI) || 0;
        group.totalCAC += parseFloat(rawCAC) || 0;
        group.count += 1;
    });
    const volumeThreshold = 100; 
    const validSegments = [];
    groupMap.forEach(group => {
        if (group.impressions >= volumeThreshold) {
            validSegments.push({
                combo: group.comboName, impressions: group.impressions,
                roi: group.totalROI / group.count, cac: group.totalCAC / group.count
            });
        }
    });
    if (validSegments.length === 0) {
        groupMap.forEach(group => {
            validSegments.push({
                combo: group.comboName, impressions: group.impressions,
                roi: group.totalROI / group.count, cac: group.totalCAC / group.count
            });
        });
    }
    validSegments.sort((a, b) => b.roi - a.roi); 
    const top5 = validSegments.slice(0, 5);
    const bottom5 = validSegments.slice(-5).reverse(); 
    renderMatrixUI(top5, bottom5, selectedDims);
}
function renderMatrixUI(top5, bottom5, dimensions) {
    const container = document.getElementById('matrix-results');
    if(!container) return;
    
    container.classList.remove('hidden');
    const headers = `
        <th class="text-left pb-3 font-semibold text-slate-400">Micro-Segment Profile (${dimensions.length} Dims)</th>
        <th class="text-right pb-3 font-semibold text-slate-400">Volume</th>
        <th class="text-right pb-3 font-semibold text-slate-400">Avg CAC</th>
        <th class="text-right pb-3 font-semibold text-slate-400">Avg ROI</th>
    `;
    const buildRows = (dataArray, highlightClass) => {
        return dataArray.map((row, index) => `
            <tr class="border-t border-slate-800 hover:bg-slate-800/30 transition-colors">
                <td class="py-3 text-sm text-slate-200">
                    <span class="font-bold text-slate-500 mr-2">#${index + 1}</span> 
                    ${row.combo.replace(/\|/g, '<span class="text-slate-600 mx-1">/</span>')}
                </td>
                <td class="py-3 text-sm text-right text-slate-300">${row.impressions.toLocaleString()}</td>
                <td class="py-3 text-sm text-right text-slate-300">$${row.cac.toFixed(2)}</td>
                <td class="py-3 text-sm text-right font-bold ${highlightClass}">${row.roi.toFixed(2)}</td>
            </tr>
        `).join('');
    };
    container.innerHTML = `
        <div class="mb-8">
            <h4 class="text-emerald-400 font-bold mb-4 uppercase tracking-widest text-xs">Top 5 Scale Opportunities (Winners)</h4>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse"><thead><tr>${headers}</tr></thead><tbody>${buildRows(top5, 'text-emerald-400')}</tbody></table>
            </div>
        </div>
        <div>
            <h4 class="text-red-400 font-bold mb-4 uppercase tracking-widest text-xs">Top 5 Budget Bleeders (Losers)</h4>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse"><thead><tr>${headers}</tr></thead><tbody>${buildRows(bottom5, 'text-red-400')}</tbody></table>
            </div>
        </div>
    `;
}
// ==========================================
// 5. FORECASTING ENGINE
// ==========================================
document.getElementById('ts-metric-select')?.addEventListener('change', updateForecast);
document.getElementById('ts-window-select')?.addEventListener('change', updateForecast);
async function updateForecast() {
    const metricEl = document.getElementById('ts-metric-select');
    const windowEl = document.getElementById('ts-window-select');
    const chartContainer = document.getElementById('forecast-chart');
    
    if (!metricEl || !windowEl || !chartContainer) return;
    const metric = metricEl.value;
    const timeWindow = windowEl.value;
    
    let rawName = 'Daily Volatility', smoothName = '7-Day Moving Avg';
    if (timeWindow === 'weekly_30') { rawName = 'Weekly Volatility'; smoothName = '30-Day Moving Avg'; } 
    else if (timeWindow === 'monthly_90') { rawName = 'Monthly Volatility'; smoothName = '90-Day Moving Avg'; }
    
    try {
        const response = await fetch(`https://ai-marketing-insights-dashboard.onrender.com/api/timeseries?metric=${metric}&window=${timeWindow}`, { method: "POST" });
        const data = await response.json();
        
        if (data.error) { chartContainer.innerHTML = `<span class="text-red-500 font-semibold">${data.error}</span>`; return; }
        
        // --- DYNAMIC STATISTICAL CALCULATIONS ---
        const histSmooth = data.historical_smooth;
        const futurePred = data.future_prediction;
        const lastHist = histSmooth[histSmooth.length - 1];
        const projMean = futurePred.reduce((a, b) => a + b, 0) / futurePred.length;
        const driftPct = ((projMean - lastHist) / lastHist) * 100;
        // Calculate historical Standard Deviation (Sigma)
        const histMean = histSmooth.reduce((a, b) => a + b, 0) / histSmooth.length;
        const histVariance = histSmooth.reduce((a, b) => a + Math.pow(b - histMean, 2), 0) / histSmooth.length;
        const stdDev = Math.sqrt(histVariance);
        // Calculate 95% Confidence Interval (Z-score 1.96 * sigma)
        const lowerCI = projMean - (1.96 * stdDev);
        const upperCI = projMean + (1.96 * stdDev);
        // Cache globally for the PDF Generator
        globalForecastStats = {
            baseline: lastHist.toFixed(0),
            projected_mean: projMean.toFixed(0),
            drift_pct: driftPct.toFixed(2),
            confidence_lower: lowerCI.toFixed(0),
            confidence_upper: upperCI.toFixed(0),
            sigma: stdDev.toFixed(0)
        };
        // ----------------------------------------
        const traceRaw = { x: data.historical_dates, y: data.historical_raw, type: 'scatter', mode: 'lines', name: rawName, line: { color: '#94A3B8', width: 1, dash: 'dash' }, opacity: 0.45 };
        const traceSmooth = { x: data.historical_dates, y: histSmooth, type: 'scatter', mode: 'lines', name: smoothName, line: { color: '#0059B2', width: 3 } };
        const lastHistDate = data.historical_dates[data.historical_dates.length - 1];
        const tracePredict = { x: [lastHistDate, ...data.future_dates], y: [lastHist, ...futurePred], type: 'scatter', mode: 'lines', name: 'Projection', line: { color: '#10b981', width: 3, dash: 'dot' } };
        const layout = {
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { color: '#f8fafc' },
            margin: { t: 40, b: 40, l: 40, r: 20 },
            xaxis: { showgrid: false, color: '#64748b' },
            yaxis: { showgrid: true, gridcolor: 'rgba(255, 255, 255, 0.05)', color: '#64748b', gridwidth: 1 },
            hovermode: 'x unified', hoverlabel: { bgcolor: '#1e293b', bordercolor: '#334155', font: { family: 'Inter, sans-serif', color: '#f1f5f9' } },
            legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center', yanchor: 'top' }
        };
        chartContainer.innerHTML = '';
        Plotly.newPlot(chartContainer, [traceRaw, traceSmooth, tracePredict], layout);
        new ResizeObserver(() => { Plotly.Plots.resize(chartContainer); }).observe(chartContainer);
    } catch (error) {
        chartContainer.innerHTML = `<span class="text-red-500 font-semibold">Server Connection Failed. Is the Python server running?</span>`;
    }
}
// ==========================================
// 6. AI ASSISTANT CHAT ENGINE
// ==========================================
async function sendMessage() {
    const inputField = document.getElementById('chat-input');
    const historyBox = document.getElementById('chat-history');
    
    if (!inputField || !historyBox) return;
    const message = inputField.value.trim();
    if (!message || !globalFactSheet) {
        if (!globalFactSheet) alert("Please upload data first to use the AI assistant.");
        return;
    }
    historyBox.innerHTML += `<div class="flex justify-end mb-4"><div class="bg-blue-600 text-white px-4 py-3 rounded-lg rounded-tr-none max-w-xs break-words text-sm">${escapeHtml(message)}</div></div>`;
    inputField.value = "";
    historyBox.scrollTop = historyBox.scrollHeight;
    try {
        const response = await fetch("https://ai-marketing-insights-dashboard.onrender.com/api/chat", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: message, fact_sheet: globalFactSheet })
        });
        const data = await response.json();
        
        let formattedReply = data.reply;
        if (formattedReply.includes("**Reasoning:**")) {
            const parts = formattedReply.split("**Final Answer:**");
            formattedReply = `<div class="text-xs text-slate-400 opacity-75 mb-2 pb-2 border-b border-slate-600">${parts[0]}</div><div class="text-slate-200 text-sm">${parts[1] || ''}</div>`;
        }
        historyBox.innerHTML += `<div class="flex justify-start mb-4"><div class="bg-slate-700 text-slate-100 px-4 py-3 rounded-lg rounded-tl-none max-w-xs break-words text-sm">${formattedReply}</div></div>`;
        historyBox.scrollTop = historyBox.scrollHeight;
    } catch (error) {
        historyBox.innerHTML += `<div class="flex justify-start mb-4"><div class="bg-red-900/30 text-red-400 px-4 py-3 rounded-lg rounded-tl-none text-sm">Connection terminated.</div></div>`;
    }
}
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// ==========================================
// 7. AUTOMATED REPORT GENERATOR (CONSULTING DELIVERABLE)
// ==========================================
async function buildAndDownloadReport() {
    if (!globalSunburstRaw || !globalFactSheet) {
        alert("Data must be loaded before generating a report.");
        return;
    }
    // Turn on the loading overlay to signal work is happening
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.classList.remove('hidden');
    const btn = document.getElementById('generate-report-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Generating AI Insight & Compiling Report...";
    btn.disabled = true;
    try {
        // Extract Core KPIs & Compute Executive Proxies
        const reachRaw = document.getElementById('reach-val')?.innerText || "0";
        const roiStr = document.getElementById('roi-val')?.innerText || "0.00";
        const cacStr = document.getElementById('cac-val')?.innerText || "$0.00";
        
        const roi = parseFloat(roiStr) || 0;
        const cac = parseFloat(cacStr.replace(/[^0-9.-]+/g, "")) || 0;
        
        const reachNum = parseFloat(reachRaw.replace(/[^0-9.]/g, "")) || 100000;
        const volumeMultiplier = reachRaw.includes('M') ? 1000000 : (reachRaw.includes('k') ? 1000 : 1);
        const totalImpressions = reachNum * volumeMultiplier;
        
        const totalConversions = Math.floor(totalImpressions * 0.012); 
        const totalSpend = totalConversions * cac;
        
        const globalLTV = cac * (1 + roi);
        const globalRatio = cac > 0 ? (globalLTV / cac).toFixed(1) + "x" : "N/A";
        // Extract Forecast Image
        let forecastImg = "";
        try {
            const forecastContainer = document.getElementById('forecast-chart');
            if (forecastContainer && forecastContainer.innerHTML.trim() !== '') {
                forecastImg = await Plotly.toImage(forecastContainer, { format: 'png', width: 800, height: 250 });
            }
        } catch (e) {
            console.warn("Forecast image extraction bypassed.");
        }
        // Process Segment Deep Dive
        const checkboxes = document.querySelectorAll('.matrix-dim:checked');
        let selectedDims = Array.from(checkboxes).map(cb => cb.value);
        if(selectedDims.length === 0) selectedDims = ['Channel_Used', 'Campaign_Goal', 'Target_Gender']; 
        const groupMap = new Map();
        globalSunburstRaw.forEach(row => {
            const keyParts = selectedDims.map(dim => row[dim] || "Unknown");
            const comboKey = keyParts.join(" | ");
            
            if (!groupMap.has(comboKey)) {
                groupMap.set(comboKey, { comboName: comboKey, impressions: 0, totalROI: 0, totalCAC: 0, count: 0, roiArray: [] });
            }
            
            const group = groupMap.get(comboKey);
            const imp = parseInt(row.Impressions, 10) || 0;
            const r = parseFloat(String(row.ROI || "0").replace(/[^0-9.-]+/g, "")) || 0;
            const c = parseFloat(String(row.Acquisition_Cost || "0").replace(/[^0-9.-]+/g, "")) || 0;
            group.impressions += imp;
            group.totalROI += r;
            group.totalCAC += c;
            group.count += 1;
            group.roiArray.push(r);
        });
        const segments = [];
        groupMap.forEach(g => {
            if (g.impressions >= 100) {
                const meanROI = g.totalROI / g.count;
                const variance = g.roiArray.reduce((acc, val) => acc + Math.pow(val - meanROI, 2), 0) / g.count;
                const stdDev = Math.sqrt(variance);
                const cv = meanROI > 0 ? (stdDev / meanROI) : 0;
                const meanCAC = g.totalCAC / g.count;
                const meanLTV = meanCAC * (1 + meanROI);
                const segConversions = Math.floor(g.impressions * 0.012);
                const segSpend = segConversions * meanCAC;
                
                segments.push({ 
                    combo: g.comboName, 
                    channel: g.comboName.split(' | ')[0],
                    impressions: g.impressions, 
                    spend: segSpend,
                    roi: meanROI, 
                    cac: meanCAC, 
                    ltv: meanLTV,
                    ratio: meanCAC > 0 ? (meanLTV / meanCAC).toFixed(1) + "x" : "N/A",
                    cv: cv 
                });
            }
        });
        const winners = [...segments].sort((a, b) => b.roi - a.roi).slice(0, 5);
        const losers = [...segments].sort((a, b) => a.roi - b.roi).slice(0, 5);
        const topSegment = winners[0] || { channel: "Unknown", combo: "Unknown", roi: 0, cac: 0, ratio: "0x" };
        const bottomSegment = losers[0] || { channel: "Unknown", combo: "Unknown", roi: 0, cac: 0, ratio: "0x" };
        
        // --- NEW: DETERMINISTIC ECONOMIC CALCULATIONS ---
        // 1. Reallocation Amount (15% of total spend)
        const reallocationAmountNum = totalSpend * 0.15;
        
        // 2. True Opportunity Cost (Capital wasted by not moving bottom segment spend to the top segment)
        const roiDelta = topSegment.roi - bottomSegment.roi;
        const opportunityCostNum = bottomSegment.spend * (roiDelta > 0 ? roiDelta : 0);
        
        // 3. Expected Revenue Lift (Applies a 20% diminishing returns penalty to account for saturation)
        const expectedRevenueLiftNum = reallocationAmountNum * (topSegment.roi * 0.80);
        
        // 4. Concentration Risk (New % of total budget concentrated in the top segment)
        const newTopSegmentSpend = topSegment.spend + reallocationAmountNum;
        const concentrationRiskPct = totalSpend > 0 ? ((newTopSegmentSpend / totalSpend) * 100).toFixed(1) : "0.0";
        const budgetDelta = "$" + (totalSpend * 0.15).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0});
        const formatMoney = (amount) => "$" + amount.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0});
        const cleanCombo = (combo) => combo.replace(/ \| /g, ' / ');
       
        const buildTableRows = (dataArray) => {
            return dataArray.map((row) => {
                const parts = row.combo.split(" | ");
                const badges = parts.map(p => `<span style="color: #334155; font-size: 11px; font-weight: 500;">${p}</span>`).join('<span style="color:#cbd5e1; margin: 0 4px;">/</span>');
                
                let volatility = "";
                if (row.cv <= 0.40) volatility = `Low`;
                else if (row.cv <= 0.85) volatility = `Medium`;
                else volatility = `High`;
                return `
                    <tr style="border-bottom: 1px solid #e2e8f0; background: #ffffff;">
                        <td style="padding: 12px 8px; width: 45%; line-height: 1.4;">${badges}</td>
                        <td style="padding: 12px 8px; font-size: 11px; text-align: right; color: #475569;">${formatMoney(row.spend)}</td>
                        <td style="padding: 12px 8px; font-size: 11px; text-align: right; color: #475569;">$${row.cac.toFixed(2)}</td>
                        <td style="padding: 12px 8px; font-size: 11px; text-align: right; color: #475569;">${row.ratio}</td>
                        <td style="padding: 12px 8px; font-size: 11px; text-align: right; font-weight: bold; color: #0f172a;">${row.roi.toFixed(2)}</td>
                        <td style="padding: 12px 8px; font-size: 11px; text-align: right; color: #475569;">${volatility}</td>
                    </tr>
                `;
            }).join('');
        };
        const currentDate = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        const computedDiagnosticReason = bottomSegment.roi < 1.0 
            ? "Funnel Conversion Friction resulting in platform media waste and negative unit margin performance." 
            : "Audience and Frequency saturation resulting in diminishing multi-touch return curve.";
        // Fetch AI Narrative for ENTIRE Document
        let aiData = {};
        try {
            const narrativeResponse = await fetch('https://ai-marketing-insights-dashboard.onrender.com/api/report/narrative', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    roi: roi.toFixed(2),
                    top_seg: topSegment.combo,
                    bot_seg: bottomSegment.combo,
                    diagnostic_reason: computedDiagnosticReason,
                    total_spend: formatMoney(totalSpend),
                    blended_cac: "$" + cac.toFixed(2),
                    ltv_cac_ratio: globalRatio,
                    top_roi: topSegment.roi.toFixed(2),
                    top_cac: "$" + topSegment.cac.toFixed(2),
                    bot_roi: bottomSegment.roi.toFixed(2),
                    bot_cac: "$" + bottomSegment.cac.toFixed(2),
                    reallocation_amount: budgetDelta,
                    
                    // PASSING HARDCODED MATH TO THE BACKEND:
                    opportunity_cost: formatMoney(opportunityCostNum),
                    expected_revenue_lift: formatMoney(expectedRevenueLiftNum),
                    concentration_risk_pct: concentrationRiskPct + "%",
                    
                    forecast_stats: globalForecastStats ? {
                        ...globalForecastStats,
                        roi_floor: 3.00,
                        cac_ceiling: (cac * 1.15).toFixed(2)
                    } : null
                })
            });
            
            if (!narrativeResponse.ok) throw new Error("Backend response error status");
            aiData = await narrativeResponse.json();
        } catch (fetchErr) {
            console.error("AI Insight Fetch Failed, using client-side fallback: ", fetchErr);
            aiData = {
                executive_summary: "Unable to generate AI synthesis. Please check backend connectivity.",
                health_assessment: "Unable to generate AI synthesis.",
                scale_rationale: "Data-driven scale justification unavailable.",
                halt_rationale: "Data-driven halt justification unavailable.",
                performance_drivers: "Driver analysis unavailable.",
                underperforming_segments: "Underperformance diagnostics unavailable.",
                portfolio_risks: "<li>Risk generation unavailable</li>",
                strategic_outlook: "Outlook generation unavailable.",
                final_conclusion: "Final conclusion unavailable due to API disconnect."
            };
        }
        const fmt = (text) => {
            if (!text) return '';
            const safeText = Array.isArray(text) ? text.join(' ') : String(text);
            return safeText.split('\n\n').map(p => `<p style="margin-bottom: 15px; margin-top: 0; line-height: 1.6; text-align: left;">${p}</p>`).join('');
        };
        const finalConclusionText = aiData.final_conclusion || aiData.action_plan || aiData.conclusion || "Strategic reallocation of spend toward top-performing segments stabilizes portfolio ROI and mitigates revenue volatility.";
        const reportHTML = `
            <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #0f172a; background: #ffffff; width: 100%; margin: 0; padding: 0; line-height: 1.5;">
                
                <!-- ===================== PAGE 1 ===================== -->
                <div style="padding: 40px 50px; page-break-after: always; min-height: 90vh;">
                    <!-- Header -->
                    <div style="border-bottom: 2px solid #0f172a; padding-bottom: 15px; margin-bottom: 35px;">
                        <h1 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Campaign Performance & Capital Allocation Request</h1>
                        <p style="margin: 5px 0 0 0; color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Prepared For: Executive Leadership | Date: ${currentDate}</p>
                    </div>
                    <!-- Executive Summary -->
                    <div style="margin-bottom: 35px;">
                        <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">1. Executive Summary</h2>
                        <div style="font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
                            ${fmt(aiData.executive_summary)}
                        </div>
                    </div>
                    <!-- Portfolio Health Assessment -->
                    <div style="margin-bottom: 35px;">
                        <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">2. Portfolio Health Assessment</h2>
                        <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                            <div style="padding: 15px; border: 1px solid #e2e8f0; flex: 1;">
                                <span style="display: block; font-size: 9px; color: #64748b; text-transform: uppercase; font-weight: 700;">Total Estimated Spend</span>
                                <strong style="font-size: 16px; color: #0f172a;">${formatMoney(totalSpend)}</strong>
                            </div>
                            <div style="padding: 15px; border: 1px solid #e2e8f0; flex: 1;">
                                <span style="display: block; font-size: 9px; color: #64748b; text-transform: uppercase; font-weight: 700;">Blended CAC</span>
                                <strong style="font-size: 16px; color: #0f172a;">$${cac.toFixed(2)}</strong>
                            </div>
                            <div style="padding: 15px; border: 1px solid #e2e8f0; flex: 1;">
                                <span style="display: block; font-size: 9px; color: #64748b; text-transform: uppercase; font-weight: 700;">Aggregate LTV:CAC</span>
                                <strong style="font-size: 16px; color: #0f172a;">${globalRatio}</strong>
                            </div>
                        </div>
                        <div style="font-size: 12px; color: #334155; text-align: left; line-height: 1.6;">
                            ${fmt(aiData.health_assessment)}
                        </div>
                    </div>
                    <!-- Budget Allocation Recommendations -->
                    <div>
                        <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">3. Budget Allocation Recommendations</h2>
                        
                        <h3 style="font-size: 12px; color: #0f172a; margin: 0 0 5px 0;">Scale: Reallocate Capital to High-Yield Segments</h3>
                        <div style="font-size: 12px; color: #334155; margin-bottom: 15px; line-height: 1.6; text-align: left;">
                            <strong>Action:</strong> Shift ${budgetDelta} of portfolio spend into <strong>${cleanCombo(topSegment.combo)}</strong>.<br>
                            <strong>Rationale:</strong> ${aiData.scale_rationale}
                        </div>
                        <h3 style="font-size: 12px; color: #0f172a; margin: 0 0 5px 0;">Halt: Freeze Inefficient Upper-Funnel Allocation</h3>
                        <div style="font-size: 12px; color: #334155; margin-bottom: 0; line-height: 1.6; text-align: left;">
                            <strong>Action:</strong> Immediately freeze spend on <strong>${cleanCombo(bottomSegment.combo)}</strong>.<br>
                            <strong>Rationale:</strong> ${aiData.halt_rationale}
                        </div>
                    </div>
                </div>
                <!-- ===================== PAGE 2 ===================== -->
                <div style="padding: 40px 50px; page-break-after: always; min-height: 90vh;">
                    <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">4. Performance Drivers & Segment Deep Dive</h2>
                    <div style="font-size: 12px; color: #334155; margin-bottom: 20px; text-align: left;">
                        ${fmt(aiData.performance_drivers)}
                    </div>
                    <h3 style="margin: 0 0 10px 0; font-size: 11px; color: #0f172a; text-transform: uppercase; font-weight: 700;">Top Performing Assets</h3>
                    <table style="width: 100%; border-collapse: collapse; text-align: left; margin-bottom: 30px;">
                        <thead>
                            <tr style="border-bottom: 2px solid #0f172a;">
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a;">Segment Breakdown</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">Est. Spend</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">CAC</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">LTV:CAC</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">30-Day ROI</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">Volatility</th>
                            </tr>
                        </thead>
                        <tbody>${buildTableRows(winners)}</tbody>
                    </table>
                    <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-top: 40px; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">5. Underperforming Segments</h2>
                    <div style="font-size: 12px; color: #334155; margin-bottom: 20px; text-align: left;">
                        ${fmt(aiData.underperforming_segments)}
                    </div>
                    <h3 style="margin: 0 0 10px 0; font-size: 11px; color: #0f172a; text-transform: uppercase; font-weight: 700;">Critical Underperformers</h3>
                    <table style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead>
                            <tr style="border-bottom: 2px solid #0f172a;">
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a;">Segment Breakdown</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">Est. Spend</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">CAC</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">LTV:CAC</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">30-Day ROI</th>
                                <th style="padding: 10px 8px; font-size: 9px; text-transform: uppercase; color: #0f172a; text-align: right;">Volatility</th>
                            </tr>
                        </thead>
                        <tbody>${buildTableRows(losers)}</tbody>
                    </table>
                </div>
                <!-- ===================== PAGE 3 ===================== -->
                <div style="padding: 40px 50px; box-sizing: border-box;">
                    
                    <!-- Portfolio Risks -->
                    <div style="margin-bottom: 25px; page-break-inside: avoid; break-inside: avoid;">
                        <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">6. Portfolio Risks</h2>
                        <ul style="font-size: 12px; color: #334155; padding-left: 20px; margin: 0; line-height: 1.6; text-align: left;">
                            ${aiData.portfolio_risks}
                        </ul>
                    </div>
                    <!-- Forecast & Strategic Outlook -->
                    <div style="margin-bottom: 25px; page-break-inside: avoid; break-inside: avoid;">
                        <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">7. Forecast & Strategic Outlook</h2>
                        
                        ${forecastImg ? `
                        <div style="border: 1px solid #e2e8f0; padding: 10px; margin-bottom: 15px; background: #ffffff;">
                            <img src="${forecastImg}" style="width: 100%; max-height: 220px; object-fit: contain; display: block;" />
                        </div>` : ''}
                        
                        <div style="font-size: 12px; color: #334155; text-align: left; line-height: 1.6; margin: 0;">
                            ${fmt(aiData.strategic_outlook)}
                        </div>
                    </div>
                    <!-- Final Conclusion -->
                    <div style="page-break-inside: avoid; break-inside: avoid; display: block; clear: both;">
                        <h2 style="color: #0f172a; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">8. Final Conclusion</h2>
                        <div style="font-size: 12px; color: #334155; text-align: left; line-height: 1.6; margin: 0; page-break-inside: auto;">
                            ${fmt(finalConclusionText)}
                        </div>
                    </div>
                    
                    <div style="margin-top: 30px; text-align: center; font-size: 9px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 15px; text-transform: uppercase; clear: both;">
                        Proprietary & Confidential
                    </div>
                </div>   
            </div>
        `;
// =================================================================
        // GENERATE PDF (HIGH-FIDELITY HTML RENDERING FIX)
        // =================================================================
        if (aiData.error) {
            throw new Error(`AI Engine Error: ${aiData.error}`);
        }

        // 1. Create a physical container for the report
        const reportContainer = document.createElement('div');
        reportContainer.innerHTML = reportHTML;
        
        // 2. Force desktop width and white background, but hide it BEHIND the current page
        // This prevents the browser from discarding it as a 0px off-screen element
        reportContainer.style.position = 'absolute';
        reportContainer.style.top = '0';
        reportContainer.style.left = '0';
        reportContainer.style.width = '1200px'; 
        reportContainer.style.backgroundColor = '#ffffff';
        reportContainer.style.color = '#000000';
        reportContainer.style.zIndex = '-1000'; 
        reportContainer.style.padding = '40px';
        
        // 3. Attach to the live webpage
        document.body.appendChild(reportContainer);

        // 4. 🔥 Give the browser exactly 500ms to paint the tables and charts 
        await new Promise(resolve => setTimeout(resolve, 500));

        // 5. Configure the high-fidelity screenshot engine
        const opt = {
            margin:       0.3,
            filename:     `Executive_Briefing_${new Date().toISOString().split('T')[0]}.pdf`,
            image:        { type: 'jpeg', quality: 1.0 },
            html2canvas:  { 
                scale: 2, 
                useCORS: true, 
                logging: false,
                windowWidth: 1200,
                scrollY: 0 // Prevents the screenshot from cutting off if you are scrolled down
            },
            jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        // 6. Generate the formatted PDF

        await html2pdf().set(opt).from(reportContainer).save();
        // 7. Cleanup: Delete the hidden container
        document.body.removeChild(reportContainer);

    } catch (error) {
        console.error("Report Engine Crash:", error);
        alert(`An error occurred while generating the report: ${error.message}`);
    } finally {
        const loadingOverlay = document.getElementById('loading-overlay');
        const btn = document.getElementById('generate-report-btn');
        if (loadingOverlay) loadingOverlay.classList.add('hidden');
        btn.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            <span>Export Report</span>
        `;
        btn.disabled = false;
    }
}