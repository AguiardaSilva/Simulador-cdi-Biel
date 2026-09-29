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

    if rpm <= rpmMap[0]:
        return advanceMap[0]
    if rpm >= rpmMap[-1]:
        return advanceMap[-1]

    for i in range(len(rpmMap) - 1):
        if rpmMap[i] <= rpm <= rpmMap[i + 1]:
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
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #121214;
            color: #e1e1e6;
            padding: 40px;
            text-align: center;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: #202024;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
        h1 { color: #00b37e; margin-bottom: 20px; font-size: 24px; }
        label { display: block; margin: 15px 0 5px; text-align: left; }
        select, input {
            width: 100%;
            padding: 12px;
            background: #121214;
            border: 1px solid #29292e;
            color: #fff;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #00b37e;
            color: white;
            border: none;
            border-radius: 4px;
            margin-top: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { background: #00875f; }
        .resultado {
            margin-top: 25px;
            padding: 15px;
            background: #29292e;
            border-radius: 4px;
            font-size: 18px;
            display: none;
        }
        span { color: #00b37e; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Simulador CDI - Arrancada 2T 190cc</h1>
        
        <label for="combustivel">Combustível:</label>
        <select id="combustivel">
            <option value="gasolina">Gasolina</option>
            <option value="etanol">Etanol</option>
            <option value="metanol">Metanol</option>
            <option value="nitrometano">Nitrometano</option>
        </select>

        <label for="rpm">Rotação Atual (RPM):</label>
        <input type="number" id="rpm" value="5000" min="0" max="11000">

        <button onclick="calcularAvanco()">Calcular Avanço</button>

        <div id="resultado" class="resultado">
            O avanço do ponto é de: <span id="graus">0</span>°
        </div>
    </div>

    <script>
        function calcularAvanco() {
            const rpm = document.getElementById('rpm').value;
            const combustivel = document.getElementById('combustivel').value;

            fetch('/api/calcular', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rpm: parseFloat(rpm), combustivel: combustivel })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('graus').innerText = data.avanco_graus.toFixed(2);
                document.getElementById('resultado').style.display = 'block';
            })
            .catch(err => alert('Erro ao conectar com o simulador.'));
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
    dados = request.get_json()
    rpm = dados.get('rpm', 1000)
    combustivel = dados.get('combustivel', 'gasolina')
    
    avanco = get_advance_from_map(rpm, combustivel)
    return jsonify({"avanco_graus": avanco})

if __name__ == "__main__":
    # O Railway exige que o app use a porta injetada dinamicamente pelo servidor deles
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
