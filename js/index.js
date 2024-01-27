document.addEventListener('DOMContentLoaded', function () {
    const yearSelect = document.getElementById('yearSelect');
    const currentYear = new Date().getFullYear();

    // Add an option for the current year (Last)
    const lastOption = document.createElement('option');
    lastOption.value = 'last';
    lastOption.textContent = 'Last';
    yearSelect.appendChild(lastOption);

    // Add options for years from 1872 to current year
    for (let year = currentYear-1; year >= 1872; year--) {
        const option = document.createElement('option');
        option.value = year.toString();
        option.textContent = year.toString();
        yearSelect.appendChild(option);
    }

    // Default JSON file path
    let jsonFilePath = 'data/json/years/LastRankings.json';

    // Function to load the JSON file
    async function loadJSON(filePath) {
        const response = await fetch(filePath);
        const jsonData = await response.json();
        return jsonData;
    }

    // Reference to table body
    const tableBody = document.getElementById('table-body');

    // Initial JSON loading
    loadJSON(jsonFilePath).then(jsonData => {
       // console.log('Year Ranking Data:', jsonData)
       // console.log(jsonData.year);
       // console.log(jsonData.last_date[0]);

       lastDateSpan = document.getElementById('lastDate');
       lastDateSpan.textContent = jsonData.last_date[0];

       const rankingArray = jsonData.rankings || [];
        // Loops through JSON data and constructs array rows
        rankingArray.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
            <td>${item.ranking}</td>
            <td data-toggle="tooltip" title="${item.ranking_change >= 0 ? '+' : ''}${item.ranking_change}">
                ${item.ranking_change !== 0 ? `<i class="${item.ranking_change > 0 ? 'text-success' : 'text-danger'} fa fa-chevron-${item.ranking_change > 0 ? 'up style="color=green"' : 'down style="color=red"'}"></i>` : '<i class="fa fa-chevron-right" aria-hidden="true" style="color=gray"></i>'}
            </td>
            <td><img src="img/flags/${item.flag}" alt="${item.team}" width="30"></td>
            <td><a href="matches.html?team=${item.reference_team.replace(/&/g, "%26")}">${item.team}</a></td>
            <td>${item.points}</td>
            <td>${item.points_change}</td>
            <td>${item.confederation}</td>
            `;
            tableBody.appendChild(row);
        });

        // Activate DataTables on the array with Select
        const dataTable = $('#myTable').DataTable({
            //select: true  // Activate Select functionality
        });

        // Add an event manager to change the year
        yearSelect.addEventListener('change', function () {
            const selectedYear = this.value;
            if (selectedYear === 'last') {
                jsonFilePath = 'data/json/years/LastRankings.json';
            } else {
                jsonFilePath = `data/json/years/${selectedYear}Rankings.json`;
            };
            console.log(selectedYear);

            // Empty existing table
            dataTable.clear().draw();

            // Load the new JSON and update the table
            loadJSON(jsonFilePath).then(newJsonData => {
                // console.log(newJsonData.year);
                // console.log(newJsonData.last_date[0]);

                lastDateSpan.textContent = newJsonData.last_date[0];

                const rankingArray = newJsonData.rankings || [];
                rankingArray.forEach(newItem => {
                    const newRow = dataTable.row.add([
                        newItem.ranking,
                        `<a data-toggle="tooltip" title="${newItem.ranking_change >= 0 ? '+' : ''}${newItem.ranking_change}">
                        ${newItem.ranking_change !== 0 ? `<i class="${newItem.ranking_change > 0 ? 'text-success' : 'text-danger'} fa fa-chevron-${newItem.ranking_change > 0 ? 'up style="color=green"' : 'down style="color=red"'}"></i>` : '<i class="fa fa-chevron-right" aria-hidden="true" style="color=gray"></i>'}
                        </a>`,
                        `<img src="img/flags/${newItem.flag}" alt="${newItem.team}" width="30">`,
                        `<a href="matches.html?team=${newItem.reference_team.replace(/&/g, "%26")}">${newItem.team}</a>`,
                        newItem.points,
                        newItem.points_change,
                        newItem.confederation
                    ]).draw(false).node();
                });
            });
        });
    });
});