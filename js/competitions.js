import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

let JSON_file = 'data/json/competitions/euro2024_champion.json';

// Declare the dimensions of the chart and margins
const width = 960;
const height = 500;
const marginTop = 20;
const marginRight = 30;
const marginBottom = 30;
const marginLeft = 40;

// Create the x scale (horizontal position)
const x = d3.scaleUtc()
    .range([marginLeft, width - marginRight]);

// Create the y scale (vertical position)
const y = d3.scaleLinear()
    .range([height - marginBottom, marginTop]);

// Create the line generator
const line = d3.line()
    .x(d => x(d.date))
    .y(d => y(d.champion_pb));

// Create the SVG container
const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

// Create a container for tooltips
const tooltip = d3.select("#graph").append("div")
    .style("position", "absolute")
    .style("visibility", "hidden")
    .style("background", "white")
    .style("border", "1px solid black")
    .style("padding", "5px")
    .style("border-radius", "5px")
    .style("pointer-events", "none")
    .style("font-family", "Segoe UI")
    .attr("class", "tooltip");

// Function to load and display JSON data
function loadDataAndUpdate(jsonFile, title) {
    d3.json(jsonFile).then(data => {
        // Clear old data
        svg.selectAll("*").remove();
        d3.select("#table-body").html("");
        d3.select("thead tr").html('<th>Team</th>');

        // Transform the data
        const parseDate = d3.utcParse("%Y-%m-%d");
        const teams = data.map(d => ({
            team: d.team,
            values: Object.keys(d)
                .filter(key => key !== "team")
                .map(date => ({ date: parseDate(date), champion_pb: d[date] }))
                .filter(d => !isNaN(d.date) && d.champion_pb !== null)
        }));

        // Define the domains of the x and y scales
        const xDomain = d3.extent(data.flatMap(d => Object.keys(d).filter(k => k !== "team").map(date => parseDate(date))));
        const yDomain = [0, d3.max(data.flatMap(d => Object.values(d).filter(value => typeof value === "number")))];

        x.domain(xDomain);
        y.domain(yDomain);

        // Update the axes
        const xAxis = d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0);
        const yAxis = d3.axisLeft(y);

        svg.append("g")
            .attr("transform", `translate(0,${height - marginBottom})`)
            .call(xAxis);

        svg.append("g")
            .attr("transform", `translate(${marginLeft},0)`)
            .call(yAxis);

        // Create a color scale
        const color = d3.scaleOrdinal(d3.schemeCategory10)
            .domain(teams.map(d => d.team));

        // Create a line for each team
        svg.append("g")
            .selectAll("path")
            .data(teams)
            .enter()
            .append("path")
            .attr("fill", "none")
            .attr("stroke", d => color(d.team))
            .attr("stroke-width", 1.5)
            .attr("d", d => line(d.values))
            .on("mouseover", function(event, d) {
                d3.select(this)
                    .attr("stroke-width", 3);

                tooltip.style("visibility", "visible")
                    .text(`Team: ${d.team}`);
            })
            .on("mousemove", function(event, d) {
                const [xPos, yPos] = d3.pointer(event);
                const date = x.invert(xPos);
                const closestData = d.values.reduce((a, b) => {
                    return Math.abs(b.date - date) < Math.abs(a.date - date) ? b : a;
                });
                const probabilityPercentage = closestData.champion_pb * 100;
                tooltip.style("top", `${event.pageY - 10}px`)
                    .style("left", `${event.pageX + 10}px`)
                    .html(`<b>Team:</b> ${d.team}<br/><b>Date:</b> ${d3.utcFormat("%Y-%m-%d")(closestData.date)}<br/><b>Probability:</b> ${probabilityPercentage.toFixed(0)}%`);
            })
            .on("mouseout", function() {
                d3.select(this)
                    .attr("stroke-width", 1.5);

                tooltip.style("visibility", "hidden");
            });

        document.getElementById('graph').appendChild(svg.node());

        // Update the table
        const allDates = Array.from(new Set(data.flatMap(d => Object.keys(d).filter(key => key !== "team"))));
        const tableHeaderRow = d3.select("thead tr");
        allDates.forEach(date => {
            tableHeaderRow.append("th").text(date);
        });

        const tableBody = d3.select("#table-body");
        data.forEach(d => {
            const team = d.team;
            const newRow = tableBody.append("tr");
            newRow.append("td").text(team);
            allDates.forEach(date => {
                const probability = d[date] !== undefined ? d[date] * 100 : 0;
                const cell = newRow.append("td").text(probability.toFixed(0) + "%");
                const color = 255 - d[date] * 255;
                cell.style("background-color", `rgb(${color}, 255, ${color})`);
            });
        });

        // Update the title
        d3.select("#table-title").text(title);
    });
}

// Attach events to buttons
document.getElementById('champion-btn').addEventListener('click', () => loadDataAndUpdate('data/json/competitions/euro2024_champion.json', 'Champion Probability'));
document.getElementById('final-btn').addEventListener('click', () => loadDataAndUpdate('data/json/competitions/euro2024_final.json', 'Final Probability'));
document.getElementById('semi-final-btn').addEventListener('click', () => loadDataAndUpdate('data/json/competitions/euro2024_semiFinal.json', 'Semi Final Probability'));
document.getElementById('quarter-final-btn').addEventListener('click', () => loadDataAndUpdate('data/json/competitions/euro2024_quarterFinal.json', 'Quarter Final Probability'));
document.getElementById('round-of-16-btn').addEventListener('click', () => loadDataAndUpdate('data/json/competitions/euro2024_roundOf16.json', 'Round of 16 Probability'));

// Load initial data
loadDataAndUpdate(JSON_file, 'Champion Probability');