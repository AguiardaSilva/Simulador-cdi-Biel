from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

# CONFIGURAÇÕES REPLICADAS DO ESP32
DWELL_US = 3000
MAX_RPM = 11000

# BANCO DE DADOS DE MAPAS PARA MOTOR 2T 190cc (ARRANCADA)
MAPAS_COMBUSTIVEL = {
    "gasolina": {
        "rpm": [1000, 3000, 5000, 7000, 9000, 11000],
        "avanco": [15.0, 24.0, 26.0, 25.0, 20.0, 16.0]
    },
    "etanol": {
        "rpm": [1000, 3000, 5000, 7000, 9000, 11000],
        "avanco": [16.0, 26.0, 29.0, 28.0, 23.0, 19.0]
    },
    "metanol": {
        "rpm": [1000, 3000, 5000, 7000, 9000, 11000],
        "avanco": [16.0, 26.0, 30.0, 29.0, 24.0, 20.0]
    },
    "nitrometano": {
        "rpm": [1000, 3000, 5000, 7000, 9000, 11000],
        "avanco": [14.0, 22.0, 25.0, 24.0, 18.0, 14.0]
    }
}

def get_advance_from_map(rpm, combustivel):
    mapa = MAPAS_COMBUSTIVEL.get(combustivel, MAPAS_COMBUSTIVEL["gasolina"])
    rpmMap = mapa["rpm"]
    advanceMap = mapa["avanco"]

    # Proteção para rotações abaixo do mínimo do mapa
    if rpm <= rpmMap[0]:
        return advanceMap[0]

    # Proteção para rotações acima do máximo do mapa
    if rpm >= rpmMap[-1]:
        return advanceMap[-1]

    for i in range(len(rpmMap) - 1):
        if rpmMap[i] <= rpm <= rpmMap[i + 1]:
            # Interpolação linear idêntica ao algoritmo em C++ do ESP32
            ratio = (rpm - rpmMap[i]) / (rpmMap[i + 1] - rpmMap[i])
            return advanceMap[i] + ratio * (advanceMap[i + 1] - advanceMap[i])

    return advanceMap[0]


