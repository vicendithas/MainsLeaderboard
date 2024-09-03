document.addEventListener('DOMContentLoaded', function() {
    fetchLeaderboardData();
    fetchLast10Pokemon();
    fetchLocationPercentages();

    document.getElementById('entryForm').addEventListener('submit', function(event) {
        event.preventDefault();
        addEntry();
    });
});

function sanitizeFilename(name) {
    // Convert to lowercase and replace spaces with underscores
    return name.toLowerCase().replace(/ /g, '_');
}

function getGifPath(pokemonName) {
    // 1/8192 chance to use the shiny GIF
    const chance = Math.floor(Math.random() * 8192);
    const folder = chance === 0 ? 'shiny_gifs' : 'gifs';
    const filename = sanitizeFilename(pokemonName);
    return `/static/${folder}/${filename}.gif`;
}

function fetchLeaderboardData() {
    fetch('/leaderboard')
        .then(response => response.json())
        .then(data => {
            const leaderboardTable = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            leaderboardTable.innerHTML = '';

            data.forEach((row, index) => {
                const gifPath = getGifPath(row.Pokemon);

                const newRow = leaderboardTable.insertRow();
                newRow.innerHTML = 
                    `<td>${index + 1}</td>
                    <td>
                        <img src="${gifPath}" alt="${row.Pokemon}" class="pokemon-gif">
                        ${row.Pokemon}
                    </td>
                    <td>${row.Count}</td>
                    <td>${row['Last Time Ran']}</td>`;
            });
        })
        .catch(error => {
            console.error('Error fetching leaderboard data:', error);
        });
}

function fetchLast10Pokemon() {
    fetch('/last10')
        .then(response => response.json())
        .then(data => {
            const last10Table = document.getElementById('last10Table').getElementsByTagName('tbody')[0];
            last10Table.innerHTML = '';

            data.forEach(entry => {
                const gifPath = getGifPath(entry.Pokemon);

                const newRow = last10Table.insertRow();
                newRow.innerHTML = 
                    `<td>
                        <img src="${gifPath}" alt="${entry.Pokemon}" class="pokemon-gif">
                        ${entry.Pokemon}
                    </td>
                    <td>${entry.Date}</td>`;
            });
        })
        .catch(error => {
            console.error('Error fetching last 10 Pokemon data:', error);
        });
}

function fetchLocationPercentages() {
    fetch('/location_percentages')
        .then(response => response.json())
        .then(data => {
            const locationPercentagesTable = document.getElementById('locationPercentages').getElementsByTagName('tbody')[0];
            locationPercentagesTable.innerHTML = '';

            data.forEach(entry => {
                const newRow = locationPercentagesTable.insertRow();
                newRow.innerHTML = 
                    `<td>${entry.Location}</td>
                    <td>${entry.Percentage.toFixed(2)}%</td>`;
            });
        })
        .catch(error => {
            console.error('Error fetching location percentages data:', error);
        });
}

function addEntry() {
    const formData = new FormData(document.getElementById('entryForm'));

    fetch('/add_entry', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetchLeaderboardData();
            fetchLast10Pokemon();
            fetchLocationPercentages();
            document.getElementById('entryForm').reset();
            document.getElementById('message').textContent = 'Entry added successfully.';
        } else {
            document.getElementById('message').textContent = 'Failed to add entry.';
        }
    })
    .catch(error => {
        console.error('Error adding new entry:', error);
        document.getElementById('message').textContent = 'Error adding new entry.';
    });
}

