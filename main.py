from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

# CONFIGURAÇÕES REPLICADAS DO ESP32
DWELL_US = 3000
MAX_RPM = 11000

# MAPA DE AVANÇO ORIGINAL
rpmMap = [1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000]
advanceMap = [12.0, 18.0, 22.0, 25.0, 26.0, 25.0, 20.0, 16.0]

def get_advance_from_map(rpm):
    if rpm <= rpmMap[0]:
        return advanceMap[0]
    if rpm >= rpmMap[-1]:
        return advanceMap[-1]
        
    for i in range(len(rpmMap) - 1):
        if rpmMap[i] <= rpm <= rpmMap[i+1]:
            ratio = (rpm - rpmMap[i]) / (rpmMap[i+1] - rpmMap[i])
            return advanceMap[i] + ratio * (advanceMap[i+1] - advanceMap[i])
    return advanceMap[0]

# INTERFACE INTERATIVA (HTML + CSS + JS)
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador CDI - Motor 2T</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background-color: #0d1117;
            color: #c9d1d9;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
            position: relative;
        }

        /* Imagem de fundo do motor 2T translúcido */
        body::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://unsplash.com');
            background-size: cover;
            background-position: center;
            opacity: 0.12; /* Deixa o fundo meio translúcido */
            z-index: 1;
        }

        .container {
            position: relative;
            z-index: 2;
            background: rgba(22, 27, 34, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(48, 54, 61, 0.8);
            border-radius: 16px;
            padding: 30px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }

        h1 {
            font-size: 1.8rem;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .control-group {
            margin-bottom: 25px;
        }

        label {
            display: block;
            font-size: 1rem;
            margin-bottom: 8px;
            color: #8b949e;
        }

        .rpm-display {
            font-size: 2rem;
            font-weight: bold;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 10px;
            font-family: monospace;
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #30363d;
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #58a6ff;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(88, 166, 255, 0.5);
        }

        .results {
            background: rgba(1, 4, 9, 0.6);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #30363d;
        }

        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            font-size: 0.95rem;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .label {
            color: #8b949e;
        }

        .value {
            font-weight: bold;
            color: #f0883e;
            font-family: monospace;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-running { background: #238636; color: white; }
        .status-limit { background: #da3633; color: white; }
    </style>
</head>
<body>

    <div class="container">
        <h1>Simulador CDI (2 Tempos)</h1>
        
        <div class="control-group">
            <label for="rpmSlider">Controle de Giro (RPM):</label>
            <div class="rpm-display" id="rpmValue">1000 RPM</div>
            <input type="range" id="rpmSlider" min="500" max="12000" step="100" value="1000">
        </div>

        <div class="results">
            <div class="result-item">
                <span class="label">Status do Motor:</span>
                <span id="status" class="status-badge status-running">MOTOR RODANDO</span>
            </div>
            <div class="result-item">
                <span class="label">Avanço Calculado:</span>
                <span class="value" id="avanco">--</span>
            </div>
            <div class="result-item">
                <span class="label">Tempo de 1 Volta:</span>
                <span class="value" id="tempoVolta">--</span>
            </div>
            <div class="result-item">
                <span class="label">Espera da Ignição:</span>
                <span class="value" id="tempoEspera">--</span>
            </div>
            <div class="result-item">
                <span class="label">Dwell (Carga Bobina):</span>
                <span class="value" id="dwell">--</span>
            </div>
        </div>
    </div>

    <script>
        const slider = document.getElementById('rpmSlider');
        const rpmValue = document.getElementById('rpmValue');
        
        function atualizarDados(rpm) {
            rpmValue.innerText = rpm + " RPM";
            
            // Faz a requisição em tempo real para a sua rota de simulação
            fetch(`/simular?rpm=${rpm}`)
                .then(response => response.json())
                .then(data => {
                    const statusEl = document.getElementById('status');
                    statusEl.innerText = data.status;
                    
                    if (data.status === "LIMITADOR ATIVO") {
                        statusEl.className = "status-badge status-limit";
                        document.getElementById('avanco').innerText = "CORTE";
                        document.getElementById('tempoVolta').innerText = "-------";
                        document.getElementById('tempoEspera').innerText = "-------";
                        document.getElementById('dwell').innerText = "-------";
                    } else {
                        statusEl.className = "status-badge status-running";
                        document.getElementById('avanco').innerText = data.avanco_calculado_graus + "°";
                        document.getElementById('tempoVolta').innerText = data.tempo_de_uma_volta_us + " µs";
                        document.getElementById('tempoEspera').innerText = data.tempo_espera_ignicao_us + " µs";
                        document.getElementById('dwell').innerText = data.tempo_carga_bobina_dwell_us + " µs";
                    }
                });
        }

        // Escuta as mudanças no controle deslizante
        slider.addEventListener('input', (e) => atualizarDados(e.target.value));
        
        // Carrega os dados iniciais
        atualizarDados(slider.value);
    </script>
</body>
</html>
"""

# AGORA A PÁGINA INICIAL RETORNA A INTERFACE VISUAL
@app.route('/', methods=['GET'])
def pagina_inicial():
    return render_template_string(HTML_INTERFACE)

# ROTA DO SIMULADOR (Continua igual para servir os dados ao HTML)
@app.route('/simular', methods=['GET'])
def simular_ignicao():
    rpm = request.args.get('rpm', default=1000, type=int)
    kill_switch = request.args.get('kill', default='false', type=str).lower() == 'true'

    if kill_switch:
        return jsonify({"status": "CORTE ATIVADO", "ignicao": False, "motivo": "Kill Switch Pressionado"})

    if rpm >= MAX_RPM:
        return jsonify({"status": "LIMITADOR ATIVO", "ignicao": False, "rpm": rpm, "motivo": "Giro Máximo Excedido"})

    if rpm <= 0:
        return jsonify({"status": "MOTOR DESLIGADO", "ignicao": False, "rpm": rpm})

    periodo_us = 60000000 / rpm
    avanco_graus = get_advance_from_map(rpm)
    
    avanco_us = (avanco_graus / 360.0) * periodo_us
    atraso_centelha_us = periodo_us - avanco_us

    if atraso_centelha_us < 80:
        atraso_centelha_us = 80

    return jsonify({
        "status": "MOTOR RODANDO",
        "ignicao": True,
        "rpm_atual": rpm,
        "avanco_calculado_graus": round(avanco_graus, 2),
        "tempo_de_uma_volta_us": round(periodo_us, 0),
        "tempo_espera_ignicao_us": round(atraso_centelha_us, 0),
        "tempo_carga_bobina_dwell_us": DWELL_US
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