# INTERFACE INTERATIVA INTEGRADA
HTML_INTERFACE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador CDI - Protótipo Arrancada 2T</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
            padding: 20px;
            line-height: 1.5;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            font-size: 1.8rem;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #58a6ff, #f0883e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            text-align: center;
            color: #8b949e;
            font-size: 0.95rem;
            margin-bottom: 28px;
        }

        .panel {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .panel h2 {
            font-size: 1.1rem;
            margin-bottom: 16px;
            color: #e6edf3;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .fuel-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }

        .fuel-btn {
            background: #21262d;
            border: 2px solid #30363d;
            border-radius: 10px;
            padding: 14px 10px;
            color: #8b949e;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            font-size: 0.95rem;
            font-weight: 500;
        }

        .fuel-btn .icon {
            font-size: 1.6rem;
        }

        .fuel-btn:hover {
            border-color: #8b949e;
            color: #c9d1d9;
            transform: translateY(-2px);
        }

        .fuel-btn.active[data-fuel="gasolina"] {
            background: rgba(240, 136, 62, 0.15);
            border-color: #f0883e;
            color: #f0883e;
            box-shadow: 0 0 12px rgba(240,136,62,0.25);
        }

        .fuel-btn.active[data-fuel="etanol"] {
            background: rgba(88, 166, 255, 0.15);
            border-color: #58a6ff;
            color: #58a6ff;
            box-shadow: 0 0 12px rgba(88,166,255,0.25);
        }

        .fuel-btn.active[data-fuel="metanol"] {
            background: rgba(53, 194, 91, 0.15);
            border-color: #35c25b;
            color: #35c25b;
            box-shadow: 0 0 12px rgba(53,194,91,0.25);
        }

        .fuel-btn.active[data-fuel="nitrometano"] {
            background: rgba(218, 54, 51, 0.15);
            border-color: #da3633;
            color: #da3633;
            box-shadow: 0 0 12px rgba(218,54,51,0.25);
        }

        .controls {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 20px;
            align-items: end;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .input-group label {
            font-size: 0.9rem;
            color: #8b949e;
        }

        .input-group input[type="range"] {
            width: 100%;
            height: 8px;
            -webkit-appearance: none;
            background: #30363d;
            border-radius: 4px;
            outline: none;
        }

        .input-group input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 22px;
            height: 22px;
            background: #58a6ff;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(88,166,255,0.5);
        }

        .rpm-display {
            font-size: 2.4rem;
            font-weight: 700;
            color: #58a6ff;
            text-align: center;
            min-width: 160px;
        }

        .rpm-display span {
            font-size: 1rem;
            color: #8b949e;
            font-weight: 400;
        }

        .result-box {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }

        .result-card {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
        }

        .result-card .label {
            font-size: 0.85rem;
            color: #8b949e;
            margin-bottom: 6px;
        }

        .result-card .value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #e6edf3;
        }

        .result-card .value.advance {
            color: #f0883e;
        }

        .chart-container {
            position: relative;
            height: 340px;
            margin-top: 10px;
        }

        .info {
            font-size: 0.85rem;
            color: #8b949e;
            margin-top: 12px;
            text-align: center;
        }

        @media (max-width: 600px) {
            .controls {
                grid-template-columns: 1fr;
            }
            .rpm-display {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Biel CDI Drag-Sim</h1>
        <p class="subtitle">Simulador de Avanço de Ignição • Motor 2T 190cc Arrancada</p>

        <div class="panel">
            <h2>⛽ Combustível Alvo (Parâmetros 2T)</h2>
            <div class="fuel-selector">
                <button class="fuel-btn active" data-fuel="gasolina" onclick="selecionarCombustivel('gasolina')">
                    <span class="icon">⛽</span>
                    <span>Gasolina</span>
                </button>
                <button class="fuel-btn" data-fuel="etanol" onclick="selecionarCombustivel('etanol')">
                    <span class="icon">🌽</span>
                    <span>Etanol</span>
                </button>
                <button class="fuel-btn" data-fuel="metanol" onclick="selecionarCombustivel('metanol')">
                    <span class="icon">🧪</span>
                    <span>Metanol</span>
                </button>
                <button class="fuel-btn" data-fuel="nitrometano" onclick="selecionarCombustivel('nitrometano')">
                    <span class="icon">💥</span>
                    <span>Nitrometano</span>
                </button>
            </div>
        </div>

        <div class="panel">
            <h2>🔄 Rotação do Motor</h2>
            <div class="controls">
                <div class="input-group">
                    <label for="rpmSlider">RPM (1000 — 11000)</label>
                    <input type="range" id="rpmSlider" min="1000" max="11000" step="50" value="5000"
                           oninput="atualizarRPM(this.value)">
                </div>
                <div class="rpm-display">
                    <span id="rpmValue">5000</span> <span>RPM</span>
                </div>
            </div>

            <div class="result-box">
                <div class="result-card">
                    <div class="label">Avanço de Ignição</div>
                    <div class="value advance" id="advanceValue">-- °</div>
                </div>
                <div class="result-card">
                    <div class="label">Combustível Atual</div>
                    <div class="value" id="fuelName">Gasolina</div>
                </div>
                <div class="result-card">
                    <div class="label">Dwell (fix32)</div>
                    <div class="value">3000 µs</div>
                </div>
            </div>
        </div>

        <div class="panel">
            <h2>📈 Curva de Avanço (Mapa Atual)</h2>
            <div class="chart-container">
                <canvas id="advanceChart"></canvas>
            </div>
            <p class="info">Interpolação linear idêntica ao algoritmo C++ do ESP32 • MAX_RPM = 11000</p>
        </div>
    </div>

    <script>
        let combustivelAtual = 'gasolina';
        let chart = null;

        const nomesCombustivel = {
            gasolina: 'Gasolina',
            etanol: 'Etanol',
            metanol: 'Metanol',
            nitrometano: 'Nitrometano'
        };

        function selecionarCombustivel(fuel) {
            combustivelAtual = fuel;
            document.querySelectorAll('.fuel-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.fuel === fuel);
            });
            document.getElementById('fuelName').textContent = nomesCombustivel[fuel];
            atualizarTudo();
        }

        function atualizarRPM(val) {
            document.getElementById('rpmValue').textContent = val;
            buscarAvanco(val);
        }

        async function buscarAvanco(rpm) {
            try {
                const res = await fetch(`/api/advance?rpm=${rpm}&combustivel=${combustivelAtual}`);
                const data = await res.json();
                document.getElementById('advanceValue').textContent = data.avanco.toFixed(1) + ' °';
            } catch (e) {
                document.getElementById('advanceValue').textContent = 'Erro';
            }
        }

        async function atualizarTudo() {
            const rpm = document.getElementById('rpmSlider').value;
            await buscarAvanco(rpm);
            await atualizarGrafico();
        }

        async function atualizarGrafico() {
            try {
                const res = await fetch(`/api/mapa?combustivel=${combustivelAtual}`);
                const data = await res.json();

                const ctx = document.getElementById('advanceChart').getContext('2d');

                if (chart) chart.destroy();

                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.rpm,
                        datasets: [{
                            label: 'Avanço (°)',
                            data: data.avanco,
                            borderColor: getCorCombustivel(combustivelAtual),
                            backgroundColor: getCorCombustivel(combustivelAtual) + '33',
                            borderWidth: 3,
                            tension: 0.3,
                            pointRadius: 5,
                            pointHoverRadius: 8,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: ctx => `Avanço: ${ctx.parsed.y.toFixed(1)}°`
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'RPM', color: '#8b949e' },
                                ticks: { color: '#8b949e' },
                                grid: { color: '#21262d' }
                            },
                            y: {
                                title: { display: true, text: 'Avanço (°)', color: '#8b949e' },
                                ticks: { color: '#8b949e' },
                                grid: { color: '#21262d' },
                                min: 10,
                                max: 35
                            }
                        }
                    }
                });
            } catch (e) {
                console.error(e);
            }
        }

        function getCorCombustivel(fuel) {
            const cores = {
                gasolina: '#f0883e',
                etanol: '#58a6ff',
                metanol: '#35c25b',
                nitrometano: '#da3633'
            };
            return cores[fuel] || '#58a6ff';
        }

        // Inicialização
        document.addEventListener('DOMContentLoaded', () => {
            atualizarTudo();
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)


@app.route('/api/advance')
def api_advance():
    try:
        rpm = float(request.args.get('rpm', 5000))
        combustivel = request.args.get('combustivel', 'gasolina')
        avanco = get_advance_from_map(rpm, combustivel)
        return jsonify({
            "rpm": rpm,
            "combustivel": combustivel,
            "avanco": round(avanco, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/mapa')
def api_mapa():
    combustivel = request.args.get('combustivel', 'gasolina')
    mapa = MAPAS_COMBUSTIVEL.get(combustivel, MAPAS_COMBUSTIVEL["gasolina"])
    return jsonify(mapa)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
