// Utilitaires pour les drapeaux
function flagImgFromFile(flag, team) {
    if (!flag) return '';
    return `<img src="img/flags/${flag}" alt="${team}" class="flag mr-1" style="height:1.5em;">`;
}

// Liste des équipes chargée dynamiquement
let teamsList = [];
let rankingsMap = {}; // Pour accès rapide aux points/rank/flag

async function loadTeamsList() {
    const resp = await fetch('data/json/rankings/LatestRankings.json');
    const data = await resp.json();
    teamsList = data.rankings.map(r => r.team);
    rankingsMap = {};
    data.rankings.forEach(r => {
        rankingsMap[r.team] = r;
    });
}

function populateTeamSelects() {
    const team1Select = document.getElementById('team1Select');
    const team2Select = document.getElementById('team2Select');
    team1Select.innerHTML = teamsList.map(t => `<option value="${t}">${t}</option>`).join('');
    team2Select.innerHTML = teamsList.map(t => `<option value="${t}">${t}</option>`).join('');
    team1Select.value = "France";
    team2Select.value = "Argentina";
}

// Chargement des JSON d'équipes
async function loadTeamData(team) {
    const resp = await fetch(`data/json/matches/${team}.json`);
    return await resp.json();
}

// Calcul de la proba selon la formule Python
function calcExpectedResult(points1, points2, neutral) {
    let expected_result = ((1/(1+Math.exp(-1*(points1-points2)/850))-0.5)*33+1.25*(neutral ? 0 : 1))/6.5;
    expected_result = Math.max(-2.5, Math.min(2.5, expected_result));
    return expected_result;
}
function calcWinProb(expected_result) {
    return Math.round((1/(1+Math.exp(-expected_result*2.95))*1000))/10;
}

// Affichage du panel équipe (gauche/droite)
function renderTeamPanel(teamData, side) {
    if (!teamData) return '';
    const lastMatch = teamData.matches.find(m => m.type === 'past');
    const lastPoints = lastMatch ? lastMatch.rating1 : '?';
    const latestRank = rankingsMap[teamData.team]?.rank ?? (lastMatch?.rank ?? '?');
    // Trie les matchs par date décroissante et prend les 10 plus récents
    const last10 = teamData.matches
        .filter(m => m.type === 'past')
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 10);

    // Calcule les stats sur les 10 derniers matchs
    let sumPts = 0, sumOppLevel = 0, sumEv = 0, count = 0;
    for (const match of last10) {
        // Points du match
        let pts = 0;
        if (typeof match.score1 === 'number' && typeof match.score2 === 'number') {
            if (match.score1 > match.score2) pts = 3;
            else if (match.score1 === match.score2) pts = 1;
            // sinon 0
        }
        sumPts += pts;
        // Niveau adversaire
        if (typeof match.rating2 === 'number') sumOppLevel += match.rating2;
        // Evolution points
        if (typeof match.rating_ev === 'number') sumEv += match.rating_ev;
        count++;
    }
    const avgPts = count ? (sumPts / count).toFixed(2) : '?';
    const avgOpp = count ? Math.round(sumOppLevel / count) : '?';
    const totalEv = count ? (sumEv > 0 ? '+' : '') + sumEv : '?';

    let html = `
        <div class="d-flex align-items-center mb-2">
            <h5 class="mb-0">${teamData.team}</h5>
        </div>
        <div class="mb-2">
            <div class="stats-cards">
                <div class="stats-card"><span class="icon">⭐</span>
                    <div>
                        <div style="font-size:0.9em;color:#888;">Latest points</div>
                        <strong>${lastPoints}</strong>
                    </div>
                </div>
                <div class="stats-card"><span class="icon">🏆</span>
                    <div>
                        <div style="font-size:0.9em;color:#888;">Latest ranking</div>
                        <strong>${latestRank}</strong>
                    </div>
                </div>
                <div class="stats-card"><span class="icon">📊</span>
                    <div>
                        <div style="font-size:0.9em;color:#888;">Avg points (last 10)</div>
                        <strong>${avgPts}</strong>
                    </div>
                </div>
                <div class="stats-card"><span class="icon">🎯</span>
                    <div>
                        <div style="font-size:0.9em;color:#888;">Avg opponent level</div>
                        <strong>${avgOpp}</strong>
                    </div>
                </div>
                <div class="stats-card"><span class="icon">🔺</span>
                    <div>
                        <div style="font-size:0.9em;color:#888;">Total Δpts</div>
                        <strong>${totalEv}</strong>
                    </div>
                </div>
            </div>
        </div>
        <div class="mb-2">Last 10 matches:</div>
        <div class="table-responsive">
        <table class="table table-sm mb-2" style="font-size:0.75em;">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>${side === 'left' ? 'Home' : 'Away'}</th>
                    <th>Score</th>
                    <th>${side === 'left' ? 'Away' : 'Home'}</th>
                    <th>Venue</th>
                    <th>Tournament</th>
                    <th>Δpts</th>
                    <th>Rank</th>
                </tr>
            </thead>
            <tbody>
    `;
    for (const match of last10) {
        let leftTeam, rightTeam, leftScore, rightScore, leftFlag, rightFlag;
        if (match.country === match.team1) {
            leftTeam = match.team1;
            rightTeam = match.original_team2;
            leftScore = match.score1;
            rightScore = match.score2;
            leftFlag = match.flag1;
            rightFlag = match.flag2;
        } else if (match.country === match.team2) {
            leftTeam = match.original_team2;
            rightTeam = match.team1;
            leftScore = match.score2;
            rightScore = match.score1;
            leftFlag = match.flag2;
            rightFlag = match.flag1;
        } else {
            if (side === 'left') {
                leftTeam = match.team1;
                rightTeam = match.original_team2;
                leftScore = match.score1;
                rightScore = match.score2;
                leftFlag = match.flag1;
                rightFlag = match.flag2;
            } else {
                leftTeam = match.original_team2;
                rightTeam = match.team1;
                leftScore = match.score2;
                rightScore = match.score1;
                leftFlag = match.flag2;
                rightFlag = match.flag1;
            }
        }
        const venue = match.country || '';
        const tournament = match.tournament || '';
        let ratingEv = match.rating_ev;
        const pts = ratingEv !== undefined && ratingEv !== null && ratingEv !== "" ? (ratingEv > 0 ? '+' : '') + ratingEv : '';
        const rank = match.rank ?? '';
        html += `
            <tr>
                <td>${match.date}</td>
                <td>${flagImgFromFile(leftFlag, leftTeam)} ${leftTeam}</td>
                <td class="font-weight-bold">${leftScore} - ${rightScore}</td>
                <td>${flagImgFromFile(rightFlag, rightTeam)} ${rightTeam}</td>
                <td>${venue}</td>
                <td>${tournament}</td>
                <td>${pts}</td>
                <td>${rank}</td>
            </tr>
        `;
    }
    html += `
            </tbody>
        </table>
        </div>
    `;
    return html;
}

