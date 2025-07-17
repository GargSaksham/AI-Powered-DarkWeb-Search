function updateSuggestions() {
    const input = document.getElementById("searchQuery");
    const suggestionsList = document.getElementById("suggestions");
    const prefix = input.value.trim();

    if (prefix.length === 0) {
        suggestionsList.innerHTML = "";
        suggestionsList.classList.add('hidden');
        return;
    }

    // Get the current context (last few words) for better AI suggestions
    const context = input.value;

    fetch(`/suggest?prefix=${encodeURIComponent(prefix)}&context=${encodeURIComponent(context)}`)
        .then(response => response.json())
        .then(data => {
            suggestionsList.innerHTML = "";
            if (data.error) {
                console.error("Error fetching suggestions:", data.error);
                return;
            }

            if (data.suggestions && data.suggestions.length > 0) {
                suggestionsList.classList.remove('hidden');
                data.suggestions.forEach(suggestion => {
                    const li = document.createElement("div");
                    li.className = "suggestion-item p-3 text-gray-300 border-b border-cyan-500/10 last:border-0";
                    li.innerHTML = `
                        <div class="flex items-center justify-between">
                            <span class="font-mono">${suggestion}</span>
                            ${data.is_ai_powered ? `
                                <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                    AI
                                </span>
                            ` : ''}
                        </div>
                    `;
                    li.addEventListener("click", () => {
                        input.value = suggestion;
                        suggestionsList.classList.add('hidden');
                    });
                    suggestionsList.appendChild(li);
                });
            } else {
                suggestionsList.classList.add('hidden');
            }
        })
        .catch(error => {
            console.error("Error fetching suggestions:", error);
            suggestionsList.classList.add('hidden');
        });
} 