document.addEventListener('DOMContentLoaded', function () {
    // Extract team name from the URL
    const teamName = decodeURIComponent(new URLSearchParams(window.location.search).get('team'));

    // Default JSON file path for team results (adjust as needed)
    const jsonFilePath = `data/json/matches/${teamName}.json`;

    // Modifiy page name and h1 title
    document.title = `${teamName} Results`;
    document.getElementById('h1title').textContent = teamName + " Results";

    // Function to load team results JSON file
    async function loadTeamResultsJSON(filePath) {
        const response = await fetch(filePath);
        const jsonData = await response.json();
        return jsonData;
    }

    // Reference to team results table body
    const teamResultsBody = document.getElementById('team-results-body');

    // Initial JSON loading
    loadTeamResultsJSON(jsonFilePath).then(teamResultsData => {
        // console.log('Team Results Data:', teamResultsData);

        // Extracting flag value for title
        const firstLine = teamResultsData.matches[0];
        const flag1Value = firstLine.flag1;
        const flagA = document.getElementById('flagTitle');
        if (flagA) {
            flagA.innerHTML = `<img src="img/flags/${flag1Value}" alt="${teamName}">`;
        }

        const matchesArray = teamResultsData.matches || [];
        // Loop through team results data and construct table rows
        matchesArray.forEach(match => {
            var color;
            if(match.score1 - match.score2 > 0) {
            color = 'green';
            }
            else if (match.score1 - match.score2 < 0) {
            color = 'red';
            }
            else {
            color = 'black';
            }
            const row = document.createElement('tr');
            row.innerHTML = `
            <td>${match.date}</td>
            <td>${match.country}</td>
            <td>${match.tournament}</td>
            <td>vs <a href="matches.html?team=${match.team2.replace(/&/g, "%26")}"><img class="flag" src="img/flags/${match.flag2}" alt="${match.team2}"></a> <a href="matches.html?team=${match.team2}">${match.original_team2}</a></td>
            <td>${Math.round(match.rating1-match.rating_ev)}</td>
            <td>${Math.round(match.rating2+match.rating_ev)}</td>
            <td>
                <div class="percentage-indicator" data-percent="${match.win_prob}">
                    <div class="fill"></div>
                        <span class="text">${match.win_prob} %</span>
                </div>
            </td>
            <td class="match" style="color:${color};"><b>${match.score1} - ${match.score2}</b></td>
            <td>${Math.round(match.rating1)} (${match.rating_ev >= 0 ? '+' : ''}${Math.round(match.rating_ev)})</td>
            `;
            teamResultsBody.appendChild(row);
        });

        // % Win Gauge Indicator
        const percentageIndicators = document.querySelectorAll('.percentage-indicator');

        percentageIndicators.forEach(indicator => {
            const percentValue = parseFloat(indicator.getAttribute('data-percent'));
            const fillElement = document.createElement('div');
            fillElement.classList.add('fill');
            fillElement.classList.add('lv-'+Math.ceil(percentValue/20).toString());
            fillElement.style.width = percentValue + '%';
            indicator.innerHTML = '';
            indicator.appendChild(fillElement);
            indicator.innerHTML += `<span class="text">${percentValue}%</span>`;
        });
    });
});