// Affichage du donut ou de l'historique cumulé
function renderDonutOrHistory(prob1, prob2, h2hStats, donutMode, team1, team2) {
    const donutDiv = document.getElementById('donutContainer');
    donutDiv.innerHTML = '';
    // Détruit l'ancien graphique s'il existe
    if (window.apexDonutChart) {
        window.apexDonutChart.destroy();
        window.apexDonutChart = null;
    }
    if (!donutMode) {
        const options = {
            chart: { type: 'donut', height: 300 },
            series: [prob2, prob1],
            labels: [team2, team1],
            colors: ['#008FFB', '#FF4560'],
            dataLabels: { formatter: (val) => val.toFixed(1) + '%' },
            legend: { show: false }
        };
        window.apexDonutChart = new ApexCharts(donutDiv, options);
        window.apexDonutChart.render();
    } else {
        const options = {
            chart: { type: 'donut', height: 300 },
            series: [h2hStats.win2, h2hStats.draw, h2hStats.win1],
            labels: [`Wins ${team2}`, 'Draws', `Wins ${team1}`],
            colors: ['#008FFB', '#999', '#FF4560'],
            dataLabels: { formatter: (val) => val.toFixed(1) + '%' },
            legend: { show: false }
        };
        window.apexDonutChart = new ApexCharts(donutDiv, options);
        window.apexDonutChart.render();
    }
}

