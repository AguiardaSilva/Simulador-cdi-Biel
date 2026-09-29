from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

# CONFIGURAÇÕES REPLICADAS DO ESP32
DWELL_US = 3000
MAX_RPM = 11000

# BANCO DE DADOS DE MAPAS PARA MOTOR 2T 190cc (ARRANCADA)
MAPAS_COMBUSTIVEL = {
    "gasolina": {
        "rpm":,
        "avanco": [15.0, 24.0, 26.0, 25.0, 20.0, 16.0]
    },
    "etanol": {
        "rpm":,
        "avanco": [16.0, 26.0, 29.0, 28.0, 23.0, 19.0]
    },
    "metanol": {
        "rpm":,
        "avanco": [16.0, 26.0, 30.0, 29.0, 24.0, 20.0]
    },
    "nitrometano": {
        "rpm":,
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
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #121214;
            color: #e1e1e6;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            max-width: 480px;
            width: 100%;
            background: #202024;
            padding: 35px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
            border: 1px solid #29292e;
        }
        h1 { 
            color: #00b37e; 
            margin-bottom: 25px; 
            font-size: 22px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        label { 
            display: block; 
            margin: 18px 0 6px; 
            text-align: left;
            font-size: 14px;
            color: #c4c4cc;
        }
        select, input {
            width: 100%;
            padding: 14px;
            background: #121214;
            border: 1px solid #29292e;
            color: #fff;
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #00b37e;
        }
        button {
            width: 100%;
            padding: 16px;
            background: #00b37e;
            color: white;
            border: none;
            border-radius: 6px;
            margin-top: 30px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            transition: background 0.2s;
        }
        button:hover { 
            background: #00875f; 
        }
        .resultado {
            margin-top: 30px;
            padding: 20px;
            background: #29292e;
            border-radius: 8px;
            font-size: 18px;
            text-align: center;
            display: none;
            border: 1px dashed #00b37e;
        }
        span { 
            color: #00b37e; 
            font-weight: bold; 
            font-size: 24px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Simulador CDI - Arrancada 2T</h1>
        
        <label for="combustivel">Combustível Selecionado:</label>
        <select id="combustivel">
            <option value="gasolina">Gasolina</option>
            <option value="etanol">Etanol</option>
            <option value="metanol">Metanol</option>
            <option value="nitrometano">Nitrometano</option>
        </select>

        <label for="rpm">Rotação Atual do Motor (RPM):</label>
        <input type="number" id="rpm" value="5000" min="0" max="11000">

        <button onclick="calcularAvanco()">Calcular Avanço do Ponto</button>

        <div id="resultado" class="resultado">
            Avanço calculado: <span id="graus">0</span>°
        </div>
    </div>

    <script>
        function calcularAvanco() {
            const rpmInput = document.getElementById('rpm').value;
            const combustivelInput = document.getElementById('combustivel').value;

            if (!rpmInput || rpmInput < 0) {
                alert('Por favor, insira um valor válido de RPM.');
                return;
            }

            fetch('/api/calcular', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rpm: parseFloat(rpmInput), combustivel: combustivelInput })
            })
            .then(res => {
                if (!res.ok) throw new Error();
                return res.json();
            })
            .then(data => {
                document.getElementById('graus').innerText = data.avanco_graus.toFixed(2);
                document.getElementById('resultado').style.display = 'block';
            })
            .catch(err => {
                alert('Erro ao processar cálculo no servidor.');
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_INTERFACE)

@app.route('/api/calcular', methods=['POST'])
def calcular():
    dados = request.get_json() or {}
    rpm = dados.get('rpm', 1000)
    combustivel = dados.get('combustivel', 'gasolina')
    
    avanco = get_advance_from_map(rpm, combustivel)
    return jsonify({"avanco_graus": avanco})

if __name__ == "__main__":
    # Configuração de escuta obrigatória do Railway utilizando a variável de ambiente PORT
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
