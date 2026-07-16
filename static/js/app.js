/* ==========================================================================
   SPARKMARG CORE SIMULATION ENGINE
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Application State
    const state = {
        simulationId: null,
        currentStep: 0,
        metrics: {
            technical_skill: 50,
            industry_knowledge: 50,
            professional_network: 50,
            adaptability: 50
        },
        history: []
    };

    // DOM Elements Cache
    const elements = {
        startContainer: document.getElementById('start-container'),
        simContainer: document.getElementById('simulation-container'),
        scenarioText: document.getElementById('scenario-text'),
        choicesGrid: document.getElementById('choices-grid'),
        startBtn: document.getElementById('start-sim-btn'),
        careerTrackSelect: document.getElementById('career-track'),
        // Metrics Progress Bars
        techBar: document.getElementById('bar-tech'),
        indBar: document.getElementById('bar-ind'),
        netBar: document.getElementById('bar-net'),
        adaptBar: document.getElementById('bar-adapt')
    };

    // Initialize Event Listeners
    if (elements.startBtn) {
        elements.startBtn.addEventListener('click', initializeSimulation);
    }

    /**
     * Bootstraps a new career simulation path
     */
    async function initializeSimulation() {
        const trackId = elements.careerTrackSelect.value;
        
        try {
            const response = await fetch('/api/simulation/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ track_id: trackId })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                state.simulationId = data.simulation_id;
                state.metrics = data.initial_metrics;
                
                // Smooth Layout Transition
                elements.startContainer.classList.add('d-none');
                elements.simContainer.classList.remove('d-none');
                elements.simContainer.classList.add('fade-in');
                
                updateMetricsUI();
                renderNode(data.first_node);
            } else {
                console.error('Initialization Failed:', data.error);
            }
        } catch (error) {
            console.error('Network error during initialization:', error);
        }
    }

    /**
     * Renders a specific active simulation node and choices
     * @param {Object} node - Contains scenario metadata and option array
     */
    function renderNode(node) {
        state.currentStep++;
        
        // Render core narrative text with slide-up profile
        elements.scenarioText.innerHTML = `
            <div class="slide-up">
                <span class="badge bg-indigo-soft text-indigo mb-2">Decision Point #${state.currentStep}</span>
                <p class="lead text-white fw-medium">${node.narrative}</p>
            </div>
        `;
        
        // Clear previous interactions
        elements.choicesGrid.innerHTML = '';
        
        // Build choice nodes with staggered animation layout
        node.options.forEach((option, index) => {
            const choiceBtn = document.createElement('button');
            choiceBtn.className = `btn btn-outline-custom text-start p-3 w-100 hover-lift choice-click-effect slide-up delay-${index + 1}`;
            choiceBtn.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="choice-index-marker me-3">${String.fromCharCode(65 + index)}</div>
                    <div class="flex-grow-1">
                        <p class="mb-1 text-white fw-semibold">${option.text}</p>
                        <small class="text-muted d-block">${option.context_hint || 'Evaluate the trade-offs of this action.'}</small>
                    </div>
                </div>
            `;
            
            choiceBtn.addEventListener('click', () => handleChoiceSelection(option.id));
            elements.choicesGrid.appendChild(choiceBtn);
        });
    }

    /**
     * Submits selected path and processes consequence payload
     * @param {string} optionId - Selected option node ID
     */
    async function handleChoiceSelection(optionId) {
        // Add visual loading feedback while locking further input
        elements.choicesGrid.querySelectorAll('button').forEach(btn => btn.disabled = true);
        
        try {
            const response = await fetch('/api/simulation/submit-choice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: state.simulationId,
                    option_id: optionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Mutate internal state tracking
                state.metrics = data.updated_metrics;
                state.history.push(optionId);
                
                // Animate metric tracking nodes
                updateMetricsUI();
                
                if (data.is_terminal) {
                    renderEndingNode(data.outcome);
                } else {
                    renderNode(data.next_node);
                }
            }
        } catch (error) {
            console.error('Error recording simulation progress:', error);
            elements.choicesGrid.querySelectorAll('button').forEach(btn => btn.disabled = false);
        }
    }

    /**
     * Updates profile metrics progress tracking components
     */
    function updateMetricsUI() {
        const updateBar = (bar, val) => {
            if (bar) {
                bar.style.width = `${val}%`;
                bar.setAttribute('aria-valuenow', val);
            }
        };

        updateBar(elements.techBar, state.metrics.technical_skill);
        updateBar(elements.indBar, state.metrics.industry_knowledge);
        updateBar(elements.netBar, state.metrics.professional_network);
        updateBar(elements.adaptBar, state.metrics.adaptability);
    }

    /**
     * Renders terminal state evaluation summary
     * @param {Object} outcome - Final trajectory breakdown data
     */
    function renderEndingNode(outcome) {
        elements.scenarioText.innerHTML = `
            <div class="slide-up text-center py-4">
                <div class="mb-3">✨</div>
                <h3 class="text-indigo-gradient fw-bold mb-2">Simulation Complete!</h3>
                <h4 class="text-white mb-3">${outcome.title}</h4>
                <p class="text-muted max-w-2xl mx-auto">${outcome.analysis}</p>
            </div>
        `;
        
        elements.choicesGrid.innerHTML = `
            <div class="col-12 text-center slide-up delay-2">
                <button class="btn btn-indigo px-5 py-3 hover-lift fw-bold" onclick="window.location.reload()">
                    Run Another Path
                </button>
            </div>
        `;
    }
});