// Affichage de l'historique des confrontations
function renderHeadToHead(matches, team1, team2) {
    // On ne prend que les matches de team1 contre team2
    const filtered = matches
        .filter(m => m.original_team2 === team2)
        .sort((a, b) => new Date(b.date) - new Date(a.date));
    if (!filtered.length) return '<div class="alert alert-info">No direct match found.</div>';
    let html = `<table class="table table-bordered table-sm align-middle">
        <thead>
            <tr>
                <th>Date</th>
                <th>Venue</th>
                <th>Tournament</th>
                <th>Home</th>
                <th>Score</th>
                <th>Away</th>
                <th>Δpts</th>
                <th>Rank</th>
            </tr>
        </thead>
        <tbody>
    `;
    for (const m of filtered) {
        let homeTeam, awayTeam, homeScore, awayScore, homeFlag, awayFlag;
        if (m.country === m.team1) {
            homeTeam = m.team1;
            awayTeam = m.original_team2;
            homeScore = m.score1;
            awayScore = m.score2;
            homeFlag = m.flag1;
            awayFlag = m.flag2;
        } else if (m.country === m.team2) {
            homeTeam = m.original_team2;
            awayTeam = m.team1;
            homeScore = m.score2;
            awayScore = m.score1;
            homeFlag = m.flag2;
            awayFlag = m.flag1;
        } else {
            homeTeam = m.team1;
            awayTeam = m.original_team2;
            homeScore = m.score1;
            awayScore = m.score2;
            homeFlag = m.flag1;
            awayFlag = m.flag2;
        }
        const venue = m.country || '';
        const delta = m.rating_ev !== undefined && m.rating_ev !== null && m.rating_ev !== "" ? (m.rating_ev > 0 ? '+' : '') + m.rating_ev : '';
        html += `<tr>
            <td>${m.date}</td>
            <td>${venue}</td>
            <td>${m.tournament}</td>
            <td class="text-end">${flagImgFromFile(homeFlag, homeTeam)}${homeTeam}</td>
            <td class="text-center">${homeScore} - ${awayScore}</td>
            <td class="text-start">${flagImgFromFile(awayFlag, awayTeam)}${awayTeam}</td>
            <td>${delta}</td>
            <td>${m.rank ?? ''}</td>
        </tr>`;
    }
    html += '</tbody></table>';
    return html;
}

// Calcul de l'historique cumulé
function computeH2HStats(matches, team1) {
    let win1 = 0, win2 = 0, draw = 0;
    for (const m of matches) {
        if (m.score1 > m.score2) {
            if (m.team1 === team1) win1++; else win2++;
        } else if (m.score1 < m.score2) {
            if (m.team1 === team1) win2++; else win1++;
        } else {
            draw++;
        }
    }
    const total = win1 + win2 + draw || 1;
    return {
        win1: Math.round(win1/total*1000)/10,
        win2: Math.round(win2/total*1000)/10,
        draw: Math.round(draw/total*1000)/10
    };
}

// Rafraîchit toute la page
async function refreshAll() {
    const team1 = document.getElementById('team1Select').value;
    const team2 = document.getElementById('team2Select').value;
    const neutral = document.getElementById('neutralToggle').checked;
    const donutMode = document.getElementById('toggleDonutMode').checked;

    // Charge les données
    const [data1, data2] = await Promise.all([loadTeamData(team1), loadTeamData(team2)]);
    data1.team = team1;
    data2.team = team2;

    // Derniers points
    // Utilise le ranking officiel si dispo, sinon le dernier match
    const lastPoints1 = rankingsMap[team1]?.points ?? (data1.matches.find(m => m.type === 'past')?.rating1 ?? 0);
    const lastPoints2 = rankingsMap[team2]?.points ?? (data2.matches.find(m => m.type === 'past')?.rating1 ?? 0);

    // Calcul proba
    const expected_result = calcExpectedResult(lastPoints1, lastPoints2, neutral);
    const prob1 = calcWinProb(expected_result);
    const prob2 = Math.round((100 - prob1)*10)/10;

    // Historique des confrontations
    const h2hMatches = [
        ...data1.matches.filter(m => m.original_team2 === team2),
        ...data2.matches.filter(m => m.original_team2 === team1)
    ].sort((a, b) => new Date(b.date) - new Date(a.date));

    // Stats cumulées
    const h2hStats = computeH2HStats(h2hMatches, team1);

    // Affichage panels
    document.getElementById('team1Panel').innerHTML = renderTeamPanel(data1, 'left');
    document.getElementById('team2Panel').innerHTML = renderTeamPanel(data2, 'right');

    // Affichage donut/historique cumulé
    renderDonutOrHistory(prob1, prob2, h2hStats, donutMode, team1, team2);

    // Affiche ou masque le switch "Neutral ground" selon le mode
    const neutralSwitchWrapper = document.getElementById('neutralSwitchWrapper');
    if (neutralSwitchWrapper) {
        neutralSwitchWrapper.style.display = donutMode ? 'none' : '';
    }

    // Affichage historique des confrontations
    document.getElementById('headToHeadHistory').innerHTML = renderHeadToHead(h2hMatches, team1, team2);
}

// Listeners
document.addEventListener('DOMContentLoaded', async () => {
    await loadTeamsList();
    populateTeamSelects();
    refreshAll();
    document.getElementById('team1Select').addEventListener('change', refreshAll);
    document.getElementById('team2Select').addEventListener('change', refreshAll);
    document.getElementById('neutralToggle').addEventListener('change', refreshAll);
    document.getElementById('toggleDonutMode').addEventListener('change', refreshAll);

    // Dark mode switch (comme dans matches)
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.textContent = '☀️';
        }
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            themeToggle.textContent = isDark ? '☀️' : '🌙';
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }
});