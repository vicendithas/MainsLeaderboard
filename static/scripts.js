let shinyOdds = 8192; // Default value

document.addEventListener('DOMContentLoaded', function() {
    // Fetch shiny odds from config
    fetch('/config')
        .then(response => response.json())
        .then(cfg => {
            shinyOdds = cfg.shiny_odds || 8192;
            fetchTotalPokemon();
            fetchLeaderboardData();
            fetchLast10Pokemon();
            fetchLocationPercentages();
            fetchCurrentStreak(); // <-- Updated line
            fetchLongestStreak(); // <-- Added line

            document.getElementById('entryForm').addEventListener('submit', function(event) {
                event.preventDefault();
                addEntry();
            });
        })
        .catch(() => {
            // If config fetch fails, use default odds
            fetchTotalPokemon();
            fetchLeaderboardData();
            fetchLast10Pokemon();
            fetchLocationPercentages();
            fetchCurrentStreak(); // <-- Updated line
            fetchLongestStreak(); // <-- Added line

            document.getElementById('entryForm').addEventListener('submit', function(event) {
                event.preventDefault();
                addEntry();
            });
        });
});

function sanitizeFilename(name) {
    // Convert to lowercase and replace spaces with underscores
    return name.toLowerCase().replace(/ /g, '_');
}

function getGifPath(pokemonName, shinyCheckCallback) {
    // Use shinyOdds from config
    const isShiny = Math.floor(Math.random() * shinyOdds) === 0;
    if (isShiny && typeof shinyCheckCallback === 'function') {
        shinyCheckCallback();
    }
    const folder = isShiny ? 'shiny_gifs' : 'gifs';
    const filename = sanitizeFilename(pokemonName);
    return `/static/${folder}/${filename}.gif`;
}

let shinyMessageShown = false;

function showShinyMessageAndAudio() {
    if (!shinyMessageShown) {
        shinyMessageShown = true;
        const messageElem = document.getElementById('message');
        if (messageElem) {
            messageElem.textContent = '✨ A shiny Pokémon appeared! ✨';
        }
        const audio = new Audio('/static/shiny.mp3');
        audio.play().catch(() => {
            if (messageElem) {
                messageElem.textContent += ' (Click anywhere to hear the shiny sound!)';
            }
            const playShinyAudio = () => {
                audio.play();
                document.removeEventListener('click', playShinyAudio);
            };
            document.addEventListener('click', playShinyAudio);
        });
    }
}

function fetchTotalPokemon() {
    fetch('/total_pokemon')
        .then(response => response.json())
        .then(data => {
            const totalEntriesDiv = document.getElementById('totalEntries');
            totalEntriesDiv.textContent = `Total Pokemon: ${data.total_pokemon}`;
        })
        .catch(error => {
            console.error('Error fetching total Pokemon data:', error);
            document.getElementById('totalEntries').textContent = 'Total Pokemon: Error loading data.';
        });
}

function fetchLeaderboardData() {
    fetch('/leaderboard')
        .then(response => response.json())
        .then(data => {
            const leaderboardTable = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            leaderboardTable.innerHTML = '';

            data.forEach((row, index) => {
                const gifPath = getGifPath(row.Pokemon, showShinyMessageAndAudio);

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
                const gifPath = getGifPath(entry.Pokemon, showShinyMessageAndAudio);

                const newRow = last10Table.insertRow();
                newRow.innerHTML = 
                    `<td>
                        <img src="${gifPath}" alt="${entry.Pokemon}" class="pokemon-gif">
                        ${entry.Pokemon}
                    </td>
                    <td>${entry.Date}</td>
                    <td>${entry.Location}</td>
                    <td>${entry["Days Since Last Ran"] || ""}</td>`;
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

function fetchCurrentStreak() {
    fetch('/current_streak')
        .then(response => response.json())
        .then(data => {
            const streakDiv = document.getElementById('currentStreak');
            streakDiv.textContent = `Current Streak: ${data.current_streak} day${data.current_streak === 1 ? '' : 's'}`;
        })
        .catch(error => {
            console.error('Error fetching current streak:', error);
            document.getElementById('currentStreak').textContent = 'Current Streak: Error loading data.';
        });
}

function fetchLongestStreak() {
    fetch('/longest_streak')
        .then(response => response.json())
        .then(data => {
            const longestStreakDiv = document.getElementById('longestStreak');
            let streakText = `Longest Streak: ${data.longest_streak} day${data.longest_streak === 1 ? '' : 's'}`;
            if (data.start_date && data.end_date) {
                streakText += ` (${data.start_date} - ${data.end_date})`;
            }
            longestStreakDiv.textContent = streakText;
        })
        .catch(error => {
            console.error('Error fetching longest streak:', error);
            document.getElementById('longestStreak').textContent = 'Longest Streak: Error loading data.';
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
            fetchTotalPokemon(); // Update the total Pokemon count
            fetchLeaderboardData();
            fetchLast10Pokemon();
            fetchLocationPercentages();
            fetchCurrentStreak(); // <-- Updated line
            fetchLongestStreak(); // <-- Added line
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

let sortOrder = [true, false, true, true]; // Track sort order for each column (true = ascending)

function sortTable(columnIndex) {
    const table = document.getElementById('leaderboard');
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));

    // Determine the sort direction
    sortOrder[columnIndex] = !sortOrder[columnIndex];

    // Clear existing arrows
    const arrows = ['rankArrow', 'pokemonArrow', 'countArrow', 'lastTimeRanArrow'];
    arrows.forEach((id, index) => {
        const arrow = document.getElementById(id);
        arrow.classList.remove('up', 'down');
        arrow.style.visibility = 'hidden'; // Hide all arrows
    });

    // Sort rows based on the specified column index
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();

        // Handle different column types
        if (columnIndex === 0) { // Rank (numeric sort)
            return sortOrder[columnIndex] ? parseInt(aText) - parseInt(bText) : parseInt(bText) - parseInt(aText);
        } else if (columnIndex === 2) { // Count (numeric sort)
            return sortOrder[columnIndex] ? aText - bText : bText - aText;
        } else if (columnIndex === 3) { // Last Time Ran (date sort)
            const aDate = new Date(aText);
            const bDate = new Date(bText);
            return sortOrder[columnIndex] ? aDate - bDate : bDate - aDate;
        } else { // Alphabetical sort for Pokemon name
            return sortOrder[columnIndex] ? aText.localeCompare(bText) : bText.localeCompare(aText);
        }
    });

    // Update the arrow for the sorted column
    const arrow = document.getElementById(arrows[columnIndex]);
    arrow.style.visibility = 'visible'; // Show the arrow
    arrow.classList.add(sortOrder[columnIndex] ? 'up' : 'down');

    // Remove existing rows and append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

