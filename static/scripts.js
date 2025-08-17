let shinyOdds = 8192; // Default value

document.addEventListener('DOMContentLoaded', function() {
    // Fetch shiny odds from config
    fetch('/config')
        .then(response => response.json())
        .then(cfg => {
            shinyOdds = cfg.shiny_odds || 8192;
            fetchTotalPokemon();
            fetchAverageBst();
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
            fetchAverageBst();
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

function fetchAverageBst() {
    fetch('/average_bst')
        .then(response => response.json())
        .then(data => {
            const averageBstDiv = document.getElementById('averageBst');
            averageBstDiv.textContent = `Average BST: ${data.average_bst}`;
        })
        .catch(error => {
            console.error('Error fetching average BST data:', error);
            document.getElementById('averageBst').textContent = 'Average BST: Error loading data.';
        });
}

let showTimeSinceLast = false; // Start with Runs Since Last Ran
let showTimeSinceLastLeaderboard = false; // Separate toggle for leaderboard

function toggleSinceLastColumn() {
    showTimeSinceLast = !showTimeSinceLast;
    const header = document.getElementById('sinceLastHeader');
    header.innerHTML = `🔄 ${showTimeSinceLast ? 'Time Since Last Ran' : 'Runs Since Last Ran'}`;
    
    // Update only the column instead of refreshing the whole table
    updateLast10SinceLastColumn();
}

function updateLast10SinceLastColumn() {
    const last10Table = document.getElementById('last10Table').getElementsByTagName('tbody')[0];
    const rows = last10Table.getElementsByTagName('tr');
    
    fetch('/last10')
        .then(response => response.json())
        .then(data => {
            // Update only the 4th column (index 3) for each row
            for (let i = 0; i < rows.length && i < data.length; i++) {
                const entry = data[i];
                const sinceLastValue = showTimeSinceLast ? 
                    (entry["Time Since Last Ran"] || "") : 
                    (entry["Runs Since Last Ran"] || "");
                
                // Update only the last cell (column 3)
                rows[i].cells[3].textContent = sinceLastValue;
            }
        })
        .catch(error => {
            console.error('Error updating last 10 column:', error);
        });
}

function updateLeaderboardSinceLastColumn() {
    const leaderboardTable = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
    const rows = leaderboardTable.getElementsByTagName('tr');
    
    // We need to fetch the leaderboard data to get the current values
    fetch('/leaderboard')
        .then(response => response.json())
        .then(data => {
            // Create a lookup map: Pokemon name -> data
            const pokemonDataMap = {};
            data.forEach(row => {
                pokemonDataMap[row.Pokemon] = row;
            });
            
            // Update only the 6th column (index 5) for each row based on Pokemon name
            for (let i = 0; i < rows.length; i++) {
                // Get the Pokemon name from the current row (it's in the 2nd column, after the img tag)
                const pokemonCell = rows[i].cells[1];
                const pokemonName = pokemonCell.textContent.trim();
                
                // Find the corresponding data for this Pokemon
                const pokemonData = pokemonDataMap[pokemonName];
                if (pokemonData) {
                    const sinceLastValue = showTimeSinceLastLeaderboard ? 
                        (pokemonData["Time Since Last Ran"] || "") : 
                        (pokemonData["Runs Since Last Ran"] || "");
                    
                    // Update only the last cell (column 5)
                    rows[i].cells[5].textContent = sinceLastValue;
                }
            }
        })
        .catch(error => {
            console.error('Error updating leaderboard column:', error);
        });
}

function toggleLeaderboardSinceLastColumn() {
    showTimeSinceLastLeaderboard = !showTimeSinceLastLeaderboard;
    const header = document.getElementById('leaderboardSinceLastHeader');
    header.innerHTML = `🔄 ${showTimeSinceLastLeaderboard ? 'Time Since Last Ran' : 'Runs Since Last Ran'}`;
    
    // Update only the column instead of refreshing the whole table
    updateLeaderboardSinceLastColumn();
}

function fetchLeaderboardData() {
    fetch('/leaderboard')
        .then(response => response.json())
        .then(data => {
            const leaderboardTable = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            leaderboardTable.innerHTML = '';

            data.forEach((row, index) => {
                const gifPath = getGifPath(row.Pokemon, showShinyMessageAndAudio);

                // Choose which value to display based on current toggle state
                const sinceLastValue = showTimeSinceLastLeaderboard ? 
                    (row["Time Since Last Ran"] || "") : 
                    (row["Runs Since Last Ran"] || "");

                const newRow = leaderboardTable.insertRow();
                newRow.innerHTML = 
                    `<td>${index + 1}</td>
                    <td>
                        <img src="${gifPath}" alt="${row.Pokemon}" class="pokemon-gif">
                        <span class="pokemon-name-clickable" onclick="showPokemonEntries('${row.Pokemon.replace(/'/g, "\\'")}')">${row.Pokemon}</span>
                    </td>
                    <td>${row.BST}</td>
                    <td>${row.Count}</td>
                    <td>${row['Last Time Ran']}</td>
                    <td>${sinceLastValue}</td>`;
            });
        })
        .catch(error => {
            console.error('Error fetching leaderboard data:', error);
        });
}

function showPokemonEntries(pokemonName) {
    fetch(`/pokemon_entries/${encodeURIComponent(pokemonName)}`)
        .then(response => response.json())
        .then(data => {
            const modal = document.getElementById('pokemonModal');
            const modalPokemonName = document.getElementById('modalPokemonName');
            const modalPokemonGif = document.getElementById('modalPokemonGif');
            const modalLocationTableBody = document.getElementById('modalLocationTable').getElementsByTagName('tbody')[0];
            const modalEntriesTableBody = document.getElementById('modalEntriesTable').getElementsByTagName('tbody')[0];
            
            // Set the modal title
            modalPokemonName.textContent = `${pokemonName} - All Entries (${data.total_entries} total)`;
            
            // Set the Pokemon GIF
            const gifPath = getGifPath(pokemonName, showShinyMessageAndAudio);
            modalPokemonGif.src = gifPath;
            modalPokemonGif.alt = pokemonName;
            
            // Clear existing content
            modalLocationTableBody.innerHTML = '';
            modalEntriesTableBody.innerHTML = '';
            
            // Populate location percentages table
            data.location_percentages.forEach(locationData => {
                const newRow = modalLocationTableBody.insertRow();
                newRow.innerHTML = `
                    <td>${locationData.location}</td>
                    <td>${locationData.count}</td>
                    <td>${locationData.percentage.toFixed(1)}%</td>
                `;
            });
            
            // Populate entries table
            data.entries.forEach(entry => {
                const newRow = modalEntriesTableBody.insertRow();
                newRow.innerHTML = `
                    <td>${entry.Date}</td>
                    <td>${entry.Location}</td>
                    <td>${entry.Notes || ''}</td>
                `;
            });
            
            // Show the modal and prevent background scrolling
            modal.style.display = 'block';
            document.body.classList.add('modal-open');
        })
        .catch(error => {
            console.error('Error fetching Pokemon entries:', error);
        });
}

// Modal close functionality
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    // Add modal close handlers
    const modal = document.getElementById('pokemonModal');
    const closeBtn = document.querySelector('.close');
    
    // Function to close modal and restore background scrolling
    function closeModal() {
        modal.style.display = 'none';
        document.body.classList.remove('modal-open');
    }
    
    // Close modal when clicking the X
    closeBtn.onclick = closeModal;
    
    // Close modal when clicking outside of it
    window.onclick = function(event) {
        if (event.target === modal) {
            closeModal();
        }
    }
    
    // Close modal when pressing Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            closeModal();
        }
    });
    
    // Prevent scroll propagation from modal content
    const modalContent = document.querySelector('.modal-content');
    modalContent.addEventListener('wheel', function(event) {
        // Only prevent propagation if we're at the scroll limits
        const isAtTop = modalContent.scrollTop === 0;
        const isAtBottom = modalContent.scrollTop >= modalContent.scrollHeight - modalContent.clientHeight;
        
        if ((isAtTop && event.deltaY < 0) || (isAtBottom && event.deltaY > 0)) {
            event.preventDefault();
        }
    });
});

