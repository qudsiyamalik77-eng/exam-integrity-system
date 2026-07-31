document.addEventListener("DOMContentLoaded", () => {
    // 1. Render Chart.js Vector Graph
    const ctx = document.getElementById('cheatingChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Tab Switching', 'Copy/Paste', 'Window Focus Loss', 'Multiple Logins', 'AI Pattern Match', 'Unusual Speed'],
            datasets: [{
                label: 'Detected Incidents',
                data: [42, 28, 35, 12, 19, 8],
                backgroundColor: '#3b82f6',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    // 2. Populate Flagged Candidates Table
    const mockData = [
        { id: "EMP-102", name: "Taiba Malik", integrity: "45%", suspicion: "89/100", flag: "Tab Switching + Copy/Paste", badge: "bg-rose-500/10 text-rose-500 border-rose-500/20" },
        { id: "EMP-115", name: "Adeeba", integrity: "62%", suspicion: "74/100", flag: "Rapid Typing Pattern", badge: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
        { id: "EMP-128", name: "Aqsa Sajjad", integrity: "71%", suspicion: "65/100", flag: "Window Focus Lost", badge: "bg-amber-500/10 text-amber-500 border-amber-500/20" }
    ];

    const tbody = document.getElementById("flagged-table-body");
    tbody.innerHTML = mockData.map(row => `
        <tr class="hover:bg-slate-800/50 transition">
            <td class="p-4 font-mono text-xs text-slate-400">${row.id}</td>
            <td class="p-4 font-semibold">${row.name}</td>
            <td class="p-4"><span class="px-2.5 py-1 rounded-md text-xs font-bold border ${row.badge}">${row.integrity}</span></td>
            <td class="p-4 font-semibold text-rose-400">${row.suspicion}</td>
            <td class="p-4 text-slate-300 text-xs">${row.flag}</td>
            <td class="p-4 text-right">
                <button onclick="window.location.href='session-detail.html?id=${row.id}'" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition">
                    Review Report
                </button>
            </td>
        </tr>
    `).join('');
});