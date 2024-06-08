import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

var JSON_file = 'data/json/competitions/euro2024_roundOf16.json';

// Déclarer les dimensions du graphique et les marges.
const width = 960;
const height = 500;
const marginTop = 20;
const marginRight = 30;
const marginBottom = 30;
const marginLeft = 40;

// Créer l'échelle x (position horizontale).
const x = d3.scaleUtc()
    .range([marginLeft, width - marginRight]);

// Créer l'échelle y (position verticale).
const y = d3.scaleLinear()
    .range([height - marginBottom, marginTop]);

// Créer le générateur de lignes.
const line = d3.line()
    .x(d => x(d.date))
    .y(d => y(d.champion_pb));

// Créer le conteneur SVG.
const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

// Ajouter l'axe x.
const xAxis = svg.append("g")
    .attr("transform", `translate(0,${height - marginBottom})`);

// Ajouter l'axe y.
const yAxis = svg.append("g")
    .attr("transform", `translate(${marginLeft},0)`);

// Créer un conteneur pour les infobulles.
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

// Charger les données JSON.
d3.json(JSON_file).then(data => {
    // Transformer les données
    const parseDate = d3.utcParse("%Y-%m-%d");

    const teams = data.map(d => ({
        team: d.team,
        values: Object.keys(d)
            .filter(key => key !== "team")
            .map(date => ({ date: parseDate(date), champion_pb: d[date] }))
            .filter(d => !isNaN(d.date) && d.champion_pb !== null)
    }));

    // Définir les domaines des échelles x et y
    const xDomain = d3.extent(data.flatMap(d => Object.keys(d).filter(k => k !== "team").map(date => parseDate(date))));
    const yDomain = [0, d3.max(data.flatMap(d => Object.values(d).filter(value => typeof value === "number")))];

    x.domain(xDomain);
    y.domain(yDomain);

    // Mettre à jour les axes
    xAxis.call(d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0));
    yAxis.call(d3.axisLeft(y));

    // Créer une échelle de couleurs
    const color = d3.scaleOrdinal(d3.schemeCategory10)
        .domain(teams.map(d => d.team));

    // Créer une ligne pour chaque équipe
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
            
            console.log(`Team: ${d.team}`);

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
});

// Charger les données JSON
d3.json(JSON_file).then(data => {
    // Récupérer toutes les dates uniques
    const allDates = Array.from(new Set(data.flatMap(d => Object.keys(d).filter(key => key !== "team"))));

    // Ajouter les en-têtes de colonne pour chaque date
    const tableHeaderRow = d3.select("thead tr");
    allDates.forEach(date => {
      tableHeaderRow.append("th").text(date);
    });

    // Parcourir les données et les ajouter au tableau
    const tableBody = d3.select("#table-body");
    data.forEach(d => {
      const team = d.team;
      // Créer une nouvelle ligne pour chaque équipe
      const newRow = tableBody.append("tr");
      newRow.append("td").text(team);
      allDates.forEach(date => {
        const probability = d[date] !== undefined ? d[date] * 100 : 0; // Convertir la probabilité en pourcentage
        // Créer une cellule de données pour chaque date
        const cell = newRow.append("td").text(probability.toFixed(0) + "%");
        // Appliquer le formatage conditionnel
        var color = 255-d[date]*255
        cell.style("background-color", "rgb("+color+", 255, "+color+")");
      });
    });
  });