function fetchLast10Pokemon() {
    fetch('/last10')
        .then(response => response.json())
        .then(data => {
            const last10Table = document.getElementById('last10Table').getElementsByTagName('tbody')[0];
            last10Table.innerHTML = '';

            data.forEach(entry => {
                const gifPath = getGifPath(entry.Pokemon, showShinyMessageAndAudio);
                
                // Choose which value to display based on current toggle state
                const sinceLastValue = showTimeSinceLast ? 
                    (entry["Time Since Last Ran"] || "") : 
                    (entry["Runs Since Last Ran"] || "");

                const newRow = last10Table.insertRow();
                newRow.innerHTML = 
                    `<td>
                        <img src="${gifPath}" alt="${entry.Pokemon}" class="pokemon-gif">
                        ${entry.Pokemon}
                    </td>
                    <td>${entry.Date}</td>
                    <td>${entry.Location}</td>
                    <td>${sinceLastValue}</td>`;
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
            fetchAverageBst(); // Update the average BST
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

let sortOrder = [true, false, false, false, false]; // Track sort order for each column (added one more for new column)

function sortTable(columnIndex) {
    // Prevent sorting on the toggle column (index 5)
    if (columnIndex === 5) {
        return;
    }
    
    const table = document.getElementById('leaderboard');
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));

    // Store original order for tiebreaking
    rows.forEach((row, index) => {
        row.setAttribute('data-original-order', index);
    });

    // Determine the sort direction
    sortOrder[columnIndex] = !sortOrder[columnIndex];

    // Clear existing arrows
    const arrows = ['rankArrow', 'pokemonArrow', 'bstArrow', 'countArrow', 'lastTimeRanArrow'];
    arrows.forEach((id, index) => {
        const arrow = document.getElementById(id);
        arrow.classList.remove('up', 'down');
        arrow.style.visibility = 'hidden'; // Hide all arrows
    });

    // Sort rows based on the specified column index
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();

        let comparison = 0;

        // Handle different column types
        if (columnIndex === 0) { // Rank (numeric sort)
            comparison = parseInt(aText) - parseInt(bText);
        } else if (columnIndex === 2 || columnIndex === 3) { // BST, Count (numeric sort)
            comparison = parseInt(aText) - parseInt(bText);
        } else if (columnIndex === 4) { // Last Time Ran (date sort)
            const aDate = new Date(aText);
            const bDate = new Date(bText);
            comparison = aDate - bDate;
            
            // If dates are equal, use original order as tiebreaker (most recent CSV entry first)
            if (comparison === 0) {
                const aOriginalOrder = parseInt(a.getAttribute('data-original-order'));
                const bOriginalOrder = parseInt(b.getAttribute('data-original-order'));
                comparison = aOriginalOrder - bOriginalOrder;
            }
        } else { // Alphabetical sort for Pokemon name
            comparison = aText.localeCompare(bText);
        }

        // Apply sort direction
        return sortOrder[columnIndex] ? comparison : -comparison;
    });

    // Update the arrow for the sorted column (only for columns that have arrows)
    if (columnIndex < arrows.length) {
        const arrow = document.getElementById(arrows[columnIndex]);
        arrow.style.visibility = 'visible'; // Show the arrow
        arrow.classList.add(sortOrder[columnIndex] ? 'up' : 'down');
    }

    // Remove existing rows and append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => {
        row.removeAttribute('data-original-order'); // Clean up
        tbody.appendChild(row);
    });
}

