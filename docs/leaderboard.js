
function parseCSV(text) {
    const lines = text.trim().split(/\r?\n/);

    if (lines.length < 2) {
        return [];
    }

    const headers = lines[0].split(",").map(h => h.trim());

    return lines.slice(1)
        .filter(line => line.trim())
        .map(line => {
            const values = line.split(",");
            const row = {};

            headers.forEach((header, index) => {
                row[header] = (values[index] || "").trim();
            });

            return row;
        });
}


async function main() {

    const tbody = document.querySelector("#tbl tbody");
    const status = document.getElementById("status");

    try {

        const response = await fetch("leaderboard.csv", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`CSV loading failed: ${response.status}`);
        }

        const csvText = await response.text();

        const rows = parseCSV(csvText);

        const cleaned = rows
            .filter(row => row.team && !isNaN(parseFloat(row.score)))
            .sort((a, b) => parseFloat(b.score) - parseFloat(a.score));

        tbody.innerHTML = "";

        cleaned.forEach((row, index) => {

            const tr = document.createElement("tr");

            const values = [
                index + 1,
                row.team,
                parseFloat(row.score).toFixed(8),
                row.timestamp_utc
            ];

            values.forEach(value => {
                const td = document.createElement("td");
                td.textContent = value;
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });

        // Update statistics
        const scores = cleaned.map(row => parseFloat(row.score));

        document.getElementById("statParticipants").textContent =
            new Set(cleaned.map(row => row.team)).size;

        document.getElementById("statBest").textContent =
            scores.length ? Math.max(...scores).toFixed(4) : "–";

        document.getElementById("statAvg").textContent =
            scores.length
                ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(4)
                : "–";

        status.textContent = `${cleaned.length} result(s)`;

    } catch (error) {

        status.textContent = "Failed to load leaderboard.";
        console.error(error);

    }
}

main();
